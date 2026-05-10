from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ApiChannel, ChannelRoute, ContentItem, ContentPage, ContentSection, ModelConfig, Tenant, ToolModelBinding, User, Wallet
from app.services.auth import hash_password


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_admin(session, *, tenant_id="tenant-a") -> None:
    session.add_all(
        [
            Tenant(id=tenant_id, slug=tenant_id, name="Tenant A"),
            User(
                id="admin-a",
                tenant_id=tenant_id,
                phone="13900000000",
                display_name="管理员",
                role="ADMIN",
                password_hash=hash_password("admin123456"),
            ),
        ]
    )
    session.commit()


def login_admin(client: TestClient, tenant_id: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"phone": "13900000000", "password": "admin123456"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(client: TestClient, tenant_id: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {login_admin(client, tenant_id)}"}


def test_admin_manages_channels_models_and_bindings_with_masked_api_keys(session):
    seed_admin(session)
    client = make_client(session)
    headers = auth_headers(client, "tenant-a")

    channel_response = client.post(
        "/api/v1/admin/provider-channels",
        headers=headers,
        json={
            "channel_key": "openai-image",
            "display_name": "OpenAI 图片渠道",
            "base_url": "https://api.openai.example/v1/images",
            "api_key": "sk-secret-1234",
            "channel_type": "IMAGE",
            "priority": 5,
            "enabled": True,
        },
    )

    assert channel_response.status_code == 201
    channel_payload = channel_response.json()
    assert channel_payload["api_key_mask"] == "****1234"
    assert "sk-secret" not in str(channel_payload)

    channel_id = channel_payload["id"]
    update_response = client.put(
        f"/api/v1/admin/provider-channels/{channel_id}",
        headers=headers,
        json={"display_name": "OpenAI 主图渠道", "api_key": ""},
    )

    assert update_response.status_code == 200
    assert session.get(ApiChannel, channel_id).api_key == "sk-secret-1234"
    assert update_response.json()["display_name"] == "OpenAI 主图渠道"
    assert update_response.json()["api_key_mask"] == "****1234"

    model_response = client.post(
        "/api/v1/admin/model-configs",
        headers=headers,
        json={
            "model_key": "image_text_to_image",
            "display_name": "GPT Image 2",
            "capability": "IMAGE",
            "channel_id": channel_id,
            "provider_model": "gpt-image-2",
            "default_point_cost": 120,
            "enabled": True,
        },
    )

    assert model_response.status_code == 201
    model_payload = model_response.json()
    assert model_payload["default_point_cost"] == 120
    route = session.query(ChannelRoute).filter_by(tenant_id="tenant-a", route_key="image_text_to_image").one()
    assert route.backend_model == "gpt-image-2"
    assert route.unit_cost == 120

    binding_response = client.post(
        "/api/v1/admin/tool-model-bindings",
        headers=headers,
        json={
            "target_type": "builtin",
            "target_key": "image_text_to_image",
            "model_config_id": model_payload["id"],
            "point_cost_override": 45,
            "enabled": True,
        },
    )

    assert binding_response.status_code == 201
    assert binding_response.json()["effective_point_cost"] == 45


def test_portal_payload_includes_bound_model_and_effective_cost(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    channel = ApiChannel(
        id="channel-image",
        tenant_id=tenant.id,
        channel_key="openai-image",
        display_name="OpenAI 图片渠道",
        base_url="https://api.openai.example/v1/images",
        api_key="secret",
        channel_type="IMAGE",
        enabled=True,
    )
    model = ModelConfig(
        id="model-image",
        tenant_id=tenant.id,
        model_key="image_text_to_image",
        display_name="GPT Image 2",
        capability="IMAGE",
        channel_id=channel.id,
        provider_model="gpt-image-2",
        default_point_cost=120,
        enabled=True,
    )
    page = ContentPage(id="page-home", tenant_id=tenant.id, page_key="home", label="首页", title="首页", enabled=True)
    section = ContentSection(id="section-tools", tenant_id=tenant.id, area="home", section_key="tools", title="工具", enabled=True)
    item = ContentItem(
        id="item-image",
        tenant_id=tenant.id,
        section_id=section.id,
        item_type="tool",
        title="图片生成",
        action_type="workspace",
        action_value="image_text_to_image",
        enabled=True,
    )
    binding = ToolModelBinding(
        id="binding-image",
        tenant_id=tenant.id,
        target_type="content_item",
        target_key=item.id,
        model_config_id=model.id,
        point_cost_override=45,
        enabled=True,
    )
    session.add_all([tenant, channel, model, page, section, item, binding])
    session.commit()
    client = make_client(session)

    response = client.get("/api/v1/portal/pages/home", headers={"X-Tenant-ID": tenant.id})

    assert response.status_code == 200
    payload = response.json()["sections"][0]["items"][0]
    assert payload["effective_point_cost"] == 45
    assert payload["model_config"]["model_key"] == "image_text_to_image"
    assert payload["model_config"]["provider_model"] == "gpt-image-2"


def test_image_generation_uses_bound_model_cost_and_ignores_legacy_route_key(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    user = User(id="demo-user", tenant_id=tenant.id, phone="13800000000", role="USER")
    wallet = Wallet(id="wallet-a", tenant_id=tenant.id, user_id=user.id, balance=1000, frozen_balance=0)
    channel = ApiChannel(
        id="channel-image",
        tenant_id=tenant.id,
        channel_key="openai-image",
        display_name="OpenAI 图片渠道",
        base_url="https://api.openai.example/v1/images",
        api_key="secret",
        channel_type="IMAGE",
        enabled=True,
    )
    session.add_all(
        [
            tenant,
            user,
            wallet,
            channel,
            ChannelRoute(
                id="route-bound",
                tenant_id=tenant.id,
                route_key="image_gpt_2",
                display_name="GPT Image 2",
                backend_model="gpt-image-2",
                channel_type="IMAGE",
                unit_cost=120,
                enabled=True,
            ),
            ChannelRoute(
                id="route-untrusted",
                tenant_id=tenant.id,
                route_key="expensive_route",
                display_name="Expensive",
                backend_model="expensive",
                channel_type="IMAGE",
                unit_cost=999,
                enabled=True,
            ),
            ModelConfig(
                id="model-image",
                tenant_id=tenant.id,
                model_key="image_gpt_2",
                display_name="GPT Image 2",
                capability="IMAGE",
                channel_id=channel.id,
                provider_model="gpt-image-2",
                default_point_cost=120,
                enabled=True,
            ),
            ToolModelBinding(
                id="binding-image",
                tenant_id=tenant.id,
                target_type="builtin",
                target_key="image_text_to_image",
                model_config_id="model-image",
                point_cost_override=45,
                enabled=True,
            ),
        ]
    )
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/image/generations",
        headers={"X-Tenant-ID": tenant.id},
        json={
            "prompt": "生成一张商品海报",
            "route_key": "expensive_route",
            "target_type": "builtin",
            "target_id": "image_text_to_image",
            "request_key": "image-bound-1",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["route_key"] == "image_gpt_2"
    assert payload["estimated_cost"] == 45
    assert wallet.balance == 955
    assert wallet.frozen_balance == 45

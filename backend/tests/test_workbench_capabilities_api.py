from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ApiChannel, ChannelRoute, ContentItem, ContentPage, ContentSection, ModelConfig, Tenant, ToolModelBinding, User
from app.services.auth import hash_password


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_admin_runtime(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="Admin",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    page = ContentPage(id="page-image", tenant_id=tenant.id, page_key="image", label="AI 图片", title="AI 图片", enabled=True)
    section = ContentSection(
        id="section-image-tools",
        tenant_id=tenant.id,
        area="image",
        section_key="tools",
        title="图片工具",
        layout="tool-grid",
        enabled=True,
    )
    item = ContentItem(
        id="image-tool-poster",
        tenant_id=tenant.id,
        section_id=section.id,
        item_type="tool",
        title="海报生成",
        action_type="workspace",
        action_value="image_action_poster",
        required_membership=True,
        point_cost=30,
        sort_order=8,
        enabled=True,
    )
    channel = ApiChannel(
        id="channel-image",
        tenant_id=tenant.id,
        channel_key="openai-image",
        display_name="OpenAI Image",
        base_url="https://api.openai.com/v1",
        api_key="sk-secret",
        channel_type="IMAGE",
        adapter_type="openai_compatible",
        enabled=True,
    )
    model = ModelConfig(
        id="model-image",
        tenant_id=tenant.id,
        model_key="image_text_to_image",
        display_name="GPT Image",
        capability="IMAGE",
        channel_id=channel.id,
        provider_model="gpt-image-1",
        default_point_cost=80,
        enabled=True,
    )
    route = ChannelRoute(
        id="route-image",
        tenant_id=tenant.id,
        route_key=model.model_key,
        display_name=model.display_name,
        backend_model=model.provider_model,
        channel_type="IMAGE",
        unit_cost=80,
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
    builtin_binding = ToolModelBinding(
        id="binding-builtin",
        tenant_id=tenant.id,
        target_type="builtin",
        target_key="image_action_poster",
        model_config_id=model.id,
        point_cost_override=50,
        enabled=True,
    )
    session.add_all([tenant, admin, page, section, item, channel, model, route, binding, builtin_binding])
    session.commit()


def login_admin(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"phone": "13900000000", "password": "admin123456"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_workbench_capabilities_expose_callable_managed_items(session):
    seed_admin_runtime(session)
    client = make_client(session)

    response = client.get("/api/v1/workbench/capabilities?surface=workbench", headers={"X-Tenant-ID": "tenant-a"})

    assert response.status_code == 200
    payload = response.json()
    image = payload["groups"]["image"][0]
    assert image["target_type"] == "content_item"
    assert image["target_key"] == "image-tool-poster"
    assert image["title"] == "海报生成"
    assert image["enabled"] is True
    assert image["callable"] is True
    assert image["unavailable_reason"] == ""
    assert image["required_membership"] is True
    assert image["effective_point_cost"] == 45
    assert image["model_config"]["provider_model"] == "gpt-image-1"


def test_admin_can_disable_workbench_capability_and_override_cost(session):
    seed_admin_runtime(session)
    client = make_client(session)
    token = login_admin(client)
    headers = {"X-Tenant-ID": "tenant-a", "Authorization": f"Bearer {token}"}

    patch = client.patch(
        "/api/v1/admin/workbench-capabilities",
        headers=headers,
        json={
            "target_type": "content_item",
            "target_key": "image-tool-poster",
            "enabled": False,
            "point_cost_override": 12,
        },
    )
    assert patch.status_code == 200
    assert patch.json()["enabled"] is False
    assert patch.json()["effective_point_cost"] == 12

    response = client.get("/api/v1/workbench/capabilities?surface=workbench", headers={"X-Tenant-ID": "tenant-a"})
    assert response.status_code == 200
    image = response.json()["groups"]["image"][0]
    assert image["enabled"] is False
    assert image["callable"] is False
    assert image["unavailable_reason"] == "capability disabled"


def test_disabled_channel_makes_capability_uncallable_without_hiding_management_record(session):
    seed_admin_runtime(session)
    session.get(ApiChannel, "channel-image").enabled = False
    session.commit()
    client = make_client(session)

    response = client.get("/api/v1/workbench/capabilities?surface=workbench", headers={"X-Tenant-ID": "tenant-a"})

    assert response.status_code == 200
    image = response.json()["groups"]["image"][0]
    assert image["enabled"] is True
    assert image["callable"] is False
    assert image["unavailable_reason"] == "provider channel disabled"


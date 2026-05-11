from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ContentItem, ContentPage, ContentSection, Tenant, User
from app.seed import ensure_demo_data
from app.services.auth import hash_password


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_admin(session, tenant_id: str = "tenant-a") -> None:
    session.add_all(
        [
            Tenant(id=tenant_id, slug=tenant_id, name="Tenant A"),
            User(
                id=f"admin-{tenant_id}",
                tenant_id=tenant_id,
                phone="13900000000",
                display_name="运营管理员",
                role="ADMIN",
                password_hash=hash_password("admin123456"),
            ),
        ]
    )
    session.commit()


def auth_headers(client: TestClient, tenant_id: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"phone": "13900000000", "password": "admin123456"},
    )
    assert response.status_code == 200
    return {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {response.json()['access_token']}"}


def seed_home_content(session, tenant_id: str = "tenant-a") -> None:
    page = ContentPage(
        id=f"page-home-{tenant_id}",
        tenant_id=tenant_id,
        page_key="home",
        label="首页",
        title="中文首页",
        subtitle="会员活动、工作台、社群和工具统一入口",
        icon="Home",
        sort_order=10,
        enabled=True,
    )
    workbench = ContentSection(
        id=f"section-workbench-{tenant_id}",
        tenant_id=tenant_id,
        area="home",
        section_key="workspace_tools",
        title="我的工作台",
        layout="tool-grid",
        sort_order=10,
        enabled=True,
    )
    communities = ContentSection(
        id=f"section-community-{tenant_id}",
        tenant_id=tenant_id,
        area="home",
        section_key="communities",
        title="社群框",
        layout="banner-row",
        sort_order=20,
        enabled=True,
    )
    tools = ContentSection(
        id=f"section-tools-{tenant_id}",
        tenant_id=tenant_id,
        area="home",
        section_key="toolkit",
        title="工具框",
        layout="template-list",
        sort_order=30,
        enabled=True,
    )
    session.add_all(
        [
            page,
            workbench,
            communities,
            tools,
            ContentItem(
                id=f"workbench-chat-{tenant_id}",
                tenant_id=tenant_id,
                section_id=workbench.id,
                item_type="tool",
                title="AI 对话",
                subtitle="写作、问答和方案梳理",
                category="应用工作台",
                icon="Bot",
                action_type="route",
                action_value="/workbench",
                sort_order=10,
                enabled=True,
            ),
            ContentItem(
                id=f"community-starter-{tenant_id}",
                tenant_id=tenant_id,
                section_id=communities.id,
                item_type="community",
                title="入门交流群",
                subtitle="新人答疑和工具清单",
                category="社群",
                icon="MessageCircle",
                action_type="route",
                action_value="/community/starter",
                sort_order=10,
                enabled=True,
                metadata_json={"menuKeys": ["basic", "growth"]},
            ),
            ContentItem(
                id=f"tool-quote-{tenant_id}",
                tenant_id=tenant_id,
                section_id=tools.id,
                item_type="template",
                title="接单报价",
                subtitle="快速生成报价单和交付边界",
                category="接单变现",
                icon="ReceiptText",
                action_type="route",
                action_value="/toolkit/quote",
                sort_order=10,
                enabled=True,
                metadata_json={"menuKeys": ["orders", "toolkit"]},
            ),
        ]
    )
    session.commit()


def test_home_dashboard_endpoint_returns_slides_and_core_blocks(session):
    seed_admin(session)
    seed_home_content(session)
    client = make_client(session)
    headers = auth_headers(client, "tenant-a")
    created = client.post(
        "/api/v1/admin/home-slides",
        headers=headers,
        json={
            "title": "会员活动限时特惠",
            "subtitle": "开通会员领取模板、社群和接单资料",
            "badge": "会员专享",
            "image_url": "/storage/home/vip.png",
            "cta_label": "立即开通",
            "action_type": "route",
            "action_value": "/membership/benefits",
            "sort_order": 10,
            "enabled": True,
            "metadata_json": {"accent": "gold", "secondaryLabel": "查看权益"},
        },
    )
    assert created.status_code == 201

    response = client.get("/api/v1/home/dashboard", headers={"X-Tenant-ID": "tenant-a"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant-a"
    assert payload["page"]["page_key"] == "home"
    assert payload["hero_slides"][0]["title"] == "会员活动限时特惠"
    assert payload["hero_slides"][0]["cta_label"] == "立即开通"
    assert payload["hero_slides"][0]["action_value"] == "/membership/benefits"
    assert [item["title"] for item in payload["workbench_shortcuts"]] == ["AI 对话"]
    assert payload["kpi_cards"][0]["label"] == "今日上新"
    assert payload["community_cards"][0]["menu_keys"] == ["basic", "growth"]
    assert payload["tool_cards"][0]["title"] == "接单报价"


def test_admin_home_slide_crud_reorder_and_tenant_isolation(session):
    seed_admin(session, "tenant-a")
    seed_admin(session, "tenant-b")
    client = make_client(session)
    headers_a = auth_headers(client, "tenant-a")
    headers_b = auth_headers(client, "tenant-b")

    first = client.post(
        "/api/v1/admin/home-slides",
        headers=headers_a,
        json={
            "title": "模板上新",
            "subtitle": "会员模板每周更新",
            "badge": "今日上新",
            "cta_label": "立即查看",
            "action_value": "/templates",
            "sort_order": 20,
        },
    ).json()
    second = client.post(
        "/api/v1/admin/home-slides",
        headers=headers_a,
        json={
            "title": "会员专享",
            "subtitle": "社群和资料限时开放",
            "badge": "会员专享",
            "cta_label": "查看权益",
            "action_value": "/membership/benefits",
            "sort_order": 10,
        },
    ).json()
    other_tenant = client.post(
        "/api/v1/admin/home-slides",
        headers=headers_b,
        json={
            "title": "租户B活动",
            "subtitle": "只属于租户B",
            "badge": "B",
            "cta_label": "查看",
            "action_value": "/b",
        },
    )
    assert other_tenant.status_code == 201

    ordered = client.get("/api/v1/admin/home-slides", headers=headers_a)
    assert ordered.status_code == 200
    assert [slide["id"] for slide in ordered.json()["slides"]] == [second["id"], first["id"]]

    reordered = client.post(
        "/api/v1/admin/home-slides/reorder",
        headers=headers_a,
        json={"ordered_ids": [first["id"], second["id"]]},
    )
    assert reordered.status_code == 200
    assert [slide["sort_order"] for slide in reordered.json()["slides"]] == [10, 20]

    updated = client.put(
        f"/api/v1/admin/home-slides/{first['id']}",
        headers=headers_a,
        json={"title": "模板上新升级", "enabled": False},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "模板上新升级"
    assert updated.json()["enabled"] is False

    public_payload = client.get("/api/v1/home/dashboard", headers={"X-Tenant-ID": "tenant-a"}).json()
    assert [slide["id"] for slide in public_payload["hero_slides"]] == [second["id"]]

    delete_response = client.delete(f"/api/v1/admin/home-slides/{second['id']}", headers=headers_a)
    assert delete_response.status_code == 200
    assert delete_response.json()["enabled"] is False

    isolated = client.get("/api/v1/admin/home-slides", headers=headers_b)
    assert [slide["title"] for slide in isolated.json()["slides"]] == ["租户B活动"]


def test_demo_seed_includes_home_dashboard_content(session):
    from app.models import HomeHeroSlide

    ensure_demo_data(session, tenant_id="demo")

    slides = session.query(HomeHeroSlide).filter_by(tenant_id="demo", enabled=True).all()
    assert len(slides) >= 3
    assert slides[0].title == "会员活动限时特惠"
    assert any(slide.action_value == "/membership/benefits" for slide in slides)
    assert session.query(ContentItem).filter_by(tenant_id="demo", action_value="/membership/benefits").count() >= 1

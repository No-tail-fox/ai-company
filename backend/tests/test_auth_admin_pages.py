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


def login_admin(client: TestClient, tenant_id: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"phone": "13900000000", "password": "admin123456"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_login_returns_jwt_and_user_profile(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="管理员",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    session.add_all([tenant, admin])
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13900000000", "password": "admin123456"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["role"] == "ADMIN"
    assert payload["user"]["phone"] == "13900000000"


def test_admin_pages_sections_and_items_are_managed_with_admin_token(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="管理员",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    session.add_all([tenant, admin])
    session.commit()
    client = make_client(session)

    unauthorized = client.post(
        "/api/v1/admin/pages",
        headers={"X-Tenant-ID": tenant.id},
        json={"page_key": "marketing", "label": "AI 营销", "title": "营销增长中心"},
    )
    assert unauthorized.status_code == 401

    token = login_admin(client, tenant.id)
    auth_headers = {"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {token}"}

    page_response = client.post(
        "/api/v1/admin/pages",
        headers=auth_headers,
        json={
            "page_key": "marketing",
            "label": "AI 营销",
            "title": "营销增长中心",
            "subtitle": "营销工具、模板与复盘数据",
            "icon": "Megaphone",
            "sort_order": 30,
            "enabled": True,
        },
    )
    assert page_response.status_code == 201
    assert page_response.json()["page_key"] == "marketing"

    section_response = client.post(
        "/api/v1/admin/sections",
        headers=auth_headers,
        json={
            "page_key": "marketing",
            "section_key": "tool_matrix",
            "title": "营销工具矩阵",
            "subtitle": "覆盖内容、投放和私域",
            "layout": "tool-grid",
            "sort_order": 10,
            "enabled": True,
        },
    )
    assert section_response.status_code == 201
    section_id = section_response.json()["id"]

    item_response = client.post(
        "/api/v1/admin/items",
        headers=auth_headers,
        json={
            "section_id": section_id,
            "item_type": "tool",
            "title": "爆款文案生成",
            "subtitle": "标题、卖点、脚本一键生成",
            "category": "内容营销",
            "icon": "Feather",
            "image_url": "",
            "sort_order": 10,
            "enabled": True,
            "action_type": "workspace",
            "action_value": "marketing-copy",
            "required_membership": True,
            "point_cost": 20,
        },
    )
    assert item_response.status_code == 201
    item_id = item_response.json()["id"]

    page_config = client.get("/api/v1/portal/pages/marketing", headers={"X-Tenant-ID": tenant.id}).json()
    assert page_config["page"]["title"] == "营销增长中心"
    assert page_config["sections"][0]["items"][0]["title"] == "爆款文案生成"

    delete_response = client.delete(f"/api/v1/admin/items/{item_id}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["enabled"] is False

    refreshed = client.get("/api/v1/portal/pages/marketing", headers={"X-Tenant-ID": tenant.id}).json()
    assert refreshed["sections"][0]["items"] == []


def test_admin_can_reorder_sections_and_items(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="管理员",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    section_a = ContentSection(
        id="section-a",
        tenant_id=tenant.id,
        area="home",
        section_key="a",
        title="模块A",
        sort_order=10,
        enabled=True,
    )
    section_b = ContentSection(
        id="section-b",
        tenant_id=tenant.id,
        area="home",
        section_key="b",
        title="模块B",
        sort_order=20,
        enabled=True,
    )
    session.add_all(
        [
            tenant,
            admin,
            ContentPage(
                id="page-home",
                tenant_id=tenant.id,
                page_key="home",
                label="首页",
                title="首页",
                sort_order=10,
                enabled=True,
            ),
            section_a,
            section_b,
            ContentItem(
                id="item-a",
                tenant_id=tenant.id,
                section_id=section_a.id,
                item_type="tool",
                title="卡片A",
                sort_order=10,
                enabled=True,
                action_value="a",
            ),
            ContentItem(
                id="item-b",
                tenant_id=tenant.id,
                section_id=section_a.id,
                item_type="tool",
                title="卡片B",
                sort_order=20,
                enabled=True,
                action_value="b",
            ),
        ]
    )
    session.commit()
    client = make_client(session)
    headers = {"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {login_admin(client, tenant.id)}"}

    section_response = client.post(
        "/api/v1/admin/sections/reorder",
        headers=headers,
        json={"ordered_ids": ["section-b", "section-a"]},
    )
    assert section_response.status_code == 200
    assert [section["id"] for section in section_response.json()] == ["section-b", "section-a"]
    assert [section["sort_order"] for section in section_response.json()] == [10, 20]

    item_response = client.post(
        "/api/v1/admin/items/reorder",
        headers=headers,
        json={"section_id": "section-a", "ordered_ids": ["item-b", "item-a"]},
    )
    assert item_response.status_code == 200
    assert [item["id"] for item in item_response.json()] == ["item-b", "item-a"]
    assert [item["sort_order"] for item in item_response.json()] == [10, 20]

    page_config = client.get("/api/v1/portal/pages/home", headers={"X-Tenant-ID": tenant.id}).json()
    assert [section["id"] for section in page_config["sections"]] == ["section-b", "section-a"]
    assert [item["id"] for item in page_config["sections"][1]["items"]] == ["item-b", "item-a"]


def test_admin_can_reorder_pages(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="管理员",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    session.add_all(
        [
            tenant,
            admin,
            ContentPage(
                id="page-home",
                tenant_id=tenant.id,
                page_key="home",
                label="首页",
                title="首页",
                sort_order=10,
                enabled=True,
            ),
            ContentPage(
                id="page-marketing",
                tenant_id=tenant.id,
                page_key="marketing",
                label="AI 营销",
                title="营销增长中心",
                sort_order=20,
                enabled=True,
            ),
        ]
    )
    session.commit()
    client = make_client(session)
    headers = {"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {login_admin(client, tenant.id)}"}

    response = client.post(
        "/api/v1/admin/pages/reorder",
        headers=headers,
        json={"ordered_ids": ["page-marketing", "page-home"]},
    )

    assert response.status_code == 200
    assert [page["id"] for page in response.json()] == ["page-marketing", "page-home"]
    assert [page["sort_order"] for page in response.json()] == [10, 20]

    config = client.get("/api/v1/portal/config", headers={"X-Tenant-ID": tenant.id}).json()
    assert [page["id"] for page in config["pages"]] == ["page-marketing", "page-home"]
    assert [channel["key"] for channel in config["channels"]] == ["marketing", "home"]


def test_admin_page_content_includes_disabled_records_and_can_restore_visibility(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="管理员",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    page = ContentPage(
        id="page-home",
        tenant_id=tenant.id,
        page_key="home",
        label="首页",
        title="首页",
        sort_order=10,
        enabled=True,
    )
    section = ContentSection(
        id="section-hidden",
        tenant_id=tenant.id,
        area="home",
        section_key="hidden",
        title="隐藏模块",
        sort_order=10,
        enabled=False,
    )
    item = ContentItem(
        id="item-hidden",
        tenant_id=tenant.id,
        section_id=section.id,
        item_type="tool",
        title="隐藏卡片",
        sort_order=10,
        enabled=False,
        action_value="hidden",
    )
    session.add_all([tenant, admin, page, section, item])
    session.commit()
    client = make_client(session)
    headers = {"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {login_admin(client, tenant.id)}"}

    public_before = client.get("/api/v1/portal/pages/home", headers={"X-Tenant-ID": tenant.id}).json()
    assert public_before["sections"] == []

    admin_content = client.get("/api/v1/admin/page-content/home", headers=headers)
    assert admin_content.status_code == 200
    assert admin_content.json()["sections"][0]["enabled"] is False
    assert admin_content.json()["sections"][0]["items"][0]["enabled"] is False

    restored_section = client.put("/api/v1/admin/sections/section-hidden", headers=headers, json={"enabled": True})
    restored_item = client.put("/api/v1/admin/items/item-hidden", headers=headers, json={"enabled": True})
    assert restored_section.status_code == 200
    assert restored_item.status_code == 200

    public_after = client.get("/api/v1/portal/pages/home", headers={"X-Tenant-ID": tenant.id}).json()
    assert public_after["sections"][0]["id"] == "section-hidden"
    assert public_after["sections"][0]["items"][0]["id"] == "item-hidden"


def test_non_admin_token_cannot_access_admin_routes(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    user = User(
        id="user-a",
        tenant_id=tenant.id,
        phone="13800000000",
        display_name="普通用户",
        role="USER",
        password_hash=hash_password("user123456"),
    )
    session.add_all([tenant, user])
    session.commit()
    client = make_client(session)

    login = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13800000000", "password": "user123456"},
    )
    assert login.status_code == 200

    response = client.get(
        "/api/v1/admin/pages",
        headers={"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 403


def test_demo_seed_creates_portal_pages_and_admin_user(session):
    ensure_demo_data(session, tenant_id="demo")

    client = make_client(session)
    config = client.get("/api/v1/portal/config", headers={"X-Tenant-ID": "demo"}).json()
    page_keys = [page["page_key"] for page in config["pages"]]

    assert page_keys == [
        "home",
        "assistant",
        "marketing",
        "image",
        "video",
        "audio",
        "coding",
        "writing",
        "ecommerce",
        "legal",
        "office",
    ]
    assert session.query(ContentSection).filter_by(tenant_id="demo").count() >= 30
    assert session.query(ContentItem).filter_by(tenant_id="demo").count() >= 60

    login = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": "demo"},
        json={"phone": "13900000000", "password": "admin123456"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "ADMIN"

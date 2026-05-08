from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ContentItem, ContentSection, Tenant


def override_session(session):
    def _override():
        yield session

    return _override


def test_portal_config_api_uses_tenant_header(session):
    tenant_a = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    tenant_b = Tenant(id="tenant-b", slug="tenant-b", name="Tenant B")
    section_a = ContentSection(
        id="section-a",
        tenant_id=tenant_a.id,
        area="home",
        section_key="learning",
        title="学习中心",
        sort_order=1,
        enabled=True,
    )
    section_b = ContentSection(
        id="section-b",
        tenant_id=tenant_b.id,
        area="home",
        section_key="learning",
        title="学习中心",
        sort_order=1,
        enabled=True,
    )
    session.add_all(
        [
            tenant_a,
            tenant_b,
            section_a,
            section_b,
            ContentItem(
                id="item-a",
                tenant_id=tenant_a.id,
                section_id=section_a.id,
                item_type="course",
                title="租户A课程",
                subtitle="A",
                category="基础必备",
                sort_order=1,
                enabled=True,
                action_type="route",
                action_value="/a",
            ),
            ContentItem(
                id="item-b",
                tenant_id=tenant_b.id,
                section_id=section_b.id,
                item_type="course",
                title="租户B课程",
                subtitle="B",
                category="基础必备",
                sort_order=1,
                enabled=True,
                action_type="route",
                action_value="/b",
            ),
        ]
    )
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    client = TestClient(app)

    response = client.get("/api/v1/portal/config", headers={"X-Tenant-ID": tenant_a.id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["home_sections"][0]["items"][0]["title"] == "租户A课程"
    assert payload["home_sections"][0]["items"][0]["tenant_id"] == tenant_a.id


def test_admin_content_item_create_is_visible_in_portal(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    section = ContentSection(
        id="section-a",
        tenant_id=tenant.id,
        area="home",
        section_key="orders",
        title="OPC 接单中心",
        sort_order=1,
        enabled=True,
    )
    session.add_all([tenant, section])
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    client = TestClient(app)

    created = client.post(
        "/api/v1/admin/content/items",
        headers={"X-Tenant-ID": tenant.id},
        json={
            "section_id": section.id,
            "item_type": "service",
            "title": "AI 自动化定制",
            "subtitle": "自动化办公流程交付",
            "category": "接单变现",
            "sort_order": 3,
            "enabled": True,
            "action_type": "route",
            "action_value": "/workspace/automation",
            "required_membership": True,
            "point_cost": 50,
        },
    )

    assert created.status_code == 201
    config = client.get("/api/v1/portal/config", headers={"X-Tenant-ID": tenant.id}).json()
    assert config["home_sections"][0]["items"][0]["title"] == "AI 自动化定制"
    assert config["home_sections"][0]["items"][0]["required_membership"] is True

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from datetime import timedelta

from app.models import ContentItem, ContentPage, ContentSection, MembershipPlan, Tenant, User, UserMembership, UserPortalAction, utcnow
from app.seed import ensure_demo_data


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
        title="新商机 接单中心",
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


def test_demo_seed_brand_copy_uses_new_business(session):
    ensure_demo_data(session)

    tenant = session.get(Tenant, "demo")
    orders_section = session.query(ContentSection).filter_by(id="section-orders").one()

    assert tenant.name == "新商机"
    assert orders_section.title == "新商机 接单中心"


def test_demo_seed_updates_existing_old_brand_copy(session):
    session.add(Tenant(id="demo", slug="demo", name="新商机 AI 社区"))
    session.add(
        ContentSection(
            id="section-orders",
            tenant_id="demo",
            area="home",
            section_key="order_center",
            title="OPC 接单中心",
            sort_order=20,
            enabled=True,
        )
    )
    session.commit()

    ensure_demo_data(session)

    tenant = session.get(Tenant, "demo")
    orders_section = session.get(ContentSection, "section-orders")
    assert tenant.name == "新商机"
    assert orders_section.title == "新商机 接单中心"


def test_audio_page_config_exposes_workbench_actions(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    page = ContentPage(
        id="page-audio",
        tenant_id=tenant.id,
        page_key="audio",
        label="AI 音频",
        title="AI音频创作中心",
        subtitle="配音、转写、降噪、播客和音色库",
        icon="Headphones",
        sort_order=50,
        enabled=True,
    )
    session.add_all([tenant, page])
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    client = TestClient(app)

    response = client.get("/api/v1/portal/pages/audio", headers={"X-Tenant-ID": tenant.id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"]["page_key"] == "audio"
    assert [section["section_key"] for section in payload["sections"]] == ["overview", "tools", "templates", "ranking"]
    assert payload["sections"][1]["items"][0]["action_type"] == "workspace"
    assert payload["sections"][1]["items"][0]["action_value"] == "audio_tts"


def test_portal_detail_resolves_shared_route_with_configurable_metadata(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    page = ContentPage(
        id="page-home",
        tenant_id=tenant.id,
        page_key="home",
        label="首页",
        title="首页",
        subtitle="新手入口",
        icon="Home",
        sort_order=1,
        enabled=True,
    )
    section = ContentSection(
        id="section-learning",
        tenant_id=tenant.id,
        area="home",
        section_key="learning_center",
        title="常用AI学习中心",
        sort_order=1,
        enabled=True,
    )
    session.add_all(
        [
            tenant,
            page,
            section,
            User(id="demo-user", tenant_id=tenant.id, phone="13800000000", role="USER"),
            ContentItem(
                id="learn-a",
                tenant_id=tenant.id,
                section_id=section.id,
                item_type="course",
                title="0基础AI通识课",
                subtitle="入门课程",
                category="基础必备",
                icon="FileVideo",
                sort_order=1,
                enabled=True,
                action_type="route",
                action_value="/workspace/course",
                metadata_json={
                    "detail": {
                        "summary": "系统学习 AI 基础能力。",
                        "highlights": ["12 个核心模块"],
                        "steps": ["完成入门测评", "按章节学习"],
                        "deliverables": ["学习路线图"],
                        "faqs": [{"question": "适合谁？", "answer": "适合零基础用户。"}],
                        "primaryAction": {"key": "enroll", "label": "报名学习"},
                        "secondaryActions": [{"key": "favorite", "label": "收藏"}],
                        "download": {"fileName": "starter-kit.md", "url": "/storage/resources/starter-kit.md"},
                    }
                },
            ),
            ContentItem(
                id="learn-b",
                tenant_id=tenant.id,
                section_id=section.id,
                item_type="course",
                title="AI 实战必修课",
                subtitle="实战课程",
                category="基础必备",
                icon="MonitorPlay",
                sort_order=2,
                enabled=True,
                action_type="route",
                action_value="/workspace/course",
                required_membership=True,
            ),
        ]
    )
    session.commit()
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    client = TestClient(app)

    response = client.get("/api/v1/portal/details/workspace/course?user_id=demo-user", headers={"X-Tenant-ID": tenant.id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["path"] == "/workspace/course"
    assert payload["kind"] == "directory"
    assert payload["title"] == "常用AI学习中心"
    assert [item["id"] for item in payload["items"]] == ["learn-a", "learn-b"]
    assert payload["detail"]["summary"] == "系统学习 AI 基础能力。"
    assert payload["detail"]["primaryAction"]["key"] == "enroll"
    assert payload["userState"]["membershipActive"] is False
    assert payload["userState"]["locked"] is True


def test_portal_action_records_completion_idempotently_and_returns_download(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    user = User(id="demo-user", tenant_id=tenant.id, phone="13800000000", role="USER")
    plan = MembershipPlan(
        id="plan-vip",
        tenant_id=tenant.id,
        plan_key="vip",
        name="VIP",
        price_cents=100,
        duration_days=30,
        entitlements=["template.vip"],
        enabled=True,
    )
    membership = UserMembership(
        id="membership-a",
        tenant_id=tenant.id,
        user_id=user.id,
        plan_id=plan.id,
        status="ACTIVE",
        expires_at=utcnow() + timedelta(days=7),
    )
    section = ContentSection(
        id="section-resources",
        tenant_id=tenant.id,
        area="home",
        section_key="resource_hub",
        title="资源对接库",
        sort_order=1,
        enabled=True,
    )
    item = ContentItem(
        id="resource-a",
        tenant_id=tenant.id,
        section_id=section.id,
        item_type="resource",
        title="工具优惠合集",
        subtitle="权益合集",
        category="资源对接",
        icon="Gift",
        action_type="route",
        action_value="/resources/tools",
        required_membership=True,
        enabled=True,
        metadata_json={
            "detail": {
                "summary": "工具权益合集。",
                "primaryAction": {"key": "download", "label": "领取资料"},
                "download": {"fileName": "tools.md", "url": "/storage/resources/tools.md"},
            }
        },
    )
    session.add_all([tenant, user, plan, membership, section, item])
    session.commit()
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    client = TestClient(app)

    body = {"user_id": user.id, "detail_path": "/resources/tools", "item_id": item.id, "action_key": "download"}
    first = client.post("/api/v1/portal/actions", headers={"X-Tenant-ID": tenant.id}, json=body)
    second = client.post("/api/v1/portal/actions", headers={"X-Tenant-ID": tenant.id}, json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "completed"
    assert first.json()["download"]["url"] == "/storage/resources/tools.md"
    assert second.json()["action"]["id"] == first.json()["action"]["id"]
    assert session.query(UserPortalAction).filter_by(tenant_id=tenant.id, user_id=user.id, detail_path="/resources/tools").count() == 1


def test_portal_action_reports_locked_without_membership(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    user = User(id="demo-user", tenant_id=tenant.id, phone="13800000000", role="USER")
    section = ContentSection(
        id="section-orders",
        tenant_id=tenant.id,
        area="home",
        section_key="order_center",
        title="接单中心",
        sort_order=1,
        enabled=True,
    )
    item = ContentItem(
        id="order-a",
        tenant_id=tenant.id,
        section_id=section.id,
        item_type="service",
        title="AI创作订单",
        subtitle="交付服务",
        category="接单变现",
        icon="Feather",
        action_type="route",
        action_value="/workspace/orders",
        required_membership=True,
        enabled=True,
    )
    session.add_all([tenant, user, section, item])
    session.commit()
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    client = TestClient(app)

    response = client.post(
        "/api/v1/portal/actions",
        headers={"X-Tenant-ID": tenant.id},
        json={"user_id": user.id, "detail_path": "/workspace/orders", "item_id": item.id, "action_key": "enroll"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "locked"
    assert session.query(UserPortalAction).count() == 0


def test_portal_search_finds_pages_items_assistants_and_templates(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    page = ContentPage(
        id="page-home",
        tenant_id=tenant.id,
        page_key="home",
        label="首页",
        title="常用AI学习中心",
        subtitle="新手入口",
        icon="Home",
        sort_order=1,
        enabled=True,
    )
    section = ContentSection(
        id="section-quick",
        tenant_id=tenant.id,
        area="home",
        section_key="quick_start",
        title="新人快速上手",
        sort_order=1,
        enabled=True,
    )
    item = ContentItem(
        id="quick-a",
        tenant_id=tenant.id,
        section_id=section.id,
        item_type="task",
        title="领取新手资料包",
        subtitle="下载工具清单",
        category="基础必备",
        icon="Download",
        action_type="route",
        action_value="/resources/starter-kit",
        enabled=True,
    )
    session.add_all([tenant, page, section, item])
    session.commit()
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    client = TestClient(app)

    response = client.get("/api/v1/portal/search?q=新手&limit=5", headers={"X-Tenant-ID": tenant.id})

    assert response.status_code == 200
    results = response.json()["results"]
    assert any(result["title"] == "领取新手资料包" and result["path"] == "/resources/starter-kit" for result in results)
    assert any(result["type"] == "page" and result["path"] == "/home" for result in results)

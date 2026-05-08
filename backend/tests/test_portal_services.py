from datetime import timedelta

from app.models import AiAssistant, ContentItem, ContentSection, MembershipPlan, PromptTemplate, Tenant, User, UserMembership, utcnow
from app.services.memberships import MembershipService
from app.services.portal import PortalService


def test_portal_config_filters_tenant_content_and_orders_enabled_items(session):
    tenant_a = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    tenant_b = Tenant(id="tenant-b", slug="tenant-b", name="Tenant B")
    section = ContentSection(
        id="section-learning",
        tenant_id=tenant_a.id,
        area="home",
        section_key="learning_center",
        title="常用AI学习中心",
        sort_order=10,
        enabled=True,
    )
    session.add_all(
        [
            tenant_a,
            tenant_b,
            section,
            ContentItem(
                id="item-second",
                tenant_id=tenant_a.id,
                section_id=section.id,
                item_type="course",
                title="《AI 实战必修课》",
                subtitle="办公/剪辑/写作全场景效率翻倍",
                category="基础必备",
                sort_order=20,
                enabled=True,
                action_type="route",
                action_value="/workspace/course",
            ),
            ContentItem(
                id="item-first",
                tenant_id=tenant_a.id,
                section_id=section.id,
                item_type="course",
                title="《0基础AI通识课》",
                subtitle="从认知到上手一站式通关",
                category="基础必备",
                sort_order=10,
                enabled=True,
                action_type="route",
                action_value="/workspace/course",
            ),
            ContentItem(
                id="item-disabled",
                tenant_id=tenant_a.id,
                section_id=section.id,
                item_type="course",
                title="下架课程",
                subtitle="should not show",
                category="基础必备",
                sort_order=5,
                enabled=False,
                action_type="route",
                action_value="/hidden",
            ),
            ContentItem(
                id="item-other-tenant",
                tenant_id=tenant_b.id,
                section_id="foreign-section",
                item_type="course",
                title="其他租户课程",
                subtitle="should not show",
                category="基础必备",
                sort_order=1,
                enabled=True,
                action_type="route",
                action_value="/foreign",
            ),
        ]
    )
    session.commit()

    config = PortalService(session).get_portal_config(tenant_id=tenant_a.id)

    assert [item["title"] for item in config["home_sections"][0]["items"]] == [
        "《0基础AI通识课》",
        "《AI 实战必修课》",
    ]
    assert all(item["tenant_id"] == tenant_a.id for item in config["home_sections"][0]["items"])


def test_assistant_center_returns_cards_ranking_and_prompt_templates(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    session.add_all(
        [
            tenant,
            AiAssistant(
                id="assistant-ppt",
                tenant_id=tenant.id,
                assistant_key="ppt_generator",
                name="PPT 生成助理",
                description="一键生成专业级 PPT",
                category="办公助理",
                icon="Presentation",
                usage_count=234500,
                sort_order=10,
                enabled=True,
                action_type="workspace",
                action_value="ppt",
                required_membership=True,
                point_cost=20,
            ),
            AiAssistant(
                id="assistant-copy",
                tenant_id=tenant.id,
                assistant_key="copywriter",
                name="文案创作助理",
                description="快速生成营销内容",
                category="营销助理",
                icon="Feather",
                usage_count=197000,
                sort_order=20,
                enabled=True,
                action_type="workspace",
                action_value="copywriting",
            ),
            PromptTemplate(
                id="template-writing",
                tenant_id=tenant.id,
                template_key="general_writing",
                title="通用写作模板",
                category="写作",
                content="请帮我写一份...",
                sort_order=10,
                enabled=True,
            ),
        ]
    )
    session.commit()

    center = PortalService(session).get_assistant_center(tenant_id=tenant.id)

    assert center["featured"][0]["name"] == "PPT 生成助理"
    assert center["ranking"][0]["usage_count_label"] == "23.4万次使用"
    assert center["prompt_templates"][0]["title"] == "通用写作模板"


def test_membership_entitlements_respect_active_user_membership(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    user = User(id="user-a", tenant_id=tenant.id, phone="13800000000", role="USER")
    plan = MembershipPlan(
        id="plan-vip",
        tenant_id=tenant.id,
        plan_key="vip_monthly",
        name="VIP 月卡",
        price_cents=1990,
        duration_days=31,
        entitlements=["course.premium", "assistant.vip", "template.vip"],
        enabled=True,
    )
    membership = UserMembership(
        id="membership-a",
        tenant_id=tenant.id,
        user_id=user.id,
        plan_id=plan.id,
        status="ACTIVE",
        started_at=utcnow() - timedelta(days=1),
        expires_at=utcnow() + timedelta(days=30),
    )
    session.add_all([tenant, user, plan, membership])
    session.commit()

    service = MembershipService(session)

    assert service.can_use_entitlement(tenant_id=tenant.id, user_id=user.id, entitlement="assistant.vip")
    assert not service.can_use_entitlement(tenant_id=tenant.id, user_id=user.id, entitlement="admin.panel")


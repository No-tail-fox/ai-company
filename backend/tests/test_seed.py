from app.models import AiAssistant, ChannelRoute, ChatMessage, ChatSession, ContentItem, ContentPage, ContentSection, ModelConfig, PromptTemplate, Tenant, User
from app.seed import ensure_demo_data
from app.services.auth import verify_password


def test_demo_seed_creates_portal_content_idempotently(session):
    ensure_demo_data(session, tenant_id="demo")
    ensure_demo_data(session, tenant_id="demo")

    assert session.query(Tenant).filter_by(id="demo").count() == 1
    assert session.query(ContentSection).filter_by(tenant_id="demo").count() >= 3
    assert session.query(ContentItem).filter_by(tenant_id="demo").count() >= 10
    assert session.query(AiAssistant).filter_by(tenant_id="demo").count() >= 12
    assert session.query(PromptTemplate).filter_by(tenant_id="demo").count() >= 5
    audio_sections = {
        row.section_key: row
        for row in session.query(ContentSection).filter_by(tenant_id="demo", area="audio").all()
    }
    assert {"overview", "tools", "templates", "ranking"}.issubset(audio_sections)
    assert session.query(ContentItem).join(ContentSection).filter(
        ContentSection.tenant_id == "demo",
        ContentSection.area == "audio",
        ContentItem.item_type == "tool",
    ).count() >= 8
    audio_routes = {
        route.route_key
        for route in session.query(ChannelRoute).filter_by(tenant_id="demo", channel_type="AUDIO").all()
    }
    assert {"audio_tts", "audio_transcription", "audio_music"}.issubset(audio_routes)
    video_route = session.query(ChannelRoute).filter_by(
        tenant_id="demo",
        route_key="video_text_to_video",
        channel_type="VIDEO",
    ).one()
    assert video_route.unit_cost == 200
    assert video_route.backend_model == "demo-video-renderer"
    image_route = session.query(ChannelRoute).filter_by(
        tenant_id="demo",
        route_key="image_text_to_image",
        channel_type="IMAGE",
    ).one()
    assert image_route.unit_cost == 80
    assert image_route.backend_model == "demo-image-renderer"
    image_sections = {
        row.section_key: row
        for row in session.query(ContentSection)
        .filter_by(tenant_id="demo", area="image")
        .all()
    }
    assert {"overview", "tools", "templates", "ranking"}.issubset(image_sections)
    assert (
        session.query(ContentItem)
        .filter_by(tenant_id="demo", section_id=image_sections["tools"].id)
        .count()
        >= 7
    )
    assistant_categories = {
        row.category for row in session.query(AiAssistant).filter_by(tenant_id="demo").all()
    }
    assert {"办公助理", "营销助理", "学习助理", "法务助理", "客服助理", "设计助理", "开发助理"}.issubset(
        assistant_categories
    )


def test_demo_seed_sets_default_user_password(session):
    ensure_demo_data(session, tenant_id="demo")

    user = session.get(User, "demo-user")

    assert user is not None
    assert user.phone == "13800000000"
    assert verify_password("user123456", user.password_hash)


def test_demo_seed_contains_marketing_dashboard_content(session):
    ensure_demo_data(session, tenant_id="demo")

    marketing_sections = {
        row.section_key: row
        for row in session.query(ContentSection)
        .filter_by(tenant_id="demo", area="marketing")
        .all()
    }

    assert {"overview", "tools", "templates", "ranking"}.issubset(marketing_sections)
    assert (
        session.query(ContentItem)
        .filter_by(tenant_id="demo", section_id=marketing_sections["tools"].id)
        .count()
        >= 9
    )
    assert (
        session.query(ContentItem)
        .filter_by(tenant_id="demo", section_id=marketing_sections["templates"].id)
        .count()
        >= 5
    )
    assert (
        session.query(ContentItem)
        .filter_by(tenant_id="demo", section_id=marketing_sections["ranking"].id)
        .count()
        >= 5
    )
    workspace_section = session.query(ContentSection).filter_by(
        tenant_id="demo",
        area="home",
        section_key="workspace_tools",
    ).one()
    assert session.query(ContentItem).filter_by(
        tenant_id="demo",
        section_id=workspace_section.id,
        title="AI 工作台",
        action_value="/workbench",
    ).count() == 1
    third_party_section = session.query(ContentSection).filter_by(
        tenant_id="demo",
        area="home",
        section_key="third_party_tools",
    ).one()
    third_party_tool = session.query(ContentItem).filter_by(
        tenant_id="demo",
        section_id=third_party_section.id,
        title="剪映专业版",
    ).one()
    assert third_party_section.layout == "third-party-tools"
    assert third_party_tool.item_type == "third_party_tool"
    assert third_party_tool.action_type == "external_link"
    assert third_party_tool.action_value.startswith("https://")
    assert third_party_tool.metadata_json["brandMark"] == "JY"
    assert third_party_tool.metadata_json["detail"]["download"]["url"].startswith("https://")


def test_demo_seed_includes_workbench_and_chat_runtime(session):
    ensure_demo_data(session, tenant_id="demo")

    workbench = session.query(ContentPage).filter_by(tenant_id="demo", page_key="workbench").one()
    assert workbench.label == "工作台"
    assert workbench.title == "AI 工作台"
    text_route = session.query(ChannelRoute).filter_by(
        tenant_id="demo",
        route_key="general_text_default",
        channel_type="TEXT",
    ).one()
    assert text_route.backend_model == "demo-general-text"
    assert session.query(ModelConfig).filter_by(
        tenant_id="demo",
        model_key="general_text_default",
        capability="TEXT",
    ).count() >= 1
    chat = session.query(ChatSession).filter_by(tenant_id="demo", user_id="demo-user").one()
    assert chat.title
    assert session.query(ChatMessage).filter_by(session_id=chat.id).count() >= 2

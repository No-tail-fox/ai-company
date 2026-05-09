from app.models import AiAssistant, ChannelRoute, ContentItem, ContentSection, PromptTemplate, Tenant
from app.seed import ensure_demo_data


def test_demo_seed_creates_portal_content_idempotently(session):
    ensure_demo_data(session, tenant_id="demo")
    ensure_demo_data(session, tenant_id="demo")

    assert session.query(Tenant).filter_by(id="demo").count() == 1
    assert session.query(ContentSection).filter_by(tenant_id="demo").count() >= 3
    assert session.query(ContentItem).filter_by(tenant_id="demo").count() >= 10
    assert session.query(AiAssistant).filter_by(tenant_id="demo").count() >= 12
    assert session.query(PromptTemplate).filter_by(tenant_id="demo").count() >= 5
    audio_sections = session.query(ContentSection).filter_by(tenant_id="demo", area="audio").all()
    audio_layouts = {section.layout for section in audio_sections}
    assert {
        "audio-workbench",
        "audio-stats",
        "audio-tools",
        "audio-voices",
        "audio-table",
        "audio-queue",
        "audio-resources",
        "audio-guides",
    }.issubset(audio_layouts)
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

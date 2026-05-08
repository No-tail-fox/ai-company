from app.models import AiAssistant, ContentItem, ContentSection, PromptTemplate, Tenant
from app.seed import ensure_demo_data


def test_demo_seed_creates_portal_content_idempotently(session):
    ensure_demo_data(session, tenant_id="demo")
    ensure_demo_data(session, tenant_id="demo")

    assert session.query(Tenant).filter_by(id="demo").count() == 1
    assert session.query(ContentSection).filter_by(tenant_id="demo").count() >= 3
    assert session.query(ContentItem).filter_by(tenant_id="demo").count() >= 10
    assert session.query(AiAssistant).filter_by(tenant_id="demo").count() >= 8
    assert session.query(PromptTemplate).filter_by(tenant_id="demo").count() >= 5

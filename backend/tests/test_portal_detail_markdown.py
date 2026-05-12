from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ContentItem, ContentSection, Tenant, User
from app.services.auth import AuthService


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session):
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def bearer(session, tenant_id: str, user_id: str) -> dict[str, str]:
    user = session.get(User, user_id)
    assert user is not None
    return {"Authorization": f"Bearer {AuthService(session).create_access_token(user)}", "X-Tenant-ID": tenant_id}


def seed_detail_item(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    section = ContentSection(
        id="section-resources",
        tenant_id=tenant.id,
        area="resources",
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
        subtitle="模型、剪辑、设计和办公工具权益",
        category="资源对接",
        icon="Gift",
        action_type="route",
        action_value="/resources/tools",
        enabled=True,
        tags=["工具权益", "Markdown"],
        metadata_json={
            "authorUserId": "author-user",
            "detail": {
                "summary": "工具权益合集。",
                "highlights": ["支持 Markdown 正文"],
                "primaryAction": {"key": "download", "label": "下载资料"},
            }
        },
    )
    users = [
        User(id="author-user", tenant_id=tenant.id, phone="13800000001", display_name="作者", role="USER", status="ACTIVE"),
        User(id="viewer-user", tenant_id=tenant.id, phone="13800000002", display_name="浏览者", role="USER", status="ACTIVE"),
        User(id="editor-user", tenant_id=tenant.id, phone="13800000003", display_name="编辑", role="CONTENT_EDITOR", status="ACTIVE"),
    ]
    session.add_all([tenant, section, item, *users])
    session.commit()
    return tenant


def test_portal_detail_returns_markdown_document_versions_comments_and_permissions(session):
    tenant = seed_detail_item(session)
    client = make_client(session)

    response = client.get(
        "/api/v1/portal/details/resources/tools?user_id=viewer-user",
        headers={"X-Tenant-ID": tenant.id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["detail"]["body_markdown"].startswith("# 工具优惠合集")
    assert payload["detail"]["tags"] == ["工具权益", "Markdown"]
    assert payload["detail"]["version"]["version"] == 1
    assert payload["detail"]["versions"][0]["version"] == 1
    assert payload["detail"]["comments"] == []
    assert payload["detail"]["publish_info"]["type_label"] == "资源合集"
    assert payload["permissions"]["can_edit"] is False


def test_portal_detail_author_can_publish_and_rollback_versions(session):
    tenant = seed_detail_item(session)
    client = make_client(session)
    author_headers = bearer(session, tenant.id, "author-user")

    update_response = client.patch(
        "/api/v1/portal/details/resources/tools",
        headers=author_headers,
        json={
            "title": "工具优惠合集 v1.5",
            "summary": "更新后的权益合集",
            "body_markdown": "# 工具优惠合集 v1.5\n\n新增一批可申请权益。",
            "tags": ["工具权益", "资源对接"],
            "visibility": "community",
        },
    )
    publish_response = client.post(
        "/api/v1/portal/details/resources/tools/versions",
        headers=author_headers,
        json={"release_note": "补充 v1.5 权益"},
    )

    assert update_response.status_code == 200
    assert publish_response.status_code == 200
    published = publish_response.json()
    assert published["detail"]["title"] == "工具优惠合集 v1.5"
    assert published["detail"]["version"]["version"] == 2
    first_version_id = published["detail"]["versions"][-1]["id"]

    rollback_response = client.post(
        f"/api/v1/portal/details/resources/tools/versions/{first_version_id}/rollback",
        headers=author_headers,
        json={"release_note": "回滚到初始版本"},
    )

    assert rollback_response.status_code == 200
    rolled_back = rollback_response.json()
    assert rolled_back["detail"]["version"]["version"] == 3
    assert rolled_back["detail"]["body_markdown"].startswith("# 工具优惠合集")


def test_portal_detail_rejects_viewer_edits_and_requires_login_for_comments(session):
    tenant = seed_detail_item(session)
    client = make_client(session)

    unauthenticated_comment = client.post(
        "/api/v1/portal/details/resources/tools/comments",
        headers={"X-Tenant-ID": tenant.id},
        json={"content": "这个权益还有效吗？"},
    )
    viewer_edit = client.patch(
        "/api/v1/portal/details/resources/tools",
        headers=bearer(session, tenant.id, "viewer-user"),
        json={"summary": "不应该能修改"},
    )

    assert unauthenticated_comment.status_code == 401
    assert viewer_edit.status_code == 403


def test_portal_detail_logged_in_viewer_can_comment(session):
    tenant = seed_detail_item(session)
    client = make_client(session)

    response = client.post(
        "/api/v1/portal/details/resources/tools/comments",
        headers=bearer(session, tenant.id, "viewer-user"),
        json={"content": "建议增加商用授权列。"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["comment"]["content"] == "建议增加商用授权列。"
    assert payload["comment"]["author_name"] == "浏览者"
    assert payload["detail"]["comments"][0]["content"] == "建议增加商用授权列。"

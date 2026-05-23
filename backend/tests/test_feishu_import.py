from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ContentItem, ContentSection, FeishuSyncNode, FeishuSyncRun, PortalDetailDocument, PortalDetailVersion, Tenant, User
from app.services.feishu_import import FeishuImportService, FeishuWikiNode
from app.services.content_sanitizer import clean_markdown, clean_text


def override_session(session):
    def _override():
        yield session

    return _override


class FakeFeishuClient:
    def __init__(self, nodes: dict[str, list[FeishuWikiNode]], markdown: dict[str, str]):
        self.nodes = nodes
        self.markdown = markdown

    def iter_child_nodes(self, *, space_id: str, parent_node_token: str):
        del space_id
        yield from self.nodes.get(parent_node_token, [])

    def get_docx_markdown(self, document_id: str) -> str:
        if document_id not in self.markdown:
            raise RuntimeError("missing markdown")
        return self.markdown[document_id]


def test_feishu_import_creates_courses_documents_and_tracks_unsupported_nodes(session):
    session.add_all(
        [
            Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"),
            User(id="demo-admin", tenant_id="tenant-a", phone="13900000000", role="ADMIN"),
        ]
    )
    session.commit()
    client = FakeFeishuClient(
        nodes={
            "root": [
                FeishuWikiNode(node_token="cat-a", obj_token="cat-doc", obj_type="docx", title="AI 副业", has_child=True),
                FeishuWikiNode(node_token="sheet-a", obj_token="sheet-token", obj_type="sheet", title="资料表", has_child=False),
            ],
            "cat-a": [
                FeishuWikiNode(node_token="doc-a", obj_token="doc-token-a", obj_type="docx", title="小红书选品", has_child=False),
            ],
        },
        markdown={
            "cat-doc": "# AI 副业\n\n目录说明",
            "doc-token-a": "# 小红书选品\n\n正文内容",
        },
    )

    result = FeishuImportService(session, client=client).sync_wiki(
        tenant_id="tenant-a",
        actor_user_id="demo-admin",
        space_id="space-a",
        root_node_token="root",
        required_membership=True,
    )

    assert result["status"] == "SUCCESS"
    assert result["stats"]["created"] == 2
    assert result["stats"]["unsupported"] == 1
    item = session.query(ContentItem).filter_by(tenant_id="tenant-a", action_value="/learning/courses/doc-a").one()
    assert item.item_type == "course"
    assert item.category == "AI 副业"
    assert item.required_membership is True
    document = session.query(PortalDetailDocument).filter_by(tenant_id="tenant-a", detail_path="/learning/courses/doc-a").one()
    assert document.body_markdown == "# 小红书选品\n\n正文内容"
    unsupported = session.query(FeishuSyncNode).filter_by(tenant_id="tenant-a", node_token="sheet-a").one()
    assert unsupported.status == "UNSUPPORTED"
    assert "sheet" in unsupported.error_message


def test_feishu_import_skips_unchanged_content_and_versions_changed_content(session):
    session.add_all(
        [
            Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"),
            User(id="demo-admin", tenant_id="tenant-a", phone="13900000000", role="ADMIN"),
        ]
    )
    session.commit()
    nodes = {"root": [FeishuWikiNode(node_token="doc-a", obj_token="doc-token-a", obj_type="docx", title="小红书选品", has_child=False)]}
    service = FeishuImportService(
        session,
        client=FakeFeishuClient(nodes=nodes, markdown={"doc-token-a": "# v1"}),
    )

    first = service.sync_wiki(
        tenant_id="tenant-a",
        actor_user_id="demo-admin",
        space_id="space-a",
        root_node_token="root",
        required_membership=False,
    )
    second = service.sync_wiki(
        tenant_id="tenant-a",
        actor_user_id="demo-admin",
        space_id="space-a",
        root_node_token="root",
        required_membership=False,
    )
    service.client = FakeFeishuClient(nodes=nodes, markdown={"doc-token-a": "# v2"})
    third = service.sync_wiki(
        tenant_id="tenant-a",
        actor_user_id="demo-admin",
        space_id="space-a",
        root_node_token="root",
        required_membership=False,
    )

    document = session.query(PortalDetailDocument).filter_by(tenant_id="tenant-a", detail_path="/learning/courses/doc-a").one()
    versions = session.query(PortalDetailVersion).filter_by(tenant_id="tenant-a", document_id=document.id).order_by(PortalDetailVersion.version.asc()).all()
    assert first["stats"]["created"] == 1
    assert second["stats"]["skipped"] == 1
    assert third["stats"]["updated"] == 1
    assert document.current_version == 2
    assert [version.body_markdown for version in versions] == ["# v1", "# v2"]


def test_feishu_import_admin_api_starts_sync_and_exposes_run_status(session, monkeypatch):
    session.add_all(
        [
            Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"),
            User(id="admin-a", tenant_id="tenant-a", phone="13900000000", role="ADMIN"),
            User(id="user-a", tenant_id="tenant-a", phone="13800000000", role="USER"),
        ]
    )
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    app.dependency_overrides.clear()
    app.dependency_overrides[get_session] = override_session(session)

    from app.services import auth as auth_module

    monkeypatch.setattr(auth_module.AuthService, "user_from_token", lambda self, tenant_id, token: session.get(User, token))
    monkeypatch.setattr(
        "app.main.FeishuImportService",
        lambda db: FeishuImportService(
            db,
            client=FakeFeishuClient(
                nodes={"root": [FeishuWikiNode(node_token="doc-a", obj_token="doc-token-a", obj_type="docx", title="课程 A", has_child=False)]},
                markdown={"doc-token-a": "# 课程 A"},
            ),
        ),
    )
    client = TestClient(app)

    denied = client.post(
        "/api/v1/admin/imports/feishu/wiki/sync",
        headers={"X-Tenant-ID": "tenant-a", "Authorization": "Bearer user-a"},
        json={"space_id": "space-a", "root_node_token": "root"},
    )
    started = client.post(
        "/api/v1/admin/imports/feishu/wiki/sync",
        headers={"X-Tenant-ID": "tenant-a", "Authorization": "Bearer admin-a"},
        json={"space_id": "space-a", "root_node_token": "root"},
    )
    run_id = started.json()["run"]["id"]
    fetched = client.get(
        f"/api/v1/admin/imports/feishu/wiki/runs/{run_id}",
        headers={"X-Tenant-ID": "tenant-a", "Authorization": "Bearer admin-a"},
    )

    assert denied.status_code == 403
    assert started.status_code == 200
    assert started.json()["run"]["status"] == "SUCCESS"
    assert fetched.status_code == 200
    assert fetched.json()["run"]["stats"]["created"] == 1


def test_feishu_browser_snapshot_admin_api_imports_visible_markdown_and_skips_unchanged(session, monkeypatch):
    session.add_all(
        [
            Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"),
            User(id="admin-a", tenant_id="tenant-a", phone="13900000000", role="ADMIN"),
        ]
    )
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)

    from app.services import auth as auth_module

    monkeypatch.setattr(auth_module.AuthService, "user_from_token", lambda self, tenant_id, token: session.get(User, token))
    client = TestClient(app)
    headers = {"X-Tenant-ID": "tenant-a", "Authorization": "Bearer admin-a"}
    payload = {
        "title": "Snapshot Course",
        "source_url": "https://my.feishu.cn/wiki/Ntvew2RsCi0u3Gkq3VxcS6wNnhg",
        "node_token": "Ntvew2RsCi0u3Gkq3VxcS6wNnhg",
        "source_path": ["Browser Library", "Snapshot Course"],
        "body_markdown": "# Snapshot Course\n\nVisible body",
        "required_membership": False,
    }

    created = client.post("/api/v1/admin/imports/feishu/browser/snapshot", headers=headers, json=payload)
    skipped = client.post("/api/v1/admin/imports/feishu/browser/snapshot", headers=headers, json=payload)

    assert created.status_code == 200
    assert created.json()["stats"]["created"] == 1
    assert skipped.status_code == 200
    assert skipped.json()["stats"]["skipped"] == 1
    item = session.query(ContentItem).filter_by(tenant_id="tenant-a", action_value="/learning/courses/Ntvew2RsCi0u3Gkq3VxcS6wNnhg").one()
    assert item.category == "Browser Library"
    assert item.required_membership is False
    document = session.query(PortalDetailDocument).filter_by(tenant_id="tenant-a", detail_path=item.action_value).one()
    versions = session.query(PortalDetailVersion).filter_by(tenant_id="tenant-a", document_id=document.id).all()
    assert document.body_markdown == "# Snapshot Course\n\nVisible body"
    assert len(versions) == 1


def test_feishu_browser_snapshot_sanitizes_inline_span_html(session, monkeypatch):
    session.add_all(
        [
            Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"),
            User(id="admin-a", tenant_id="tenant-a", phone="13900000000", role="ADMIN"),
        ]
    )
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)

    from app.services import auth as auth_module

    monkeypatch.setattr(auth_module.AuthService, "user_from_token", lambda self, tenant_id, token: session.get(User, token))
    client = TestClient(app)
    payload = {
        "title": "Styled Snapshot",
        "source_url": "https://my.feishu.cn/wiki/styled-node",
        "node_token": "styled-node",
        "source_path": ["Browser Library", "Styled Snapshot"],
        "body_markdown": '# **<span style="color: inherit; background-color: rgba(255,246,122,0.8)">手机用户使用指南：</span>**\n\n正文',
    }

    response = client.post(
        "/api/v1/admin/imports/feishu/browser/snapshot",
        headers={"X-Tenant-ID": "tenant-a", "Authorization": "Bearer admin-a"},
        json=payload,
    )

    assert response.status_code == 200
    document = session.query(PortalDetailDocument).filter_by(tenant_id="tenant-a", detail_path="/learning/courses/styled-node").one()
    assert document.body_markdown == "# **手机用户使用指南：**\n\n正文"
    assert "<span" not in document.summary


def test_feishu_browser_snapshot_rewrites_imported_image_assets(session, monkeypatch):
    session.add_all(
        [
            Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"),
            User(id="admin-a", tenant_id="tenant-a", phone="13900000000", role="ADMIN"),
        ]
    )
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)

    from app.services import auth as auth_module

    monkeypatch.setattr(auth_module.AuthService, "user_from_token", lambda self, tenant_id, token: session.get(User, token))
    client = TestClient(app)
    feishu_image_url = "https://my.feishu.cn/space/api/box/stream/download/asynccode/?code=abc123"
    local_image_url = "/storage/uploads/tenant-a/course-assets/asset.png"
    payload = {
        "title": "Image Snapshot",
        "source_url": "https://my.feishu.cn/wiki/image-node",
        "node_token": "image-node",
        "source_path": ["Browser Library", "Image Snapshot"],
        "body_markdown": f"# Image Snapshot\n\n![]({feishu_image_url})\n\n![alt]({feishu_image_url})",
        "asset_url_map": {feishu_image_url: local_image_url},
    }

    response = client.post(
        "/api/v1/admin/imports/feishu/browser/snapshot",
        headers={"X-Tenant-ID": "tenant-a", "Authorization": "Bearer admin-a"},
        json=payload,
    )

    assert response.status_code == 200
    document = session.query(PortalDetailDocument).filter_by(tenant_id="tenant-a", detail_path="/learning/courses/image-node").one()
    assert feishu_image_url not in document.body_markdown
    assert document.body_markdown.count(local_image_url) == 2
    assert f"![]({local_image_url})" in document.body_markdown
    assert f"![alt]({local_image_url})" in document.body_markdown


def test_content_sanitizer_cleans_feishu_markdown_html_entities_and_unsafe_blocks():
    dirty = (
        '# <span style="color: inherit; background-color: rgba(255,246,122,0.8)">标题&#x20;</span>\n'
        '<script>alert(1)</script><style>.x{}</style><svg><path /></svg>\n'
        '<p>第一行<br>第二行</p>\u200b\n'
        '<img src="https://example.com/a.png" alt="配图">\n'
        '<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>\n'
        'utm\\_source=feishu\n'
    )

    cleaned = clean_markdown(dirty)

    assert '# 标题' in cleaned
    assert '第一行\n第二行' in cleaned
    assert '![配图](https://example.com/a.png)' in cleaned
    assert '| A | B |' in cleaned
    assert '| 1 | 2 |' in cleaned
    assert 'utm_source=feishu' in cleaned
    assert '<span' not in cleaned
    assert '<script' not in cleaned
    assert '<style' not in cleaned
    assert '<svg' not in cleaned
    assert '&#x20;' not in cleaned
    assert '\u200b' not in cleaned


def test_content_sanitizer_repairs_common_mojibake_text():
    assert clean_text('DeepSeek å®Œæ•´ä½¿ç”¨æ‰‹å†Œ') == 'DeepSeek 完整使用手册'
    assert clean_text('â™¨ï¸ çƒ­é—¨AIå·¥å…·ä½¿ç”¨æ•™ç¨‹') == '♨️ 热门AI工具使用教程'


def test_feishu_browser_snapshot_sanitizes_invalid_unicode_surrogates(session):
    session.add_all(
        [
            Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"),
            User(id="admin-a", tenant_id="tenant-a", phone="13900000000", role="ADMIN"),
        ]
    )
    session.commit()

    result = FeishuImportService(session).import_browser_snapshot(
        tenant_id="tenant-a",
        actor_user_id="admin-a",
        title="Bad Emoji Snapshot\udc49",
        source_url="https://my.feishu.cn/wiki/bad-emoji-node",
        node_token="bad-emoji-node",
        source_path=["Browser Library", "Bad Emoji Snapshot\udc49"],
        body_markdown="# Title\n\nBroken marker \udc49 should disappear",
        required_membership=True,
    )

    assert result["status"] == "SUCCESS"
    document = session.query(PortalDetailDocument).filter_by(tenant_id="tenant-a", detail_path="/learning/courses/bad-emoji-node").one()
    item = session.query(ContentItem).filter_by(tenant_id="tenant-a", action_value="/learning/courses/bad-emoji-node").one()
    assert "\udc49" not in document.body_markdown
    assert "\udc49" not in document.title
    assert all("\udc49" not in part for part in item.metadata_json["source"]["path"])


def test_courses_api_searches_categories_and_paginates(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    section = ContentSection(
        id="section-feishu-courses",
        tenant_id=tenant.id,
        area="home",
        section_key="feishu_courses",
        title="副业课程库",
        layout="course-library",
        enabled=True,
    )
    session.add_all([tenant, section])
    for index, title in enumerate(["小红书选品", "YouTube 长视频", "AI 自动化"], start=1):
        path = f"/learning/courses/node-{index}"
        session.add(
            ContentItem(
                id=f"course-{index}",
                tenant_id=tenant.id,
                section_id=section.id,
                item_type="course",
                title=title,
                subtitle=f"{title} 复盘",
                category="实操复盘" if index < 3 else "AI 工具",
                icon="NotebookTabs",
                action_type="route",
                action_value=path,
                sort_order=index,
                enabled=True,
                metadata_json={"source": {"path": ["2026年合集", "1月", title]}},
            )
        )
        session.add(
            PortalDetailDocument(
                id=f"detail-{index}",
                tenant_id=tenant.id,
                detail_path=path,
                title=title,
                summary=f"{title} 摘要",
                body_markdown=f"# {title}",
                tags=["2026年合集", "1月"],
            )
        )
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    client = TestClient(app)

    response = client.get("/api/v1/courses?q=小红书&category=实操复盘&page=1&page_size=2", headers={"X-Tenant-ID": tenant.id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["categories"] == ["AI 工具", "实操复盘"]
    assert payload["items"][0]["title"] == "小红书选品"
    assert payload["items"][0]["detail_path"] == "/learning/courses/node-1"
    assert payload["items"][0]["source_path"] == ["2026年合集", "1月", "小红书选品"]


def test_admin_courses_api_lists_and_batch_cleans_course_documents(session, monkeypatch):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(id="admin-a", tenant_id=tenant.id, phone="13900000000", role="ADMIN")
    section = ContentSection(
        id="section-feishu-courses",
        tenant_id=tenant.id,
        area="home",
        section_key="feishu_courses",
        title="副业课程库",
        layout="course-library",
        enabled=True,
    )
    item = ContentItem(
        id="course-dirty",
        tenant_id=tenant.id,
        section_id=section.id,
        item_type="course",
        title="DeepSeek å®Œæ•´ä½¿ç”¨æ‰‹å†Œ",
        subtitle="带有 HTML 的课程",
        category="â™¨ï¸ çƒ­é—¨AIå·¥å…·ä½¿ç”¨æ•™ç¨‹",
        icon="NotebookTabs",
        action_type="route",
        action_value="/learning/courses/dirty-node",
        enabled=True,
        metadata_json={"source": {"path": ["â™¨ï¸ çƒ­é—¨AIå·¥å…·ä½¿ç”¨æ•™ç¨‹", "DeepSeek å®Œæ•´ä½¿ç”¨æ‰‹å†Œ"]}},
    )
    document = PortalDetailDocument(
        id="detail-dirty",
        tenant_id=tenant.id,
        detail_path="/learning/courses/dirty-node",
        title="DeepSeek å®Œæ•´ä½¿ç”¨æ‰‹å†Œ",
        summary='<span style="color:red">摘要&#x20;</span>',
        body_markdown='# <span style="color:red">标题&#x20;</span>\n<script>alert(1)</script>\n正文\u200b',
        tags=["â™¨ï¸ çƒ­é—¨AIå·¥å…·ä½¿ç”¨æ•™ç¨‹"],
    )
    session.add_all([tenant, admin, section, item, document])
    session.commit()

    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)

    from app.services import auth as auth_module

    monkeypatch.setattr(auth_module.AuthService, "user_from_token", lambda self, tenant_id, token: session.get(User, token))
    client = TestClient(app)
    headers = {"X-Tenant-ID": tenant.id, "Authorization": "Bearer admin-a"}

    listed_before = client.get("/api/v1/admin/courses?q=DeepSeek&page=1&page_size=20", headers=headers)
    cleaned = client.post("/api/v1/admin/courses/cleanup", headers=headers, json={})
    listed_after = client.get("/api/v1/admin/courses?q=DeepSeek&page=1&page_size=20", headers=headers)

    assert listed_before.status_code == 200
    assert listed_before.json()["total"] == 1
    assert listed_before.json()["items"][0]["dirty"] is True
    assert cleaned.status_code == 200
    assert cleaned.json()["changed"] == 1
    assert cleaned.json()["scanned"] == 1
    assert listed_after.status_code == 200
    cleaned_item = listed_after.json()["items"][0]
    assert cleaned_item["dirty"] is False
    assert cleaned_item["title"] == "DeepSeek 完整使用手册"
    assert cleaned_item["category"] == "♨️ 热门AI工具使用教程"
    assert cleaned_item["source_path"] == ["♨️ 热门AI工具使用教程", "DeepSeek 完整使用手册"]
    refreshed = session.get(PortalDetailDocument, "detail-dirty")
    assert refreshed is not None
    assert refreshed.body_markdown == "# 标题\n\n正文"
    assert refreshed.summary == "摘要"

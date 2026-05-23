from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import re
import time
from typing import Any, Iterable, Protocol
import urllib.error
import urllib.parse
import urllib.request

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    ContentItem,
    ContentSection,
    FeishuSyncNode,
    FeishuSyncRun,
    PortalDetailDocument,
    PortalDetailVersion,
    utcnow,
)
from app.services.content_sanitizer import clean_markdown, clean_text, is_dirty_markdown, sanitize_markdown
from app.settings import get_settings


FEISHU_BASE_URL = "https://open.feishu.cn"
COURSE_DETAIL_PREFIX = "/learning/courses"
COURSE_SECTION_KEY = "feishu_courses"


@dataclass(frozen=True)
class FeishuWikiNode:
    node_token: str
    obj_token: str
    obj_type: str
    title: str
    has_child: bool = False


class FeishuWikiClientProtocol(Protocol):
    def iter_child_nodes(self, *, space_id: str, parent_node_token: str) -> Iterable[FeishuWikiNode]:
        ...

    def get_docx_markdown(self, document_id: str) -> str:
        ...


class FeishuApiError(RuntimeError):
    pass


class FeishuWikiClient:
    def __init__(self, *, app_id: str, app_secret: str, base_url: str = FEISHU_BASE_URL, sleep_seconds: float = 0.12):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self.sleep_seconds = sleep_seconds
        self._tenant_access_token = ""

    def iter_child_nodes(self, *, space_id: str, parent_node_token: str) -> Iterable[FeishuWikiNode]:
        page_token = ""
        while True:
            params = {"page_size": "50"}
            if parent_node_token:
                params["parent_node_token"] = parent_node_token
            if page_token:
                params["page_token"] = page_token
            payload = self._request_json(
                "GET",
                f"/open-apis/wiki/v2/spaces/{urllib.parse.quote(space_id, safe='')}/nodes",
                query=params,
            )
            data = payload.get("data") or {}
            for item in data.get("items") or []:
                yield _node_from_payload(item)
            if not data.get("has_more"):
                break
            page_token = str(data.get("page_token") or "")
            if not page_token:
                break

    def get_docx_markdown(self, document_id: str) -> str:
        payload = self._request_json(
            "GET",
            f"/open-apis/docx/v1/documents/{urllib.parse.quote(document_id, safe='')}/raw_content",
            query={"lang": "0"},
        )
        data = payload.get("data") or {}
        content = data.get("content") or data.get("raw_content") or data.get("text") or ""
        if not isinstance(content, str):
            raise FeishuApiError("Feishu raw content response did not include markdown text")
        return content

    def _tenant_token(self) -> str:
        if self._tenant_access_token:
            return self._tenant_access_token
        payload = self._request_json(
            "POST",
            "/open-apis/auth/v3/tenant_access_token/internal",
            body={"app_id": self.app_id, "app_secret": self.app_secret},
            authenticated=False,
        )
        token = str((payload.get("tenant_access_token") or payload.get("data", {}).get("tenant_access_token") or "")).strip()
        if not token:
            raise FeishuApiError("Feishu tenant_access_token response was empty")
        self._tenant_access_token = token
        return token

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        if self.sleep_seconds > 0 and authenticated:
            time.sleep(self.sleep_seconds)
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if authenticated:
            headers["Authorization"] = f"Bearer {self._tenant_token()}"
        data = None if body is None else _json_bytes(body)
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    payload = _json_loads(response.read().decode("utf-8"))
                code = int(payload.get("code", 0) or 0)
                if code not in {0, 200}:
                    raise FeishuApiError(str(payload.get("msg") or payload.get("message") or payload))
                return payload
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 3:
                    break
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt == 3:
                    break
            time.sleep(0.5 * (2 ** attempt))
        raise FeishuApiError(str(last_error or "Feishu request failed"))


class FeishuImportService:
    def __init__(self, session: Session, client: FeishuWikiClientProtocol | None = None):
        self.session = session
        self.client = client

    def sync_wiki(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        space_id: str,
        root_node_token: str,
        required_membership: bool,
    ) -> dict[str, Any]:
        run = FeishuSyncRun(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            space_id=space_id,
            root_node_token=root_node_token,
            status="RUNNING",
            started_at=utcnow(),
        )
        self.session.add(run)
        self.session.flush()
        errors: list[str] = []
        try:
            if self.client is None:
                self.client = _client_from_settings()
            self._ensure_course_section(tenant_id=tenant_id)
            for node, source_path in self._walk(space_id=space_id, root_node_token=root_node_token):
                self._sync_node(
                    tenant_id=tenant_id,
                    run=run,
                    node=node,
                    source_path=source_path,
                    required_membership=required_membership,
                    errors=errors,
                )
            run.status = "SUCCESS" if run.failed_count == 0 else "PARTIAL_SUCCESS"
        except Exception as exc:
            run.status = "FAILED"
            run.failed_count += 1
            errors.append(str(exc))
        run.error_summary = "\n".join(errors[:20])
        run.finished_at = utcnow()
        self.session.commit()
        return {"run": self.run_payload(run), "stats": _run_stats(run), "status": run.status}

    def get_run(self, *, tenant_id: str, run_id: str) -> dict[str, Any] | None:
        run = self.session.scalar(select(FeishuSyncRun).where(FeishuSyncRun.tenant_id == tenant_id, FeishuSyncRun.id == run_id))
        if run is None:
            return None
        return {"run": self.run_payload(run)}

    def import_browser_snapshot(
        self,
        *,
        tenant_id: str,
        actor_user_id: str,
        title: str,
        source_url: str,
        node_token: str | None,
        source_path: list[str],
        body_markdown: str,
        asset_url_map: dict[str, str] | None = None,
        required_membership: bool,
    ) -> dict[str, Any]:
        clean_title = _sanitize_feishu_text(title).strip() or "Feishu Course"
        clean_source_path = [
            cleaned
            for part in source_path
            if (cleaned := _sanitize_feishu_text(part).strip())
        ]
        if not clean_source_path:
            clean_source_path = ["Feishu Browser", clean_title]
        elif clean_source_path[-1] != clean_title:
            clean_source_path = [*clean_source_path, clean_title]
        token = _snapshot_node_token(source_url=source_url, node_token=node_token, title=clean_title)
        body = _sanitize_feishu_markdown(body_markdown).strip()
        body = _rewrite_markdown_image_urls(body, asset_url_map or {})
        node = FeishuWikiNode(
            node_token=token,
            obj_token=token,
            obj_type="browser_snapshot",
            title=clean_title,
            has_child=False,
        )
        run = FeishuSyncRun(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            space_id="browser",
            root_node_token=token,
            status="RUNNING",
            started_at=utcnow(),
        )
        self.session.add(run)
        self.session.flush()
        self._ensure_course_section(tenant_id=tenant_id)
        detail_path = f"{COURSE_DETAIL_PREFIX}/{token}"
        sync_node = self._ensure_sync_node(tenant_id=tenant_id, run_id=run.id, node=node)
        sync_node.run_id = run.id
        sync_node.obj_token = token
        sync_node.obj_type = "browser_snapshot"
        sync_node.title = clean_title
        sync_node.source_path = clean_source_path
        sync_node.detail_path = detail_path
        sync_node.error_message = ""
        run.total_nodes = 1
        try:
            content_hash = sha256(body.encode("utf-8")).hexdigest()
            if sync_node.content_hash == content_hash and self._detail_document(tenant_id=tenant_id, detail_path=detail_path):
                sync_node.status = "SKIPPED"
                sync_node.synced_at = utcnow()
                run.skipped_count = 1
            else:
                is_new = not bool(sync_node.content_hash)
                item = self._upsert_content_item(
                    tenant_id=tenant_id,
                    node=node,
                    source_path=clean_source_path,
                    detail_path=detail_path,
                    required_membership=required_membership,
                )
                item.metadata_json = {
                    **(item.metadata_json or {}),
                    "source": {
                        "provider": "feishu-browser",
                        "nodeToken": token,
                        "objToken": token,
                        "objType": "browser_snapshot",
                        "path": clean_source_path,
                        "url": source_url,
                    },
                    "menuKeys": ["growth"],
                }
                document = self._upsert_document(
                    tenant_id=tenant_id,
                    item=item,
                    node=node,
                    source_path=clean_source_path,
                    detail_path=detail_path,
                    body_markdown=body,
                    created=is_new,
                )
                document.author_user_id = actor_user_id
                sync_node.content_hash = content_hash
                sync_node.status = "SYNCED"
                sync_node.synced_at = utcnow()
                if is_new:
                    run.created_count = 1
                else:
                    run.updated_count = 1
                self._snapshot_version(document=document, release_note="Feishu browser snapshot")
            run.status = "SUCCESS"
        except Exception as exc:
            sync_node.status = "FAILED"
            sync_node.error_message = str(exc)
            sync_node.synced_at = utcnow()
            run.failed_count = 1
            run.status = "FAILED"
            run.error_summary = str(exc)
        run.finished_at = utcnow()
        self.session.commit()
        return {"run": self.run_payload(run), "stats": _run_stats(run), "status": run.status}

    def _walk(self, *, space_id: str, root_node_token: str) -> Iterable[tuple[FeishuWikiNode, list[str]]]:
        stack: list[tuple[str, list[str]]] = [(root_node_token, [])]
        while stack:
            parent_token, parent_path = stack.pop()
            children = list(self.client.iter_child_nodes(space_id=space_id, parent_node_token=parent_token))
            for node in reversed(children):
                path = [*parent_path, node.title]
                if node.has_child:
                    stack.append((node.node_token, path))
                yield node, path

    def _sync_node(
        self,
        *,
        tenant_id: str,
        run: FeishuSyncRun,
        node: FeishuWikiNode,
        source_path: list[str],
        required_membership: bool,
        errors: list[str],
    ) -> None:
        run.total_nodes += 1
        detail_path = f"{COURSE_DETAIL_PREFIX}/{node.node_token}"
        sync_node = self._ensure_sync_node(tenant_id=tenant_id, run_id=run.id, node=node)
        sync_node.run_id = run.id
        sync_node.obj_token = node.obj_token
        sync_node.obj_type = node.obj_type
        sync_node.title = node.title
        sync_node.source_path = source_path
        sync_node.detail_path = detail_path
        sync_node.error_message = ""
        try:
            if node.obj_type != "docx":
                sync_node.status = "UNSUPPORTED"
                sync_node.error_message = f"unsupported Feishu obj_type: {node.obj_type}"
                sync_node.synced_at = utcnow()
                run.unsupported_count += 1
                self.session.flush()
                return
            body = _sanitize_feishu_markdown(self.client.get_docx_markdown(node.obj_token)).strip()
            content_hash = sha256(body.encode("utf-8")).hexdigest()
            if sync_node.content_hash == content_hash and self._detail_document(tenant_id=tenant_id, detail_path=detail_path):
                sync_node.status = "SKIPPED"
                sync_node.synced_at = utcnow()
                run.skipped_count += 1
                self.session.flush()
                return
            is_new = not bool(sync_node.content_hash)
            item = self._upsert_content_item(
                tenant_id=tenant_id,
                node=node,
                source_path=source_path,
                detail_path=detail_path,
                required_membership=required_membership,
            )
            document = self._upsert_document(
                tenant_id=tenant_id,
                item=item,
                node=node,
                source_path=source_path,
                detail_path=detail_path,
                body_markdown=body,
                created=is_new,
            )
            sync_node.content_hash = content_hash
            sync_node.status = "SYNCED"
            sync_node.synced_at = utcnow()
            if is_new:
                run.created_count += 1
            else:
                run.updated_count += 1
            self._snapshot_version(document=document, release_note="飞书知识库同步")
            self.session.flush()
        except Exception as exc:
            sync_node.status = "FAILED"
            sync_node.error_message = str(exc)
            sync_node.synced_at = utcnow()
            run.failed_count += 1
            errors.append(f"{node.title}: {exc}")
            self.session.flush()

    def _ensure_sync_node(self, *, tenant_id: str, run_id: str, node: FeishuWikiNode) -> FeishuSyncNode:
        record = self.session.scalar(
            select(FeishuSyncNode).where(
                FeishuSyncNode.tenant_id == tenant_id,
                FeishuSyncNode.node_token == node.node_token,
            )
        )
        if record is not None:
            return record
        record = FeishuSyncNode(
            tenant_id=tenant_id,
            run_id=run_id,
            node_token=node.node_token,
            obj_token=node.obj_token,
            obj_type=node.obj_type,
            title=node.title,
        )
        self.session.add(record)
        return record

    def _ensure_course_section(self, *, tenant_id: str) -> ContentSection:
        section = self.session.scalar(
            select(ContentSection).where(
                ContentSection.tenant_id == tenant_id,
                ContentSection.area == "home",
                ContentSection.section_key == COURSE_SECTION_KEY,
            )
        )
        if section is not None:
            return section
        section = ContentSection(
            id=f"section-feishu-courses-{tenant_id}",
            tenant_id=tenant_id,
            area="home",
            section_key=COURSE_SECTION_KEY,
            title="副业课程库",
            subtitle="从飞书知识库同步的课程与实操复盘",
            layout="course-library",
            sort_order=65,
            enabled=True,
        )
        self.session.add(section)
        self.session.flush()
        return section

    def _upsert_content_item(
        self,
        *,
        tenant_id: str,
        node: FeishuWikiNode,
        source_path: list[str],
        detail_path: str,
        required_membership: bool,
    ) -> ContentItem:
        section = self._ensure_course_section(tenant_id=tenant_id)
        item_id = f"feishu-course-{node.node_token}"[:120]
        item = self.session.scalar(
            select(ContentItem).where(
                ContentItem.tenant_id == tenant_id,
                ContentItem.action_value == detail_path,
            )
        )
        if item is None:
            item = self.session.get(ContentItem, item_id)
        if item is None:
            item = ContentItem(id=item_id, tenant_id=tenant_id, section_id=section.id)
            self.session.add(item)
        item.item_type = "course"
        item.title = node.title[:255]
        item.subtitle = _subtitle_from_path(source_path)
        item.category = _category_from_path(source_path)
        item.icon = "NotebookTabs"
        item.badge = item.category
        item.tags = _tags_from_path(source_path)
        item.sort_order = 100
        item.enabled = True
        item.action_type = "route"
        item.action_value = detail_path
        item.required_membership = required_membership
        item.point_cost = 0
        item.metadata_json = {
            **(item.metadata_json or {}),
            "source": {
                "provider": "feishu",
                "nodeToken": node.node_token,
                "objToken": node.obj_token,
                "objType": node.obj_type,
                "path": source_path,
            },
            "menuKeys": ["growth"],
        }
        return item

    def _upsert_document(
        self,
        *,
        tenant_id: str,
        item: ContentItem,
        node: FeishuWikiNode,
        source_path: list[str],
        detail_path: str,
        body_markdown: str,
        created: bool,
    ) -> PortalDetailDocument:
        document = self._detail_document(tenant_id=tenant_id, detail_path=detail_path)
        if document is None:
            document = PortalDetailDocument(
                id=f"detail-feishu-{node.node_token}"[:120],
                tenant_id=tenant_id,
                detail_path=detail_path,
                current_version=0,
                author_user_id="demo-admin",
                status="PUBLISHED",
                published_at=utcnow(),
            )
            self.session.add(document)
        document.title = node.title[:255]
        document.summary = _summary_from_markdown(body_markdown, fallback=item.subtitle)
        document.body_markdown = body_markdown
        document.tags = _tags_from_path(source_path)
        document.visibility = "members" if item.required_membership else "community"
        document.release_note = "飞书知识库同步" if created else "飞书知识库更新"
        document.status = "PUBLISHED"
        document.published_at = utcnow()
        document.current_version = max(0, document.current_version)
        return document

    def _snapshot_version(self, *, document: PortalDetailDocument, release_note: str) -> None:
        next_version = document.current_version + 1
        version_id = f"{document.id}-v{next_version}"
        if self.session.get(PortalDetailVersion, version_id) is not None:
            return
        document.current_version = next_version
        document.release_note = release_note
        self.session.add(
            PortalDetailVersion(
                id=version_id,
                tenant_id=document.tenant_id,
                document_id=document.id,
                detail_path=document.detail_path,
                version=next_version,
                title=document.title,
                summary=document.summary,
                body_markdown=document.body_markdown,
                tags=document.tags or [],
                visibility=document.visibility,
                release_note=release_note,
                author_user_id=document.author_user_id,
            )
        )

    def _detail_document(self, *, tenant_id: str, detail_path: str) -> PortalDetailDocument | None:
        return self.session.scalar(
            select(PortalDetailDocument).where(
                PortalDetailDocument.tenant_id == tenant_id,
                PortalDetailDocument.detail_path == detail_path,
            )
        )

    @staticmethod
    def run_payload(run: FeishuSyncRun) -> dict[str, Any]:
        return {
            "id": run.id,
            "tenant_id": run.tenant_id,
            "actor_user_id": run.actor_user_id,
            "space_id": run.space_id,
            "root_node_token": run.root_node_token,
            "status": run.status,
            "stats": _run_stats(run),
            "error_summary": run.error_summary,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }


class CourseCatalogService:
    def __init__(self, session: Session):
        self.session = session

    def list_courses(self, *, tenant_id: str, query: str = "", category: str = "", page: int = 1, page_size: int = 20) -> dict[str, Any]:
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        stmt = self._base_query(tenant_id=tenant_id)
        if query.strip():
            term = f"%{query.strip()}%"
            stmt = stmt.where(or_(ContentItem.title.ilike(term), ContentItem.subtitle.ilike(term), ContentItem.category.ilike(term)))
        if category.strip():
            stmt = stmt.where(ContentItem.category == category.strip())
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self.session.execute(
            stmt.order_by(ContentItem.updated_at.desc(), ContentItem.sort_order.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        categories = [
            value
            for value in self.session.scalars(
                select(ContentItem.category)
                .join(ContentSection, ContentSection.id == ContentItem.section_id)
                .where(
                    ContentItem.tenant_id == tenant_id,
                    ContentItem.item_type == "course",
                    ContentItem.enabled.is_(True),
                    ContentSection.section_key == COURSE_SECTION_KEY,
                )
                .distinct()
                .order_by(ContentItem.category.asc())
            ).all()
            if value
        ]
        return {
            "tenant_id": tenant_id,
            "page": page,
            "page_size": page_size,
            "total": total,
            "categories": categories,
            "items": [self._course_payload(item, document) for item, document in rows],
        }

    def _base_query(self, *, tenant_id: str):
        return (
            select(ContentItem, PortalDetailDocument)
            .join(ContentSection, ContentSection.id == ContentItem.section_id)
            .outerjoin(
                PortalDetailDocument,
                (PortalDetailDocument.tenant_id == ContentItem.tenant_id)
                & (PortalDetailDocument.detail_path == ContentItem.action_value),
            )
            .where(
                ContentItem.tenant_id == tenant_id,
                ContentItem.item_type == "course",
                ContentItem.enabled.is_(True),
                ContentSection.section_key == COURSE_SECTION_KEY,
            )
        )

    @staticmethod
    def _course_payload(item: ContentItem, document: PortalDetailDocument | None) -> dict[str, Any]:
        metadata = item.metadata_json or {}
        source = metadata.get("source") if isinstance(metadata, dict) else {}
        source_path = source.get("path") if isinstance(source, dict) else []
        return {
            "id": item.id,
            "title": document.title if document and document.title else item.title,
            "subtitle": document.summary if document and document.summary else item.subtitle,
            "category": item.category,
            "tags": item.tags or [],
            "detail_path": item.action_value,
            "required_membership": item.required_membership,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "source_path": source_path if isinstance(source_path, list) else [],
        }


class CourseAdminService:
    def __init__(self, session: Session):
        self.session = session
        self.catalog = CourseCatalogService(session)

    def list_courses(
        self,
        *,
        tenant_id: str,
        query: str = "",
        category: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        payload = self.catalog.list_courses(
            tenant_id=tenant_id,
            query=query,
            category=category,
            page=page,
            page_size=page_size,
        )
        items_by_id = {
            item.id: (item, document)
            for item, document in self.session.execute(self.catalog._base_query(tenant_id=tenant_id)).all()
        }
        payload["items"] = [
            {
                **item_payload,
                "dirty": _course_is_dirty(*items_by_id.get(item_payload["id"], (None, None))),
            }
            for item_payload in payload["items"]
        ]
        return payload

    def cleanup_courses(self, *, tenant_id: str) -> dict[str, Any]:
        rows = self.session.execute(self.catalog._base_query(tenant_id=tenant_id)).all()
        changed = 0
        dirty_remaining = 0
        for item, document in rows:
            did_change = self._cleanup_item(item=item, document=document)
            if did_change:
                changed += 1
            if _course_is_dirty(item, document):
                dirty_remaining += 1
        self.session.commit()
        return {
            "tenant_id": tenant_id,
            "scanned": len(rows),
            "changed": changed,
            "dirty_remaining": dirty_remaining,
        }

    def _cleanup_item(self, *, item: ContentItem, document: PortalDetailDocument | None) -> bool:
        changed = False
        cleaned_title = clean_text(item.title)
        cleaned_subtitle = clean_text(item.subtitle)
        cleaned_category = clean_text(item.category)
        cleaned_badge = clean_text(item.badge)
        cleaned_tags = [clean_text(tag) for tag in (item.tags or []) if clean_text(tag)]
        if item.title != cleaned_title:
            item.title = cleaned_title
            changed = True
        if item.subtitle != cleaned_subtitle:
            item.subtitle = cleaned_subtitle
            changed = True
        if item.category != cleaned_category:
            item.category = cleaned_category
            changed = True
        if item.badge != cleaned_badge:
            item.badge = cleaned_badge
            changed = True
        if (item.tags or []) != cleaned_tags:
            item.tags = cleaned_tags
            changed = True
        metadata = item.metadata_json or {}
        source = metadata.get("source") if isinstance(metadata, dict) else None
        if isinstance(source, dict):
            source_path = source.get("path")
            if isinstance(source_path, list):
                cleaned_path = [clean_text(part) for part in source_path if clean_text(part)]
                if source_path != cleaned_path:
                    item.metadata_json = {
                        **metadata,
                        "source": {
                            **source,
                            "path": cleaned_path,
                        },
                    }
                    changed = True
        if document is not None:
            cleaned_doc_title = clean_text(document.title)
            cleaned_summary = clean_markdown(document.summary)
            cleaned_body = sanitize_markdown(document.body_markdown)
            cleaned_doc_tags = [clean_text(tag) for tag in (document.tags or []) if clean_text(tag)]
            if document.title != cleaned_doc_title:
                document.title = cleaned_doc_title
                changed = True
            if document.summary != cleaned_summary:
                document.summary = cleaned_summary
                changed = True
            if document.body_markdown != cleaned_body.text:
                document.body_markdown = cleaned_body.text
                changed = True
            if (document.tags or []) != cleaned_doc_tags:
                document.tags = cleaned_doc_tags
                changed = True
        return changed


def _client_from_settings() -> FeishuWikiClient:
    settings = get_settings()
    if not settings.feishu_app_id or not settings.feishu_app_secret:
        raise FeishuApiError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")
    return FeishuWikiClient(app_id=settings.feishu_app_id, app_secret=settings.feishu_app_secret)


def _node_from_payload(payload: dict[str, Any]) -> FeishuWikiNode:
    return FeishuWikiNode(
        node_token=str(payload.get("node_token") or ""),
        obj_token=str(payload.get("obj_token") or ""),
        obj_type=str(payload.get("obj_type") or ""),
        title=str(payload.get("title") or "未命名课程"),
        has_child=bool(payload.get("has_child")),
    )


def _snapshot_node_token(*, source_url: str, node_token: str | None, title: str) -> str:
    value = (node_token or "").strip()
    if not value:
        match = re.search(r"/wiki/([A-Za-z0-9]+)", source_url)
        if match:
            value = match.group(1)
    if not value:
        value = sha256(f"{source_url}|{title}".encode("utf-8")).hexdigest()[:24]
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")[:120] or sha256(title.encode("utf-8")).hexdigest()[:24]


def _sanitize_feishu_markdown(markdown: str) -> str:
    return clean_markdown(markdown)


def _sanitize_feishu_text(value: str) -> str:
    return clean_text(value)


def _rewrite_markdown_image_urls(markdown: str, asset_url_map: dict[str, str]) -> str:
    replacements = {
        str(source).strip(): str(target).strip()
        for source, target in asset_url_map.items()
        if str(source).strip() and _is_local_storage_url(str(target).strip())
    }
    if not replacements:
        return markdown

    def replace(match: re.Match[str]) -> str:
        alt_text = match.group(1)
        raw_url = match.group(2).strip()
        return f"![{alt_text}]({replacements.get(raw_url, raw_url)})"

    return re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", replace, markdown)


def _is_local_storage_url(value: str) -> bool:
    return value.startswith("/storage/") and not any(char in value for char in "\r\n<>\"'")


def _course_is_dirty(item: ContentItem | None, document: PortalDetailDocument | None) -> bool:
    if item is None:
        return False
    text_values = [
        item.title,
        item.subtitle,
        item.category,
        item.badge,
        *(item.tags or []),
    ]
    if any(clean_text(value) != value for value in text_values):
        return True
    metadata = item.metadata_json or {}
    source = metadata.get("source") if isinstance(metadata, dict) else None
    if isinstance(source, dict):
        source_path = source.get("path")
        if isinstance(source_path, list) and any(clean_text(part) != part for part in source_path):
            return True
    if document is None:
        return False
    document_values = [document.title, *(document.tags or [])]
    if any(clean_text(value) != value for value in document_values):
        return True
    if clean_markdown(document.summary) != document.summary:
        return True
    return is_dirty_markdown(document.body_markdown) or clean_markdown(document.body_markdown) != document.body_markdown


def _run_stats(run: FeishuSyncRun) -> dict[str, int]:
    return {
        "total": run.total_nodes,
        "created": run.created_count,
        "updated": run.updated_count,
        "skipped": run.skipped_count,
        "unsupported": run.unsupported_count,
        "failed": run.failed_count,
    }


def _category_from_path(source_path: list[str]) -> str:
    if len(source_path) >= 2:
        return source_path[0]
    return "飞书课程"


def _subtitle_from_path(source_path: list[str]) -> str:
    if len(source_path) <= 1:
        return "飞书知识库同步课程"
    return " / ".join(source_path[:-1])


def _tags_from_path(source_path: list[str]) -> list[str]:
    return [value for value in source_path[:-1] if value][:8]


def _summary_from_markdown(markdown: str, *, fallback: str) -> str:
    for line in markdown.splitlines():
        cleaned = line.strip().lstrip("#").strip()
        if cleaned:
            return cleaned[:500]
    return fallback[:500]


def _json_bytes(payload: dict[str, Any]) -> bytes:
    import json

    return json.dumps(payload).encode("utf-8")


def _json_loads(raw: str) -> dict[str, Any]:
    import json

    value = json.loads(raw)
    return value if isinstance(value, dict) else {}

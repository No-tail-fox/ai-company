from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import AiAssistant, ContentItem, ContentPage, ContentSection, PromptTemplate, UserPortalAction
from app.schemas import PortalActionCreate
from app.services.memberships import MembershipService
from app.services.model_configs import ModelConfigService


class PortalService:
    def __init__(self, session: Session):
        self.session = session
        self.model_configs = ModelConfigService(session)

    def get_portal_config(self, *, tenant_id: str) -> dict:
        pages = self._enabled_pages(tenant_id=tenant_id)
        home_sections = self._enabled_sections(tenant_id=tenant_id, page_key="home")
        home_items = self._enabled_items_by_section(tenant_id=tenant_id, sections=home_sections)

        page_payloads = [self._page_payload(page) for page in pages] or self._default_pages()
        return {
            "tenant_id": tenant_id,
            "pages": page_payloads,
            "channels": [{"key": page["page_key"], "label": page["label"]} for page in page_payloads],
            "left_nav": self._default_left_nav(),
            "home_sections": [
                self._section_payload(section, home_items.get(section.id, []))
                for section in home_sections
            ],
        }

    def get_page_config(self, *, tenant_id: str, page_key: str) -> dict | None:
        page = self.session.scalar(
            select(ContentPage).where(
                ContentPage.tenant_id == tenant_id,
                ContentPage.page_key == page_key,
                ContentPage.enabled.is_(True),
            )
        )
        if page is None:
            return None
        if page_key == "audio":
            return {
                "tenant_id": tenant_id,
                "page": self._page_payload(page),
                "sections": self._audio_catalog_sections(tenant_id=tenant_id, page=page),
            }
        sections = self._enabled_sections(tenant_id=tenant_id, page_key=page_key)
        items_by_section = self._enabled_items_by_section(tenant_id=tenant_id, sections=sections)
        return {
            "tenant_id": tenant_id,
            "page": self._page_payload(page),
            "sections": [
                self._section_payload(section, items_by_section.get(section.id, []))
                for section in sections
            ],
        }

    def get_detail(self, *, tenant_id: str, detail_path: str, user_id: str = "demo-user") -> dict | None:
        path = _normalize_detail_path(detail_path)
        rows = self._items_for_path(tenant_id=tenant_id, detail_path=path)
        if not rows:
            return None

        items = [row[0] for row in rows]
        sections = [row[1] for row in rows]
        primary_item = items[0]
        primary_section = sections[0]
        detail = _detail_metadata(primary_item, path=path)
        membership_active = MembershipService(self.session).get_status(tenant_id=tenant_id, user_id=user_id)["active"]
        required_membership = any(item.required_membership for item in items)
        completed_actions = self._completed_action_keys(tenant_id=tenant_id, user_id=user_id, detail_path=path)
        return {
            "path": path,
            "kind": "directory" if len(items) > 1 else primary_item.item_type,
            "title": primary_section.title if len(items) > 1 else primary_item.title,
            "subtitle": primary_section.subtitle if len(items) > 1 else primary_item.subtitle,
            "icon": primary_item.icon or "Sparkles",
            "requiredMembership": required_membership,
            "effectivePointCost": max(
                self._item_payload(item)["effective_point_cost"]
                for item in items
            ),
            "items": [self._item_payload(item) for item in items],
            "detail": detail,
            "userState": {
                "membershipActive": membership_active,
                "locked": required_membership and not membership_active,
                "completedActions": completed_actions,
            },
        }

    def search(self, *, tenant_id: str, query: str, page_key: str | None = None, limit: int = 8) -> dict:
        keyword = query.strip()
        if not keyword:
            return {"results": []}
        term = f"%{keyword}%"
        limit = max(1, min(limit, 20))
        results: list[dict] = []

        page_query = select(ContentPage).where(
            ContentPage.tenant_id == tenant_id,
            ContentPage.enabled.is_(True),
            or_(
                ContentPage.label.ilike(term),
                ContentPage.title.ilike(term),
                ContentPage.subtitle.ilike(term),
            ),
        )
        if page_key:
            page_query = page_query.where(ContentPage.page_key == page_key)
        for page in self.session.scalars(page_query.order_by(ContentPage.sort_order.asc())).all():
            results.append(
                {
                    "id": page.id,
                    "title": page.title,
                    "subtitle": page.subtitle,
                    "type": "page",
                    "pageKey": page.page_key,
                    "path": f"/{page.page_key}",
                    "icon": page.icon,
                }
            )
            if len(results) >= limit:
                return {"results": results}

        item_query = (
            select(ContentItem, ContentSection)
            .join(ContentSection, ContentSection.id == ContentItem.section_id)
            .where(
                ContentItem.tenant_id == tenant_id,
                ContentItem.enabled.is_(True),
                ContentSection.enabled.is_(True),
                or_(
                    ContentItem.title.ilike(term),
                    ContentItem.subtitle.ilike(term),
                    ContentItem.category.ilike(term),
                    ContentSection.title.ilike(term),
                ),
            )
            .order_by(ContentSection.sort_order.asc(), ContentItem.sort_order.asc())
        )
        if page_key:
            item_query = item_query.where(ContentSection.area == page_key)
        for item, section in self.session.execute(item_query).all():
            results.append(
                {
                    "id": item.id,
                    "title": item.title,
                    "subtitle": item.subtitle,
                    "type": item.item_type,
                    "pageKey": section.area,
                    "path": item.action_value if item.action_value.startswith("/") else f"/{section.area}",
                    "icon": item.icon or "Sparkles",
                }
            )
            if len(results) >= limit:
                return {"results": results}

        if not page_key:
            for assistant in self.session.scalars(
                select(AiAssistant)
                .where(
                    AiAssistant.tenant_id == tenant_id,
                    AiAssistant.enabled.is_(True),
                    or_(
                        AiAssistant.name.ilike(term),
                        AiAssistant.description.ilike(term),
                        AiAssistant.category.ilike(term),
                    ),
                )
                .order_by(AiAssistant.sort_order.asc())
            ).all():
                results.append(
                    {
                        "id": assistant.id,
                        "title": assistant.name,
                        "subtitle": assistant.description,
                        "type": "assistant",
                        "pageKey": "assistant",
                        "path": "/assistant",
                        "icon": assistant.icon,
                    }
                )
                if len(results) >= limit:
                    return {"results": results}

            for template in self.session.scalars(
                select(PromptTemplate)
                .where(
                    PromptTemplate.tenant_id == tenant_id,
                    PromptTemplate.enabled.is_(True),
                    or_(
                        PromptTemplate.title.ilike(term),
                        PromptTemplate.content.ilike(term),
                        PromptTemplate.category.ilike(term),
                    ),
                )
                .order_by(PromptTemplate.sort_order.asc())
            ).all():
                results.append(
                    {
                        "id": template.id,
                        "title": template.title,
                        "subtitle": template.content[:80],
                        "type": "prompt_template",
                        "pageKey": "assistant",
                        "path": "/assistant",
                        "icon": "FileText",
                    }
                )
                if len(results) >= limit:
                    break

        return {"results": results[:limit]}

    def perform_action(self, *, tenant_id: str, payload: PortalActionCreate) -> dict:
        path = _normalize_detail_path(payload.detail_path)
        rows = self._items_for_path(tenant_id=tenant_id, detail_path=path)
        item = _select_action_item([row[0] for row in rows], payload.item_id)
        membership_active = MembershipService(self.session).get_status(tenant_id=tenant_id, user_id=payload.user_id)["active"]
        if item is not None and item.required_membership and not membership_active:
            return {
                "status": "locked",
                "message": "该内容需要会员权限，开通会员后即可使用。",
                "action": None,
                "download": None,
                "route": None,
            }

        item_id = item.id if item is not None else payload.item_id or ""
        existing = self.session.scalar(
            select(UserPortalAction).where(
                UserPortalAction.tenant_id == tenant_id,
                UserPortalAction.user_id == payload.user_id,
                UserPortalAction.detail_path == path,
                UserPortalAction.action_key == payload.action_key,
                UserPortalAction.item_id == item_id,
            )
        )
        detail = _detail_metadata(item, path=path) if item is not None else _default_detail(path=path, title=path.strip("/") or "操作")
        download = detail.get("download") if payload.action_key in {"download", "claim", "backup"} else None
        result = {"download": download} if download else None
        message = _action_message(payload.action_key)
        if existing is None:
            existing = UserPortalAction(
                tenant_id=tenant_id,
                user_id=payload.user_id,
                detail_path=path,
                item_id=item_id,
                action_key=payload.action_key,
                status="COMPLETED",
                message=message,
                result_json=result,
            )
            self.session.add(existing)
        else:
            existing.status = "COMPLETED"
            existing.message = existing.message or message
            existing.result_json = existing.result_json or result
        self.session.commit()
        return {
            "status": "completed",
            "message": existing.message,
            "action": self._action_payload(existing),
            "download": download,
            "route": item.action_value if item is not None and item.action_type == "workspace" else None,
        }

    def user_actions(self, *, tenant_id: str, user_id: str, kind: str = "all", limit: int = 20) -> dict:
        query = select(UserPortalAction).where(
            UserPortalAction.tenant_id == tenant_id,
            UserPortalAction.user_id == user_id,
        )
        if kind != "all":
            query = query.where(UserPortalAction.action_key == kind)
        records = list(
            self.session.scalars(
                query.order_by(UserPortalAction.updated_at.desc(), UserPortalAction.created_at.desc()).limit(max(1, min(limit, 50)))
            )
        )
        return {"actions": [self._action_payload(record) for record in records]}

    def _audio_catalog_sections(self, *, tenant_id: str, page: ContentPage) -> list[dict]:
        page_key = page.page_key
        return [
            self._catalog_section(
                tenant_id=tenant_id,
                page_key=page_key,
                section_key="overview",
                title=page.title,
                layout="stat-strip",
                items=[
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-overview",
                        item_id=f"{page_key}-stat-1",
                        item_type="stat",
                        title="本周热度",
                        subtitle="使用量持续增长",
                        category="概览",
                        icon="Flame",
                        action_value=f"/{page_key}",
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-overview",
                        item_id=f"{page_key}-stat-2",
                        item_type="stat",
                        title="会员专享",
                        subtitle="高阶模板开放",
                        category="概览",
                        icon="Gift",
                        action_value=f"/{page_key}",
                        required_membership=True,
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-overview",
                        item_id=f"{page_key}-stat-3",
                        item_type="stat",
                        title="交付案例",
                        subtitle="沉淀可复用方案",
                        category="概览",
                        icon="BriefcaseBusiness",
                        action_value=f"/{page_key}",
                    ),
                ],
            ),
            self._catalog_section(
                tenant_id=tenant_id,
                page_key=page_key,
                section_key="tools",
                title=f"{page.label}工具矩阵",
                layout="tool-grid",
                items=[
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-tools",
                        item_id=f"{page_key}-tool-1",
                        item_type="tool",
                        title="文本转语音",
                        subtitle="多音色高拟真配音",
                        category="工具",
                        icon="Headphones",
                        action_value="audio_tts",
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-tools",
                        item_id=f"{page_key}-tool-2",
                        item_type="tool",
                        title="声音克隆",
                        subtitle="复用品牌或个人音色",
                        category="工具",
                        icon="CircleUserRound",
                        action_value="audio_voice_clone",
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-tools",
                        item_id=f"{page_key}-tool-3",
                        item_type="tool",
                        title="播客生成",
                        subtitle="一键生成播客旁白内容",
                        category="工具",
                        icon="Mic",
                        action_value="audio_podcast",
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-tools",
                        item_id=f"{page_key}-tool-4",
                        item_type="tool",
                        title="智能降噪",
                        subtitle="去除环境噪音并提升清晰度",
                        category="工具",
                        icon="AudioWaveform",
                        action_value="audio_denoise",
                        required_membership=True,
                    ),
                ],
            ),
            self._catalog_section(
                tenant_id=tenant_id,
                page_key=page_key,
                section_key="templates",
                title="模板与工作流",
                layout="template-list",
                items=[
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-templates",
                        item_id=f"{page_key}-tpl-1",
                        item_type="template",
                        title="播客开场模板",
                        subtitle="适合栏目化内容快速启动",
                        category="模板",
                        icon="Podcast",
                        action_value="audio_podcast",
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-templates",
                        item_id=f"{page_key}-tpl-2",
                        item_type="template",
                        title="广告配音模板",
                        subtitle="适合品牌宣发和产品介绍",
                        category="模板",
                        icon="Megaphone",
                        action_value="audio_tts",
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-templates",
                        item_id=f"{page_key}-tpl-3",
                        item_type="template",
                        title="降噪修复模板",
                        subtitle="适合会议录音和素材清理",
                        category="模板",
                        icon="Waves",
                        action_value="audio_denoise",
                        required_membership=True,
                    ),
                ],
            ),
            self._catalog_section(
                tenant_id=tenant_id,
                page_key=page_key,
                section_key="ranking",
                title="热门推荐",
                layout="ranking-list",
                items=[
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-ranking",
                        item_id=f"{page_key}-rank-1",
                        item_type="ranking",
                        title="最近音频",
                        subtitle="近 7 日 12.8 万次使用",
                        category="热门",
                        icon="Headphones",
                        action_value=f"/{page_key}/recent",
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-ranking",
                        item_id=f"{page_key}-rank-2",
                        item_type="ranking",
                        title="音色库",
                        subtitle="近 7 日 8.6 万次使用",
                        category="热门",
                        icon="CircleUserRound",
                        action_value=f"/{page_key}/voices",
                    ),
                    self._catalog_item(
                        tenant_id=tenant_id,
                        section_id=f"{page_key}-ranking",
                        item_id=f"{page_key}-rank-3",
                        item_type="ranking",
                        title="音频资源",
                        subtitle="近 7 日 7.9 万次使用",
                        category="热门",
                        icon="Music",
                        action_value=f"/{page_key}/resources",
                    ),
                ],
            ),
        ]

    def get_assistant_center(self, *, tenant_id: str, category: str | None = None) -> dict:
        query = select(AiAssistant).where(AiAssistant.tenant_id == tenant_id, AiAssistant.enabled.is_(True))
        if category and category != "全部":
            query = query.where(AiAssistant.category == category)
        assistants = list(self.session.scalars(query.order_by(AiAssistant.sort_order.asc(), AiAssistant.created_at.asc())))
        ranking = sorted(assistants, key=lambda item: item.usage_count, reverse=True)[:10]
        templates = list(
            self.session.scalars(
                select(PromptTemplate)
                .where(
                    PromptTemplate.tenant_id == tenant_id,
                    PromptTemplate.enabled.is_(True),
                )
                .order_by(PromptTemplate.sort_order.asc(), PromptTemplate.created_at.asc())
            )
        )
        categories = ["全部"]
        for assistant in assistants:
            if assistant.category and assistant.category not in categories:
                categories.append(assistant.category)
        return {
            "tenant_id": tenant_id,
            "categories": categories,
            "featured": [self._assistant_payload(item) for item in assistants[:4]],
            "assistants": [self._assistant_payload(item) for item in assistants],
            "ranking": [self._assistant_payload(item) for item in ranking],
            "prompt_templates": [self._template_payload(item) for item in templates],
        }

    def _enabled_pages(self, *, tenant_id: str) -> list[ContentPage]:
        return list(
            self.session.scalars(
                select(ContentPage)
                .where(ContentPage.tenant_id == tenant_id, ContentPage.enabled.is_(True))
                .order_by(ContentPage.sort_order.asc(), ContentPage.created_at.asc())
            )
        )

    def _enabled_sections(self, *, tenant_id: str, page_key: str) -> list[ContentSection]:
        return list(
            self.session.scalars(
                select(ContentSection)
                .where(
                    ContentSection.tenant_id == tenant_id,
                    ContentSection.area == page_key,
                    ContentSection.enabled.is_(True),
                )
                .order_by(ContentSection.sort_order.asc(), ContentSection.created_at.asc())
            )
        )

    def _enabled_items_by_section(self, *, tenant_id: str, sections: list[ContentSection]) -> dict[str, list[ContentItem]]:
        section_ids = [section.id for section in sections]
        if not section_ids:
            return {}
        items = list(
            self.session.scalars(
                select(ContentItem)
                .where(
                    ContentItem.tenant_id == tenant_id,
                    ContentItem.section_id.in_(section_ids),
                    ContentItem.enabled.is_(True),
                )
                .order_by(ContentItem.sort_order.asc(), ContentItem.created_at.asc())
            )
        )
        grouped: dict[str, list[ContentItem]] = {}
        for item in items:
            grouped.setdefault(item.section_id, []).append(item)
        return grouped

    @staticmethod
    def _page_payload(page: ContentPage) -> dict:
        return {
            "id": page.id,
            "tenant_id": page.tenant_id,
            "page_key": page.page_key,
            "label": page.label,
            "title": page.title,
            "subtitle": page.subtitle,
            "icon": page.icon,
            "sort_order": page.sort_order,
            "enabled": page.enabled,
        }

    def _section_payload(self, section: ContentSection, items: list[ContentItem]) -> dict:
        return {
            "id": section.id,
            "tenant_id": section.tenant_id,
            "area": section.area,
            "page_key": section.area,
            "section_key": section.section_key,
            "title": section.title,
            "subtitle": section.subtitle,
            "layout": section.layout,
            "sort_order": section.sort_order,
            "enabled": section.enabled,
            "items": [self._item_payload(item) for item in items],
        }

    def _item_payload(self, item: ContentItem) -> dict:
        model_context = self.model_configs.model_context_for_target(
            tenant_id=item.tenant_id,
            target_type="content_item",
            target_key=item.id,
        )
        return {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "section_id": item.section_id,
            "item_type": item.item_type,
            "title": item.title,
            "subtitle": item.subtitle,
            "category": item.category,
            "icon": item.icon,
            "image_url": item.image_url,
            "badge": item.badge,
            "tags": item.tags or [],
            "sort_order": item.sort_order,
            "enabled": item.enabled,
            "action_type": item.action_type,
            "action_value": item.action_value,
            "required_membership": item.required_membership,
            "point_cost": item.point_cost,
            "effective_point_cost": model_context["effective_point_cost"] if model_context["effective_point_cost"] is not None else item.point_cost,
            "model_config": model_context["model_config"],
            "metadata_json": item.metadata_json or {},
        }

    def _items_for_path(self, *, tenant_id: str, detail_path: str) -> list[tuple[ContentItem, ContentSection]]:
        return list(
            self.session.execute(
                select(ContentItem, ContentSection)
                .join(ContentSection, ContentSection.id == ContentItem.section_id)
                .where(
                    ContentItem.tenant_id == tenant_id,
                    ContentItem.enabled.is_(True),
                    ContentItem.action_value == detail_path,
                    ContentSection.enabled.is_(True),
                )
                .order_by(ContentSection.sort_order.asc(), ContentItem.sort_order.asc(), ContentItem.created_at.asc())
            ).all()
        )

    def _completed_action_keys(self, *, tenant_id: str, user_id: str, detail_path: str) -> list[str]:
        records = self.session.scalars(
            select(UserPortalAction).where(
                UserPortalAction.tenant_id == tenant_id,
                UserPortalAction.user_id == user_id,
                UserPortalAction.detail_path == detail_path,
                UserPortalAction.status == "COMPLETED",
            )
        )
        return sorted({record.action_key for record in records})

    @staticmethod
    def _action_payload(action: UserPortalAction) -> dict:
        return {
            "id": action.id,
            "tenant_id": action.tenant_id,
            "user_id": action.user_id,
            "detail_path": action.detail_path,
            "item_id": action.item_id,
            "action_key": action.action_key,
            "status": action.status,
            "message": action.message,
            "result": action.result_json or {},
            "created_at": action.created_at.isoformat() if action.created_at else None,
            "updated_at": action.updated_at.isoformat() if action.updated_at else None,
        }

    @staticmethod
    def _catalog_section(*, tenant_id: str, page_key: str, section_key: str, title: str, layout: str, items: list[dict]) -> dict:
        return {
            "id": f"section-{page_key}-{section_key}",
            "tenant_id": tenant_id,
            "area": page_key,
            "page_key": page_key,
            "section_key": section_key,
            "title": title,
            "subtitle": "",
            "layout": layout,
            "sort_order": 100,
            "enabled": True,
            "items": items,
        }

    @staticmethod
    def _catalog_item(
        *,
        tenant_id: str,
        section_id: str,
        item_id: str,
        item_type: str,
        title: str,
        subtitle: str,
        category: str,
        icon: str,
        action_value: str,
        required_membership: bool = False,
    ) -> dict:
        return {
            "id": item_id,
            "tenant_id": tenant_id,
            "section_id": section_id,
            "item_type": item_type,
            "title": title,
            "subtitle": subtitle,
            "category": category,
            "icon": icon,
            "image_url": "",
            "badge": "",
            "tags": [],
            "sort_order": 100,
            "enabled": True,
            "action_type": "workspace" if action_value.startswith("audio_") else "route",
            "action_value": action_value,
            "required_membership": required_membership,
            "point_cost": 0,
            "effective_point_cost": 0,
            "model_config": None,
        }

    def _assistant_payload(self, assistant: AiAssistant) -> dict:
        model_context = self.model_configs.model_context_for_target(
            tenant_id=assistant.tenant_id,
            target_type="assistant",
            target_key=assistant.id,
        )
        return {
            "id": assistant.id,
            "tenant_id": assistant.tenant_id,
            "assistant_key": assistant.assistant_key,
            "name": assistant.name,
            "description": assistant.description,
            "category": assistant.category,
            "icon": assistant.icon,
            "usage_count": assistant.usage_count,
            "usage_count_label": self._usage_label(assistant.usage_count),
            "action_type": assistant.action_type,
            "action_value": assistant.action_value,
            "required_membership": assistant.required_membership,
            "point_cost": assistant.point_cost,
            "effective_point_cost": model_context["effective_point_cost"] if model_context["effective_point_cost"] is not None else assistant.point_cost,
            "model_config": model_context["model_config"],
        }

    def _template_payload(self, template: PromptTemplate) -> dict:
        model_context = self.model_configs.model_context_for_target(
            tenant_id=template.tenant_id,
            target_type="prompt_template",
            target_key=template.id,
        )
        return {
            "id": template.id,
            "tenant_id": template.tenant_id,
            "template_key": template.template_key,
            "title": template.title,
            "category": template.category,
            "content": template.content,
            "required_membership": template.required_membership,
            "effective_point_cost": model_context["effective_point_cost"] if model_context["effective_point_cost"] is not None else 0,
            "model_config": model_context["model_config"],
        }

    @staticmethod
    def _usage_label(count: int) -> str:
        if count >= 10000:
            return f"{count / 10000:.1f}万次使用"
        return f"{count}次使用"

    @staticmethod
    def _default_pages() -> list[dict]:
        return [
            {"page_key": "home", "label": "首页", "title": "首页", "subtitle": "", "icon": "Home"},
            {"page_key": "assistant", "label": "AI 助理", "title": "智能助理广场", "subtitle": "", "icon": "Bot"},
            {"page_key": "marketing", "label": "AI 营销", "title": "营销增长中心", "subtitle": "", "icon": "Megaphone"},
            {"page_key": "video", "label": "AI 视频", "title": "AI视频创作中心", "subtitle": "", "icon": "FileVideo"},
            {"page_key": "audio", "label": "AI 音频", "title": "AI音频创作中心", "subtitle": "", "icon": "Headphones"},
            {"page_key": "coding", "label": "AI 编程", "title": "AI编程工作台", "subtitle": "", "icon": "Workflow"},
            {"page_key": "writing", "label": "AI 写作", "title": "AI写作中心", "subtitle": "", "icon": "Feather"},
            {"page_key": "ecommerce", "label": "AI 电商", "title": "AI电商运营中心", "subtitle": "", "icon": "WandSparkles"},
            {"page_key": "legal", "label": "AI 法务", "title": "AI法务服务台", "subtitle": "", "icon": "Scale"},
            {"page_key": "office", "label": "AI 办公", "title": "AI办公效率中心", "subtitle": "", "icon": "BriefcaseBusiness"},
        ]

    @staticmethod
    def _default_left_nav() -> list[dict[str, str]]:
        return [
            {"key": "basic", "label": "基础必备", "icon": "Flame"},
            {"key": "growth", "label": "学习成长", "icon": "Sprout"},
            {"key": "orders", "label": "接单变现", "icon": "ReceiptText"},
            {"key": "resources", "label": "资源对接", "icon": "Handshake"},
            {"key": "projects", "label": "项目共创", "icon": "PanelsTopLeft"},
            {"key": "workspace", "label": "应用工作台", "icon": "LayoutGrid"},
            {"key": "toolkit", "label": "专业工具包", "icon": "BriefcaseBusiness"},
        ]


def _normalize_detail_path(value: str) -> str:
    path = (value or "").strip()
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


def _select_action_item(items: list[ContentItem], item_id: str | None) -> ContentItem | None:
    if item_id:
        for item in items:
            if item.id == item_id:
                return item
    return items[0] if items else None


def _detail_metadata(item: ContentItem | None, *, path: str) -> dict:
    if item is None:
        return _default_detail(path=path, title=path.strip("/") or "详情")
    metadata = item.metadata_json or {}
    configured = metadata.get("detail") if isinstance(metadata, dict) else None
    detail = _default_detail(path=path, title=item.title, subtitle=item.subtitle, category=item.category)
    if isinstance(configured, dict):
        detail.update({key: value for key, value in configured.items() if value is not None})
    return detail


def _default_detail(*, path: str, title: str, subtitle: str = "", category: str = "") -> dict:
    action_key = _default_action_key(path=path, category=category)
    return {
        "summary": subtitle or f"{title} 的完整能力说明、使用流程和交付结果。",
        "highlights": [
            "站内记录学习或使用进度",
            "可在个人动作记录中继续跟进",
            "支持会员权限检查和后续运营配置",
        ],
        "steps": ["阅读详情", "确认适用场景", "点击主按钮完成站内动作"],
        "deliverables": ["可追踪的站内动作记录"],
        "faqs": [{"question": "操作会扣费吗？", "answer": "本版本只记录站内动作，不接入真实支付。"}],
        "primaryAction": {"key": action_key, "label": _default_action_label(action_key)},
        "secondaryActions": [{"key": "favorite", "label": "收藏"}],
        "download": None,
    }


def _default_action_key(*, path: str, category: str) -> str:
    if "download" in path or "resources" in path or "资料" in category or "资源" in category:
        return "download"
    if "community" in path or "社群" in category:
        return "join"
    if "orders" in path or "projects" in path or "接单" in category or "项目" in category:
        return "apply"
    if "template" in path or "toolkit" in path or "模板" in category:
        return "claim"
    return "enroll"


def _default_action_label(action_key: str) -> str:
    labels = {
        "apply": "立即报名",
        "backup": "开启备份",
        "claim": "领取模板",
        "download": "下载资料",
        "enroll": "开始学习",
        "favorite": "收藏",
        "join": "加入社群",
    }
    return labels.get(action_key, "立即使用")


def _action_message(action_key: str) -> str:
    messages = {
        "apply": "报名已提交，运营团队会在站内消息中跟进。",
        "backup": "备份已开启，后续文件会记录在下载与动作中心。",
        "claim": "模板已领取，可在下载记录中继续查看。",
        "download": "资料已领取，下载记录已更新。",
        "enroll": "学习入口已开启，进度已记录。",
        "favorite": "已收藏到个人动作记录。",
        "join": "加入申请已记录，社群入口已解锁。",
    }
    return messages.get(action_key, "操作已记录。")

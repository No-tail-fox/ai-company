from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AiAssistant, ContentItem, ContentPage, ContentSection, PromptTemplate


class PortalService:
    def __init__(self, session: Session):
        self.session = session

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

    @staticmethod
    def _item_payload(item: ContentItem) -> dict:
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
        }

    def _assistant_payload(self, assistant: AiAssistant) -> dict:
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
        }

    @staticmethod
    def _template_payload(template: PromptTemplate) -> dict:
        return {
            "id": template.id,
            "tenant_id": template.tenant_id,
            "template_key": template.template_key,
            "title": template.title,
            "category": template.category,
            "content": template.content,
            "required_membership": template.required_membership,
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
            {"page_key": "audio", "label": "AI 音频", "title": "AI音频工作台", "subtitle": "", "icon": "Headphones"},
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

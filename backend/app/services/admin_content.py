from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AiAssistant, ContentItem, ContentPage, ContentSection
from app.schemas import (
    AssistantCreate,
    ContentItemCreate,
    ContentItemUpdate,
    ContentPageCreate,
    ContentPageUpdate,
    ContentSectionCreate,
    ContentSectionUpdate,
)


class AdminContentService:
    def __init__(self, session: Session):
        self.session = session

    def list_pages(self, *, tenant_id: str) -> list[ContentPage]:
        return list(
            self.session.scalars(
                select(ContentPage)
                .where(ContentPage.tenant_id == tenant_id)
                .order_by(ContentPage.sort_order.asc(), ContentPage.created_at.asc())
            )
        )

    def get_page_content(self, *, tenant_id: str, page_key: str) -> tuple[ContentPage, list[ContentSection], dict[str, list[ContentItem]]]:
        page = self.session.scalar(
            select(ContentPage).where(
                ContentPage.tenant_id == tenant_id,
                ContentPage.page_key == page_key,
            )
        )
        if page is None:
            raise ValueError("page not found for tenant")
        sections = list(
            self.session.scalars(
                select(ContentSection)
                .where(
                    ContentSection.tenant_id == tenant_id,
                    ContentSection.area == page_key,
                )
                .order_by(ContentSection.sort_order.asc(), ContentSection.created_at.asc())
            )
        )
        section_ids = [section.id for section in sections]
        grouped: dict[str, list[ContentItem]] = {}
        if section_ids:
            items = list(
                self.session.scalars(
                    select(ContentItem)
                    .where(
                        ContentItem.tenant_id == tenant_id,
                        ContentItem.section_id.in_(section_ids),
                    )
                    .order_by(ContentItem.sort_order.asc(), ContentItem.created_at.asc())
                )
            )
            for item in items:
                grouped.setdefault(item.section_id, []).append(item)
        return page, sections, grouped

    def create_page(self, *, tenant_id: str, payload: ContentPageCreate) -> ContentPage:
        page = ContentPage(tenant_id=tenant_id, **payload.model_dump())
        self.session.add(page)
        self.session.commit()
        return page

    def update_page(self, *, tenant_id: str, page_id: str, payload: ContentPageUpdate) -> ContentPage:
        page = self._get_page(tenant_id=tenant_id, page_id=page_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(page, key, value)
        self.session.commit()
        return page

    def disable_page(self, *, tenant_id: str, page_id: str) -> ContentPage:
        page = self._get_page(tenant_id=tenant_id, page_id=page_id)
        page.enabled = False
        self.session.commit()
        return page

    def reorder_pages(self, *, tenant_id: str, ordered_ids: list[str]) -> list[ContentPage]:
        if not ordered_ids:
            return []
        pages = list(
            self.session.scalars(
                select(ContentPage).where(
                    ContentPage.tenant_id == tenant_id,
                    ContentPage.id.in_(ordered_ids),
                )
            )
        )
        by_id = {page.id: page for page in pages}
        if set(by_id) != set(ordered_ids):
            raise ValueError("one or more pages were not found for tenant")
        for index, page_id in enumerate(ordered_ids, start=1):
            by_id[page_id].sort_order = index * 10
        self.session.commit()
        return [by_id[page_id] for page_id in ordered_ids]

    def list_sections(self, *, tenant_id: str, page_key: str | None = None) -> list[ContentSection]:
        query = select(ContentSection).where(ContentSection.tenant_id == tenant_id)
        if page_key:
            query = query.where(ContentSection.area == page_key)
        return list(self.session.scalars(query.order_by(ContentSection.sort_order.asc(), ContentSection.created_at.asc())))

    def create_section(self, *, tenant_id: str, payload: ContentSectionCreate) -> ContentSection:
        page = self.session.scalar(
            select(ContentPage).where(
                ContentPage.tenant_id == tenant_id,
                ContentPage.page_key == payload.page_key,
            )
        )
        if page is None:
            raise ValueError("page not found for tenant")
        section = ContentSection(
            tenant_id=tenant_id,
            area=payload.page_key,
            section_key=payload.section_key,
            title=payload.title,
            subtitle=payload.subtitle,
            layout=payload.layout,
            sort_order=payload.sort_order,
            enabled=payload.enabled,
        )
        self.session.add(section)
        self.session.commit()
        return section

    def update_section(self, *, tenant_id: str, section_id: str, payload: ContentSectionUpdate) -> ContentSection:
        section = self._get_section(tenant_id=tenant_id, section_id=section_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(section, key, value)
        self.session.commit()
        return section

    def disable_section(self, *, tenant_id: str, section_id: str) -> ContentSection:
        section = self._get_section(tenant_id=tenant_id, section_id=section_id)
        section.enabled = False
        self.session.commit()
        return section

    def reorder_sections(self, *, tenant_id: str, ordered_ids: list[str]) -> list[ContentSection]:
        if not ordered_ids:
            return []
        sections = list(
            self.session.scalars(
                select(ContentSection).where(
                    ContentSection.tenant_id == tenant_id,
                    ContentSection.id.in_(ordered_ids),
                )
            )
        )
        by_id = {section.id: section for section in sections}
        if set(by_id) != set(ordered_ids):
            raise ValueError("one or more sections were not found for tenant")
        for index, section_id in enumerate(ordered_ids, start=1):
            by_id[section_id].sort_order = index * 10
        self.session.commit()
        return [by_id[section_id] for section_id in ordered_ids]

    def list_items(self, *, tenant_id: str, section_id: str | None = None) -> list[ContentItem]:
        query = select(ContentItem).where(ContentItem.tenant_id == tenant_id)
        if section_id:
            query = query.where(ContentItem.section_id == section_id)
        return list(self.session.scalars(query.order_by(ContentItem.sort_order.asc(), ContentItem.created_at.asc())))

    def create_content_item(self, *, tenant_id: str, payload: ContentItemCreate) -> ContentItem:
        section = self.session.scalar(
            select(ContentSection).where(
                ContentSection.tenant_id == tenant_id,
                ContentSection.id == payload.section_id,
            )
        )
        if section is None:
            raise ValueError("section not found for tenant")
        item = ContentItem(tenant_id=tenant_id, **payload.model_dump())
        self.session.add(item)
        self.session.commit()
        return item

    def update_content_item(self, *, tenant_id: str, item_id: str, payload: ContentItemUpdate) -> ContentItem:
        item = self._get_item(tenant_id=tenant_id, item_id=item_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        self.session.commit()
        return item

    def disable_content_item(self, *, tenant_id: str, item_id: str) -> ContentItem:
        item = self._get_item(tenant_id=tenant_id, item_id=item_id)
        item.enabled = False
        self.session.commit()
        return item

    def reorder_items(self, *, tenant_id: str, section_id: str, ordered_ids: list[str]) -> list[ContentItem]:
        if not ordered_ids:
            return []
        items = list(
            self.session.scalars(
                select(ContentItem).where(
                    ContentItem.tenant_id == tenant_id,
                    ContentItem.section_id == section_id,
                    ContentItem.id.in_(ordered_ids),
                )
            )
        )
        by_id = {item.id: item for item in items}
        if set(by_id) != set(ordered_ids):
            raise ValueError("one or more items were not found for section")
        for index, item_id in enumerate(ordered_ids, start=1):
            by_id[item_id].sort_order = index * 10
        self.session.commit()
        return [by_id[item_id] for item_id in ordered_ids]

    def create_assistant(self, *, tenant_id: str, payload: AssistantCreate) -> AiAssistant:
        assistant = AiAssistant(tenant_id=tenant_id, **payload.model_dump())
        self.session.add(assistant)
        self.session.commit()
        return assistant

    def _get_page(self, *, tenant_id: str, page_id: str) -> ContentPage:
        page = self.session.scalar(select(ContentPage).where(ContentPage.tenant_id == tenant_id, ContentPage.id == page_id))
        if page is None:
            raise ValueError("page not found for tenant")
        return page

    def _get_section(self, *, tenant_id: str, section_id: str) -> ContentSection:
        section = self.session.scalar(
            select(ContentSection).where(ContentSection.tenant_id == tenant_id, ContentSection.id == section_id)
        )
        if section is None:
            raise ValueError("section not found for tenant")
        return section

    def _get_item(self, *, tenant_id: str, item_id: str) -> ContentItem:
        item = self.session.scalar(select(ContentItem).where(ContentItem.tenant_id == tenant_id, ContentItem.id == item_id))
        if item is None:
            raise ValueError("item not found for tenant")
        return item

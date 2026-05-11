from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ContentItem, ContentPage, ContentSection, HomeHeroSlide
from app.services.portal import PortalService


class HomeDashboardService:
    def __init__(self, session: Session):
        self.session = session
        self.portal = PortalService(session)

    def dashboard(self, *, tenant_id: str, user_id: str = "demo-user") -> dict:
        del user_id
        page = self._home_page(tenant_id=tenant_id)
        hero_slides = self.list_home_slides(tenant_id=tenant_id) or self._default_hero_slides(tenant_id=tenant_id)
        workbench_shortcuts = self._items_for_sections(
            tenant_id=tenant_id,
            section_keys=["workbench_shortcuts", "workspace_tools", "task_board"],
            limit=6,
        )
        community_cards = self._items_for_sections(
            tenant_id=tenant_id,
            section_keys=["communities", "resource_hub"],
            limit=4,
        )
        tool_cards = self._items_for_sections(
            tenant_id=tenant_id,
            section_keys=["home_tools", "toolkit", "earning_templates", "project_cocreation"],
            limit=5,
        )
        task_cards = self._items_for_sections(
            tenant_id=tenant_id,
            section_keys=["task_board"],
            limit=4,
        )
        return {
            "tenant_id": tenant_id,
            "page": page,
            "hero_slides": hero_slides,
            "kpi_cards": self._kpi_cards(
                tenant_id=tenant_id,
                hero_slides=hero_slides,
                workbench_shortcuts=workbench_shortcuts,
                community_cards=community_cards,
                task_cards=task_cards,
                tool_cards=tool_cards,
            ),
            "workbench_shortcuts": workbench_shortcuts,
            "community_cards": community_cards,
            "tool_cards": tool_cards,
        }

    def list_home_slides(self, *, tenant_id: str, include_disabled: bool = False) -> list[dict]:
        stmt = select(HomeHeroSlide).where(HomeHeroSlide.tenant_id == tenant_id)
        if not include_disabled:
            stmt = stmt.where(HomeHeroSlide.enabled.is_(True))
        slides = list(
            self.session.scalars(
                stmt.order_by(HomeHeroSlide.sort_order.asc(), HomeHeroSlide.created_at.asc())
            )
        )
        return [self._slide_payload(slide) for slide in slides]

    def create_home_slide(self, *, tenant_id: str, payload) -> dict:
        slide = HomeHeroSlide(tenant_id=tenant_id, **self._normalize_payload(payload))
        self.session.add(slide)
        self.session.commit()
        self.session.refresh(slide)
        return self._slide_payload(slide)

    def update_home_slide(self, *, tenant_id: str, slide_id: str, payload) -> dict:
        slide = self._home_slide(tenant_id=tenant_id, slide_id=slide_id)
        for key, value in self._normalize_payload(payload, exclude_unset=True).items():
            setattr(slide, key, value)
        self.session.commit()
        self.session.refresh(slide)
        return self._slide_payload(slide)

    def disable_home_slide(self, *, tenant_id: str, slide_id: str) -> dict:
        slide = self._home_slide(tenant_id=tenant_id, slide_id=slide_id)
        slide.enabled = False
        self.session.commit()
        self.session.refresh(slide)
        return self._slide_payload(slide)

    def reorder_home_slides(self, *, tenant_id: str, ordered_ids: list[str]) -> list[dict]:
        if not ordered_ids:
            return []
        slides = list(
            self.session.scalars(
                select(HomeHeroSlide).where(
                    HomeHeroSlide.tenant_id == tenant_id,
                    HomeHeroSlide.id.in_(ordered_ids),
                )
            )
        )
        by_id = {slide.id: slide for slide in slides}
        if set(by_id) != set(ordered_ids):
            raise ValueError("one or more home slides were not found for tenant")
        for index, slide_id in enumerate(ordered_ids, start=1):
            by_id[slide_id].sort_order = index * 10
        self.session.commit()
        return [self._slide_payload(by_id[slide_id]) for slide_id in ordered_ids]

    def _home_page(self, *, tenant_id: str) -> dict:
        page = self.session.scalar(
            select(ContentPage).where(
                ContentPage.tenant_id == tenant_id,
                ContentPage.page_key == "home",
                ContentPage.enabled.is_(True),
            )
        )
        if page is not None:
            return self.portal._page_payload(page)
        return {
            "tenant_id": tenant_id,
            "page_key": "home",
            "label": "首页",
            "title": "中文首页",
            "subtitle": "会员活动、工作台、社群和工具统一入口",
            "icon": "Home",
            "sort_order": 10,
            "enabled": True,
        }

    def _items_for_sections(self, *, tenant_id: str, section_keys: list[str], limit: int) -> list[dict]:
        if limit <= 0 or not section_keys:
            return []
        sections = list(
            self.session.scalars(
                select(ContentSection)
                .where(
                    ContentSection.tenant_id == tenant_id,
                    ContentSection.area == "home",
                    ContentSection.section_key.in_(section_keys),
                    ContentSection.enabled.is_(True),
                )
                .order_by(ContentSection.sort_order.asc(), ContentSection.created_at.asc())
            )
        )
        if not sections:
            return self._fallback_items(tenant_id=tenant_id, section_keys=section_keys, limit=limit)
        items_by_section = self.portal._enabled_items_by_section(tenant_id=tenant_id, sections=sections)
        results: list[dict] = []
        seen: set[str] = set()
        for section in sections:
            for item in items_by_section.get(section.id, []):
                if item.id in seen:
                    continue
                seen.add(item.id)
                results.append(self._home_item_payload(self.portal._item_payload(item)))
                if len(results) >= limit:
                    return results
        if results:
            return results
        return self._fallback_items(tenant_id=tenant_id, section_keys=section_keys, limit=limit)

    @staticmethod
    def _home_item_payload(payload: dict) -> dict:
        metadata = payload.get("metadata_json") or {}
        payload["menu_keys"] = metadata.get("menuKeys") or metadata.get("menu_keys") or []
        return payload

    def _fallback_items(self, *, tenant_id: str, section_keys: list[str], limit: int) -> list[dict]:
        self._fallback_tenant_id = tenant_id
        fallback_rows = {
            "workbench_shortcuts": [
                self._fallback_item(
                    id="fallback-home-chat",
                    item_type="tool",
                    title="AI 对话",
                    subtitle="写作、问答和方案梳理",
                    category="应用工作台",
                    icon="Bot",
                    action_value="/workbench",
                    sort_order=10,
                ),
                self._fallback_item(
                    id="fallback-home-image",
                    item_type="tool",
                    title="图片生成",
                    subtitle="海报、封面和详情图",
                    category="应用工作台",
                    icon="Image",
                    action_value="/workbench/image",
                    sort_order=20,
                ),
                self._fallback_item(
                    id="fallback-home-video",
                    item_type="tool",
                    title="视频脚本",
                    subtitle="选题、分镜和口播脚本",
                    category="应用工作台",
                    icon="MonitorPlay",
                    action_value="/workbench/video",
                    sort_order=30,
                ),
                self._fallback_item(
                    id="fallback-home-ppt",
                    item_type="tool",
                    title="PPT 办公",
                    subtitle="大纲到页面快速生成",
                    category="应用工作台",
                    icon="Presentation",
                    action_value="/workspace/ppt",
                    sort_order=40,
                ),
                self._fallback_item(
                    id="fallback-home-orders",
                    item_type="tool",
                    title="接单交付",
                    subtitle="报价、交付和复购跟进",
                    category="接单变现",
                    icon="BriefcaseBusiness",
                    action_value="/workspace/deliveries",
                    sort_order=50,
                ),
                self._fallback_item(
                    id="fallback-home-assets",
                    item_type="tool",
                    title="素材库",
                    subtitle="图片、模板和提示词资产",
                    category="应用工作台",
                    icon="CloudUpload",
                    action_value="/workspace/assets",
                    sort_order=60,
                ),
            ],
            "communities": [
                self._fallback_item(
                    id="fallback-community-starter",
                    item_type="community",
                    title="入门交流群",
                    subtitle="新人答疑、工具清单和上手路线",
                    category="社群",
                    icon="MessageCircle",
                    action_value="/community/starter",
                    sort_order=10,
                    metadata_json={"menuKeys": ["basic", "growth"]},
                ),
                self._fallback_item(
                    id="fallback-community-study",
                    item_type="community",
                    title="学习打卡群",
                    subtitle="每日任务、案例拆解和作业反馈",
                    category="学习成长",
                    icon="GraduationCap",
                    action_value="/community/study",
                    sort_order=20,
                    metadata_json={"menuKeys": ["growth"]},
                ),
                self._fallback_item(
                    id="fallback-community-orders",
                    item_type="community",
                    title="接单变现群",
                    subtitle="接单案例、报价模板和交付流程",
                    category="接单变现",
                    icon="Handshake",
                    action_value="/community/orders",
                    sort_order=30,
                    metadata_json={"menuKeys": ["orders"]},
                ),
                self._fallback_item(
                    id="fallback-community-resource",
                    item_type="community",
                    title="资源对接群",
                    subtitle="工具资源、客户线索和行业资料交换",
                    category="资源对接",
                    icon="Network",
                    action_value="/community/resources",
                    sort_order=40,
                    metadata_json={"menuKeys": ["resources", "toolkit"]},
                ),
            ],
            "home_tools": [
                self._fallback_item(
                    id="fallback-tool-common",
                    item_type="template",
                    title="常用工具",
                    subtitle="高频 AI 工具入口集合",
                    category="工作台",
                    icon="LayoutGrid",
                    action_value="/workbench",
                    sort_order=10,
                    metadata_json={"menuKeys": ["basic", "workspace"]},
                ),
                self._fallback_item(
                    id="fallback-tool-office",
                    item_type="template",
                    title="办公模板",
                    subtitle="PPT、表格和会议纪要模板",
                    category="工具框",
                    icon="Presentation",
                    action_value="/toolkit/office",
                    sort_order=20,
                    metadata_json={"menuKeys": ["workspace", "toolkit"]},
                ),
                self._fallback_item(
                    id="fallback-tool-quote",
                    item_type="template",
                    title="接单报价",
                    subtitle="报价、验收和复购话术",
                    category="接单变现",
                    icon="ReceiptText",
                    action_value="/templates/quote",
                    sort_order=30,
                    metadata_json={"menuKeys": ["orders"]},
                ),
                self._fallback_item(
                    id="fallback-tool-copy",
                    item_type="template",
                    title="内容生成",
                    subtitle="文案、脚本和社媒内容",
                    category="增长",
                    icon="Feather",
                    action_value="/marketing",
                    sort_order=40,
                    metadata_json={"menuKeys": ["growth", "orders"]},
                ),
                self._fallback_item(
                    id="fallback-tool-ecommerce",
                    item_type="template",
                    title="电商优化",
                    subtitle="标题、详情页和客服话术",
                    category="电商",
                    icon="WandSparkles",
                    action_value="/workspace/ecommerce",
                    sort_order=50,
                    metadata_json={"menuKeys": ["orders", "resources"]},
                ),
            ],
        }
        results: list[dict] = []
        for section_key in section_keys:
            for item in fallback_rows.get(section_key, []):
                results.append(item)
                if len(results) >= limit:
                    return results
        return results

    def _kpi_cards(
        self,
        *,
        tenant_id: str,
        hero_slides: list[dict],
        workbench_shortcuts: list[dict],
        community_cards: list[dict],
        task_cards: list[dict],
        tool_cards: list[dict],
    ) -> list[dict]:
        vip_count = self._count_home_items(tenant_id=tenant_id, required_membership_only=True)
        task_count = len(task_cards) or len(workbench_shortcuts)
        community_activity = max(len(community_cards) * 8, len(community_cards))
        tool_total = len(tool_cards)
        return [
            {
                "id": "today-new",
                "label": "今日上新",
                "value": str(len(hero_slides)),
                "trend": "轮播与模板持续更新",
                "icon": "Sparkles",
                "tone": "blue",
                "action_type": "route",
                "action_value": "/admin",
            },
            {
                "id": "vip-exclusive",
                "label": "会员专享",
                "value": str(max(vip_count, 1 if hero_slides and any("会员" in slide["badge"] for slide in hero_slides) else 0)),
                "trend": "权益与内容已就绪",
                "icon": "Crown",
                "tone": "gold",
                "action_type": "route",
                "action_value": "/membership/benefits",
            },
            {
                "id": "todo-task",
                "label": "待办任务",
                "value": str(task_count),
                "trend": "继续处理工作台任务",
                "icon": "CheckSquare",
                "tone": "orange",
                "action_type": "route",
                "action_value": "/workbench",
            },
            {
                "id": "community-active",
                "label": "社群活跃",
                "value": str(community_activity or tool_total),
                "trend": "社群与工具持续补充",
                "icon": "Users",
                "tone": "green",
                "action_type": "route",
                "action_value": "/community/starter",
            },
        ]

    def _count_home_items(self, *, tenant_id: str, required_membership_only: bool = False) -> int:
        stmt = (
            select(func.count(ContentItem.id))
            .select_from(ContentItem)
            .join(ContentSection, ContentSection.id == ContentItem.section_id)
            .where(
                ContentItem.tenant_id == tenant_id,
                ContentSection.tenant_id == tenant_id,
                ContentSection.area == "home",
                ContentItem.enabled.is_(True),
                ContentSection.enabled.is_(True),
            )
        )
        if required_membership_only:
            stmt = stmt.where(ContentItem.required_membership.is_(True))
        return int(self.session.scalar(stmt) or 0)

    def _home_slide(self, *, tenant_id: str, slide_id: str) -> HomeHeroSlide:
        slide = self.session.scalar(
            select(HomeHeroSlide).where(
                HomeHeroSlide.tenant_id == tenant_id,
                HomeHeroSlide.id == slide_id,
            )
        )
        if slide is None:
            raise ValueError(f"home slide {slide_id} was not found")
        return slide

    def _slide_payload(self, slide: HomeHeroSlide) -> dict:
        return {
            "id": slide.id,
            "tenant_id": slide.tenant_id,
            "title": slide.title,
            "subtitle": slide.subtitle,
            "badge": slide.badge,
            "cta_label": slide.cta_label,
            "cta_subtitle": slide.cta_subtitle,
            "image_url": slide.image_url,
            "action_type": slide.action_type,
            "action_value": slide.action_value,
            "sort_order": slide.sort_order,
            "enabled": slide.enabled,
            "metadata_json": slide.metadata_json or {},
            "created_at": slide.created_at.isoformat() if slide.created_at else None,
            "updated_at": slide.updated_at.isoformat() if slide.updated_at else None,
        }

    def _normalize_payload(self, payload, *, exclude_unset: bool = False) -> dict:
        values = payload.model_dump(exclude_unset=exclude_unset)
        if exclude_unset:
            normalized: dict[str, object] = {}
            for key in (
                "title",
                "subtitle",
                "badge",
                "cta_label",
                "cta_subtitle",
                "image_url",
                "action_type",
                "action_value",
                "sort_order",
                "enabled",
                "metadata_json",
            ):
                if key not in values:
                    continue
                value = values[key]
                if value is None:
                    continue
                if isinstance(value, str):
                    value = value.strip()
                if key == "metadata_json":
                    value = value or {}
                normalized[key] = value
            return normalized
        return {
            "title": str(values.get("title", "")).strip(),
            "subtitle": str(values.get("subtitle", "")).strip(),
            "badge": str(values.get("badge", "")).strip(),
            "cta_label": str(values.get("cta_label", "立即查看")).strip() or "立即查看",
            "cta_subtitle": str(values.get("cta_subtitle", "")).strip(),
            "image_url": str(values.get("image_url", "")).strip(),
            "action_type": str(values.get("action_type", "route")).strip() or "route",
            "action_value": str(values.get("action_value", "")).strip(),
            "sort_order": int(values.get("sort_order", 100) or 100),
            "enabled": bool(values.get("enabled", True)),
            "metadata_json": values.get("metadata_json") or {},
        }

    def _fallback_item(
        self,
        *,
        id: str,
        item_type: str,
        title: str,
        subtitle: str,
        category: str,
        icon: str,
        action_value: str,
        sort_order: int,
        metadata_json: dict | None = None,
    ) -> dict:
        tenant_id = getattr(self, "_fallback_tenant_id", "")
        payload = {
            "id": id,
            "tenant_id": tenant_id,
            "section_id": f"fallback-{id}",
            "item_type": item_type,
            "title": title,
            "subtitle": subtitle,
            "category": category,
            "icon": icon,
            "image_url": "",
            "badge": "",
            "tags": [],
            "sort_order": sort_order,
            "enabled": True,
            "action_type": "route",
            "action_value": action_value,
            "required_membership": False,
            "point_cost": 0,
            "effective_point_cost": 0,
            "model_config": None,
            "metadata_json": metadata_json or {},
        }
        return self._home_item_payload(payload)

    @staticmethod
    def _default_hero_slides(*, tenant_id: str) -> list[dict]:
        return [
            {
                "id": f"fallback-slide-membership-{tenant_id}",
                "tenant_id": tenant_id,
                "title": "会员活动限时特惠",
                "subtitle": "开通会员解锁模板、社群和交付资料",
                "badge": "会员专享",
                "cta_label": "立即开通",
                "cta_subtitle": "查看权益，不走支付",
                "image_url": "",
                "action_type": "route",
                "action_value": "/membership/benefits",
                "sort_order": 10,
                "enabled": True,
                "metadata_json": {"accent": "gold", "theme": "vip"},
            },
            {
                "id": f"fallback-slide-template-{tenant_id}",
                "tenant_id": tenant_id,
                "title": "模板上新不停",
                "subtitle": "PPT、报价单、社媒和交付模板持续更新",
                "badge": "今日上新",
                "cta_label": "立即查看",
                "cta_subtitle": "今天就能直接用",
                "image_url": "",
                "action_type": "route",
                "action_value": "/templates",
                "sort_order": 20,
                "enabled": True,
                "metadata_json": {"accent": "blue", "theme": "template"},
            },
            {
                "id": f"fallback-slide-community-{tenant_id}",
                "tenant_id": tenant_id,
                "title": "社群和工作台一起用",
                "subtitle": "入门群、打卡群、接单群和资源群都在这里",
                "badge": "社群活跃",
                "cta_label": "进入社群",
                "cta_subtitle": "打开首页就能直达",
                "image_url": "",
                "action_type": "route",
                "action_value": "/community/starter",
                "sort_order": 30,
                "enabled": True,
                "metadata_json": {"accent": "green", "theme": "community"},
            },
        ]

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ContentItem,
    ContentSection,
    PortalDetailComment,
    PortalDetailDocument,
    PortalDetailVersion,
    User,
    UserPortalAction,
    new_id,
    utcnow,
)
from app.schemas import CommunicationPostCreate


COMMUNICATION_SECTION_KEY = "posts"
COMMUNICATION_SECTION_ID = "section-communication-posts"
COMMUNICATION_POST_TYPE = "communication_post"

COMMUNICATION_CATEGORIES = [
    {"key": "all", "label": "全部"},
    {"key": "order", "label": "接单"},
    {"key": "template", "label": "模板"},
    {"key": "talk", "label": "交流"},
    {"key": "benefit", "label": "工具权益"},
    {"key": "resource", "label": "资源对接"},
    {"key": "pitch", "label": "项目路演"},
    {"key": "local-order", "label": "本地订单"},
    {"key": "short-drama", "label": "AI 短剧"},
    {"key": "ecommerce", "label": "电商运营"},
]

COMMUNICATION_HOT_TAGS = ["AI短剧", "接单报价", "模板包", "工具权益", "算力券", "本地订单", "合同经验"]

COMMUNICATION_HOT_TOPICS = [
    {"title": "AI 客服 Demo 怎么报价", "count": 52},
    {"title": "工具权益失效反馈", "count": 34},
    {"title": "短剧剪辑交付规范", "count": 28},
    {"title": "OPC 合同主体经验", "count": 21},
]

SEED_COMMUNICATION_POSTS: list[dict[str, Any]] = [
    {
        "id": "short-drama-editing-team",
        "category_key": "order",
        "badge_label": "接单",
        "mark": "接",
        "tone": "order",
        "title": "寻找 AI 短剧剪辑团队：20 条口播混剪，3 天交付",
        "summary": "预算 3000-5000，需要提供过往案例；可在帖子下方报价并补充交付周期。",
        "comments": 18,
        "views": 246,
        "view_label": "246",
        "time_label": "2 分钟前",
        "timestamp": "2026-05-12T03:20:00",
        "tags": ["AI短剧", "接单报价", "短剧剪辑"],
        "actions": [
            {"key": "quote", "label": "我要报价", "tone": "blue", "kind": "detail"},
            {"key": "requirement", "label": "查看需求", "tone": "pink", "kind": "detail"},
        ],
        "body_markdown": """# 寻找 AI 短剧剪辑团队

20 条口播混剪，3 天交付，预算 3000-5000。

## 需求

- 需要提供过往短剧或口播混剪案例
- 交付包含成片、字幕文件和工程说明
- 报价请写清楚排期、修改次数和素材要求
""",
    },
    {
        "id": "ecommerce-detail-template",
        "category_key": "template",
        "badge_label": "模板",
        "mark": "模",
        "tone": "template",
        "title": "上新：AI 电商详情页提示词模板包",
        "summary": "包含主图卖点、详情页结构、短视频脚本三类 Markdown 模板，可复制后改写。",
        "comments": 34,
        "views": 1200,
        "view_label": "1.2k",
        "time_label": "置顶",
        "timestamp": "2026-05-12T03:10:00",
        "pinned": True,
        "tags": ["模板包", "电商运营", "Markdown"],
        "actions": [
            {"key": "copy-template", "label": "获取模板", "tone": "blue", "kind": "copy"},
            {"key": "favorite", "label": "收藏", "tone": "pink", "kind": "favorite"},
        ],
        "template_text": "# AI 电商详情页提示词模板包\n\n请按主图卖点、详情页结构、短视频脚本输出可直接改写的 Markdown。",
        "body_markdown": """# AI 电商详情页提示词模板包

这个模板包用于快速拆出商品卖点、详情页结构和短视频脚本。

## 使用方式

1. 先填写商品基础信息、目标人群和核心利益点。
2. 让 AI 输出主图卖点、详情页模块和短视频分镜。
3. 按平台规范二次校对，再进入设计或投放流程。
""",
    },
    {
        "id": "rag-or-finetune",
        "category_key": "talk",
        "badge_label": "交流",
        "mark": "聊",
        "tone": "talk",
        "title": "大家现在做企业知识库，选 RAG 还是微调？",
        "summary": "想听听本地企业项目的实际经验：成本、交付周期、后期维护分别怎么控。",
        "reply_strip": "最新回复：先做 RAG，合同里把数据清洗和验收标准写清楚。",
        "comments": 52,
        "views": 908,
        "view_label": "908",
        "time_label": "12 分钟前",
        "timestamp": "2026-05-12T03:08:00",
        "tags": ["RAG", "企业知识库", "项目交付"],
        "actions": [],
        "body_markdown": """# 企业知识库：RAG 还是微调？

想听听本地企业项目的真实经验，尤其是成本、交付周期和后期维护。

欢迎把你踩过的坑、验收口径和报价方式补充到评论区。
""",
    },
    {
        "id": "tool-benefits-v14",
        "category_key": "benefit",
        "badge_label": "资源",
        "mark": "资",
        "tone": "resource",
        "title": "工具优惠合集 v1.4：模型、剪辑、设计权益更新",
        "summary": "正文使用 Markdown 渲染，失效链接可在评论区反馈，管理员每周统一更新。",
        "comments": 23,
        "views": 768,
        "view_label": "768",
        "time_label": "今天",
        "timestamp": "2026-05-12T02:38:00",
        "tags": ["工具权益", "资源对接", "Markdown"],
        "actions": [
            {"key": "read", "label": "查看正文", "tone": "blue", "kind": "detail"},
            {"key": "invalid", "label": "反馈失效", "tone": "pink", "kind": "detail"},
        ],
        "body_markdown": """# 工具优惠合集 v1.4

本页汇总模型调用、视频剪辑、设计协作、办公效率等工具权益，适合接单、内容制作、模板生产和轻量团队协作场景。

## 更新说明

- 模型调用券：新增两组可申请渠道
- 剪辑工具会员：补充有效期和账号归属说明
- 设计与办公套件：标记商业授权状态

如果发现链接失效，请在评论区反馈失效项目和可替代渠道。
""",
    },
    {
        "id": "local-customer-service-demo",
        "category_key": "local-order",
        "badge_label": "本地订单",
        "mark": "单",
        "tone": "order",
        "title": "本地商贸企业需要 AI 客服知识库 Demo",
        "summary": "希望一周内出可演示版本，包含 FAQ 导入、问答记录、转人工规则。",
        "reply_strip": "报价区开放：请附技术方案、交付物和后续维护费用。",
        "comments": 9,
        "views": 312,
        "view_label": "312",
        "time_label": "36 分钟前",
        "timestamp": "2026-05-12T02:44:00",
        "tags": ["本地订单", "接单报价", "企业知识库"],
        "actions": [],
        "body_markdown": """# AI 客服知识库 Demo 需求

本地商贸企业希望一周内完成可演示版本。

## 交付范围

- FAQ 批量导入
- 问答记录留存
- 转人工规则
- 演示账号和部署说明
""",
    },
    {
        "id": "poster-copy-template",
        "category_key": "template",
        "badge_label": "模板",
        "mark": "稿",
        "tone": "template",
        "title": "招商海报文案模板：适合园区、联盟、路演",
        "summary": "支持按“主标题 / 六大权益 / 入驻条件 / 联系方式”快速生成。",
        "comments": 16,
        "views": 650,
        "view_label": "650",
        "time_label": "昨天",
        "timestamp": "2026-05-11T03:20:00",
        "tags": ["模板包", "项目路演", "电商运营"],
        "actions": [
            {"key": "copy-template", "label": "复制模板", "tone": "blue", "kind": "copy"},
            {"key": "edit", "label": "二次编辑", "tone": "pink", "kind": "detail"},
        ],
        "template_text": "# 招商海报文案模板\n\n主标题：\n六大权益：\n入驻条件：\n联系方式：",
        "body_markdown": """# 招商海报文案模板

适用于园区招商、联盟招募和项目路演报名页。

请按主标题、六大权益、入驻条件和联系方式四段生成文案，再根据渠道版式压缩字数。
""",
    },
    {
        "id": "opc-contract-subject",
        "category_key": "talk",
        "badge_label": "交流",
        "mark": "问",
        "tone": "talk",
        "title": "OPC 公司做 AI 接单，合同主体怎么写更稳？",
        "summary": "欢迎法务、财税和有实际接单经验的伙伴补充注意事项。",
        "reply_strip": "管理员提醒：不要在公开评论区发布客户隐私和未脱敏合同。",
        "comments": 41,
        "views": 1000,
        "view_label": "1.0k",
        "time_label": "2 天前",
        "timestamp": "2026-05-10T03:20:00",
        "tags": ["合同经验", "接单报价", "法务"],
        "actions": [],
        "body_markdown": """# 合同主体怎么写更稳？

OPC 公司做 AI 接单时，合同主体、发票、服务范围和交付验收需要统一口径。

请有法务、财税或实战经验的伙伴补充注意事项。
""",
    },
    {
        "id": "compute-voucher-materials",
        "category_key": "resource",
        "badge_label": "资源对接",
        "mark": "算",
        "tone": "resource",
        "title": "算力券申请材料清单，有没有可复用版本？",
        "summary": "征集申请材料、项目说明、预算表模板，沉淀成社区共享资源。",
        "comments": 27,
        "views": 540,
        "view_label": "540",
        "time_label": "3 天前",
        "timestamp": "2026-05-09T03:20:00",
        "tags": ["算力券", "资源对接", "模板包"],
        "actions": [
            {"key": "contribute", "label": "贡献资料", "tone": "blue", "kind": "detail"},
            {"key": "follow", "label": "关注更新", "tone": "pink", "kind": "follow"},
        ],
        "body_markdown": """# 算力券申请材料清单

征集可复用的申请材料、项目说明和预算表模板。

后续会整理成社区共享资源，欢迎在评论区补充材料名称、适用地区和注意事项。
""",
    },
    {
        "id": "roadshow-next-week",
        "category_key": "pitch",
        "badge_label": "路演",
        "mark": "演",
        "tone": "order",
        "title": "下周项目路演征集：AI 短剧、电商、工具类优先",
        "summary": "报名后在评论区提交一句话介绍、Demo 链接和需要对接的资源。",
        "comments": 12,
        "views": 388,
        "view_label": "388",
        "time_label": "本周",
        "timestamp": "2026-05-08T03:20:00",
        "tags": ["AI短剧", "项目路演", "电商运营"],
        "actions": [
            {"key": "signup", "label": "我要报名", "tone": "blue", "kind": "detail"},
            {"key": "rules", "label": "查看规则", "tone": "pink", "kind": "detail"},
        ],
        "body_markdown": """# 下周项目路演征集

本期优先开放 AI 短剧、电商运营和工具类项目。

报名请在评论区提交一句话介绍、Demo 链接、当前阶段和希望对接的资源。
""",
    },
]


class CommunicationService:
    def __init__(self, session: Session):
        self.session = session

    def hall_payload(self, *, tenant_id: str, user_id: str = "demo-user") -> dict:
        posts = self._posts(tenant_id=tenant_id)
        comment_counts = self._comment_counts(tenant_id=tenant_id, paths=[post.action_value for post in posts])
        favorite_paths = self._favorite_paths(tenant_id=tenant_id, user_id=user_id)
        return {
            "categories": COMMUNICATION_CATEGORIES,
            "hot_tags": COMMUNICATION_HOT_TAGS,
            "hot_topics": COMMUNICATION_HOT_TOPICS,
            "posts": [
                self._post_payload(post, comment_counts=comment_counts, favorite_paths=favorite_paths)
                for post in posts
            ],
        }

    def create_post(self, *, tenant_id: str, payload: CommunicationPostCreate, actor: User) -> dict:
        title = payload.title.strip()
        body = payload.body_markdown.strip()
        category_key = payload.category_key.strip() or "talk"
        if not title:
            raise ValueError("title is required")
        if not body:
            raise ValueError("body_markdown is required")

        section = self._ensure_posts_section(tenant_id=tenant_id)
        slug = self._unique_slug(tenant_id=tenant_id, title=title)
        detail_path = f"/communication/detail/{slug}"
        category_label = category_label_for(category_key)
        summary = summarize_markdown(body)
        tags = [category_label, "用户发布"]
        now = utcnow()
        metadata = {
            "communication": {
                "category_key": category_key,
                "badge_label": category_label,
                "mark": category_label[:1] or "帖",
                "tone": tone_for_category(category_key),
                "comments": 0,
                "views": 1,
                "view_label": "1",
                "time_label": "刚刚",
                "timestamp": int(now.timestamp() * 1000),
                "pinned": False,
                "actions": [
                    {"key": "read", "label": "查看正文", "tone": "blue", "kind": "detail"},
                    {"key": "favorite", "label": "收藏", "tone": "pink", "kind": "favorite"},
                ],
            },
            "authorUserId": actor.id,
            "visibility": "community",
            "detail": {
                "summary": summary,
                "actions": [{"key": "favorite", "label": "收藏", "tone": "pink"}],
            },
        }
        item = ContentItem(
            id=slug,
            tenant_id=tenant_id,
            section_id=section.id,
            item_type=COMMUNICATION_POST_TYPE,
            title=title,
            subtitle=summary,
            category=category_label,
            icon="MessageCircle",
            badge=category_label,
            tags=tags,
            sort_order=0,
            enabled=True,
            action_type="route",
            action_value=detail_path,
            metadata_json=metadata,
        )
        document = PortalDetailDocument(
            tenant_id=tenant_id,
            detail_path=detail_path,
            title=title,
            summary=summary,
            body_markdown=body,
            tags=tags,
            visibility="community",
            author_user_id=actor.id,
            current_version=1,
            release_note="初始化帖子",
            status="PUBLISHED",
            published_at=now,
        )
        self.session.add_all([item, document])
        self.session.flush()
        self.session.add(
            PortalDetailVersion(
                tenant_id=tenant_id,
                document_id=document.id,
                detail_path=detail_path,
                version=1,
                title=title,
                summary=summary,
                body_markdown=body,
                tags=tags,
                visibility="community",
                release_note="初始化帖子",
                author_user_id=actor.id,
            )
        )
        self.session.commit()
        self.session.refresh(item)
        return {
            "post": self._post_payload(item, comment_counts={}, favorite_paths=set()),
            "detail_path": detail_path,
        }

    def ensure_seed_posts(self, *, tenant_id: str) -> None:
        section = self._ensure_posts_section(tenant_id=tenant_id, static_id=COMMUNICATION_SECTION_ID)
        for index, seed in enumerate(SEED_COMMUNICATION_POSTS, start=1):
            self._upsert_seed_post(tenant_id=tenant_id, section=section, seed=seed, sort_order=index * 10)

    def _upsert_seed_post(self, *, tenant_id: str, section: ContentSection, seed: dict[str, Any], sort_order: int) -> None:
        post_id = str(seed["id"])
        detail_path = f"/communication/detail/{post_id}"
        category_label = category_label_for(str(seed["category_key"]))
        metadata = {
            "communication": {
                "category_key": seed["category_key"],
                "badge_label": seed.get("badge_label") or category_label,
                "mark": seed.get("mark") or category_label[:1],
                "tone": seed.get("tone") or tone_for_category(str(seed["category_key"])),
                "reply_strip": seed.get("reply_strip") or "",
                "comments": int(seed.get("comments") or 0),
                "views": int(seed.get("views") or 0),
                "view_label": seed.get("view_label") or str(seed.get("views") or 0),
                "time_label": seed.get("time_label") or "",
                "timestamp": timestamp_value(seed.get("timestamp")),
                "pinned": bool(seed.get("pinned")),
                "actions": seed.get("actions") or [],
                "template_text": seed.get("template_text") or "",
            },
            "authorUserId": "demo-admin",
            "visibility": "community",
            "detail": {
                "summary": seed["summary"],
                "actions": seed.get("actions") or [],
            },
        }
        item = self.session.get(ContentItem, post_id)
        if item is None:
            item = ContentItem(id=post_id, tenant_id=tenant_id, section_id=section.id, item_type=COMMUNICATION_POST_TYPE)
            self.session.add(item)
        item.tenant_id = tenant_id
        item.section_id = section.id
        item.item_type = COMMUNICATION_POST_TYPE
        item.title = str(seed["title"])
        item.subtitle = str(seed["summary"])
        item.category = category_label
        item.icon = "MessageCircle"
        item.badge = str(seed.get("badge_label") or category_label)
        item.tags = list(seed.get("tags") or [category_label])
        item.sort_order = sort_order
        item.enabled = True
        item.action_type = "route"
        item.action_value = detail_path
        item.required_membership = False
        item.point_cost = 0
        item.metadata_json = metadata

        document_id = f"comm-detail-{index_key(sort_order)}"
        version_id = f"{document_id}-v1"
        document = self.session.get(PortalDetailDocument, document_id)
        if document is None:
            document = self.session.scalar(
                select(PortalDetailDocument).where(
                    PortalDetailDocument.tenant_id == tenant_id,
                    PortalDetailDocument.detail_path == detail_path,
                )
            )
        if document is None:
            document = PortalDetailDocument(id=document_id, tenant_id=tenant_id, detail_path=detail_path)
            self.session.add(document)
        document.tenant_id = tenant_id
        document.detail_path = detail_path
        document.title = str(seed["title"])
        document.summary = str(seed["summary"])
        document.body_markdown = str(seed.get("body_markdown") or seed["summary"])
        document.tags = list(seed.get("tags") or [category_label])
        document.visibility = "community"
        document.author_user_id = "demo-admin"
        document.current_version = 1
        document.release_note = "初始化大厅帖子"
        document.status = "PUBLISHED"
        document.published_at = document.published_at or utcnow()

        version = self.session.get(PortalDetailVersion, version_id)
        if version is None:
            version = self.session.scalar(
                select(PortalDetailVersion).where(
                    PortalDetailVersion.tenant_id == tenant_id,
                    PortalDetailVersion.document_id == document.id,
                    PortalDetailVersion.version == 1,
                )
            )
        if version is None:
            version = PortalDetailVersion(id=version_id, tenant_id=tenant_id, document_id=document.id, version=1)
            self.session.add(version)
        version.tenant_id = tenant_id
        version.document_id = document.id
        version.detail_path = detail_path
        version.version = 1
        version.title = document.title
        version.summary = document.summary
        version.body_markdown = document.body_markdown
        version.tags = document.tags or []
        version.visibility = document.visibility
        version.release_note = document.release_note
        version.author_user_id = document.author_user_id

    def _posts(self, *, tenant_id: str) -> list[ContentItem]:
        return list(
            self.session.scalars(
                select(ContentItem)
                .join(ContentSection, ContentSection.id == ContentItem.section_id)
                .where(
                    ContentItem.tenant_id == tenant_id,
                    ContentItem.item_type == COMMUNICATION_POST_TYPE,
                    ContentItem.enabled.is_(True),
                    ContentSection.area == "communication",
                    ContentSection.enabled.is_(True),
                )
                .order_by(ContentItem.sort_order.asc(), ContentItem.created_at.desc())
            )
        )

    def _ensure_posts_section(self, *, tenant_id: str, static_id: str | None = None) -> ContentSection:
        section = self.session.scalar(
            select(ContentSection).where(
                ContentSection.tenant_id == tenant_id,
                ContentSection.area == "communication",
                ContentSection.section_key == COMMUNICATION_SECTION_KEY,
            )
        )
        if section is not None:
            return section
        section = ContentSection(
            id=static_id or new_id(),
            tenant_id=tenant_id,
            area="communication",
            section_key=COMMUNICATION_SECTION_KEY,
            title="沟通大厅帖子",
            subtitle="接单、模板、交流、资源对接都在这里沉淀",
            layout="communication-post-grid",
            sort_order=15,
            enabled=True,
        )
        self.session.add(section)
        self.session.flush()
        return section

    def _unique_slug(self, *, tenant_id: str, title: str) -> str:
        base = slugify_title(title)
        slug = base
        suffix = utcnow().strftime("%H%M%S")
        counter = 1
        while self._slug_exists(tenant_id=tenant_id, slug=slug):
            ending = suffix if counter == 1 else f"{suffix}{counter}"
            slug = f"{base[: max(8, 31 - len(ending))]}-{ending}"[:32].strip("-")
            counter += 1
        return slug

    def _slug_exists(self, *, tenant_id: str, slug: str) -> bool:
        path = f"/communication/detail/{slug}"
        return bool(
            self.session.scalar(
                select(ContentItem.id).where(
                    ContentItem.tenant_id == tenant_id,
                    ContentItem.action_value == path,
                )
            )
        )

    def _comment_counts(self, *, tenant_id: str, paths: list[str]) -> dict[str, int]:
        if not paths:
            return {}
        rows = self.session.execute(
            select(PortalDetailComment.detail_path, func.count(PortalDetailComment.id))
            .where(
                PortalDetailComment.tenant_id == tenant_id,
                PortalDetailComment.detail_path.in_(paths),
                PortalDetailComment.status == "VISIBLE",
            )
            .group_by(PortalDetailComment.detail_path)
        ).all()
        return {path: int(count) for path, count in rows}

    def _favorite_paths(self, *, tenant_id: str, user_id: str) -> set[str]:
        records = self.session.scalars(
            select(UserPortalAction).where(
                UserPortalAction.tenant_id == tenant_id,
                UserPortalAction.user_id == user_id,
                UserPortalAction.status == "COMPLETED",
                UserPortalAction.action_key.in_(["favorite", "follow"]),
            )
        )
        return {record.detail_path for record in records}

    def _post_payload(
        self,
        post: ContentItem,
        *,
        comment_counts: dict[str, int],
        favorite_paths: set[str],
    ) -> dict:
        metadata = post.metadata_json or {}
        communication = metadata.get("communication") if isinstance(metadata, dict) else {}
        if not isinstance(communication, dict):
            communication = {}
        views = int(communication.get("views") or 0)
        base_comments = int(communication.get("comments") or 0)
        comments = base_comments + int(comment_counts.get(post.action_value, 0))
        category_key = str(communication.get("category_key") or key_for_category(post.category))
        category_label = category_label_for(category_key, fallback=post.category or post.badge)
        timestamp = communication.get("timestamp") or int((post.created_at or utcnow()).timestamp() * 1000)
        return {
            "id": post.id,
            "item_id": post.id,
            "detail_path": post.action_value,
            "category_key": category_key,
            "category_label": category_label,
            "badge_label": str(communication.get("badge_label") or post.badge or category_label),
            "mark": str(communication.get("mark") or category_label[:1] or "帖"),
            "tone": str(communication.get("tone") or tone_for_category(category_key)),
            "title": post.title,
            "summary": post.subtitle,
            "reply_strip": str(communication.get("reply_strip") or ""),
            "comments": comments,
            "views": views,
            "view_label": str(communication.get("view_label") or format_view_count(views)),
            "time_label": str(communication.get("time_label") or "刚刚"),
            "timestamp": timestamp,
            "pinned": bool(communication.get("pinned")),
            "tags": post.tags or [],
            "actions": communication.get("actions") or [],
            "template_text": str(communication.get("template_text") or ""),
            "is_favorite": post.action_value in favorite_paths,
        }


def category_label_for(category_key: str, fallback: str = "交流") -> str:
    category = next((item for item in COMMUNICATION_CATEGORIES if item["key"] == category_key), None)
    return str(category["label"]) if category else fallback


def key_for_category(label: str) -> str:
    category = next((item for item in COMMUNICATION_CATEGORIES if item["label"] == label), None)
    return str(category["key"]) if category else "talk"


def tone_for_category(category_key: str) -> str:
    if category_key == "template":
        return "template"
    if category_key == "talk":
        return "talk"
    if category_key in {"benefit", "resource"}:
        return "resource"
    if category_key == "pitch":
        return "pitch"
    return "order"


def summarize_markdown(value: str) -> str:
    text = re.sub(r"[#>*_`\-\[\]\(\)]", " ", value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:160] or "用户发布内容"


def slugify_title(title: str) -> str:
    normalized = title.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    if not normalized:
        normalized = f"post-{utcnow().strftime('%Y%m%d%H%M%S')}"
    return normalized[:32].strip("-") or new_id()[:16]


def timestamp_value(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value:
        try:
            return int(datetime.fromisoformat(value).timestamp() * 1000)
        except ValueError:
            return int(utcnow().timestamp() * 1000)
    return int(utcnow().timestamp() * 1000)


def index_key(sort_order: int) -> str:
    return f"{max(1, sort_order // 10):02d}"


def format_view_count(value: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return str(value)

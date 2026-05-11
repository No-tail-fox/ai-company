from __future__ import annotations

import hashlib
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ApiChannel,
    AiAssistant,
    ChannelRoute,
    ContentItem,
    ContentPage,
    ContentSection,
    ChatMessage,
    ChatSession,
    HomeHeroSlide,
    MembershipPlan,
    ModelConfig,
    PromptTemplate,
    Tenant,
    ToolModelBinding,
    User,
    UserMembership,
    Wallet,
    utcnow,
)
from app.services.auth import hash_password


BRAND_NAME = "新商机"
DEMO_TENANT_NAME = BRAND_NAME
DEMO_ORDER_SECTION_TITLE = f"{BRAND_NAME} 接单中心"
LEGACY_DEMO_TENANT_NAMES = {"新商机 AI 社区", "新商盟 AI 社区", "OPC社区", "Light AI SaaS"}
LEGACY_ORDER_SECTION_TITLES = {"OPC 接单中心"}


def ensure_demo_data(session: Session, *, tenant_id: str = "demo") -> None:
    tenant = session.get(Tenant, tenant_id)
    if tenant is None:
        session.add(Tenant(id=tenant_id, slug="demo", name=DEMO_TENANT_NAME))
    elif tenant.name in LEGACY_DEMO_TENANT_NAMES:
        tenant.name = DEMO_TENANT_NAME

    user = session.get(User, "demo-user")
    if user is None:
        session.add(User(id="demo-user", tenant_id=tenant_id, phone="13800000000", display_name="演示用户", role="USER"))
        session.add(Wallet(id="demo-wallet", tenant_id=tenant_id, user_id="demo-user", balance=120000, frozen_balance=0))

    admin = session.get(User, "demo-admin")
    if admin is None:
        session.add(
            User(
                id="demo-admin",
                tenant_id=tenant_id,
                phone="13900000000",
                display_name="运营管理员",
                role="ADMIN",
                password_hash=hash_password("admin123456"),
            )
        )

    _add_pages(session, tenant_id)
    _add_home_hero_slides(session, tenant_id)
    _add_sections(session, tenant_id)
    _add_items(session, tenant_id)
    _add_assistants(session, tenant_id)
    _add_templates(session, tenant_id)
    _add_memberships(session, tenant_id)
    _add_audio_routes(session, tenant_id)
    _add_model_configurations(session, tenant_id)
    _add_chat_runtime(session, tenant_id)
    session.commit()


PAGES = [
    ("page-home", "home", "首页", "常用AI学习中心", "学习、接单、社群和活动的统一入口", "Home", 10),
    ("page-assistant", "assistant", "AI 助理", "智能助理广场", "办公、营销、学习、法务等场景助理集合", "Bot", 20),
    ("page-workbench", "workbench", "工作台", "AI 工作台", "真实对话、队列和快捷操作的统一工作区", "LayoutDashboard", 25),
    ("page-marketing", "marketing", "AI 营销", "营销增长中心", "从内容生成到投放复盘的一站式工具台", "Megaphone", 30),
    ("page-image", "image", "AI 图片", "AI图片创作中心", "提示词、模板、批量出图和生成队列", "Image", 35),
    ("page-video", "video", "AI 视频", "AI视频创作中心", "脚本、数字人、剪辑、字幕和渲染队列", "FileVideo", 40),
    ("page-audio", "audio", "AI 音频", "AI音频创作中心", "配音、转写、降噪、播客和音色库", "Headphones", 50),
    ("page-coding", "coding", "AI 编程", "AI编程工作台", "代码生成、审查、测试和自动化脚本", "Workflow", 60),
    ("page-writing", "writing", "AI 写作", "AI写作中心", "文章、报告、简历、论文和提示词模板", "Feather", 70),
    ("page-ecommerce", "ecommerce", "AI 电商", "AI电商运营中心", "商品内容、客服话术、店铺分析和素材生成", "WandSparkles", 80),
    ("page-legal", "legal", "AI 法务", "AI法务服务台", "合同审查、法律咨询、证据整理和文书草拟", "Scale", 90),
    ("page-office", "office", "AI 办公", "AI办公效率中心", "PPT、表格、会议、邮件和流程自动化", "BriefcaseBusiness", 100),
]


def _add_pages(session: Session, tenant_id: str) -> None:
    for id_, page_key, label, title, subtitle, icon, order in PAGES:
        if session.get(ContentPage, id_) is None:
            session.add(
                ContentPage(
                    id=id_,
                    tenant_id=tenant_id,
                    page_key=page_key,
                    label=label,
                    title=title,
                    subtitle=subtitle,
                    icon=icon,
                    sort_order=order,
                    enabled=True,
                )
            )


def _add_home_hero_slides(session: Session, tenant_id: str) -> None:
    slides = [
        (
            "home-slide-vip",
            "会员活动限时特惠",
            "开通会员解锁模板、社群和交付资料",
            "会员专享",
            "立即开通",
            "查看权益，不走支付",
            "/membership/benefits",
            10,
            {"accent": "gold", "theme": "vip"},
        ),
        (
            "home-slide-template",
            "模板上新不停",
            "PPT、报价单、社媒和交付模板持续更新",
            "今日上新",
            "立即查看",
            "今天就能直接用",
            "/templates",
            20,
            {"accent": "blue", "theme": "template"},
        ),
        (
            "home-slide-community",
            "社群和工作台一起用",
            "入门群、打卡群、接单群和资源群都在这里",
            "社群活跃",
            "进入社群",
            "打开首页就能直达",
            "/community/starter",
            30,
            {"accent": "green", "theme": "community"},
        ),
    ]
    for id_, title, subtitle, badge, cta_label, cta_subtitle, action_value, order, metadata in slides:
        existing = session.get(HomeHeroSlide, id_)
        if existing is None:
            session.add(
                HomeHeroSlide(
                    id=id_,
                    tenant_id=tenant_id,
                    title=title,
                    subtitle=subtitle,
                    badge=badge,
                    cta_label=cta_label,
                    cta_subtitle=cta_subtitle,
                    image_url="",
                    action_type="route",
                    action_value=action_value,
                    sort_order=order,
                    enabled=True,
                    metadata_json=metadata,
                )
            )
        else:
            existing.title = title
            existing.subtitle = subtitle
            existing.badge = badge
            existing.cta_label = cta_label
            existing.cta_subtitle = cta_subtitle
            existing.action_value = action_value
            existing.sort_order = order
            existing.enabled = True
            existing.metadata_json = metadata


def _add_sections(session: Session, tenant_id: str) -> None:
    sections = _section_definitions()
    for id_, area, key, title, subtitle, layout, order in sections:
        existing = session.get(ContentSection, id_)
        if existing is None:
            session.add(
                ContentSection(
                    id=id_,
                    tenant_id=tenant_id,
                    area=area,
                    section_key=key,
                    title=title,
                    subtitle=subtitle,
                    layout=layout,
                    sort_order=order,
                    enabled=True,
                )
            )
        elif id_ == "section-orders" and existing.title in LEGACY_ORDER_SECTION_TITLES:
            existing.title = title


def _add_items(session: Session, tenant_id: str) -> None:
    items = _item_definitions()
    for id_, section_id, item_type, title, subtitle, category, icon, image_url, action_type, action_value, sort_order, required_membership, point_cost in items:
        metadata = _default_item_metadata(
            title=title,
            subtitle=subtitle,
            category=category,
            action_value=action_value,
        )
        custom_metadata = _third_party_tool_metadata(
            item_id=id_,
            title=title,
            subtitle=subtitle,
            action_value=action_value,
        )
        if custom_metadata:
            metadata = _merge_item_metadata(metadata, custom_metadata)
        existing = session.get(ContentItem, id_)
        if existing is None:
            session.add(
                ContentItem(
                    id=id_,
                    tenant_id=tenant_id,
                    section_id=section_id,
                    item_type=item_type,
                    title=title,
                    subtitle=subtitle,
                    category=category,
                    icon=icon,
                    image_url=image_url,
                    action_type=action_type,
                    action_value=action_value,
                    sort_order=sort_order,
                    required_membership=required_membership,
                    point_cost=point_cost,
                    metadata_json=metadata,
                    enabled=True,
                )
            )
        elif not existing.metadata_json:
            existing.metadata_json = metadata


def _section_definitions() -> list[tuple[str, str, str, str, str, str, int]]:
    sections = [
        ("section-learning", "home", "learning_center", "常用AI学习中心", "课程、实战和变现路径", "learning-grid", 10),
        ("section-orders", "home", "order_center", DEMO_ORDER_SECTION_TITLE, "适合新手和团队交付的接单入口", "order-grid", 20),
        ("section-communities", "home", "communities", "兴趣社群", "按成长阶段和赛道加入社群", "banner-row", 30),
        ("section-banners", "home", "banners", "热门活动", "模板、活动和会员福利", "promo", 40),
        ("section-home-promo", "home", "membership_benefits", "会员权益详情", "一键查看会员专享内容", "promo-carousel", 15),
        ("section-home-workbench", "home", "workbench_shortcuts", "我的工作台", "AI 对话、图片生成、视频脚本、PPT 办公、接单交付、素材库", "tool-grid", 16),
        ("section-home-tools", "home", "home_tools", "工具框", "常用工具、办公模板、接单报价、内容生成、电商优化", "tool-grid", 35),
        ("section-quick-start", "home", "quick_start", "新人快速上手", "账号、工具和首个提示词任务", "task-list", 50),
        ("section-growth-path", "home", "growth_path", "进阶成长路径", "训练营、作业拆解和案例复盘", "learning-grid", 60),
        ("section-earning-templates", "home", "earning_templates", "接单交付模板", "报价、验收和复购跟进", "template-list", 70),
        ("section-resource-hub", "home", "resource_hub", "资源对接库", "工具权益、行业资料和合作需求", "banner-row", 80),
        ("section-project-cocreation", "home", "project_cocreation", "项目共创广场", "组队招募、协作交付和共创案例", "order-grid", 90),
        ("section-workspace-tools", "home", "workspace_tools", "常用工作台", "高频 AI 工具一键启动", "tool-grid", 100),
        ("section-task-board", "home", "task_board", "任务入口", "最近使用、待交付项目和素材库", "stat-strip", 110),
        ("section-third-party-tools", "home", "third_party_tools", "第三方工具展示区", "外部工具、官网链接和客户端下载入口", "third-party-tools", 115),
        ("section-toolkit", "home", "toolkit", "专业工具包", "模板列表、行业工具和效率组件", "template-list", 120),
        ("section-template-ranking", "home", "template_ranking", "工具包排行榜", "近期高频使用模板", "ranking-list", 130),
    ]
    for _, page_key, label, title, subtitle, _, order in PAGES:
        if page_key == "home":
            continue
        sections.extend(
            [
                (f"section-{page_key}-overview", page_key, "overview", title, subtitle, "stat-strip", 10),
                (f"section-{page_key}-tools", page_key, "tools", f"{label}工具矩阵", "高频能力一键进入工作台", "tool-grid", 20),
                (f"section-{page_key}-templates", page_key, "templates", "模板与工作流", "沉淀可复用交付资产", "template-list", 30),
                (f"section-{page_key}-ranking", page_key, "ranking", "热门推荐", "近期高频使用工具榜", "ranking-list", 40),
            ]
        )
    return sections


def _item_definitions() -> list[tuple[str, str, str, str, str, str, str, str, str, str, int, bool, int]]:
    items: list[tuple[str, str, str, str, str, str, str, str, str, str, int, bool, int]] = [
        ("learn-01", "section-learning", "course", "《0基础AI通识课》", "12 大核心渠道从认知到上手一站式通关", "基础必备", "FileVideo", "", "route", "/workspace/course", 10, False, 0),
        ("learn-02", "section-learning", "course", "《AI 实战必修课》", "办公/剪辑/写作全场景效率翻倍", "基础必备", "MonitorPlay", "", "route", "/workspace/course", 20, True, 0),
        ("learn-03", "section-learning", "course", "《AI 商业变现课》", "内容创作 + 电商营销全链路落地盈利", "接单变现", "ScanSearch", "", "route", "/workspace/course", 30, True, 0),
        ("learn-04", "section-learning", "course", "《AI 爆款内容创作》", "短视频脚本、标题、封面和投放流程", "AI营销", "Presentation", "", "route", "/workspace/course", 40, True, 20),
        ("learn-05", "section-learning", "course", "《AI降本增效》", "企业办公和运营流程自动化改造", "AI办公", "Workflow", "", "route", "/workspace/course", 50, True, 20),
        ("learn-06", "section-learning", "course", "《AI高阶实战》", "从工具使用到项目交付训练", "学习成长", "NotebookTabs", "", "route", "/workspace/course", 60, True, 30),
        ("order-01", "section-orders", "service", "AI创作订单", "PPT、文案、图片与短视频交付", "接单变现", "Feather", "", "route", "/workspace/orders", 10, True, 20),
        ("order-02", "section-orders", "service", "AI自动化定制", "为客户定制办公自动化流程", "项目共创", "FileText", "", "route", "/workspace/automation", 20, True, 50),
        ("order-03", "section-orders", "service", "AI电商优化", "商品标题、详情页与客服话术", "AI电商", "WandSparkles", "", "route", "/workspace/ecommerce", 30, True, 30),
        ("order-04", "section-orders", "service", "AI专业定制", "行业知识库、客服和运营方案", "项目共创", "PenTool", "", "route", "/workspace/custom", 40, True, 50),
        ("order-05", "section-orders", "service", "AI企业陪跑", "企业团队AI落地陪跑和培训", "学习成长", "Building2", "", "route", "/workspace/consulting", 50, True, 0),
        ("comm-01", "section-communities", "community", "入门交流群", "新人答疑、工具清单和上手路线", "社群", "MessageCircle", "", "route", "/community/starter", 10, False, 0),
        ("comm-02", "section-communities", "community", "学习打卡群", "每日任务、案例拆解和作业反馈", "学习成长", "GraduationCap", "", "route", "/community/study", 20, True, 0),
        ("comm-03", "section-communities", "community", "接单变现群", "接单案例、报价模板和交付流程", "接单变现", "Handshake", "", "route", "/community/orders", 30, True, 0),
        ("comm-04", "section-communities", "community", "垂直赛道群", "短视频、电商、教育和办公赛道", "资源对接", "Network", "", "route", "/community/vertical", 40, True, 0),
        ("banner-01", "section-banners", "banner", "热门模板上新！", "一键轻松取用办公模板", "运营活动", "Gift", "linear-red", "route", "/templates", 10, True, 0),
        ("banner-02", "section-banners", "banner", "商业计划书模板", "融资路演、商业策划、项目计划", "专业工具包", "ChartColumn", "linear-blue", "route", "/templates/business", 20, True, 0),
        ("banner-03", "section-banners", "banner", "资源内测邀请", "优先体验新的合作资源和资料包", "资源对接", "Sparkles", "linear-purple", "route", "/resources/trial", 30, False, 0),
        ("banner-vip", "section-home-promo", "banner", "会员活动限时特惠", "开通会员领取模板、社群和接单资料", "会员专享", "Crown", "", "route", "/membership/benefits", 15, True, 0),
        ("home-vip-1", "section-home-promo", "promo", "会员权益详情", "查看会员专享模板、社群和资料", "会员专享", "Crown", "", "route", "/membership/benefits", 10, False, 0),
        ("home-workbench-1", "section-home-workbench", "tool", "AI 对话", "写作、问答和方案梳理", "应用工作台", "Bot", "", "route", "/workbench", 10, False, 0),
        ("home-workbench-2", "section-home-workbench", "tool", "图片生成", "海报、封面和详情图", "应用工作台", "Image", "", "route", "/workbench/image", 20, False, 0),
        ("home-workbench-3", "section-home-workbench", "tool", "视频脚本", "选题、分镜和口播脚本", "应用工作台", "MonitorPlay", "", "route", "/workbench/video", 30, False, 0),
        ("home-workbench-4", "section-home-workbench", "tool", "PPT 办公", "大纲到页面快速生成", "应用工作台", "Presentation", "", "route", "/workspace/ppt", 40, False, 0),
        ("home-workbench-5", "section-home-workbench", "tool", "接单交付", "报价、交付和复购跟进", "接单变现", "BriefcaseBusiness", "", "route", "/workspace/deliveries", 50, True, 0),
        ("home-workbench-6", "section-home-workbench", "tool", "素材库", "图片、模板和提示词资产", "应用工作台", "CloudUpload", "", "route", "/workspace/assets", 60, True, 0),
        ("home-tool-1", "section-home-tools", "template", "常用工具", "高频 AI 工具入口集合", "工具框", "LayoutGrid", "", "route", "/workbench", 10, False, 0),
        ("home-tool-2", "section-home-tools", "template", "办公模板", "PPT、表格和会议纪要模板", "工具框", "Presentation", "", "route", "/toolkit/office", 20, False, 0),
        ("home-tool-3", "section-home-tools", "template", "接单报价", "报价、验收和复购话术", "接单变现", "ReceiptText", "", "route", "/templates/quote", 30, False, 0),
        ("home-tool-4", "section-home-tools", "template", "内容生成", "文案、脚本和社媒内容", "增长", "Feather", "", "route", "/marketing", 40, False, 0),
        ("home-tool-5", "section-home-tools", "template", "电商优化", "标题、详情页和客服话术", "电商", "WandSparkles", "", "route", "/workspace/ecommerce", 50, True, 0),
        ("quick-01", "section-quick-start", "task", "配置个人 AI 工具箱", "完成账号、常用模型和提示词收藏", "基础必备", "LayoutGrid", "", "route", "/workspace/setup", 10, False, 0),
        ("quick-02", "section-quick-start", "task", "完成首个提示词任务", "用模板生成一份可交付内容", "基础必备", "Sparkles", "", "route", "/workspace/first-task", 20, False, 0),
        ("quick-03", "section-quick-start", "task", "领取新手资料包", "下载工具清单、学习路线和案例库", "基础必备", "Download", "", "route", "/resources/starter-kit", 30, False, 0),
        ("growth-01", "section-growth-path", "course", "每日 30 分钟训练营", "围绕真实场景拆成可执行任务", "学习成长", "Clock3", "", "route", "/learning/daily", 10, True, 0),
        ("growth-02", "section-growth-path", "case", "优秀作业拆解", "学习高质量提示词和交付结构", "学习成长", "ScanSearch", "", "route", "/learning/cases", 20, True, 10),
        ("growth-03", "section-growth-path", "course", "行业案例复盘", "短视频、电商、办公和法务案例库", "学习成长", "NotebookTabs", "", "route", "/learning/reviews", 30, True, 10),
        ("earning-01", "section-earning-templates", "template", "报价沟通模板", "快速明确需求、报价和修改次数", "接单变现", "ReceiptText", "", "route", "/templates/quote", 10, True, 0),
        ("earning-02", "section-earning-templates", "template", "交付验收清单", "按项目节点检查文件、说明和售后", "接单变现", "ShieldCheck", "", "route", "/templates/delivery", 20, True, 0),
        ("earning-03", "section-earning-templates", "template", "复购跟进话术", "交付后持续运营客户关系", "接单变现", "MessageCircle", "", "route", "/templates/follow-up", 30, True, 0),
        ("resource-01", "section-resource-hub", "resource", "工具优惠合集", "模型、剪辑、设计和办公工具权益", "资源对接", "Gift", "", "route", "/resources/tools", 10, False, 0),
        ("resource-02", "section-resource-hub", "resource", "行业资料库", "可复用的运营、法务和电商资料", "资源对接", "FileText", "", "route", "/resources/library", 20, True, 0),
        ("resource-03", "section-resource-hub", "resource", "合作需求广场", "发布资源、客户线索和合作需求", "资源对接", "Handshake", "", "route", "/resources/market", 30, True, 0),
        ("project-01", "section-project-cocreation", "project", "短视频矩阵共创", "脚本、剪辑、投放成员组队交付", "项目共创", "FileVideo", "", "route", "/projects/video", 10, True, 0),
        ("project-02", "section-project-cocreation", "project", "企业知识库搭建", "资料整理、流程设计和助手配置", "项目共创", "Workflow", "", "route", "/projects/knowledge-base", 20, True, 0),
        ("project-03", "section-project-cocreation", "project", "AI办公改造案例", "用自动化流程帮助团队降本增效", "项目共创", "BriefcaseBusiness", "", "route", "/projects/office", 30, True, 0),
        ("workspace-00", "section-workspace-tools", "tool", "AI 工作台", "真实对话、图像、视频和音频任务统一入口", "应用工作台", "LayoutGrid", "", "route", "/workbench", 5, False, 0),
        ("workspace-01", "section-workspace-tools", "tool", "PPT 生成工作台", "从大纲到页面自动生成", "应用工作台", "Presentation", "", "route", "/workspace/ppt", 10, False, 0),
        ("workspace-02", "section-workspace-tools", "tool", "视频脚本工作台", "选题、脚本、分镜一站式处理", "应用工作台", "MonitorPlay", "", "route", "/workspace/video-script", 20, False, 0),
        ("workspace-03", "section-workspace-tools", "tool", "电商运营工作台", "标题、详情和客服话术生成", "应用工作台", "WandSparkles", "", "route", "/workspace/ecommerce", 30, True, 10),
        ("workspace-04", "section-workspace-tools", "tool", "合同审查工作台", "检查风险条款和修改建议", "应用工作台", "Scale", "", "route", "/workspace/legal", 40, True, 10),
        ("task-01", "section-task-board", "task", "最近使用", "继续上次的工具和内容生成任务", "应用工作台", "Clock3", "", "route", "/workspace/recent", 10, False, 0),
        ("task-02", "section-task-board", "task", "待交付项目", "查看接单任务、素材和交付节点", "应用工作台", "BriefcaseBusiness", "", "route", "/workspace/deliveries", 20, True, 0),
        ("task-03", "section-task-board", "task", "素材库", "管理上传图片、模板和提示词资产", "应用工作台", "CloudUpload", "", "route", "/workspace/assets", 30, True, 0),
        ("third-tool-jianying", "section-third-party-tools", "third_party_tool", "剪映专业版", "视频剪辑与模板包装", "视频", "Scissors", "", "external_link", "https://example.com/tools/jianying", 10, False, 0),
        ("third-tool-feishu", "section-third-party-tools", "third_party_tool", "飞书多维表格", "项目表格与团队协作", "办公", "Sheet", "", "external_link", "https://example.com/tools/feishu-base", 20, False, 0),
        ("third-tool-meeting", "section-third-party-tools", "third_party_tool", "腾讯会议", "远程沟通与交付复盘", "协作", "Users", "", "external_link", "https://example.com/tools/meeting", 30, False, 0),
        ("third-tool-apifox", "section-third-party-tools", "third_party_tool", "Apifox", "接口调试与接口文档", "开发", "Workflow", "", "external_link", "https://example.com/tools/apifox", 40, False, 0),
        ("toolkit-01", "section-toolkit", "template", "商业计划书套件", "路演大纲、财务假设和页面结构", "专业工具包", "ChartColumn", "", "route", "/toolkit/business-plan", 10, True, 0),
        ("toolkit-02", "section-toolkit", "template", "短视频脚本套件", "选题、分镜、标题和口播脚本", "专业工具包", "FileVideo", "", "route", "/toolkit/video-script", 20, True, 0),
        ("toolkit-03", "section-toolkit", "template", "合同审查清单", "常见风险条款和修改建议模板", "专业工具包", "Scale", "", "route", "/toolkit/legal", 30, True, 0),
        ("toolkit-04", "section-toolkit", "template", "办公自动化组件", "表格、邮件和审批流程提示词", "专业工具包", "Workflow", "", "route", "/toolkit/office", 40, True, 0),
        ("rank-01", "section-template-ranking", "ranking", "PPT 提案模板", "近 7 日 12.8 万次使用", "专业工具包", "Presentation", "", "route", "/toolkit/ranking/ppt", 10, False, 0),
        ("rank-02", "section-template-ranking", "ranking", "报价单模板", "近 7 日 8.6 万次使用", "专业工具包", "ReceiptText", "", "route", "/toolkit/ranking/quote", 20, False, 0),
        ("rank-03", "section-template-ranking", "ranking", "短视频分镜模板", "近 7 日 7.9 万次使用", "专业工具包", "MonitorPlay", "", "route", "/toolkit/ranking/video", 30, False, 0),
    ]
    page_tools = {
        "assistant": [("办公助理", "会议纪要、邮件、PPT一键处理", "Users"), ("营销助理", "文案、脚本、投放素材生成", "Megaphone"), ("法务助理", "合同风险与条款解释", "Scale"), ("学习助理", "课程规划和知识点拆解", "GraduationCap")],
        "marketing": [
            ("爆款文案生成", "标题、卖点、脚本一键生成", "Feather"),
            ("私域引流方案", "社群、企微和转化路径规划", "Network"),
            ("短视频脚本", "选题、分镜、口播一体生成", "FileVideo"),
            ("小红书种草", "笔记文案与话题建议", "Megaphone"),
            ("公众号推文", "长文内容与排版建议", "MessageCircle"),
            ("邮件营销", "自动生成专业营销邮件", "Mail"),
            ("SEO 关键词", "搜索词聚合与结构优化", "Search"),
            ("投放素材", "广告图文和落地页文案", "WandSparkles"),
            ("数据复盘", "转化漏斗和优化建议", "ChartColumn"),
        ],
        "image": [
            ("一句话生成图片", "输入描述智能生成高质量图片", "Image"),
            ("商品图生成", "电商主图、场景图和细节图", "Gift"),
            ("人像写真", "头像、证件照和风格写真", "UserRound"),
            ("风格迁移", "参考风格快速统一视觉", "WandSparkles"),
            ("智能抠图", "主体分离、换背景和透明图", "ScanSearch"),
            ("电商海报", "促销活动和详情页素材", "Megaphone"),
            ("批量出图", "多尺寸多风格批量生成", "LayoutGrid"),
        ],
        "video": [("文案生成视频", "输入脚本生成短视频分镜", "MonitorPlay"), ("数字人讲解", "课程、产品和招商讲解", "UserRound"), ("批量剪辑", "批量混剪与智能包装", "FileVideo"), ("智能字幕", "识别、翻译和样式处理", "NotebookTabs")],
        "audio": [
            ("文本转语音", "多音色高拟真配音", "Headphones"),
            ("声音克隆", "复用品牌或个人音色", "CircleUserRound"),
            ("播客生成", "一键生成播客旁白内容", "Mic"),
            ("智能降噪", "去除环境噪音并提升清晰度", "AudioWaveform"),
            ("录音转写", "会议访谈快速成稿", "FileText"),
            ("会议纪要", "音频自动整理为结构化纪要", "Users"),
            ("AI 配乐", "短视频背景音乐生成", "Music"),
            ("音频剪辑", "裁剪、拼接、变速和淡入淡出", "Scissors"),
        ],
        "coding": [("代码生成", "按需求生成组件和脚本", "Workflow"), ("代码审查", "发现风险和重构建议", "ScanSearch"), ("单元测试生成", "补齐核心路径测试", "ShieldCheck"), ("接口文档", "从代码整理API说明", "FileText")],
        "writing": [("文章写作", "结构化长文和公众号稿", "Feather"), ("报告生成", "周报、复盘和行业报告", "FileText"), ("简历优化", "经历改写和版式建议", "UserRound"), ("论文润色", "摘要、提纲和表达优化", "NotebookTabs")],
        "ecommerce": [("商品标题优化", "关键词和卖点组合", "WandSparkles"), ("详情页文案", "结构、利益点和FAQ", "FileText"), ("客服话术", "售前售后标准回复", "MessageCircle"), ("店铺诊断", "流量、转化和复购分析", "ChartColumn")],
        "legal": [("合同审查", "识别高风险条款", "ShieldCheck"), ("法律咨询", "常见问题初步分析", "Scale"), ("文书草拟", "通知函、协议和声明", "FileText"), ("证据清单", "按案件场景整理材料", "NotebookTabs")],
        "office": [("PPT 生成", "大纲到页面自动成稿", "Presentation"), ("Excel 公式", "函数、透视和批处理", "Sheet"), ("会议纪要", "录音转结构化纪要", "Users"), ("自动化流程", "表单、审批和通知串联", "Workflow")],
    }
    marketing_overview_rows = [
        ("进行中活动", "8", "较昨日 ↑2", "Flame"),
        ("本月线索总数", "3,245", "较上月 ↑18.6%", "ReceiptText"),
        ("内容总曝光", "128.6万", "较上月 ↑24.3%", "Megaphone"),
        ("转化客户数", "236", "较上月 ↑15.2%", "Users"),
        ("ROI 投入产出比", "4.32", "较上月 ↑0.68", "ChartColumn"),
    ]
    marketing_template_rows = [
        ("新品上市推广文案", "适用于新品发布活动", "Gift"),
        ("双11促销活动文案", "适用于大促节点推广", "Sparkles"),
        ("行业解决方案文案", "适用于B2B方案包装", "ChartColumn"),
        ("品牌故事文案", "适用于品牌表达和官网内容", "FileText"),
        ("客户案例文案", "适用于案例展示与成交背书", "Presentation"),
    ]
    marketing_ranking_rows = [
        ("微信公众号", "曝光 28.6万", "转化 62", "MessageCircle"),
        ("小红书", "曝光 18.3万", "转化 48", "Image"),
        ("抖音", "曝光 15.7万", "转化 32", "MonitorPlay"),
        ("企业微信", "曝光 12.1万", "转化 14", "Users"),
        ("知乎", "曝光 6.8万", "转化 9", "Search"),
    ]
    audio_route_keys = [
        "audio_tts",
        "audio_voice_clone",
        "audio_podcast",
        "audio_denoise",
        "audio_transcription",
        "audio_meeting_notes",
        "audio_music",
        "audio_editor",
    ]
    audio_stats = [
        ("今日生成时长", "3.6 小时", "较昨日 ↑18%", "Clock3"),
        ("音频项目数", "23 个", "较昨日 ↑27%", "Headphones"),
        ("总生成时长", "128.7 小时", "较上月 ↑22%", "AudioWaveform"),
        ("已节省成本", "￥3,256", "较上月 ↑31%", "ChartColumn"),
    ]
    audio_voices = [
        ("知性女声", "温柔 · 知性 · 12.5w 使用", "女声", "CircleUserRound"),
        ("磁性男声", "成熟 · 沉稳 · 9.8w 使用", "男声", "UserRound"),
        ("活力女声", "活泼 · 明亮 · 8.7w 使用", "女声", "CircleUserRound"),
        ("温暖男声", "亲切 · 自然 · 7.2w 使用", "男声", "UserRound"),
        ("标准童声", "可爱 · 清晰 · 6.1w 使用", "童声", "Sparkles"),
        ("粤语女声", "粤语 · 亲切 · 5.3w 使用", "方言", "Mic"),
    ]
    audio_recent = [
        ("产品宣传片配音", "00:48 · 知性女声", "已完成", "Headphones"),
        ("播客第28期", "12:36 · 磁性男声 · 65%", "处理中", "Podcast"),
        ("AI工具使用教程", "08:22 · 活力女声 · 30%", "处理中", "FileText"),
        ("市场调研会议", "05:17 · 多人声源", "已完成", "Users"),
        ("广告配音 - 版本2", "00:30 · 温暖男声", "排队中", "Mic"),
    ]
    audio_resources = [
        ("背景音乐", "2,362 首", "资源", "Music"),
        ("音效库", "8,745 个", "资源", "Volume2"),
        ("模板库", "356 个", "资源", "FileText"),
        ("配音模板", "128 个", "资源", "Headphones"),
    ]
    audio_guides = [
        ("新手入门教程", "从文本配音到导出音频", "指南", "GraduationCap"),
        ("热门音色推荐", "按场景选择适合音色", "指南", "Star"),
        ("音频制作技巧", "降噪、节奏和后期建议", "指南", "NotebookTabs"),
    ]
    for page_key, tool_rows in page_tools.items():
        for index, (title, subtitle, icon) in enumerate(tool_rows, start=1):
            items.append((f"{page_key}-tool-{index}", f"section-{page_key}-tools", "tool", title, subtitle, "工具", icon, "", "workspace", f"{page_key}-tool-{index}", index * 10, index > 2, index * 5))
        if page_key == "marketing":
            for index, (title, value, trend, icon) in enumerate(marketing_overview_rows, start=1):
                items.append((f"{page_key}-overview-{index}", f"section-{page_key}-overview", "stat", title, value, trend, icon, "", "route", f"/{page_key}", index * 10, False, 0))
            for index, (title, subtitle, icon) in enumerate(marketing_template_rows, start=1):
                items.append((f"{page_key}-tpl-{index}", f"section-{page_key}-templates", "template", title, subtitle, "营销模板", icon, "", "workspace", f"{page_key}-template-{index}", index * 10, index > 1, 10))
            for index, (title, exposure, conversion, icon) in enumerate(marketing_ranking_rows, start=1):
                items.append((f"{page_key}-rank-{index}", f"section-{page_key}-ranking", "ranking", title, exposure, conversion, icon, "", "workspace", f"{page_key}-rank-{index}", index * 10, False, 0))
            continue
        for index in range(1, 4):
            items.append((f"{page_key}-overview-{index}", f"section-{page_key}-overview", "stat", ["本周热度", "会员专享", "交付案例"][index - 1], ["使用量持续增长", "高阶模板开放", "沉淀可复用方案"][index - 1], "概览", ["Flame", "Gift", "BriefcaseBusiness"][index - 1], "", "route", f"/{page_key}", index * 10, index == 2, 0))
        for index in range(1, 4):
            items.append((f"{page_key}-tpl-{index}", f"section-{page_key}-templates", "template", f"{tool_rows[index - 1][0]}模板", f"适合快速启动的{tool_rows[index - 1][0]}工作流", "模板", tool_rows[index - 1][2], "", "workspace", f"{page_key}-template-{index}", index * 10, index > 1, 10))
        for index in range(1, 4):
            items.append((f"{page_key}-rank-{index}", f"section-{page_key}-ranking", "ranking", tool_rows[index - 1][0], f"近 7 日 {index * 2 + 8}.0 万次使用", "热门", tool_rows[index - 1][2], "", "workspace", f"{page_key}-rank-{index}", index * 10, False, 0))
    return items


def _add_assistants(session: Session, tenant_id: str) -> None:
    assistants = [
        ("ppt", "PPT 生成助理", "一键生成专业级 PPT，自动排版美化", "办公助理", "Presentation", 234500, 10, True, 20),
        ("copywriter", "文案创作助理", "快速生成各类文案、标题、脚本和营销内容", "营销助理", "Feather", 197000, 20, False, 10),
        ("analysis", "数据分析助理", "上传数据自动分析，生成图表与洞察报告", "办公助理", "ChartColumn", 158000, 30, True, 30),
        ("contract", "合同审查助理", "智能审查合同条款，识别风险点", "法务助理", "FileShield", 132000, 40, True, 25),
        ("meeting", "会议纪要助理", "自动整理会议录音/文字，生成结构化纪要", "办公助理", "Users", 128000, 50, False, 10),
        ("mail", "邮件撰写助理", "根据需求生成专业邮件、话气灵活可调", "办公助理", "Mail", 96000, 60, False, 8),
        ("xiaohongshu", "小红书文案助理", "生成爆款笔记文案、标题与话题建议", "营销助理", "Megaphone", 107000, 70, True, 12),
        ("excel", "Excel 公式助理", "生成公式、函数解释与表格处理方案", "开发助理", "Sheet", 146000, 80, False, 8),
        ("resume", "简历优化助理", "优化简历内容与排版，提升求职竞争力", "生活助理", "UserRound", 93000, 90, True, 10),
        ("image", "图片设计助理", "根据描述生成海报、封面与设计图", "设计助理", "Image", 72000, 100, True, 20),
        ("study", "学习规划助理", "拆解学习目标，生成每日训练计划", "学习助理", "GraduationCap", 84000, 110, False, 8),
        ("customer", "客服应答助理", "生成售前售后标准回复和异议处理话术", "客服助理", "MessageCircle", 118000, 120, True, 12),
    ]
    for key, name, description, category, icon, usage, order, required_membership, point_cost in assistants:
        id_ = f"assistant-{key}"
        if session.get(AiAssistant, id_) is None:
            session.add(
                AiAssistant(
                    id=id_,
                    tenant_id=tenant_id,
                    assistant_key=key,
                    name=name,
                    description=description,
                    category=category,
                    icon=icon,
                    usage_count=usage,
                    sort_order=order,
                    required_membership=required_membership,
                    point_cost=point_cost,
                    enabled=True,
                    action_type="workspace",
                    action_value=key,
                )
            )


def _add_templates(session: Session, tenant_id: str) -> None:
    templates = [
        ("general-writing", "通用写作模板", "写作", "请围绕主题生成一份结构清晰、语气专业的内容。"),
        ("marketing", "营销文案模板", "营销", "请生成 5 条适合社媒投放的卖点文案。"),
        ("ppt-outline", "PPT 大纲模板", "办公", "请为这个主题设计一份 10 页 PPT 大纲。"),
        ("xiaohongshu-note", "小红书笔记模板", "社媒", "请生成一篇小红书爆款笔记，包含标题和标签。"),
        ("legal-consult", "法律咨询模板", "法务", "请从合同风险、证据和谈判建议三个角度分析。"),
    ]
    for order, (key, title, category, content) in enumerate(templates, start=1):
        id_ = f"template-{key}"
        if session.get(PromptTemplate, id_) is None:
            session.add(
                PromptTemplate(
                    id=id_,
                    tenant_id=tenant_id,
                    template_key=key,
                    title=title,
                    category=category,
                    content=content,
                    sort_order=order * 10,
                    enabled=True,
                    required_membership=order > 2,
                )
            )


def _add_memberships(session: Session, tenant_id: str) -> None:
    if session.get(MembershipPlan, "plan-vip-monthly") is None:
        session.add(
            MembershipPlan(
                id="plan-vip-monthly",
                tenant_id=tenant_id,
                plan_key="vip_monthly",
                name="VIP 月卡",
                price_cents=1990,
                duration_days=31,
                entitlements=["course.premium", "assistant.vip", "template.vip", "community.vip"],
                enabled=True,
                sort_order=10,
            )
        )
    if session.get(UserMembership, "demo-membership") is None:
        session.add(
            UserMembership(
                id="demo-membership",
                tenant_id=tenant_id,
                user_id="demo-user",
                plan_id="plan-vip-monthly",
                status="ACTIVE",
                started_at=utcnow() - timedelta(days=1),
                expires_at=utcnow() + timedelta(days=30),
            )
        )


def _add_audio_routes(session: Session, tenant_id: str) -> None:
    if session.get(ChannelRoute, "route-video_text_to_video") is None:
        session.add(
            ChannelRoute(
                id="route-video_text_to_video",
                tenant_id=tenant_id,
                route_key="video_text_to_video",
                display_name="文案生成视频",
                backend_model="demo-video-renderer",
                channel_type="VIDEO",
                unit_cost=200,
                priority=10,
                enabled=True,
            )
        )
    if session.get(ChannelRoute, "route-image_text_to_image") is None:
        session.add(
            ChannelRoute(
                id="route-image_text_to_image",
                tenant_id=tenant_id,
                route_key="image_text_to_image",
                display_name="一句话生成图片",
                backend_model="demo-image-renderer",
                channel_type="IMAGE",
                unit_cost=80,
                priority=10,
                enabled=True,
            )
        )
    routes = [
        ("audio_tts", "文本转语音", "generic-tts", 120),
        ("audio_voice_clone", "声音克隆", "generic-voice-clone", 180),
        ("audio_podcast", "播客生成", "generic-podcast", 160),
        ("audio_denoise", "智能降噪", "generic-denoise", 80),
        ("audio_transcription", "录音转写", "generic-transcription", 90),
        ("audio_meeting_notes", "会议纪要", "generic-meeting-notes", 110),
        ("audio_music", "AI 配乐", "generic-music", 140),
        ("audio_editor", "音频剪辑", "generic-editor", 70),
    ]
    for order, (route_key, display_name, backend_model, unit_cost) in enumerate(routes, start=1):
        id_ = f"route-{route_key}"
        if session.get(ChannelRoute, id_) is None:
            session.add(
                ChannelRoute(
                    id=id_,
                    tenant_id=tenant_id,
                    route_key=route_key,
                    display_name=display_name,
                    backend_model=backend_model,
                    channel_type="AUDIO",
                    unit_cost=unit_cost,
                    priority=order * 10,
                    enabled=True,
                )
            )

    if session.get(ApiChannel, "channel-demo-audio") is None:
        session.add(
            ApiChannel(
                id="channel-demo-audio",
                tenant_id=tenant_id,
                channel_key="demo-audio-http",
                display_name="通用音频 HTTP 渠道",
                base_url="https://audio-provider.example.com/generate",
                api_key="replace-with-provider-key",
                channel_type="AUDIO",
                priority=100,
                enabled=False,
                health_status="DEGRADED",
                metadata_json={"note": "填入真实供应商地址和密钥后启用"},
            )
        )


def _add_model_configurations(session: Session, tenant_id: str) -> None:
    _add_provider_channels(session, tenant_id)
    model_specs = [
        ("model-general-text-default", "general_text_default", "通用文本模型", "TEXT", "channel-demo-general", "demo-general-text", 10, False),
        ("model-assistant-text-default", "assistant_text_default", "助理文本模型", "TEXT", "channel-demo-general", "demo-assistant-text", 15, False),
        ("model-marketing-text-default", "marketing_text_default", "营销文本模型", "TEXT", "channel-demo-general", "demo-marketing-text", 20, False),
        ("model-ecommerce-text-default", "ecommerce_text_default", "电商文本模型", "TEXT", "channel-demo-general", "demo-ecommerce-text", 30, False),
        ("model-legal-text-default", "legal_text_default", "法务文本模型", "TEXT", "channel-demo-general", "demo-legal-text", 25, False),
        ("model-office-text-default", "office_text_default", "办公文本模型", "TEXT", "channel-demo-general", "demo-office-text", 18, False),
        ("model-coding-text-default", "coding_text_default", "编程文本模型", "TEXT", "channel-demo-general", "demo-coding-text", 28, False),
        ("model-writing-text-default", "writing_text_default", "写作文本模型", "TEXT", "channel-demo-general", "demo-writing-text", 20, False),
        ("model-image-text-to-image", "image_text_to_image", "通用图片模型", "IMAGE", "channel-demo-image", "demo-image-renderer", 80, True),
        ("model-video-text-to-video", "video_text_to_video", "通用视频模型", "VIDEO", "channel-demo-video", "demo-video-renderer", 200, True),
        ("model-audio-tts", "audio_tts", "文本转语音", "AUDIO", "channel-demo-audio", "generic-tts", 120, True),
        ("model-audio-voice-clone", "audio_voice_clone", "声音克隆", "AUDIO", "channel-demo-audio", "generic-voice-clone", 180, True),
        ("model-audio-podcast", "audio_podcast", "播客生成", "AUDIO", "channel-demo-audio", "generic-podcast", 160, True),
        ("model-audio-denoise", "audio_denoise", "智能降噪", "AUDIO", "channel-demo-audio", "generic-denoise", 80, True),
        ("model-audio-transcription", "audio_transcription", "录音转写", "AUDIO", "channel-demo-audio", "generic-transcription", 90, True),
        ("model-audio-meeting-notes", "audio_meeting_notes", "会议纪要", "AUDIO", "channel-demo-audio", "generic-meeting-notes", 110, True),
        ("model-audio-music", "audio_music", "AI 配乐", "AUDIO", "channel-demo-audio", "generic-music", 140, True),
        ("model-audio-editor", "audio_editor", "音频剪辑", "AUDIO", "channel-demo-audio", "generic-editor", 70, True),
    ]
    for id_, model_key, display_name, capability, channel_id, provider_model, default_cost, enabled in model_specs:
        if session.get(ModelConfig, id_) is None:
            session.add(
                ModelConfig(
                    id=id_,
                    tenant_id=tenant_id,
                    model_key=model_key,
                    display_name=display_name,
                    capability=capability,
                    channel_id=channel_id,
                    provider_model=provider_model,
                    default_point_cost=default_cost,
                    enabled=enabled,
                )
            )
    session.flush()
    _add_text_routes(session, tenant_id)
    _add_tool_model_bindings(session, tenant_id)


def _add_text_routes(session: Session, tenant_id: str) -> None:
    for model in session.scalars(
        select(ModelConfig).where(
            ModelConfig.tenant_id == tenant_id,
            ModelConfig.capability == "TEXT",
        )
    ):
        route_id = f"route-{model.model_key}"
        if session.get(ChannelRoute, route_id) is None:
            session.add(
                ChannelRoute(
                    id=route_id,
                    tenant_id=tenant_id,
                    route_key=model.model_key,
                    display_name=model.display_name,
                    backend_model=model.provider_model,
                    channel_type="TEXT",
                    unit_cost=model.default_point_cost,
                    priority=5,
                    enabled=model.enabled,
                )
            )


def _add_chat_runtime(session: Session, tenant_id: str) -> None:
    chat_id = "demo-workbench-chat"
    if session.get(ChatSession, chat_id) is None:
        session.add(
            ChatSession(
                id=chat_id,
                tenant_id=tenant_id,
                user_id="demo-user",
                title="项目周报整理",
                preset_role="assistant",
                model_key="general_text_default",
                status="ACTIVE",
            )
        )

    messages = [
        ("chat-demo-msg-1", "user", "整理本周项目进展并输出要点。", 1),
        ("chat-demo-msg-2", "assistant", "已整理为项目周报，可继续补充数据或导出 Markdown。", 2),
    ]
    for id_, role, content, sequence in messages:
        if session.get(ChatMessage, id_) is None:
            session.add(
                ChatMessage(
                    id=id_,
                    tenant_id=tenant_id,
                    session_id=chat_id,
                    role=role,
                    content=content,
                    sequence=sequence,
                )
            )


def _add_provider_channels(session: Session, tenant_id: str) -> None:
    channels = [
        ("channel-demo-general", "demo-general-text", "通用文本渠道", "https://text-provider.example.com/generate", "replace-with-provider-key", "TEXT", 90, False),
        ("channel-demo-image", "demo-image-http", "通用图片渠道", "https://image-provider.example.com/generate", "replace-with-provider-key", "IMAGE", 10, True),
        ("channel-demo-video", "demo-video-http", "通用视频渠道", "https://video-provider.example.com/generate", "replace-with-provider-key", "VIDEO", 20, True),
        ("channel-demo-audio", "demo-audio-http", "通用音频 HTTP 渠道", "https://audio-provider.example.com/generate", "replace-with-provider-key", "AUDIO", 100, False),
    ]
    for id_, channel_key, display_name, base_url, api_key, channel_type, priority, enabled in channels:
        existing = next(
            (
                obj
                for obj in session.new
                if isinstance(obj, ApiChannel)
                and obj.tenant_id == tenant_id
                and obj.channel_key == channel_key
            ),
            None,
        )
        if existing is None:
            existing = session.scalar(
                select(ApiChannel).where(
                    ApiChannel.tenant_id == tenant_id,
                    ApiChannel.channel_key == channel_key,
                )
            )
        if existing is None:
            session.add(
                ApiChannel(
                    id=id_,
                    tenant_id=tenant_id,
                    channel_key=channel_key,
                    display_name=display_name,
                    base_url=base_url,
                    api_key=api_key,
                    channel_type=channel_type,
                    priority=priority,
                    enabled=enabled,
                    health_status="HEALTHY" if enabled else "DEGRADED",
                    metadata_json={"note": "填入真实供应商地址和密钥后启用"} if not enabled else None,
                )
            )


def _add_tool_model_bindings(session: Session, tenant_id: str) -> None:
    model_by_key = {
        model.model_key: model
        for model in session.scalars(
            select(ModelConfig).where(ModelConfig.tenant_id == tenant_id)
        )
    }
    if not model_by_key:
        return

    content_sections = {
        section.id: section.area
        for section in session.scalars(select(ContentSection).where(ContentSection.tenant_id == tenant_id))
    }

    def bind(target_type: str, target_key: str, model_key: str, point_cost: int | None = None) -> None:
        model = model_by_key.get(model_key)
        if model is None:
            return
        binding_id = _binding_id(tenant_id, target_type, target_key)
        if session.get(ToolModelBinding, binding_id) is not None:
            return
        session.add(
            ToolModelBinding(
                id=binding_id,
                tenant_id=tenant_id,
                target_type=target_type,
                target_key=target_key,
                model_config_id=model.id,
                point_cost_override=point_cost,
                enabled=True,
            )
        )

    for item in session.scalars(select(ContentItem).where(ContentItem.tenant_id == tenant_id)):
        area = content_sections.get(item.section_id, "home")
        model_key = _model_key_for_area(area, item.action_value)
        bind("content_item", item.id, model_key, item.point_cost)

    for assistant in session.scalars(select(AiAssistant).where(AiAssistant.tenant_id == tenant_id)):
        model_key = _model_key_for_assistant(assistant.category)
        bind("assistant", assistant.id, model_key, assistant.point_cost)

    for template in session.scalars(select(PromptTemplate).where(PromptTemplate.tenant_id == tenant_id)):
        model_key = _model_key_for_template(template.category)
        bind("prompt_template", template.id, model_key, 0)

    image_bindings = [
        ("builtin", "image_text_to_image", "image_text_to_image", 80),
        ("builtin", "image_action_product", "image_text_to_image", 80),
        ("builtin", "image_action_portrait", "image_text_to_image", 80),
        ("builtin", "image_action_style", "image_text_to_image", 80),
        ("builtin", "image_action_cutout", "image_text_to_image", 80),
        ("builtin", "image_action_poster", "image_text_to_image", 80),
        ("builtin", "image_action_batch", "image_text_to_image", 80),
        ("builtin", "image_template_product", "image_text_to_image", 80),
        ("builtin", "image_template_social", "image_text_to_image", 80),
        ("builtin", "image_template_ecommerce", "image_text_to_image", 80),
        ("builtin", "image_template_portrait", "image_text_to_image", 80),
        ("builtin", "image_template_festival", "image_text_to_image", 80),
        ("builtin", "image_template_interior", "image_text_to_image", 80),
    ]
    for target_type, target_key, model_key, cost in image_bindings:
        bind(target_type, target_key, model_key, cost)

    video_bindings = [
        ("builtin", "video_text_to_video", "video_text_to_video", 200),
        ("builtin", "video_action_avatar", "video_text_to_video", 200),
        ("builtin", "video_action_product", "video_text_to_video", 200),
        ("builtin", "video_action_batch", "video_text_to_video", 200),
        ("builtin", "video_action_subtitle", "video_text_to_video", 200),
        ("builtin", "video_action_voice", "video_text_to_video", 200),
        ("builtin", "video_template_product", "video_text_to_video", 200),
        ("builtin", "video_template_promo", "video_text_to_video", 200),
        ("builtin", "video_template_knowledge", "video_text_to_video", 200),
        ("builtin", "video_template_brand", "video_text_to_video", 200),
        ("builtin", "video_template_festival", "video_text_to_video", 200),
        ("builtin", "video_template_vlog", "video_text_to_video", 200),
    ]
    for target_type, target_key, model_key, cost in video_bindings:
        bind(target_type, target_key, model_key, cost)

    coding_bindings = [
        ("builtin", "coding_action_generation", "coding_text_default", 28),
        ("builtin", "coding_action_bugfix", "coding_text_default", 28),
        ("builtin", "coding_action_review", "coding_text_default", 28),
        ("builtin", "coding_action_tests", "coding_text_default", 28),
        ("builtin", "coding_action_docs", "coding_text_default", 28),
        ("builtin", "coding_action_script", "coding_text_default", 28),
        ("builtin", "coding_template_backend", "coding_text_default", 28),
        ("builtin", "coding_template_frontend", "coding_text_default", 28),
        ("builtin", "coding_template_sql", "coding_text_default", 28),
        ("builtin", "coding_template_python", "coding_text_default", 28),
        ("builtin", "coding_template_test", "coding_text_default", 28),
        ("builtin", "coding_template_devops", "coding_text_default", 28),
    ]
    for target_type, target_key, model_key, cost in coding_bindings:
        bind(target_type, target_key, model_key, cost)

    writing_bindings = [
        ("builtin", "writing_action_article", "writing_text_default", 20),
        ("builtin", "writing_action_official_account", "writing_text_default", 20),
        ("builtin", "writing_action_xiaohongshu", "writing_text_default", 20),
        ("builtin", "writing_action_report", "writing_text_default", 20),
        ("builtin", "writing_action_thesis", "writing_text_default", 20),
        ("builtin", "writing_action_resume", "writing_text_default", 20),
        ("builtin", "writing_template_hot_titles", "writing_text_default", 20),
        ("builtin", "writing_template_outline", "writing_text_default", 20),
        ("builtin", "writing_template_resume", "writing_text_default", 20),
        ("builtin", "writing_template_brand_story", "writing_text_default", 20),
        ("builtin", "writing_template_mail", "writing_text_default", 20),
        ("builtin", "writing_template_speech", "writing_text_default", 20),
    ]
    for target_type, target_key, model_key, cost in writing_bindings:
        bind(target_type, target_key, model_key, cost)


def _default_item_metadata(*, title: str, subtitle: str, category: str, action_value: str) -> dict:
    action_key = _seed_action_key(action_value=action_value, category=category)
    download = None
    if action_key in {"download", "claim"}:
        safe_key = action_value.strip("/").replace("/", "-") or "resource"
        download = {
            "fileName": f"{safe_key}.md",
            "url": f"/storage/resources/{safe_key}.md",
            "storageKey": f"resources/{safe_key}.md",
        }
    return {
        "detail": {
            "summary": subtitle or f"{title} 的完整说明与站内操作入口。",
            "highlights": [
                f"适合「{category or '通用'}」场景",
                "支持站内状态记录",
                "可由管理端继续调整详情内容",
            ],
            "steps": [
                "查看适用场景和交付物",
                "确认会员权限和使用成本",
                "点击主按钮完成站内动作",
            ],
            "deliverables": [
                "站内动作记录",
                "后续可继续跟进的入口",
            ],
            "faqs": [
                {"question": "这是真实支付吗？", "answer": "当前版本只做站内状态闭环，不接入真实支付。"},
                {"question": "内容可以配置吗？", "answer": "可在管理端卡片详情字段中调整。"},
            ],
            "primaryAction": {"key": action_key, "label": _seed_action_label(action_key)},
            "secondaryActions": [{"key": "favorite", "label": "收藏"}],
            "download": download,
        }
    }


def _merge_item_metadata(base: dict, override: dict) -> dict:
    return {
        **base,
        **override,
        "detail": {
            **base.get("detail", {}),
            **override.get("detail", {}),
        },
    }


def _third_party_tool_metadata(*, item_id: str, title: str, subtitle: str, action_value: str) -> dict:
    brand_marks = {
        "third-tool-jianying": "JY",
        "third-tool-feishu": "FS",
        "third-tool-meeting": "TX",
        "third-tool-apifox": "AP",
    }
    download_urls = {
        "third-tool-jianying": "https://example.com/downloads/jianying",
        "third-tool-feishu": "https://example.com/downloads/feishu",
        "third-tool-meeting": "https://example.com/downloads/meeting",
        "third-tool-apifox": "https://example.com/downloads/apifox",
    }
    if item_id not in brand_marks:
        return {}
    return {
        "brandMark": brand_marks[item_id],
        "summary": subtitle,
        "detail": {
            "summary": subtitle or f"{title} 的官网和客户端下载入口。",
            "highlights": [
                "支持官网访问和客户端下载",
                "可在管理端维护跳转链接",
                "适合沉淀常用第三方工具",
            ],
            "steps": [
                "查看工具用途",
                "访问官网确认适用版本",
                "点击下载客户端",
            ],
            "deliverables": [
                "第三方工具官网入口",
                "客户端下载链接",
            ],
            "primaryAction": {"key": "download", "label": "下载客户端"},
            "download": {
                "fileName": f"{item_id}.url",
                "url": download_urls[item_id],
                "sourceUrl": action_value,
            },
        },
    }


def _seed_action_key(*, action_value: str, category: str) -> str:
    if "resources" in action_value or "download" in action_value or "资料" in category or "资源" in category:
        return "download"
    if "community" in action_value or "社群" in category:
        return "join"
    if "orders" in action_value or "projects" in action_value or "接单" in category or "项目" in category:
        return "apply"
    if "template" in action_value or "toolkit" in action_value or "模板" in category:
        return "claim"
    return "enroll"


def _seed_action_label(action_key: str) -> str:
    return {
        "apply": "立即报名",
        "claim": "领取模板",
        "download": "下载资料",
        "enroll": "开始学习",
        "join": "加入社群",
    }.get(action_key, "立即使用")


def _binding_id(tenant_id: str, target_type: str, target_key: str) -> str:
    digest = hashlib.sha1(f"{tenant_id}:{target_type}:{target_key}".encode("utf-8")).hexdigest()[:24]
    return f"bind-{digest}"


def _model_key_for_area(area: str, action_value: str) -> str:
    if area == "marketing":
        return "marketing_text_default"
    if area == "ecommerce":
        return "ecommerce_text_default"
    if area == "legal":
        return "legal_text_default"
    if area == "office":
        return "office_text_default"
    if area == "image":
        return "image_text_to_image"
    if area == "video":
        return "video_text_to_video"
    if area == "audio":
        return action_value if action_value.startswith("audio_") else "general_text_default"
    if area == "coding":
        return "coding_text_default"
    if area == "writing":
        return "writing_text_default"
    return "general_text_default"

def _model_key_for_assistant(category: str) -> str:
    if category == "营销助理":
        return "marketing_text_default"
    if category == "法务助理":
        return "legal_text_default"
    if category == "办公助理":
        return "office_text_default"
    if category == "开发助理":
        return "coding_text_default"
    if category == "设计助理":
        return "image_text_to_image"
    if category == "学习助理":
        return "writing_text_default"
    if category == "客服助理":
        return "office_text_default"
    if category == "生活助理":
        return "general_text_default"
    return "assistant_text_default"


def _model_key_for_template(category: str) -> str:
    if category == "营销":
        return "marketing_text_default"
    if category == "办公":
        return "office_text_default"
    if category == "社媒":
        return "marketing_text_default"
    if category == "法务":
        return "legal_text_default"
    if category == "写作":
        return "writing_text_default"
    return "general_text_default"

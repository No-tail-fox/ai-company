from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models import (
    AiAssistant,
    ContentItem,
    ContentPage,
    ContentSection,
    MembershipPlan,
    PromptTemplate,
    Tenant,
    User,
    UserMembership,
    Wallet,
    utcnow,
)
from app.services.auth import hash_password


def ensure_demo_data(session: Session, *, tenant_id: str = "demo") -> None:
    tenant = session.get(Tenant, tenant_id)
    if tenant is None:
        session.add(Tenant(id=tenant_id, slug="demo", name="新商机 AI 社区"))

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
    _add_sections(session, tenant_id)
    _add_items(session, tenant_id)
    _add_assistants(session, tenant_id)
    _add_templates(session, tenant_id)
    _add_memberships(session, tenant_id)
    session.commit()


PAGES = [
    ("page-home", "home", "首页", "常用AI学习中心", "学习、接单、社群和活动的统一入口", "Home", 10),
    ("page-assistant", "assistant", "AI 助理", "智能助理广场", "办公、营销、学习、法务等场景助理集合", "Bot", 20),
    ("page-marketing", "marketing", "AI 营销", "营销增长中心", "从内容生成到投放复盘的一站式工具台", "Megaphone", 30),
    ("page-video", "video", "AI 视频", "AI视频创作中心", "脚本、数字人、剪辑、字幕和渲染队列", "FileVideo", 40),
    ("page-audio", "audio", "AI 音频", "AI音频工作台", "配音、转写、降噪、播客和音色库", "Headphones", 50),
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


def _add_sections(session: Session, tenant_id: str) -> None:
    sections = _section_definitions()
    for id_, area, key, title, subtitle, layout, order in sections:
        if session.get(ContentSection, id_) is None:
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


def _add_items(session: Session, tenant_id: str) -> None:
    items = _item_definitions()
    for id_, section_id, item_type, title, subtitle, category, icon, image_url, action_type, action_value, sort_order, required_membership, point_cost in items:
        if session.get(ContentItem, id_) is None:
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
                    enabled=True,
                )
            )


def _section_definitions() -> list[tuple[str, str, str, str, str, str, int]]:
    sections = [
        ("section-learning", "home", "learning_center", "常用AI学习中心", "课程、实战和变现路径", "learning-grid", 10),
        ("section-orders", "home", "order_center", "OPC 接单中心", "适合新手和团队交付的接单入口", "order-grid", 20),
        ("section-communities", "home", "communities", "兴趣社群", "按成长阶段和赛道加入社群", "banner-row", 30),
        ("section-banners", "home", "banners", "热门活动", "模板、活动和会员福利", "promo", 40),
        ("section-quick-start", "home", "quick_start", "新人快速上手", "账号、工具和首个提示词任务", "task-list", 50),
        ("section-growth-path", "home", "growth_path", "进阶成长路径", "训练营、作业拆解和案例复盘", "learning-grid", 60),
        ("section-earning-templates", "home", "earning_templates", "接单交付模板", "报价、验收和复购跟进", "template-list", 70),
        ("section-resource-hub", "home", "resource_hub", "资源对接库", "工具权益、行业资料和合作需求", "banner-row", 80),
        ("section-project-cocreation", "home", "project_cocreation", "项目共创广场", "组队招募、协作交付和共创案例", "order-grid", 90),
        ("section-workspace-tools", "home", "workspace_tools", "常用工作台", "高频 AI 工具一键启动", "tool-grid", 100),
        ("section-task-board", "home", "task_board", "任务入口", "最近使用、待交付项目和素材库", "stat-strip", 110),
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
        ("workspace-01", "section-workspace-tools", "tool", "PPT 生成工作台", "从大纲到页面自动生成", "应用工作台", "Presentation", "", "route", "/workspace/ppt", 10, False, 0),
        ("workspace-02", "section-workspace-tools", "tool", "视频脚本工作台", "选题、脚本、分镜一站式处理", "应用工作台", "MonitorPlay", "", "route", "/workspace/video-script", 20, False, 0),
        ("workspace-03", "section-workspace-tools", "tool", "电商运营工作台", "标题、详情和客服话术生成", "应用工作台", "WandSparkles", "", "route", "/workspace/ecommerce", 30, True, 10),
        ("workspace-04", "section-workspace-tools", "tool", "合同审查工作台", "检查风险条款和修改建议", "应用工作台", "Scale", "", "route", "/workspace/legal", 40, True, 10),
        ("task-01", "section-task-board", "task", "最近使用", "继续上次的工具和内容生成任务", "应用工作台", "Clock3", "", "route", "/workspace/recent", 10, False, 0),
        ("task-02", "section-task-board", "task", "待交付项目", "查看接单任务、素材和交付节点", "应用工作台", "BriefcaseBusiness", "", "route", "/workspace/deliveries", 20, True, 0),
        ("task-03", "section-task-board", "task", "素材库", "管理上传图片、模板和提示词资产", "应用工作台", "CloudUpload", "", "route", "/workspace/assets", 30, True, 0),
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
        "marketing": [("爆款文案生成", "标题、卖点、脚本一键生成", "Feather"), ("私域引流方案", "社群、企微和转化路径规划", "Network"), ("投放素材生成", "广告图文和落地页素材", "Megaphone"), ("数据复盘", "转化漏斗和优化建议", "ChartColumn")],
        "video": [("文案生成视频", "输入脚本生成短视频分镜", "MonitorPlay"), ("数字人讲解", "课程、产品和招商讲解", "UserRound"), ("批量剪辑", "批量混剪与智能包装", "FileVideo"), ("智能字幕", "识别、翻译和样式处理", "NotebookTabs")],
        "audio": [("文本转语音", "多音色自然配音", "Headphones"), ("声音克隆", "品牌音色复用", "CircleUserRound"), ("录音转写", "会议访谈快速成稿", "FileText"), ("AI 配乐", "短视频背景音乐生成", "Sparkles")],
        "coding": [("代码生成", "按需求生成组件和脚本", "Workflow"), ("代码审查", "发现风险和重构建议", "ScanSearch"), ("单元测试生成", "补齐核心路径测试", "ShieldCheck"), ("接口文档", "从代码整理API说明", "FileText")],
        "writing": [("文章写作", "结构化长文和公众号稿", "Feather"), ("报告生成", "周报、复盘和行业报告", "FileText"), ("简历优化", "经历改写和版式建议", "UserRound"), ("论文润色", "摘要、提纲和表达优化", "NotebookTabs")],
        "ecommerce": [("商品标题优化", "关键词和卖点组合", "WandSparkles"), ("详情页文案", "结构、利益点和FAQ", "FileText"), ("客服话术", "售前售后标准回复", "MessageCircle"), ("店铺诊断", "流量、转化和复购分析", "ChartColumn")],
        "legal": [("合同审查", "识别高风险条款", "ShieldCheck"), ("法律咨询", "常见问题初步分析", "Scale"), ("文书草拟", "通知函、协议和声明", "FileText"), ("证据清单", "按案件场景整理材料", "NotebookTabs")],
        "office": [("PPT 生成", "大纲到页面自动成稿", "Presentation"), ("Excel 公式", "函数、透视和批处理", "Sheet"), ("会议纪要", "录音转结构化纪要", "Users"), ("自动化流程", "表单、审批和通知串联", "Workflow")],
    }
    for page_key, tool_rows in page_tools.items():
        for index, (title, subtitle, icon) in enumerate(tool_rows, start=1):
            items.append((f"{page_key}-tool-{index}", f"section-{page_key}-tools", "tool", title, subtitle, "工具", icon, "", "workspace", f"{page_key}-tool-{index}", index * 10, index > 2, index * 5))
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

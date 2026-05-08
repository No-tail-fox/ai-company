export interface PageConfigSummary {
  id?: string;
  tenantId?: string;
  pageKey: string;
  label: string;
  title: string;
  subtitle: string;
  icon: string;
  sortOrder: number;
  enabled: boolean;
}

export interface NavItem {
  key: string;
  label: string;
  icon: string;
}

export interface PortalItem {
  id: string;
  tenantId?: string;
  sectionId?: string;
  itemType: string;
  title: string;
  subtitle: string;
  category: string;
  icon: string;
  imageUrl?: string;
  badge?: string;
  tags?: string[];
  sortOrder: number;
  enabled: boolean;
  actionType?: string;
  actionValue: string;
  requiredMembership: boolean;
  pointCost: number;
}

export interface PortalSection {
  id: string;
  tenantId?: string;
  pageKey: string;
  sectionKey: string;
  title: string;
  subtitle: string;
  layout: string;
  sortOrder: number;
  enabled: boolean;
  items: PortalItem[];
}

export interface PortalConfig {
  tenantId: string;
  pages: PageConfigSummary[];
  channels: Array<{ key: string; label: string }>;
  leftNav: NavItem[];
  homeSections: PortalSection[];
}

export interface PortalPageConfig {
  tenantId: string;
  page: PageConfigSummary;
  sections: PortalSection[];
}

export interface AssistantCard {
  id: string;
  name: string;
  category: string;
  description: string;
  icon: string;
  usageCount: number;
  usageCountLabel?: string;
  pointCost: number;
  requiredMembership: boolean;
  actionValue: string;
}

export interface PromptTemplate {
  id: string;
  title: string;
  category: string;
  content: string;
  requiredMembership: boolean;
}

export interface AssistantCenter {
  categories: string[];
  featured: AssistantCard[];
  assistants: AssistantCard[];
  ranking: AssistantCard[];
  promptTemplates: PromptTemplate[];
}

const fallbackPages: PageConfigSummary[] = [
  page('home', '首页', '常用AI学习中心', '学习、接单、社群和活动的统一入口', 'Home', 10),
  page('assistant', 'AI 助理', '智能助理广场', '办公、营销、学习、法务等场景助理集合', 'Bot', 20),
  page('marketing', 'AI 营销', '营销增长中心', '从内容生成到投放复盘的一站式工具台', 'Megaphone', 30),
  page('video', 'AI 视频', 'AI视频创作中心', '脚本、数字人、剪辑、字幕和渲染队列', 'FileVideo', 40),
  page('audio', 'AI 音频', 'AI音频工作台', '配音、转写、降噪、播客和音色库', 'Headphones', 50),
  page('coding', 'AI 编程', 'AI编程工作台', '代码生成、审查、测试和自动化脚本', 'Workflow', 60),
  page('writing', 'AI 写作', 'AI写作中心', '文章、报告、简历、论文和提示词模板', 'Feather', 70),
  page('ecommerce', 'AI 电商', 'AI电商运营中心', '商品内容、客服话术、店铺分析和素材生成', 'WandSparkles', 80),
  page('legal', 'AI 法务', 'AI法务服务台', '合同审查、法律咨询、证据整理和文书草拟', 'Scale', 90),
  page('office', 'AI 办公', 'AI办公效率中心', 'PPT、表格、会议、邮件和流程自动化', 'BriefcaseBusiness', 100)
];

const DEFAULT_HOME_MENU_KEY = 'basic';

interface HomeMenuRule {
  key: string;
  title: string;
  subtitle: string;
  icon: string;
  hint: string;
  sectionKeys: string[];
  categories: string[];
}

const homeMenuRules: Record<string, HomeMenuRule> = {
  basic: {
    key: 'basic',
    title: '基础必备',
    subtitle: 'AI 入门课、常用工具和快速上手任务',
    icon: 'Flame',
    hint: '入门任务',
    sectionKeys: ['quick_start', 'learning_center'],
    categories: ['基础必备']
  },
  growth: {
    key: 'growth',
    title: '学习成长',
    subtitle: '进阶课程、打卡社群、学习路径和案例拆解',
    icon: 'Sprout',
    hint: '进阶打卡',
    sectionKeys: ['growth_path', 'learning_center', 'communities'],
    categories: ['学习成长']
  },
  orders: {
    key: 'orders',
    title: '接单变现',
    subtitle: '接单服务、报价模板、交付案例和变现训练',
    icon: 'ReceiptText',
    hint: '报价交付',
    sectionKeys: ['order_center', 'earning_templates'],
    categories: ['接单变现']
  },
  resources: {
    key: 'resources',
    title: '资源对接',
    subtitle: '社群入口、资源合作、活动横幅和资料库',
    icon: 'Handshake',
    hint: '社群资源',
    sectionKeys: ['resource_hub', 'communities', 'banners'],
    categories: ['资源对接']
  },
  projects: {
    key: 'projects',
    title: '项目共创',
    subtitle: '项目招募、团队协作、定制服务和共创案例',
    icon: 'PanelsTopLeft',
    hint: '协作招募',
    sectionKeys: ['project_cocreation', 'order_center'],
    categories: ['项目共创']
  },
  workspace: {
    key: 'workspace',
    title: '应用工作台',
    subtitle: '常用 AI 工具矩阵、任务入口和最近使用',
    icon: 'LayoutGrid',
    hint: '工具启动',
    sectionKeys: ['workspace_tools', 'task_board'],
    categories: ['应用工作台']
  },
  toolkit: {
    key: 'toolkit',
    title: '专业工具包',
    subtitle: '模板列表、行业工具、效率组件和排行榜',
    icon: 'BriefcaseBusiness',
    hint: '模板排行',
    sectionKeys: ['toolkit', 'template_ranking', 'banners'],
    categories: ['专业工具包']
  }
};

export function formatUsageCount(count: number): string {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万次使用`;
  }
  return `${count}次使用`;
}

export function shouldShowHomeSidebar(pageKey: string): boolean {
  return pageKey === 'home';
}

export function getHomeMenuHint(menuKey: string): string {
  return (homeMenuRules[menuKey] ?? homeMenuRules[DEFAULT_HOME_MENU_KEY]).hint;
}

export function createHomeMenuPageConfig(pageConfig: PortalPageConfig, menuKey: string): PortalPageConfig {
  if (!shouldShowHomeSidebar(pageConfig.page.pageKey)) {
    return pageConfig;
  }

  const rule = homeMenuRules[menuKey] ?? homeMenuRules[DEFAULT_HOME_MENU_KEY];
  const sections = pageConfig.sections
    .map((sectionItem) => filterHomeSection(sectionItem, rule))
    .filter((sectionItem): sectionItem is PortalSection => Boolean(sectionItem));

  return {
    ...pageConfig,
    page: {
      ...pageConfig.page,
      title: rule.title,
      subtitle: rule.subtitle,
      icon: rule.icon
    },
    sections: sections.length > 0 ? sections : pageConfig.sections
  };
}

function filterHomeSection(sectionItem: PortalSection, rule: HomeMenuRule): PortalSection | null {
  const matchesSection = rule.sectionKeys.includes(sectionItem.sectionKey);
  const matchedItems = sectionItem.items.filter((itemItem) => rule.categories.includes(itemItem.category));

  if (!matchesSection && matchedItems.length === 0) {
    return null;
  }

  return {
    ...sectionItem,
    items: matchedItems.length > 0 ? matchedItems : sectionItem.items
  };
}

export function buildAssistantRanking(assistants: AssistantCard[]): AssistantCard[] {
  return assistants
    .slice()
    .sort((left, right) => right.usageCount - left.usageCount)
    .slice(0, 10)
    .map((assistant) => ({
      ...assistant,
      usageCountLabel: assistant.usageCountLabel ?? formatUsageCount(assistant.usageCount)
    }));
}

export function createFallbackPortalConfig(): PortalConfig {
  return {
    tenantId: 'demo',
    pages: fallbackPages,
    channels: fallbackPages.map((item) => ({ key: item.pageKey, label: item.label })),
    leftNav: [
      { key: 'basic', label: '基础必备', icon: 'Flame' },
      { key: 'growth', label: '学习成长', icon: 'Sprout' },
      { key: 'orders', label: '接单变现', icon: 'ReceiptText' },
      { key: 'resources', label: '资源对接', icon: 'Handshake' },
      { key: 'projects', label: '项目共创', icon: 'PanelsTopLeft' },
      { key: 'workspace', label: '应用工作台', icon: 'LayoutGrid' },
      { key: 'toolkit', label: '专业工具包', icon: 'BriefcaseBusiness' }
    ],
    homeSections: [
      section('section-learning', 'home', 'learning_center', '常用AI学习中心', 'learning-grid', [
        item('learn-01', 'course', '《0基础AI通识课》', '12 大核心渠道从认知到上手一站式通关', '基础必备', 'FileVideo', '/workspace/course', false, 0),
        item('learn-02', 'course', '《AI 实战必修课》', '办公/剪辑/写作全场景效率翻倍', '基础必备', 'MonitorPlay', '/workspace/course', true, 0),
        item('learn-03', 'course', '《AI 商业变现课》', '内容创作 + 电商营销全链路落地盈利', '接单变现', 'ScanSearch', '/workspace/course', true, 0),
        item('learn-04', 'course', '《AI 爆款内容创作》', '短视频脚本、标题、封面和投放流程', 'AI营销', 'Presentation', '/workspace/course', true, 20),
        item('learn-05', 'course', '《AI 进阶实战营》', '从工具使用到项目交付的系统训练', '学习成长', 'NotebookTabs', '/workspace/course/advanced', true, 30),
        item('learn-06', 'course', '《AI 项目交付训练》', '拆解真实客户需求并完成可复用方案', '项目共创', 'BriefcaseBusiness', '/workspace/course/project', true, 30)
      ]),
      section('section-orders', 'home', 'order_center', 'OPC 接单中心', 'order-grid', [
        item('order-01', 'service', 'AI创作订单', 'PPT、文案、图片与短视频交付', '接单变现', 'Feather', '/workspace/orders', true, 20),
        item('order-02', 'service', 'AI自动化定制', '为客户定制办公自动化流程', '项目共创', 'FileText', '/workspace/automation', true, 50),
        item('order-03', 'service', 'AI电商优化', '商品标题、详情页与客服话术', 'AI电商', 'WandSparkles', '/workspace/ecommerce', true, 30),
        item('order-04', 'service', '报价单生成器', '按任务类型生成报价、周期和交付边界', '接单变现', 'ReceiptText', '/workspace/quotes', true, 10),
        item('order-05', 'service', '项目共创招募', '匹配设计、剪辑、运营和开发协作者', '项目共创', 'PanelsTopLeft', '/workspace/projects', true, 0)
      ]),
      section('section-communities', 'home', 'communities', '兴趣社群', 'banner-row', [
        item('comm-01', 'community', '入门交流群', '新人答疑、工具清单和上手路线', '社群', 'MessageCircle', '/community/starter', false, 0),
        item('comm-02', 'community', '学习打卡群', '每日任务、案例拆解和作业反馈', '学习成长', 'GraduationCap', '/community/study', true, 0),
        item('comm-03', 'community', '接单变现群', '接单案例、报价模板和交付流程', '接单变现', 'Handshake', '/community/orders', true, 0),
        item('comm-04', 'community', '资源对接群', '工具资源、客户线索和行业资料交换', '资源对接', 'Network', '/community/resources', true, 0)
      ]),
      section('section-banners', 'home', 'banners', '热门活动', 'promo', [
        item('banner-01', 'banner', '热门模板上新！', '一键轻松取用办公模板', '运营活动', 'Gift', '/templates', true, 0),
        item('banner-02', 'banner', '商业计划书模板', '融资路演、商业策划、项目计划', '专业工具包', 'ChartColumn', '/templates/business', true, 0),
        item('banner-03', 'banner', '资源内测邀请', '优先体验新的合作资源和资料包', '资源对接', 'Sparkles', '/resources/trial', false, 0)
      ]),
      section('section-quick-start', 'home', 'quick_start', '新人快速上手', 'task-list', [
        item('quick-01', 'task', '配置个人 AI 工具箱', '完成账号、常用模型和提示词收藏', '基础必备', 'LayoutGrid', '/workspace/setup', false, 0),
        item('quick-02', 'task', '完成首个提示词任务', '用模板生成一份可交付内容', '基础必备', 'Sparkles', '/workspace/first-task', false, 0),
        item('quick-03', 'task', '领取新手资料包', '下载工具清单、学习路线和案例库', '基础必备', 'Download', '/resources/starter-kit', false, 0)
      ]),
      section('section-growth-path', 'home', 'growth_path', '进阶成长路径', 'learning-grid', [
        item('growth-01', 'course', '每日 30 分钟训练营', '围绕真实场景拆成可执行任务', '学习成长', 'Clock3', '/learning/daily', true, 0),
        item('growth-02', 'case', '优秀作业拆解', '学习高质量提示词和交付结构', '学习成长', 'ScanSearch', '/learning/cases', true, 10),
        item('growth-03', 'course', '行业案例复盘', '短视频、电商、办公和法务案例库', '学习成长', 'NotebookTabs', '/learning/reviews', true, 10)
      ]),
      section('section-earning-templates', 'home', 'earning_templates', '接单交付模板', 'template-list', [
        item('earning-01', 'template', '报价沟通模板', '快速明确需求、报价和修改次数', '接单变现', 'ReceiptText', '/templates/quote', true, 0),
        item('earning-02', 'template', '交付验收清单', '按项目节点检查文件、说明和售后', '接单变现', 'ShieldCheck', '/templates/delivery', true, 0),
        item('earning-03', 'template', '复购跟进话术', '交付后持续运营客户关系', '接单变现', 'MessageCircle', '/templates/follow-up', true, 0)
      ]),
      section('section-resource-hub', 'home', 'resource_hub', '资源对接库', 'banner-row', [
        item('resource-01', 'resource', '工具优惠合集', '模型、剪辑、设计和办公工具权益', '资源对接', 'Gift', '/resources/tools', false, 0),
        item('resource-02', 'resource', '行业资料库', '可复用的运营、法务和电商资料', '资源对接', 'FileText', '/resources/library', true, 0),
        item('resource-03', 'resource', '合作需求广场', '发布资源、客户线索和合作需求', '资源对接', 'Handshake', '/resources/market', true, 0)
      ]),
      section('section-project-cocreation', 'home', 'project_cocreation', '项目共创广场', 'order-grid', [
        item('project-01', 'project', '短视频矩阵共创', '脚本、剪辑、投放成员组队交付', '项目共创', 'FileVideo', '/projects/video', true, 0),
        item('project-02', 'project', '企业知识库搭建', '资料整理、流程设计和助手配置', '项目共创', 'Workflow', '/projects/knowledge-base', true, 0),
        item('project-03', 'project', 'AI办公改造案例', '用自动化流程帮助团队降本增效', '项目共创', 'BriefcaseBusiness', '/projects/office', true, 0)
      ]),
      section('section-workspace-tools', 'home', 'workspace_tools', '常用工作台', 'tool-grid', [
        item('workspace-01', 'tool', 'PPT 生成工作台', '从大纲到页面自动生成', '应用工作台', 'Presentation', '/workspace/ppt', false, 0),
        item('workspace-02', 'tool', '视频脚本工作台', '选题、脚本、分镜一站式处理', '应用工作台', 'MonitorPlay', '/workspace/video-script', false, 0),
        item('workspace-03', 'tool', '电商运营工作台', '标题、详情和客服话术生成', '应用工作台', 'WandSparkles', '/workspace/ecommerce', true, 10),
        item('workspace-04', 'tool', '合同审查工作台', '检查风险条款和修改建议', '应用工作台', 'Scale', '/workspace/legal', true, 10)
      ]),
      section('section-task-board', 'home', 'task_board', '任务入口', 'stat-strip', [
        item('task-01', 'task', '最近使用', '继续上次的工具和内容生成任务', '应用工作台', 'Clock3', '/workspace/recent', false, 0),
        item('task-02', 'task', '待交付项目', '查看接单任务、素材和交付节点', '应用工作台', 'BriefcaseBusiness', '/workspace/deliveries', true, 0),
        item('task-03', 'task', '素材库', '管理上传图片、模板和提示词资产', '应用工作台', 'CloudUpload', '/workspace/assets', true, 0)
      ]),
      section('section-toolkit', 'home', 'toolkit', '专业工具包', 'template-list', [
        item('toolkit-01', 'template', '商业计划书套件', '路演大纲、财务假设和页面结构', '专业工具包', 'ChartColumn', '/toolkit/business-plan', true, 0),
        item('toolkit-02', 'template', '短视频脚本套件', '选题、分镜、标题和口播脚本', '专业工具包', 'FileVideo', '/toolkit/video-script', true, 0),
        item('toolkit-03', 'template', '合同审查清单', '常见风险条款和修改建议模板', '专业工具包', 'Scale', '/toolkit/legal', true, 0),
        item('toolkit-04', 'template', '办公自动化组件', '表格、邮件和审批流程提示词', '专业工具包', 'Workflow', '/toolkit/office', true, 0)
      ]),
      section('section-template-ranking', 'home', 'template_ranking', '工具包排行榜', 'ranking-list', [
        item('rank-01', 'ranking', 'PPT 提案模板', '近 7 日 12.8 万次使用', '专业工具包', 'Presentation', '/toolkit/ranking/ppt', false, 0),
        item('rank-02', 'ranking', '报价单模板', '近 7 日 8.6 万次使用', '专业工具包', 'ReceiptText', '/toolkit/ranking/quote', false, 0),
        item('rank-03', 'ranking', '短视频分镜模板', '近 7 日 7.9 万次使用', '专业工具包', 'MonitorPlay', '/toolkit/ranking/video', false, 0)
      ])
    ]
  };
}

export function createFallbackPageConfig(pageKey: string): PortalPageConfig {
  const portal = createFallbackPortalConfig();
  const pageSummary = portal.pages.find((candidate) => candidate.pageKey === pageKey) ?? portal.pages[0];
  return {
    tenantId: 'demo',
    page: pageSummary,
    sections: pageSummary.pageKey === 'home' ? portal.homeSections : createGenericSections(pageSummary)
  };
}

export function createFallbackAssistantCenter(): AssistantCenter {
  const assistants: AssistantCard[] = [
    assistant('ppt', 'PPT 生成助理', '办公助理', '一键生成专业级 PPT，自动排版美化', 'Presentation', 234500, true, 20),
    assistant('copywriter', '文案创作助理', '营销助理', '快速生成各类文案、标题、脚本和营销内容', 'Feather', 197000, false, 10),
    assistant('analysis', '数据分析助理', '办公助理', '上传数据自动分析，生成图表与洞察报告', 'ChartColumn', 158000, true, 30),
    assistant('contract', '合同审查助理', '法务助理', '智能审查合同条款，识别风险点', 'ShieldCheck', 132000, true, 25),
    assistant('meeting', '会议纪要助理', '办公助理', '自动整理会议录音/文字，生成结构化纪要', 'Users', 128000, false, 10),
    assistant('mail', '邮件撰写助理', '办公助理', '根据需求生成专业邮件，语气灵活可调', 'Mail', 96000, false, 8)
  ];
  return {
    categories: ['全部', '办公助理', '营销助理', '学习助理', '法务助理', '客服助理', '设计助理', '开发助理'],
    featured: assistants.slice(0, 4).map(withUsageLabel),
    assistants: assistants.map(withUsageLabel),
    ranking: buildAssistantRanking(assistants),
    promptTemplates: [
      template('tpl-writing', '通用写作模板', '写作', '请围绕主题生成一份结构清晰、语气专业的内容。', false),
      template('tpl-marketing', '营销文案模板', '营销', '请生成 5 条适合社媒投放的卖点文案。', false),
      template('tpl-ppt', 'PPT 大纲模板', '办公', '请为这个主题设计一份 10 页 PPT 大纲。', true)
    ]
  };
}

export function normalizePortalConfig(payload: any): PortalConfig {
  const pages = (payload.pages ?? []).map(normalizePageSummary);
  return {
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    pages,
    channels: payload.channels ?? pages.map((pageItem: PageConfigSummary) => ({ key: pageItem.pageKey, label: pageItem.label })),
    leftNav: (payload.left_nav ?? payload.leftNav ?? []).map((nav: any) => ({
      key: nav.key,
      label: nav.label,
      icon: nav.icon
    })),
    homeSections: (payload.home_sections ?? payload.homeSections ?? []).map(normalizeSection)
  };
}

export function normalizePageConfig(payload: any): PortalPageConfig {
  return {
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    page: normalizePageSummary(payload.page ?? {}),
    sections: (payload.sections ?? []).map(normalizeSection)
  };
}

export function normalizeAssistantCenter(payload: any): AssistantCenter {
  const assistants = (payload.assistants ?? []).map(normalizeAssistant);
  return {
    categories: payload.categories ?? [],
    featured: (payload.featured ?? []).map(normalizeAssistant),
    assistants,
    ranking: (payload.ranking ?? buildAssistantRanking(assistants)).map(normalizeAssistant),
    promptTemplates: (payload.prompt_templates ?? payload.promptTemplates ?? []).map((prompt: any) => ({
      id: prompt.id,
      title: prompt.title,
      category: prompt.category,
      content: prompt.content,
      requiredMembership: Boolean(prompt.required_membership ?? prompt.requiredMembership)
    }))
  };
}

function normalizePageSummary(payload: any): PageConfigSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    pageKey: payload.page_key ?? payload.pageKey,
    label: payload.label ?? payload.title ?? '',
    title: payload.title ?? payload.label ?? '',
    subtitle: payload.subtitle ?? '',
    icon: payload.icon ?? 'Sparkles',
    sortOrder: Number(payload.sort_order ?? payload.sortOrder ?? 100),
    enabled: Boolean(payload.enabled ?? true)
  };
}

function normalizeSection(payload: any): PortalSection {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    pageKey: payload.page_key ?? payload.pageKey ?? payload.area ?? 'home',
    sectionKey: payload.section_key ?? payload.sectionKey,
    title: payload.title,
    subtitle: payload.subtitle ?? '',
    layout: payload.layout ?? 'grid',
    sortOrder: Number(payload.sort_order ?? payload.sortOrder ?? 100),
    enabled: Boolean(payload.enabled ?? true),
    items: (payload.items ?? []).map(normalizePortalItem)
  };
}

function normalizePortalItem(payload: any): PortalItem {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    sectionId: payload.section_id ?? payload.sectionId,
    itemType: payload.item_type ?? payload.itemType,
    title: payload.title,
    subtitle: payload.subtitle ?? '',
    category: payload.category ?? '',
    icon: payload.icon ?? 'Sparkles',
    imageUrl: payload.image_url ?? payload.imageUrl ?? '',
    badge: payload.badge ?? '',
    tags: payload.tags ?? [],
    sortOrder: Number(payload.sort_order ?? payload.sortOrder ?? 100),
    enabled: Boolean(payload.enabled ?? true),
    actionType: payload.action_type ?? payload.actionType ?? 'route',
    actionValue: payload.action_value ?? payload.actionValue ?? '',
    requiredMembership: Boolean(payload.required_membership ?? payload.requiredMembership),
    pointCost: Number(payload.point_cost ?? payload.pointCost ?? 0)
  };
}

function normalizeAssistant(payload: any): AssistantCard {
  const usageCount = Number(payload.usage_count ?? payload.usageCount ?? 0);
  return {
    id: payload.id,
    name: payload.name,
    category: payload.category,
    description: payload.description ?? '',
    icon: payload.icon ?? 'Bot',
    usageCount,
    usageCountLabel: payload.usage_count_label ?? payload.usageCountLabel ?? formatUsageCount(usageCount),
    pointCost: Number(payload.point_cost ?? payload.pointCost ?? 0),
    requiredMembership: Boolean(payload.required_membership ?? payload.requiredMembership),
    actionValue: payload.action_value ?? payload.actionValue ?? ''
  };
}

function createGenericSections(pageSummary: PageConfigSummary): PortalSection[] {
  return [
    section(`section-${pageSummary.pageKey}-overview`, pageSummary.pageKey, 'overview', pageSummary.title, 'stat-strip', [
      item(`${pageSummary.pageKey}-stat-1`, 'stat', '本周热度', '使用量持续增长', '概览', 'Flame', `/${pageSummary.pageKey}`, false, 0),
      item(`${pageSummary.pageKey}-stat-2`, 'stat', '会员专享', '高阶模板开放', '概览', 'Gift', `/${pageSummary.pageKey}`, true, 0),
      item(`${pageSummary.pageKey}-stat-3`, 'stat', '交付案例', '沉淀可复用方案', '概览', 'BriefcaseBusiness', `/${pageSummary.pageKey}`, false, 0)
    ]),
    section(`section-${pageSummary.pageKey}-tools`, pageSummary.pageKey, 'tools', `${pageSummary.label}工具矩阵`, 'tool-grid', [
      item(`${pageSummary.pageKey}-tool-1`, 'tool', `${pageSummary.label}生成器`, '快速生成可交付内容', '工具', pageSummary.icon, `/${pageSummary.pageKey}`, false, 10),
      item(`${pageSummary.pageKey}-tool-2`, 'tool', '模板工作流', '复用成熟流程和提示词', '模板', 'NotebookTabs', `/${pageSummary.pageKey}`, true, 20),
      item(`${pageSummary.pageKey}-tool-3`, 'tool', '数据复盘', '查看任务状态和效果', '数据', 'ChartColumn', `/${pageSummary.pageKey}`, true, 20)
    ])
  ];
}

function page(pageKey: string, label: string, title: string, subtitle: string, icon: string, sortOrder: number): PageConfigSummary {
  return { pageKey, label, title, subtitle, icon, sortOrder, enabled: true };
}

function section(id: string, pageKey: string, sectionKey: string, title: string, layout: string, items: PortalItem[]): PortalSection {
  return { id, pageKey, sectionKey, title, subtitle: '', layout, sortOrder: 100, enabled: true, items };
}

function item(
  id: string,
  itemType: string,
  title: string,
  subtitle: string,
  category: string,
  icon: string,
  actionValue: string,
  requiredMembership: boolean,
  pointCost: number
): PortalItem {
  return {
    id,
    itemType,
    title,
    subtitle,
    category,
    icon,
    actionValue,
    requiredMembership,
    pointCost,
    sortOrder: 100,
    enabled: true,
    tags: []
  };
}

function assistant(
  key: string,
  name: string,
  category: string,
  description: string,
  icon: string,
  usageCount: number,
  requiredMembership: boolean,
  pointCost: number
): AssistantCard {
  return {
    id: `assistant-${key}`,
    name,
    category,
    description,
    icon,
    usageCount,
    usageCountLabel: formatUsageCount(usageCount),
    pointCost,
    requiredMembership,
    actionValue: key
  };
}

function withUsageLabel(assistant: AssistantCard): AssistantCard {
  return {
    ...assistant,
    usageCountLabel: assistant.usageCountLabel ?? formatUsageCount(assistant.usageCount)
  };
}

function template(id: string, title: string, category: string, content: string, requiredMembership: boolean): PromptTemplate {
  return { id, title, category, content, requiredMembership };
}

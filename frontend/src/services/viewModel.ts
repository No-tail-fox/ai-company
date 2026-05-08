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

export function formatUsageCount(count: number): string {
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}万次使用`;
  }
  return `${count}次使用`;
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
        item('learn-04', 'course', '《AI 爆款内容创作》', '短视频脚本、标题、封面和投放流程', 'AI营销', 'Presentation', '/workspace/course', true, 20)
      ]),
      section('section-orders', 'home', 'order_center', 'OPC 接单中心', 'order-grid', [
        item('order-01', 'service', 'AI创作订单', 'PPT、文案、图片与短视频交付', '接单变现', 'Feather', '/workspace/orders', true, 20),
        item('order-02', 'service', 'AI自动化定制', '为客户定制办公自动化流程', '项目共创', 'FileText', '/workspace/automation', true, 50),
        item('order-03', 'service', 'AI电商优化', '商品标题、详情页与客服话术', 'AI电商', 'WandSparkles', '/workspace/ecommerce', true, 30)
      ]),
      section('section-communities', 'home', 'communities', '兴趣社群', 'banner-row', [
        item('comm-01', 'community', '入门交流群', '新人答疑、工具清单和上手路线', '社群', 'MessageCircle', '/community/starter', false, 0),
        item('comm-02', 'community', '学习打卡群', '每日任务、案例拆解和作业反馈', '社群', 'GraduationCap', '/community/study', true, 0),
        item('comm-03', 'community', '接单变现群', '接单案例、报价模板和交付流程', '社群', 'Handshake', '/community/orders', true, 0)
      ]),
      section('section-banners', 'home', 'banners', '热门活动', 'promo', [
        item('banner-01', 'banner', '热门模板上新！', '一键轻松取用办公模板', '运营活动', 'Gift', '/templates', true, 0),
        item('banner-02', 'banner', '商业计划书模板', '融资路演、商业策划、项目计划', '模板', 'ChartColumn', '/templates/business', true, 0)
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

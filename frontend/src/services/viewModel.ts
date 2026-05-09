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

export interface AudioTaskPayload {
  task_type: string;
  route_key: string;
  prompt: string;
  source_url: string;
  voice_key: string;
}

export interface AudioTask {
  id: string;
  taskType: string;
  routeKey: string;
  prompt: string;
  status: string;
  estimatedCost: number;
  actualCost?: number | null;
  providerTaskId?: string | null;
  resultUrl?: string | null;
  errorMessage?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface MarketingMetric {
  label: string;
  value: string;
  trend: string;
  icon: string;
}

export interface MarketingChannelRank {
  name: string;
  exposure: string;
  conversion: string;
}

export interface MarketingRecord {
  title: string;
  time: string;
}

export interface MarketingDashboardModel {
  page: PageConfigSummary;
  metrics: MarketingMetric[];
  tools: PortalItem[];
  templates: PortalItem[];
  ranking: PortalItem[];
  channelRanking: MarketingChannelRank[];
  recentRecords: MarketingRecord[];
}

export interface VideoWallet {
  balance: number;
  frozenBalance: number;
}

export interface VideoRoute {
  routeKey: string;
  unitCost: number;
}

export interface VideoTask {
  id: string;
  tenantId: string;
  userId: string;
  taskType: string;
  routeKey: string;
  prompt: string;
  status: string;
  estimatedCost: number;
  actualCost?: number | null;
  providerTaskId?: string | null;
  resultUrl?: string | null;
  errorMessage?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface VideoWorkbench {
  tenantId: string;
  userId: string;
  wallet: VideoWallet;
  route: VideoRoute;
  tasks: VideoTask[];
}

export interface VideoStatusMeta {
  label: string;
  progress: number;
  tone: 'pending' | 'processing' | 'success' | 'failed';
}

export interface ImageWallet {
  balance: number;
  frozenBalance: number;
}

export interface ImageRoute {
  routeKey: string;
  unitCost: number;
}

export interface ImageTask {
  id: string;
  tenantId: string;
  userId: string;
  taskType: string;
  routeKey: string;
  prompt: string;
  status: string;
  estimatedCost: number;
  actualCost?: number | null;
  providerTaskId?: string | null;
  resultUrl?: string | null;
  errorMessage?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface ImageWorkbench {
  tenantId: string;
  userId: string;
  wallet: ImageWallet;
  route: ImageRoute;
  tasks: ImageTask[];
}

export interface ImageStatusMeta {
  label: string;
  progress: number;
  tone: 'pending' | 'processing' | 'success' | 'failed';
}

const fallbackPages: PageConfigSummary[] = [
  page('home', '首页', '常用AI学习中心', '学习、接单、社群和活动的统一入口', 'Home', 10),
  page('assistant', 'AI 助理', '智能助理广场', '办公、营销、学习、法务等场景助理集合', 'Bot', 20),
  page('marketing', 'AI 营销', '营销增长中心', '从内容生成到投放复盘的一站式工具台', 'Megaphone', 30),
  page('image', 'AI 图片', 'AI图片创作中心', '提示词、模板、批量出图和生成队列', 'Image', 35),
  page('video', 'AI 视频', 'AI视频创作中心', '脚本、数字人、剪辑、字幕和渲染队列', 'FileVideo', 40),
  page('audio', 'AI 音频', 'AI音频工作台', '配音、转写、降噪、播客和音色库', 'Headphones', 50),
  page('coding', 'AI 编程', 'AI编程工作台', '代码生成、审查、测试和自动化脚本', 'Workflow', 60),
  page('writing', 'AI 写作', 'AI写作中心', '文章、报告、简历、论文和提示词模板', 'Feather', 70),
  page('ecommerce', 'AI 电商', 'AI电商运营中心', '商品内容、客服话术、店铺分析和素材生成', 'WandSparkles', 80),
  page('legal', 'AI 法务', 'AI法务服务台', '合同审查、法律咨询、证据整理和文书草拟', 'Scale', 90),
  page('office', 'AI 办公', 'AI办公效率中心', 'PPT、表格、会议、邮件和流程自动化', 'BriefcaseBusiness', 100)
];

const DEFAULT_HOME_MENU_KEY = 'basic';
const MARKETING_PAGE_KEY = 'marketing';
const IMAGE_PAGE_KEY = 'image';
const AUDIO_PAGE_KEY = 'audio';
const VIDEO_PAGE_KEY = 'video';

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

export function shouldUseAssistantPage(pageKey: string): boolean {
  return pageKey === 'assistant';
}

export function shouldUseMarketingPage(pageKey: string): boolean {
  return pageKey === MARKETING_PAGE_KEY;
}

export function shouldUseImagePage(pageKey: string): boolean {
  return pageKey === IMAGE_PAGE_KEY;
}

export function shouldUseAudioPage(pageKey: string): boolean {
  return pageKey === AUDIO_PAGE_KEY;
}

export function getAudioSection(pageConfig: PortalPageConfig, layout: string): PortalSection | undefined {
  if (!layout.startsWith('audio-')) {
    return undefined;
  }
  return pageConfig.sections.find((sectionItem) => sectionItem.layout === layout);
}

export function buildAudioTaskPayload(
  selectedTool: PortalItem,
  prompt: string,
  selectedVoice?: PortalItem,
  sourceUrl = ''
): AudioTaskPayload {
  return {
    task_type: audioTaskTypeForRoute(selectedTool.actionValue),
    route_key: selectedTool.actionValue,
    prompt,
    source_url: sourceUrl,
    voice_key: selectedVoice?.actionValue ?? ''
  };
}

export function shouldUseVideoPage(pageKey: string): boolean {
  return pageKey === VIDEO_PAGE_KEY;
}

export function shouldHideWorkspaceDock(pageKey: string): boolean {
  return shouldUseImagePage(pageKey) || shouldUseVideoPage(pageKey);
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

export function filterAssistantCardsByCategory(assistants: AssistantCard[], category: string): AssistantCard[] {
  if (!category || category === '全部') {
    return assistants;
  }
  return assistants.filter((assistant) => assistant.category === category);
}

const marketingOverviewFallback = [
  item('marketing-metric-1', 'stat', '进行中活动', '8', '较昨日 ↑2', 'Flame', '/marketing', false, 0),
  item('marketing-metric-2', 'stat', '本月线索总数', '3,245', '较上月 ↑18.6%', 'ReceiptText', '/marketing', false, 0),
  item('marketing-metric-3', 'stat', '内容总曝光', '128.6万', '较上月 ↑24.3%', 'Megaphone', '/marketing', false, 0),
  item('marketing-metric-4', 'stat', '转化客户数', '236', '较上月 ↑15.2%', 'Users', '/marketing', false, 0),
  item('marketing-metric-5', 'stat', 'ROI 投入产出比', '4.32', '较上月 ↑0.68', 'ChartColumn', '/marketing', false, 0)
];

const marketingToolFallback = [
  item('marketing-tool-1', 'tool', '爆款文案生成', '标题、卖点、脚本一键生成', '文案', 'Feather', '/marketing/tool/copy', false, 0),
  item('marketing-tool-2', 'tool', '私域引流方案', '社群、企微和转化路径规划', '渠道', 'Network', '/marketing/tool/private-domain', false, 0),
  item('marketing-tool-3', 'tool', '短视频脚本', '选题、分镜、口播一体生成', '短视频', 'FileVideo', '/marketing/tool/video-script', false, 0),
  item('marketing-tool-4', 'tool', '小红书种草', '笔记文案与话题建议', '社媒', 'Megaphone', '/marketing/tool/xiaohongshu', false, 0),
  item('marketing-tool-5', 'tool', '公众号推文', '长文内容与排版建议', '图文', 'MessageCircle', '/marketing/tool/public-account', false, 0),
  item('marketing-tool-6', 'tool', '邮件营销', '自动生成专业营销邮件', '邮件', 'Mail', '/marketing/tool/email', false, 0),
  item('marketing-tool-7', 'tool', 'SEO 关键词', '搜索词聚合与结构优化', 'SEO', 'Search', '/marketing/tool/seo', false, 0),
  item('marketing-tool-8', 'tool', '投放素材', '广告图文和落地页文案', '投放', 'WandSparkles', '/marketing/tool/ad-materials', false, 0),
  item('marketing-tool-9', 'tool', '数据复盘', '转化漏斗和优化建议', '分析', 'ChartColumn', '/marketing/tool/data-review', false, 0)
];

const marketingTemplateFallback = [
  item('marketing-template-1', 'template', '新品上市推广文案', '适用于新品发布活动', '营销模板', 'Gift', '/marketing/template/new-product', true, 0),
  item('marketing-template-2', 'template', '双11促销活动文案', '适用于大促节点推广', '营销模板', 'Sparkles', '/marketing/template/11-11', true, 0),
  item('marketing-template-3', 'template', '行业解决方案文案', '适用于B2B方案包装', '营销模板', 'ChartColumn', '/marketing/template/solution', true, 0),
  item('marketing-template-4', 'template', '品牌故事文案', '适用于品牌表达和官网内容', '营销模板', 'FileText', '/marketing/template/brand-story', true, 0),
  item('marketing-template-5', 'template', '客户案例文案', '适用于案例展示与成交背书', '营销模板', 'Presentation', '/marketing/template/case-study', true, 0)
];

const marketingRankingFallback = [
  item('marketing-rank-1', 'ranking', '微信公众号', '曝光 28.6万', '转化 62', 'MessageCircle', '/marketing/rank/wechat', false, 0),
  item('marketing-rank-2', 'ranking', '小红书', '曝光 18.3万', '转化 48', 'Image', '/marketing/rank/xiaohongshu', false, 0),
  item('marketing-rank-3', 'ranking', '抖音', '曝光 15.7万', '转化 32', 'MonitorPlay', '/marketing/rank/douyin', false, 0),
  item('marketing-rank-4', 'ranking', '企业微信', '曝光 12.1万', '转化 14', 'Users', '/marketing/rank/wecom', false, 0),
  item('marketing-rank-5', 'ranking', '知乎', '曝光 6.8万', '转化 9', 'Search', '/marketing/rank/zhihu', false, 0)
];

const marketingChannelRankingFallback: MarketingChannelRank[] = [
  { name: '微信公众号', exposure: '曝光 28.6万', conversion: '转化 62' },
  { name: '小红书', exposure: '曝光 18.3万', conversion: '转化 48' },
  { name: '抖音', exposure: '曝光 15.7万', conversion: '转化 32' },
  { name: '企业微信', exposure: '曝光 12.1万', conversion: '转化 14' },
  { name: '知乎', exposure: '曝光 6.8万', conversion: '转化 9' }
];

const marketingRecentRecordsFallback: MarketingRecord[] = [
  { title: '小红书种草文案：智能办公椅', time: '今天 10:24' },
  { title: '投放素材：暑期课程推广', time: '今天 09:41' },
  { title: '公众号推文：行业趋势解读', time: '昨天 16:32' },
  { title: '双11促销活动文案', time: '昨天 14:18' },
  { title: 'SEO 文章优化：AI工具推荐', time: '前天 11:07' }
];

const fallbackVideoTasks: VideoTask[] = [
  {
    id: 'video-demo-1',
    tenantId: 'demo',
    userId: 'demo-user',
    taskType: 'VIDEO',
    routeKey: 'video_text_to_video',
    prompt: '夏季新品推广视频',
    status: 'PROCESSING',
    estimatedCost: 200,
    providerTaskId: 'demo-processing',
    createdAt: '2026-05-09T09:40:00'
  },
  {
    id: 'video-demo-2',
    tenantId: 'demo',
    userId: 'demo-user',
    taskType: 'VIDEO',
    routeKey: 'video_text_to_video',
    prompt: '企业宣传片',
    status: 'PENDING',
    estimatedCost: 200,
    createdAt: '2026-05-09T09:32:00'
  },
  {
    id: 'video-demo-3',
    tenantId: 'demo',
    userId: 'demo-user',
    taskType: 'VIDEO',
    routeKey: 'video_text_to_video',
    prompt: '知识科普：AI入门指南',
    status: 'SUCCESS',
    estimatedCost: 200,
    actualCost: 200,
    resultUrl: '/storage/uploads/demo/video-demo.mp4',
    createdAt: '2026-05-08T16:20:00'
  },
  {
    id: 'video-demo-4',
    tenantId: 'demo',
    userId: 'demo-user',
    taskType: 'VIDEO',
    routeKey: 'video_text_to_video',
    prompt: '618促销带货视频',
    status: 'SUCCESS',
    estimatedCost: 200,
    actualCost: 200,
    resultUrl: '/storage/uploads/demo/video-demo-2.mp4',
    createdAt: '2026-05-08T14:20:00'
  }
];

const fallbackImageTasks: ImageTask[] = [
  {
    id: 'image-demo-1',
    tenantId: 'demo',
    userId: 'demo-user',
    taskType: 'IMAGE',
    routeKey: 'image_text_to_image',
    prompt: '夏季新品推广海报，清爽蓝色背景，突出产品质感',
    status: 'PROCESSING',
    estimatedCost: 80,
    providerTaskId: 'demo-image-processing',
    createdAt: '2026-05-09T09:42:00'
  },
  {
    id: 'image-demo-2',
    tenantId: 'demo',
    userId: 'demo-user',
    taskType: 'IMAGE',
    routeKey: 'image_text_to_image',
    prompt: '企业品牌宣传配图，科技感办公场景',
    status: 'PENDING',
    estimatedCost: 80,
    createdAt: '2026-05-09T09:35:00'
  },
  {
    id: 'image-demo-3',
    tenantId: 'demo',
    userId: 'demo-user',
    taskType: 'IMAGE',
    routeKey: 'image_text_to_image',
    prompt: '知识科普封面：AI入门指南',
    status: 'SUCCESS',
    estimatedCost: 80,
    actualCost: 80,
    resultUrl: '/storage/uploads/demo/image-demo.png',
    createdAt: '2026-05-08T16:20:00'
  },
  {
    id: 'image-demo-4',
    tenantId: 'demo',
    userId: 'demo-user',
    taskType: 'IMAGE',
    routeKey: 'image_text_to_image',
    prompt: '618促销电商主图',
    status: 'SUCCESS',
    estimatedCost: 80,
    actualCost: 80,
    resultUrl: '/storage/uploads/demo/image-demo-2.png',
    createdAt: '2026-05-08T14:20:00'
  }
];

export function createFallbackVideoWorkbench(): VideoWorkbench {
  return {
    tenantId: 'demo',
    userId: 'demo-user',
    wallet: {
      balance: 120000,
      frozenBalance: 400
    },
    route: {
      routeKey: 'video_text_to_video',
      unitCost: 200
    },
    tasks: fallbackVideoTasks
  };
}

export function createFallbackImageWorkbench(): ImageWorkbench {
  return {
    tenantId: 'demo',
    userId: 'demo-user',
    wallet: {
      balance: 120000,
      frozenBalance: 160
    },
    route: {
      routeKey: 'image_text_to_image',
      unitCost: 80
    },
    tasks: fallbackImageTasks
  };
}

export function getVideoStatusMeta(status: string): VideoStatusMeta {
  const normalized = status.toUpperCase();
  if (normalized === 'PROCESSING') {
    return { label: '渲染中', progress: 65, tone: 'processing' };
  }
  if (normalized === 'SUCCESS') {
    return { label: '已完成', progress: 100, tone: 'success' };
  }
  if (normalized === 'FAILED') {
    return { label: '失败', progress: 100, tone: 'failed' };
  }
  return { label: '排队中', progress: 8, tone: 'pending' };
}

export function getImageStatusMeta(status: string): ImageStatusMeta {
  const normalized = status.toUpperCase();
  if (normalized === 'PROCESSING') {
    return { label: '生成中', progress: 65, tone: 'processing' };
  }
  if (normalized === 'SUCCESS') {
    return { label: '已完成', progress: 100, tone: 'success' };
  }
  if (normalized === 'FAILED') {
    return { label: '失败', progress: 100, tone: 'failed' };
  }
  return { label: '排队中', progress: 10, tone: 'pending' };
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
    sections:
      pageSummary.pageKey === 'home'
        ? portal.homeSections
        : pageSummary.pageKey === MARKETING_PAGE_KEY
          ? createMarketingSections(pageSummary)
          : pageSummary.pageKey === AUDIO_PAGE_KEY
            ? createFallbackAudioSections()
          : createGenericSections(pageSummary)
  };
}

export function buildMarketingDashboardModel(pageConfig: PortalPageConfig): MarketingDashboardModel {
  const fallbackSections = createMarketingSections(pageConfig.page);
  const sectionsByKey = new Map(pageConfig.sections.map((sectionItem) => [sectionItem.sectionKey, sectionItem]));
  const overviewSection = sectionsByKey.get('overview') ?? fallbackSections[0];
  const toolsSection = sectionsByKey.get('tools') ?? fallbackSections[1];
  const templatesSection = sectionsByKey.get('templates') ?? fallbackSections[2];
  const rankingSection = sectionsByKey.get('ranking') ?? fallbackSections[3];

  return {
    page: pageConfig.page,
    metrics: buildMarketingMetrics(mergePortalItems(overviewSection.items, fallbackSections[0].items, 5)),
    tools: mergePortalItems(toolsSection.items, fallbackSections[1].items, 9),
    templates: mergePortalItems(templatesSection.items, fallbackSections[2].items, 5),
    ranking: mergePortalItems(rankingSection.items, fallbackSections[3].items, 5),
    channelRanking: marketingChannelRankingFallback,
    recentRecords: marketingRecentRecordsFallback
  };
}

export function createFallbackAssistantCenter(): AssistantCenter {
  const assistants: AssistantCard[] = [
    assistant('ppt', 'PPT 生成助理', '办公助理', '一键生成专业级 PPT，自动排版美化', 'Presentation', 234500, true, 20),
    assistant('copywriter', '文案创作助理', '营销助理', '快速生成各类文案、标题、脚本和营销内容', 'Feather', 197000, false, 10),
    assistant('analysis', '数据分析助理', '办公助理', '上传数据自动分析，生成图表与洞察报告', 'ChartColumn', 158000, true, 30),
    assistant('contract', '合同审查助理', '法务助理', '智能审查合同条款，识别风险点', 'ShieldCheck', 132000, true, 25),
    assistant('meeting', '会议纪要助理', '办公助理', '自动整理会议录音/文字，生成结构化纪要', 'Users', 128000, false, 10),
    assistant('mail', '邮件撰写助理', '办公助理', '根据需求生成专业邮件，语气灵活可调', 'Mail', 96000, false, 8),
    assistant('xiaohongshu', '小红书文案助理', '营销助理', '生成爆款笔记文案、标题与话题建议', 'Megaphone', 107000, true, 12),
    assistant('excel', 'Excel 公式助理', '开发助理', '生成公式、函数解释与表格处理方案', 'Sheet', 146000, false, 8),
    assistant('resume', '简历优化助理', '生活助理', '优化简历内容与排版，提升求职竞争力', 'UserRound', 93000, true, 10),
    assistant('image', '图片设计助理', '设计助理', '根据描述生成海报、封面与设计图', 'Image', 72000, true, 20),
    assistant('study', '学习规划助理', '学习助理', '拆解学习目标，生成每日训练计划', 'GraduationCap', 84000, false, 8),
    assistant('customer', '客服应答助理', '客服助理', '生成售前售后标准回复和异议处理话术', 'MessageCircle', 118000, true, 12)
  ];
  return {
    categories: ['全部', '办公助理', '营销助理', '学习助理', '法务助理', '客服助理', '设计助理', '开发助理', '生活助理'],
    featured: assistants.slice(0, 4).map(withUsageLabel),
    assistants: assistants.map(withUsageLabel),
    ranking: buildAssistantRanking(assistants),
    promptTemplates: [
      template('tpl-writing', '通用写作模板', '写作', '请围绕主题生成一份结构清晰、语气专业的内容。', false),
      template('tpl-marketing', '营销文案模板', '营销', '请生成 5 条适合社媒投放的卖点文案。', false),
      template('tpl-ppt', 'PPT 大纲模板', '办公', '请为这个主题设计一份 10 页 PPT 大纲。', true),
      template('tpl-xiaohongshu', '小红书笔记模板', '社媒', '请生成一篇小红书爆款笔记，包含标题和标签。', true),
      template('tpl-legal', '法律咨询模板', '法务', '请从合同风险、证据和谈判建议三个角度分析。', true)
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

export function normalizeVideoWorkbench(payload: any): VideoWorkbench {
  return {
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    userId: payload.user_id ?? payload.userId ?? 'demo-user',
    wallet: {
      balance: Number(payload.wallet?.balance ?? 0),
      frozenBalance: Number(payload.wallet?.frozen_balance ?? payload.wallet?.frozenBalance ?? 0)
    },
    route: {
      routeKey: payload.route?.route_key ?? payload.route?.routeKey ?? 'video_text_to_video',
      unitCost: Number(payload.route?.unit_cost ?? payload.route?.unitCost ?? 200)
    },
    tasks: (payload.tasks ?? []).map(normalizeVideoTask)
  };
}

export function normalizeImageWorkbench(payload: any): ImageWorkbench {
  return {
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    userId: payload.user_id ?? payload.userId ?? 'demo-user',
    wallet: {
      balance: Number(payload.wallet?.balance ?? 0),
      frozenBalance: Number(payload.wallet?.frozen_balance ?? payload.wallet?.frozenBalance ?? 0)
    },
    route: {
      routeKey: payload.route?.route_key ?? payload.route?.routeKey ?? 'image_text_to_image',
      unitCost: Number(payload.route?.unit_cost ?? payload.route?.unitCost ?? 80)
    },
    tasks: (payload.tasks ?? []).map(normalizeImageTask)
  };
}

export function normalizeAudioTask(payload: any): AudioTask {
  return {
    id: payload.id,
    taskType: payload.task_type ?? payload.taskType ?? 'TTS',
    routeKey: payload.route_key ?? payload.routeKey ?? 'audio_tts',
    prompt: payload.prompt ?? '',
    status: payload.status ?? 'PENDING',
    estimatedCost: Number(payload.estimated_cost ?? payload.estimatedCost ?? 0),
    actualCost: payload.actual_cost ?? payload.actualCost ?? null,
    providerTaskId: payload.provider_task_id ?? payload.providerTaskId ?? null,
    resultUrl: payload.result_url ?? payload.resultUrl ?? null,
    errorMessage: payload.error_message ?? payload.errorMessage ?? null,
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null
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

function normalizeVideoTask(payload: any): VideoTask {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    userId: payload.user_id ?? payload.userId ?? 'demo-user',
    taskType: payload.task_type ?? payload.taskType ?? 'VIDEO',
    routeKey: payload.route_key ?? payload.routeKey ?? 'video_text_to_video',
    prompt: payload.prompt ?? '',
    status: payload.status ?? 'PENDING',
    estimatedCost: Number(payload.estimated_cost ?? payload.estimatedCost ?? 0),
    actualCost: payload.actual_cost ?? payload.actualCost ?? null,
    providerTaskId: payload.provider_task_id ?? payload.providerTaskId ?? null,
    resultUrl: payload.result_url ?? payload.resultUrl ?? null,
    errorMessage: payload.error_message ?? payload.errorMessage ?? null,
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null
  };
}

function normalizeImageTask(payload: any): ImageTask {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    userId: payload.user_id ?? payload.userId ?? 'demo-user',
    taskType: payload.task_type ?? payload.taskType ?? 'IMAGE',
    routeKey: payload.route_key ?? payload.routeKey ?? 'image_text_to_image',
    prompt: payload.prompt ?? '',
    status: payload.status ?? 'PENDING',
    estimatedCost: Number(payload.estimated_cost ?? payload.estimatedCost ?? 0),
    actualCost: payload.actual_cost ?? payload.actualCost ?? null,
    providerTaskId: payload.provider_task_id ?? payload.providerTaskId ?? null,
    resultUrl: payload.result_url ?? payload.resultUrl ?? null,
    errorMessage: payload.error_message ?? payload.errorMessage ?? null,
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null
  };
}

function createFallbackAudioSections(): PortalSection[] {
  return [
    section('section-audio-workbench', 'audio', 'workbench', 'AI音频工作台', 'audio-workbench', [
      item('audio-workbench-main', 'workbench', '文本转语音', '输入文字，选择音色与情感，一键生成自然流畅的语音', '音频工作台', 'Headphones', 'audio_tts', false, 120)
    ]),
    section('section-audio-stats', 'audio', 'stats', '音频数据概览', 'audio-stats', [
      item('audio-stat-1', 'stat', '今日生成时长', '3.6 小时', '较昨日 ↑18%', 'Clock3', '/audio', false, 0),
      item('audio-stat-2', 'stat', '音频项目数', '23 个', '较昨日 ↑27%', 'Headphones', '/audio', false, 0),
      item('audio-stat-3', 'stat', '总生成时长', '128.7 小时', '较上月 ↑22%', 'AudioWaveform', '/audio', false, 0),
      item('audio-stat-4', 'stat', '已节省成本', '￥3,256', '较上月 ↑31%', 'ChartColumn', '/audio', false, 0)
    ]),
    section('section-audio-tools', 'audio', 'tools', '音频工具中心', 'audio-tools', [
      item('audio-tool-1', 'tool', '文本转语音', '多音色高拟真配音', '音频工具', 'Headphones', 'audio_tts', false, 120),
      item('audio-tool-2', 'tool', '声音克隆', '复用品牌或个人音色', '音频工具', 'CircleUserRound', 'audio_voice_clone', false, 180),
      item('audio-tool-3', 'tool', '播客生成', '一键生成播客旁白内容', '音频工具', 'Mic', 'audio_podcast', false, 160),
      item('audio-tool-4', 'tool', '智能降噪', '去除环境噪音并提升清晰度', '音频工具', 'AudioWaveform', 'audio_denoise', false, 80),
      item('audio-tool-5', 'tool', '录音转写', '会议访谈快速成稿', '音频工具', 'FileText', 'audio_transcription', true, 90),
      item('audio-tool-6', 'tool', '会议纪要', '音频自动整理为结构化纪要', '音频工具', 'Users', 'audio_meeting_notes', true, 110),
      item('audio-tool-7', 'tool', 'AI 配乐', '短视频背景音乐生成', '音频工具', 'Music', 'audio_music', true, 140),
      item('audio-tool-8', 'tool', '音频剪辑', '裁剪、拼接、变速和淡入淡出', '音频工具', 'Scissors', 'audio_editor', true, 70)
    ]),
    section('section-audio-voices', 'audio', 'voices', '音色库', 'audio-voices', [
      item('audio-voice-1', 'voice', '知性女声', '温柔 · 知性 · 12.5w 使用', '女声', 'CircleUserRound', 'voice-warm-female', false, 0),
      item('audio-voice-2', 'voice', '磁性男声', '成熟 · 沉稳 · 9.8w 使用', '男声', 'UserRound', 'voice-deep-male', false, 0),
      item('audio-voice-3', 'voice', '活力女声', '活泼 · 明亮 · 8.7w 使用', '女声', 'CircleUserRound', 'voice-bright-female', false, 0),
      item('audio-voice-4', 'voice', '温暖男声', '亲切 · 自然 · 7.2w 使用', '男声', 'UserRound', 'voice-natural-male', false, 0),
      item('audio-voice-5', 'voice', '标准童声', '可爱 · 清晰 · 6.1w 使用', '童声', 'Sparkles', 'voice-child', true, 0),
      item('audio-voice-6', 'voice', '粤语女声', '粤语 · 亲切 · 5.3w 使用', '方言', 'Mic', 'voice-cantonese-female', true, 0)
    ]),
    section('section-audio-table', 'audio', 'recent', '最近音频', 'audio-table', [
      item('audio-recent-1', 'audio', '产品宣传片配音', '00:48 · 知性女声', '已完成', 'Headphones', '/audio', false, 0),
      item('audio-recent-2', 'audio', '播客第28期', '12:36 · 磁性男声 · 65%', '处理中', 'Podcast', '/audio', false, 0),
      item('audio-recent-3', 'audio', 'AI工具使用教程', '08:22 · 活力女声 · 30%', '处理中', 'FileText', '/audio', false, 0),
      item('audio-recent-4', 'audio', '市场调研会议', '05:17 · 多人声源', '已完成', 'Users', '/audio', false, 0),
      item('audio-recent-5', 'audio', '广告配音 - 版本2', '00:30 · 温暖男声', '排队中', 'Mic', '/audio', false, 0)
    ]),
    section('section-audio-queue', 'audio', 'queue', '音频任务队列', 'audio-queue', [
      item('audio-queue-1', 'task', '产品宣传片配音', '00:48 · 65%', '处理中', 'AudioWaveform', '/audio', false, 0),
      item('audio-queue-2', 'task', '播客第28期制作', '12:36 · 30%', '处理中', 'Podcast', '/audio', false, 0),
      item('audio-queue-3', 'task', '课程语音合成', '08:22 · 0%', '排队中', 'Mic', '/audio', false, 0),
      item('audio-queue-4', 'task', '会议录音转写', '05:17 · 0%', '排队中', 'Users', '/audio', false, 0)
    ]),
    section('section-audio-resources', 'audio', 'resources', '音频资源库', 'audio-resources', [
      item('audio-resource-1', 'resource', '背景音乐', '2,362 首', '资源', 'Music', '/audio/resources', false, 0),
      item('audio-resource-2', 'resource', '音效库', '8,745 个', '资源', 'Volume2', '/audio/resources', false, 0),
      item('audio-resource-3', 'resource', '模板库', '356 个', '资源', 'FileText', '/audio/resources', true, 0),
      item('audio-resource-4', 'resource', '配音模板', '128 个', '资源', 'Headphones', '/audio/resources', true, 0)
    ]),
    section('section-audio-guides', 'audio', 'guides', '音频创作指南', 'audio-guides', [
      item('audio-guide-1', 'guide', '新手入门教程', '从文本配音到导出音频', '指南', 'GraduationCap', '/audio/guides', false, 0),
      item('audio-guide-2', 'guide', '热门音色推荐', '按场景选择适合音色', '指南', 'Star', '/audio/guides', false, 0),
      item('audio-guide-3', 'guide', '音频制作技巧', '降噪、节奏和后期建议', '指南', 'NotebookTabs', '/audio/guides', false, 0)
    ])
  ];
}

function audioTaskTypeForRoute(routeKey: string): string {
  if (routeKey.includes('transcription')) {
    return 'TRANSCRIPTION';
  }
  if (routeKey.includes('music')) {
    return 'MUSIC';
  }
  if (routeKey.includes('denoise')) {
    return 'DENOISE';
  }
  if (routeKey.includes('meeting')) {
    return 'MEETING_NOTES';
  }
  if (routeKey.includes('editor')) {
    return 'EDITOR';
  }
  if (routeKey.includes('podcast')) {
    return 'PODCAST';
  }
  if (routeKey.includes('voice_clone')) {
    return 'VOICE_CLONE';
  }
  return 'TTS';
}

function createMarketingSections(pageSummary: PageConfigSummary): PortalSection[] {
  return [
    section('section-marketing-overview', pageSummary.pageKey, 'overview', pageSummary.title, 'stat-strip', marketingOverviewFallback),
    section('section-marketing-tools', pageSummary.pageKey, 'tools', '营销工具矩阵', 'tool-grid', marketingToolFallback),
    section('section-marketing-templates', pageSummary.pageKey, 'templates', '爆款模板推荐', 'template-list', marketingTemplateFallback),
    section('section-marketing-ranking', pageSummary.pageKey, 'ranking', '渠道效果排行', 'ranking-list', marketingRankingFallback)
  ];
}

function buildMarketingMetrics(items: PortalItem[]): MarketingMetric[] {
  return items.map((itemItem) => ({
    label: itemItem.title,
    value: itemItem.subtitle,
    trend: itemItem.badge || itemItem.category,
    icon: itemItem.icon
  }));
}

function mergePortalItems(primaryItems: PortalItem[], fallbackItems: PortalItem[], limit: number): PortalItem[] {
  const seen = new Set<string>();
  const merged: PortalItem[] = [];
  for (const itemItem of [...primaryItems, ...fallbackItems]) {
    const key = itemItem.id || itemItem.title;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    merged.push(itemItem);
    if (merged.length >= limit) {
      break;
    }
  }
  return merged;
}

function createGenericSections(pageSummary: PageConfigSummary): PortalSection[] {
  if (pageSummary.pageKey === MARKETING_PAGE_KEY) {
    return createMarketingSections(pageSummary);
  }

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

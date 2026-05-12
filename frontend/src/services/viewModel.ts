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

export type GenerationSurface = 'portal' | 'workbench';

export interface NavItem {
  key: string;
  label: string;
  icon: string;
}

export interface ModelConfigSummary {
  id: string;
  tenantId?: string;
  modelKey: string;
  displayName: string;
  capability?: string;
  channelId?: string;
  channelKey?: string;
  channelName?: string;
  providerModel?: string;
  defaultPointCost?: number;
  enabled?: boolean;
  metadataJson?: Record<string, any>;
}

export interface ChatModelProfileSummary {
  channelKey: string;
  providerName: string;
  note: string;
  officialUrl: string;
  baseUrl: string;
  apiKey: string;
  modelName: string;
  modelKey: string;
  displayName: string;
  modelReasoningEffort: string;
  providerReasoningEffort: string;
  serviceTier: string;
  contextWindow: number;
  autoCompactTokenLimit: number;
  disableResponseStorage: boolean;
  defaultPointCost: number;
  timeoutSeconds: number;
  enabled: boolean;
}

export interface ChatModelProfilePayload {
  profile: ChatModelProfileSummary;
  provider: ProviderChannelSummary | null;
  modelConfig: ModelConfigSummary | null;
  authJson: string;
  configToml: string;
}

export interface ProviderChannelSummary {
  id: string;
  tenantId?: string;
  channelKey: string;
  displayName: string;
  baseUrl: string;
  apiKeyMask?: string;
  channelType: string;
  adapterType: string;
  priority: number;
  enabled: boolean;
  healthStatus?: string;
  timeoutSeconds?: number;
  metadataJson: Record<string, any>;
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
  effectivePointCost?: number;
  modelConfig?: ModelConfigSummary | null;
  metadata: Record<string, any>;
  menuKeys?: string[];
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

export interface HomeDashboardSlide {
  id: string;
  tenantId?: string;
  title: string;
  subtitle: string;
  badge: string;
  ctaLabel: string;
  ctaSubtitle: string;
  imageUrl: string;
  actionType: string;
  actionValue: string;
  sortOrder: number;
  enabled: boolean;
  metadata: Record<string, any>;
}

export interface HomeDashboardKpiCard {
  id: string;
  label: string;
  value: string;
  trend: string;
  icon: string;
  tone: string;
  actionType: string;
  actionValue: string;
}

export interface HomeDashboardModel {
  tenantId: string;
  page: PageConfigSummary;
  sections: PortalSection[];
  heroSlides: HomeDashboardSlide[];
  kpiCards: HomeDashboardKpiCard[];
  workbenchShortcuts: PortalItem[];
  communityCards: PortalItem[];
  toolCards: PortalItem[];
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
  effectivePointCost?: number;
  requiredMembership: boolean;
  actionValue: string;
  modelConfig?: ModelConfigSummary | null;
}

export interface PromptTemplate {
  id: string;
  title: string;
  category: string;
  content: string;
  requiredMembership: boolean;
  effectivePointCost?: number;
  modelConfig?: ModelConfigSummary | null;
}

export interface ToolModelBindingSummary {
  id: string;
  tenantId?: string;
  targetType: string;
  targetKey: string;
  modelConfigId: string;
  pointCostOverride?: number | null;
  effectivePointCost?: number | null;
  enabled: boolean;
  modelConfig?: ModelConfigSummary | null;
}

export interface AdminOverviewSummary {
  tenantId?: string;
  users: {
    total: number;
    active: number;
    admins: number;
  };
  membershipPlans: {
    total: number;
    enabled: number;
  };
  wallets: {
    totalBalance: number;
    frozenBalance: number;
  };
  content: {
    pages: number;
    sections: number;
    items: number;
  };
  models: {
    channels: number;
    modelConfigs: number;
    bindings: number;
  };
  recentLogs: AdminAuditLogSummary[];
}

export interface AdminUserSummary {
  id: string;
  tenantId?: string;
  phone: string;
  displayName: string;
  role: string;
  status: string;
  balance: number;
  frozenBalance: number;
  currency: string;
  membershipPlanId?: string | null;
  membershipPlanKey?: string | null;
  membershipPlanName?: string | null;
  membershipStatus?: string | null;
  membershipExpiresAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface AdminMembershipPlanSummary {
  id: string;
  tenantId?: string;
  planKey: string;
  name: string;
  priceCents: number;
  durationDays: number;
  entitlements: string[];
  enabled: boolean;
  sortOrder: number;
  activeUserCount: number;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface AdminUserMembershipSummary {
  id: string;
  tenantId?: string;
  userId: string;
  userDisplayName: string;
  userPhone: string;
  plan: AdminMembershipPlanSummary;
  status: string;
  startedAt?: string | null;
  expiresAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface AdminWalletTransactionSummary {
  id: string;
  tenantId?: string;
  userId: string;
  userDisplayName: string;
  requestKey: string;
  amount: number;
  balanceAfter: number;
  type: string;
  remark: string;
  relatedRef: string;
  createdAt?: string | null;
}

export interface AdminAuditLogSummary {
  id: string;
  tenantId?: string;
  actorUserId: string;
  actorDisplayName: string;
  actorRole: string;
  action: string;
  targetType: string;
  targetId: string;
  summary: string;
  createdAt?: string | null;
}

export interface AdminRedemptionBatchSummary {
  id: string;
  tenantId?: string;
  name: string;
  points: number;
  membershipPlanId?: string | null;
  membershipDays?: number | null;
  quantity: number;
  status: string;
  expiresAt?: string | null;
  generatedCount: number;
  redeemedCount: number;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface AdminRedemptionCodeSummary {
  id: string;
  tenantId?: string;
  batchId: string;
  code?: string;
  maskedCode: string;
  status: string;
  redeemedByUserId?: string | null;
  redeemedAt?: string | null;
  createdAt?: string | null;
}

export interface RedemptionResult {
  status: string;
  pointsGranted: number;
  wallet: AccountWallet;
  membership: MembershipSummary;
  accountSummary: AccountSummary;
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
  target_type?: string;
  target_id?: string;
  request_key?: string;
  surface?: GenerationSurface;
  options?: Record<string, unknown>;
}

export interface AudioTask {
  id: string;
  surface?: GenerationSurface;
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

export interface AccountUser {
  id: string;
  tenantId?: string;
  phone: string;
  displayName: string;
  role: string;
  status: string;
}

export interface AccountWallet {
  balance: number;
  frozenBalance: number;
  currency: string;
}

export interface MembershipSummary {
  active: boolean;
  plan: {
    id: string;
    planKey: string;
    name: string;
  } | null;
  expiresAt?: string | null;
  entitlements: string[];
}

export interface AccountSummary {
  user: AccountUser;
  wallet: AccountWallet;
  membership: MembershipSummary;
}

export interface RechargeOrder {
  id: string;
  tenantId?: string;
  userId: string;
  provider: string;
  providerOrderNo: string;
  requestKey: string;
  packageKey: string;
  amountCents: number;
  points: number;
  status: string;
  message: string;
  createdAt?: string | null;
  paidAt?: string | null;
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
  surface?: GenerationSurface;
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
  surface?: GenerationSurface;
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
  surface?: GenerationSurface;
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
  surface?: GenerationSurface;
  wallet: ImageWallet;
  route: ImageRoute;
  tasks: ImageTask[];
}

export interface ImageStatusMeta {
  label: string;
  progress: number;
  tone: 'pending' | 'processing' | 'success' | 'failed';
}

export interface ChatExportFile {
  id?: string;
  url: string;
  storageKey: string;
  fileName: string;
  size?: number;
}

export interface ChatMessage {
  id: string;
  tenantId?: string;
  sessionId?: string;
  role: string;
  content: string;
  sequence: number;
  createdAt?: string | null;
  export?: ChatExportFile | null;
}

export interface ChatSessionSummary {
  id: string;
  tenantId?: string;
  userId?: string;
  title: string;
  preview: string;
  presetRole: string;
  modelKey: string;
  status: string;
  messageCount: number;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface ChatActiveSession extends ChatSessionSummary {
  messages: ChatMessage[];
}

export interface ChatModelSummary {
  id: string;
  modelKey: string;
  displayName: string;
  providerModel?: string;
  defaultPointCost?: number;
  channelKey?: string;
}

export interface ChatWorkbench {
  tenantId: string;
  userId: string;
  sessions: ChatSessionSummary[];
  activeSession: ChatActiveSession | null;
  models: ChatModelSummary[];
}

export interface ChatSessionGroup {
  key: 'today' | 'yesterday' | 'thisWeek' | 'older';
  label: string;
  sessions: ChatSessionSummary[];
}

export interface ChatSendResult {
  session: ChatActiveSession;
  messagesCreated: ChatMessage[];
}

export interface ChatExportResult {
  asset: ChatExportFile;
  message: ChatMessage;
}

export interface PortalDetailAction {
  key: string;
  label: string;
}

export interface PortalDetailDownload {
  fileName: string;
  url: string;
  storageKey?: string;
}

export interface PortalDetailFaq {
  question: string;
  answer: string;
}

export interface PortalDetailVersion {
  id: string;
  version: number;
  title: string;
  summary: string;
  bodyMarkdown: string;
  tags: string[];
  visibility: string;
  releaseNote: string;
  authorUserId: string;
  createdAt: string | null;
}

export interface PortalDetailComment {
  id: string;
  detailPath: string;
  userId: string;
  authorName: string;
  content: string;
  isAuthor: boolean;
  createdAt: string | null;
}

export interface PortalDetailPublishInfo {
  typeLabel: string;
  typeHint: string;
  versionLabel: string;
  versionHint: string;
  visibility: string;
  visibilityLabel: string;
  visibilityHint: string;
}

export interface PortalDetailContent {
  summary: string;
  highlights: string[];
  steps: string[];
  deliverables: string[];
  faqs: PortalDetailFaq[];
  primaryAction: PortalDetailAction;
  secondaryActions: PortalDetailAction[];
  download?: PortalDetailDownload | null;
  title: string;
  bodyMarkdown: string;
  tags: string[];
  visibility: string;
  authorUserId: string;
  currentVersion: number;
  version: PortalDetailVersion | null;
  versions: PortalDetailVersion[];
  comments: PortalDetailComment[];
  publishInfo: PortalDetailPublishInfo;
}

export interface PortalDetailUserState {
  membershipActive: boolean;
  locked: boolean;
  completedActions: string[];
}

export interface PortalDetailPayload {
  path: string;
  kind: string;
  title: string;
  subtitle: string;
  icon: string;
  requiredMembership: boolean;
  effectivePointCost: number;
  items: PortalItem[];
  detail: PortalDetailContent;
  userState: PortalDetailUserState;
  permissions: {
    canEdit: boolean;
    canComment: boolean;
  };
}

export interface PortalActionRequest {
  userId: string;
  detailPath: string;
  itemId?: string;
  actionKey: string;
}

export interface UserPortalAction {
  id: string;
  tenantId?: string;
  userId?: string;
  detailPath: string;
  itemId?: string;
  actionKey: string;
  status: string;
  message: string;
  result?: Record<string, any>;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface PortalActionResult {
  status: string;
  message: string;
  action: UserPortalAction | null;
  download?: PortalDetailDownload | null;
  route?: string | null;
}

export interface PortalSearchResult {
  id: string;
  title: string;
  subtitle: string;
  type: string;
  pageKey: string;
  path: string;
  icon: string;
}

export interface WorkbenchCapability {
  id: string;
  group: 'chat' | 'image' | 'video' | 'audio' | string;
  targetType: string;
  targetKey: string;
  title: string;
  subtitle: string;
  category: string;
  icon: string;
  actionType: string;
  actionValue: string;
  sortOrder: number;
  enabled: boolean;
  callable: boolean;
  unavailableReason: string;
  requiredMembership: boolean;
  effectivePointCost: number;
  modelConfig?: ModelConfigSummary | null;
}

export interface WorkbenchCapabilitiesPayload {
  tenantId: string;
  surface: GenerationSurface;
  capabilities: WorkbenchCapability[];
  groups: Record<string, WorkbenchCapability[]>;
}

const fallbackPages: PageConfigSummary[] = [
  page('home', '首页', '常用AI学习中心', '学习、接单、社群和活动的统一入口', 'Home', 10),
  page('assistant', 'AI 助理', '智能助理广场', '办公、营销、学习、法务等场景助理集合', 'Bot', 20),
  page('workbench', '工作台', 'AI 工作台', '真实对话、队列和快捷操作的统一工作区', 'LayoutDashboard', 25),
  page('communication', '沟通大厅', '沟通大厅', '接单、模板、交流、资源对接都在这里沉淀', 'MessageCircle', 27),
  page('marketing', 'AI 营销', '营销增长中心', '从内容生成到投放复盘的一站式工具台', 'Megaphone', 30),
  page('image', 'AI 图片', 'AI图片创作中心', '提示词、模板、批量出图和生成队列', 'Image', 35),
  page('video', 'AI 视频', 'AI视频创作中心', '脚本、数字人、剪辑、字幕和渲染队列', 'FileVideo', 40),
  page('audio', 'AI 音频', 'AI音频创作中心', '配音、转写、降噪、播客和音色库', 'Headphones', 50),
  page('coding', 'AI 编程', 'AI编程工作台', '代码生成、审查、测试和自动化脚本', 'Workflow', 60),
  page('writing', 'AI 写作', 'AI写作中心', '文章、报告、简历、论文和提示词模板', 'Feather', 70),
  page('ecommerce', 'AI 电商', 'AI电商运营中心', '商品内容、客服话术、店铺分析和素材生成', 'WandSparkles', 80),
  page('legal', 'AI 法务', 'AI法务服务台', '合同审查、法律咨询、证据整理和文书草拟', 'Scale', 90),
  page('office', 'AI 办公', 'AI办公效率中心', 'PPT、表格、会议、邮件和流程自动化', 'BriefcaseBusiness', 100)
];

const DEFAULT_HOME_MENU_KEY = 'basic';
const HOME_PAGE_KEY = 'home';
export const HOME_PROMO_CAROUSEL_LAYOUT = 'promo-carousel';
const MARKETING_PAGE_KEY = 'marketing';
const IMAGE_PAGE_KEY = 'image';
const AUDIO_PAGE_KEY = 'audio';
const VIDEO_PAGE_KEY = 'video';
const CODING_PAGE_KEY = 'coding';
const WRITING_PAGE_KEY = 'writing';
const WORKBENCH_PAGE_KEY = 'workbench';
const COMMUNICATION_PAGE_KEY = 'communication';

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
    subtitle: '模板列表、行业工具、效率组件和第三方下载入口',
    icon: 'BriefcaseBusiness',
    hint: '模板排行',
    sectionKeys: ['third_party_tools', 'banners', 'toolkit', 'template_ranking'],
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
  return pageKey === HOME_PAGE_KEY;
}

export function shouldUseHomeDashboardPage(pageKey: string, menuKey = DEFAULT_HOME_MENU_KEY): boolean {
  return pageKey === HOME_PAGE_KEY && menuKey === DEFAULT_HOME_MENU_KEY;
}

export function shouldUseAssistantPage(pageKey: string): boolean {
  return pageKey === 'assistant';
}

export function shouldUseWorkbenchPage(pageKey: string): boolean {
  return pageKey === WORKBENCH_PAGE_KEY;
}

export function shouldUseCommunicationPage(pageKey: string): boolean {
  return pageKey === COMMUNICATION_PAGE_KEY;
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

export function shouldUseCodingPage(pageKey: string): boolean {
  return pageKey === CODING_PAGE_KEY;
}

export function shouldUseWritingPage(pageKey: string): boolean {
  return pageKey === WRITING_PAGE_KEY;
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
  sourceUrl = '',
  surface: GenerationSurface = 'portal'
): AudioTaskPayload {
  const metadata = selectedTool.metadata ?? {};
  const routeKey = String(metadata.routeKey ?? metadata.route_key ?? selectedTool.actionValue ?? '');
  const targetType = String(metadata.targetType ?? metadata.target_type ?? 'builtin');
  const targetId = String(metadata.targetKey ?? metadata.target_key ?? selectedTool.actionValue ?? selectedTool.id);
  return {
    task_type: audioTaskTypeForRoute(routeKey),
    route_key: routeKey,
    prompt,
    source_url: sourceUrl,
    voice_key: selectedVoice?.actionValue ?? '',
    target_type: targetType,
    target_id: targetId,
    surface,
    options: {
      ...(sourceUrl ? { source_url: sourceUrl } : {}),
      ...(selectedVoice?.actionValue ? { voice: selectedVoice.actionValue } : {})
    }
  };
}

export function shouldUseVideoPage(pageKey: string): boolean {
  return pageKey === VIDEO_PAGE_KEY;
}

export function shouldHideWorkspaceDock(pageKey: string): boolean {
  return shouldUseHomeDashboardPage(pageKey) || shouldUseCommunicationPage(pageKey) || shouldUseCodingPage(pageKey) || shouldUseWritingPage(pageKey);
}

export function groupChatSessionsByRecency(
  sessions: ChatSessionSummary[],
  referenceDate: string | Date = new Date()
): ChatSessionGroup[] {
  const reference = startOfDay(new Date(referenceDate));
  const buckets: ChatSessionGroup[] = [
    { key: 'today', label: '今天', sessions: [] },
    { key: 'yesterday', label: '昨天', sessions: [] },
    { key: 'thisWeek', label: '本周', sessions: [] },
    { key: 'older', label: '更早', sessions: [] }
  ];

  sessions.forEach((session) => {
    const activityAt = new Date(session.updatedAt ?? session.createdAt ?? 0);
    const diffDays = Math.floor((reference.getTime() - startOfDay(activityAt).getTime()) / 86400000);
    if (diffDays <= 0) {
      buckets[0].sessions.push(session);
    } else if (diffDays === 1) {
      buckets[1].sessions.push(session);
    } else if (diffDays <= 6) {
      buckets[2].sessions.push(session);
    } else {
      buckets[3].sessions.push(session);
    }
  });

  return buckets.filter((group) => group.sessions.length > 0);
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
    .filter((sectionItem): sectionItem is PortalSection => Boolean(sectionItem))
    .sort((left, right) => homeSectionOrder(left, rule) - homeSectionOrder(right, rule));

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

export function buildHomeDashboardModel(
  pageConfig: PortalPageConfig,
  dashboard: HomeDashboardModel | null = null
): HomeDashboardModel {
  const fallback = createFallbackHomeDashboard(pageConfig);
  const source = dashboard ?? fallback;
  const sectionWorkbenchShortcuts = homeItemsFromSections(pageConfig, ['workbench_shortcuts', 'workspace_tools', 'task_board'], 6);
  const sectionCommunityCards = homeItemsFromSections(pageConfig, ['communities', 'resource_hub'], 4);
  const sectionToolCards = homeItemsFromSections(pageConfig, ['home_tools', 'toolkit', 'earning_templates', 'project_cocreation'], 5);
  return {
    tenantId: source.tenantId || pageConfig.tenantId,
    page: source.page?.pageKey ? source.page : pageConfig.page,
    sections: pageConfig.sections,
    heroSlides: source.heroSlides.length > 0 ? source.heroSlides : fallback.heroSlides,
    kpiCards: source.kpiCards.length > 0 ? source.kpiCards : fallback.kpiCards,
    workbenchShortcuts:
      source.workbenchShortcuts.length > 0
        ? source.workbenchShortcuts
        : sectionWorkbenchShortcuts.length > 0
          ? sectionWorkbenchShortcuts
          : fallback.workbenchShortcuts,
    communityCards:
      source.communityCards.length > 0
        ? source.communityCards
        : sectionCommunityCards.length > 0
          ? sectionCommunityCards
          : fallback.communityCards,
    toolCards:
      source.toolCards.length > 0
        ? source.toolCards
        : sectionToolCards.length > 0
          ? sectionToolCards
          : fallback.toolCards
  };
}

function homeItemsFromSections(pageConfig: PortalPageConfig, sectionKeys: string[], limit: number): PortalItem[] {
  const items: PortalItem[] = [];
  const seen = new Set<string>();
  const sections = pageConfig.sections
    .filter((sectionItem) => sectionKeys.includes(sectionItem.sectionKey) && sectionItem.enabled)
    .sort((left, right) => left.sortOrder - right.sortOrder);

  for (const sectionItem of sections) {
    const sectionItems = [...sectionItem.items]
      .filter((itemItem) => itemItem.enabled)
      .sort((left, right) => left.sortOrder - right.sortOrder);
    for (const itemItem of sectionItems) {
      const key = itemItem.id || itemItem.title;
      if (seen.has(key)) {
        continue;
      }
      seen.add(key);
      items.push(itemItem);
      if (items.length >= limit) {
        return items;
      }
    }
  }

  return items;
}

export function createFallbackHomeDashboard(pageConfig: PortalPageConfig = createFallbackPageConfig(HOME_PAGE_KEY)): HomeDashboardModel {
  const page = pageConfig.page.pageKey === HOME_PAGE_KEY ? pageConfig.page : createFallbackPageConfig(HOME_PAGE_KEY).page;
  const workbenchShortcuts = [
    withMenuKeys(item('home-workbench-chat', 'tool', 'AI 对话', '写作、问答和方案梳理', '应用工作台', 'Bot', '/workbench', false, 0), ['workspace']),
    withMenuKeys(item('home-workbench-image', 'tool', '图片生成', '海报、封面和详情图', '应用工作台', 'Image', '/workbench/image', false, 0), ['workspace']),
    withMenuKeys(item('home-workbench-video', 'tool', '视频脚本', '选题、分镜和口播脚本', '应用工作台', 'MonitorPlay', '/workbench/video', false, 0), ['workspace']),
    withMenuKeys(item('home-workbench-ppt', 'tool', 'PPT 办公', '大纲到页面快速生成', '应用工作台', 'Presentation', '/workspace/ppt', false, 0), ['workspace']),
    withMenuKeys(item('home-workbench-delivery', 'tool', '接单交付', '报价、交付和复购跟进', '接单变现', 'BriefcaseBusiness', '/workspace/deliveries', false, 0), ['orders']),
    withMenuKeys(item('home-workbench-assets', 'tool', '素材库', '图片、模板和提示词资产', '应用工作台', 'CloudUpload', '/workspace/assets', false, 0), ['resources', 'workspace'])
  ];
  const communityCards = [
    withMenuKeys(item('home-community-starter', 'community', '入门交流群', '新人答疑、工具清单和上手路线', '社群', 'MessageCircle', '/community/starter', false, 0), ['basic', 'growth']),
    withMenuKeys(item('home-community-study', 'community', '学习打卡群', '每日任务、案例拆解和作业反馈', '学习成长', 'GraduationCap', '/community/study', true, 0), ['growth']),
    withMenuKeys(item('home-community-orders', 'community', '接单变现群', '接单案例、报价模板和交付流程', '接单变现', 'Handshake', '/community/orders', true, 0), ['orders']),
    withMenuKeys(item('home-community-resources', 'community', '资源对接群', '工具资源、客户线索和行业资料交换', '资源对接', 'Network', '/community/resources', true, 0), ['resources', 'toolkit'])
  ];
  const toolCards = [
    withMenuKeys(item('home-tool-common', 'template', '常用工具', '高频 AI 工具入口集合', '工作台', 'LayoutGrid', '/workbench', false, 0), ['basic', 'workspace']),
    withMenuKeys(item('home-tool-office', 'template', '办公模板', 'PPT、表格和会议纪要模板', '工具框', 'Presentation', '/toolkit/office', true, 0), ['workspace', 'toolkit']),
    withMenuKeys(item('home-tool-quote', 'template', '接单报价', '报价、验收和复购话术', '接单变现', 'ReceiptText', '/templates/quote', true, 0), ['orders']),
    withMenuKeys(item('home-tool-copy', 'template', '内容生成', '文案、脚本和社媒内容', '增长', 'Feather', '/marketing', false, 0), ['growth', 'orders']),
    withMenuKeys(item('home-tool-ecommerce', 'template', '电商优化', '标题、详情页和客服话术', '电商', 'WandSparkles', '/workspace/ecommerce', true, 0), ['orders', 'resources'])
  ];

  return {
    tenantId: pageConfig.tenantId || 'demo',
    page,
    sections: pageConfig.sections,
    heroSlides: [
      {
        id: 'home-slide-vip',
        title: '会员活动限时特惠',
        subtitle: '开通会员解锁模板、社群和交付资料',
        badge: '会员专享',
        ctaLabel: '立即开通',
        ctaSubtitle: '查看权益，不走支付',
        imageUrl: '',
        actionType: 'route',
        actionValue: '/membership/benefits',
        sortOrder: 10,
        enabled: true,
        metadata: { accent: 'gold', theme: 'vip' }
      },
      {
        id: 'home-slide-template',
        title: '模板上新不停',
        subtitle: 'PPT、报价单、社媒和交付模板持续更新',
        badge: '今日上新',
        ctaLabel: '立即查看',
        ctaSubtitle: '今天就能直接用',
        imageUrl: '',
        actionType: 'route',
        actionValue: '/templates',
        sortOrder: 20,
        enabled: true,
        metadata: { accent: 'blue', theme: 'template' }
      },
      {
        id: 'home-slide-community',
        title: '社群和工作台一起用',
        subtitle: '入门群、打卡群、接单群和资源群都在这里',
        badge: '社群活跃',
        ctaLabel: '进入社群',
        ctaSubtitle: '打开首页就能直达',
        imageUrl: '',
        actionType: 'route',
        actionValue: '/community/starter',
        sortOrder: 30,
        enabled: true,
        metadata: { accent: 'green', theme: 'community' }
      }
    ],
    kpiCards: [
      { id: 'today-new', label: '今日上新', value: '3', trend: '模板与活动持续更新', icon: 'Sparkles', tone: 'blue', actionType: 'route', actionValue: '/templates' },
      { id: 'vip-exclusive', label: '会员专享', value: '18', trend: '权益与内容已就绪', icon: 'Crown', tone: 'gold', actionType: 'route', actionValue: '/membership/benefits' },
      { id: 'todo-task', label: '待办任务', value: '6', trend: '继续处理工作台任务', icon: 'CheckSquare', tone: 'orange', actionType: 'route', actionValue: '/workbench' },
      { id: 'community-active', label: '社群活跃', value: '32', trend: '社群与工具持续补充', icon: 'Users', tone: 'green', actionType: 'route', actionValue: '/community/starter' }
    ],
    workbenchShortcuts,
    communityCards,
    toolCards
  };
}

function withMenuKeys(itemItem: PortalItem, menuKeys: string[]): PortalItem {
  return {
    ...itemItem,
    menuKeys,
    metadata: { ...itemItem.metadata, menuKeys }
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
    surface: 'workbench',
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
    surface: 'workbench',
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

export function createFallbackChatWorkbench(): ChatWorkbench {
  const sessions: ChatSessionSummary[] = [
    {
      id: 'chat-demo-weekly',
      tenantId: 'demo',
      userId: 'demo-user',
      title: '项目周报整理',
      preview: '已生成并附上 Markdown 文件，请查看。',
      presetRole: '通用助手',
      modelKey: 'general_text_default',
      status: 'ACTIVE',
      messageCount: 6,
      createdAt: '2026-05-10T14:20:00',
      updatedAt: '2026-05-10T14:35:00'
    },
    {
      id: 'chat-demo-polish',
      tenantId: 'demo',
      userId: 'demo-user',
      title: '文案润色',
      preview: '可以进一步强化标题里的行动感。',
      presetRole: '通用助手',
      modelKey: 'general_text_default',
      status: 'ACTIVE',
      messageCount: 4,
      createdAt: '2026-05-09T10:12:00',
      updatedAt: '2026-05-09T10:21:00'
    },
    {
      id: 'chat-demo-meeting',
      tenantId: 'demo',
      userId: 'demo-user',
      title: '会议纪要总结',
      preview: '已按议题、决策和行动项整理。',
      presetRole: '通用助手',
      modelKey: 'general_text_default',
      status: 'ACTIVE',
      messageCount: 5,
      createdAt: '2026-05-07T16:45:00',
      updatedAt: '2026-05-07T16:45:00'
    },
    {
      id: 'chat-demo-demand',
      tenantId: 'demo',
      userId: 'demo-user',
      title: '产品需求梳理',
      preview: '建议把导出和权限边界拆成两个验收点。',
      presetRole: '通用助手',
      modelKey: 'general_text_default',
      status: 'ACTIVE',
      messageCount: 3,
      createdAt: '2026-05-03T09:18:00',
      updatedAt: '2026-05-03T09:18:00'
    }
  ];
  const activeSession: ChatActiveSession = {
    ...sessions[0],
    messages: [
      {
        id: 'chat-demo-msg-1',
        tenantId: 'demo',
        sessionId: sessions[0].id,
        role: 'user',
        content: '请帮我整理本周项目的进展情况，做一份简要的周报。',
        sequence: 1,
        createdAt: '2026-05-10T14:32:00'
      },
      {
        id: 'chat-demo-msg-2',
        tenantId: 'demo',
        sessionId: sessions[0].id,
        role: 'assistant',
        content: '好的，以下是本周项目进展周报（简要版）：\n\n1. 需求分析：已完成需求澄清，与产品、设计确认核心流程。\n2. 设计进度：完成高保真原型设计，已提交评审并收到反馈。\n3. 开发进度：完成后端接口开发，前端页面完成 3 个核心模块。\n4. 测试进度：完成接口联调测试，发现并修复 12 个问题。\n5. 下周计划：完成剩余接口联调、推进前端模块开发、开展功能测试与性能优化。',
        sequence: 2,
        createdAt: '2026-05-10T14:33:00'
      },
      {
        id: 'chat-demo-msg-3',
        tenantId: 'demo',
        sessionId: sessions[0].id,
        role: 'user',
        content: '请再帮我提炼 3 条需要重点关注的风险点。',
        sequence: 3,
        createdAt: '2026-05-10T14:34:00'
      },
      {
        id: 'chat-demo-msg-4',
        tenantId: 'demo',
        sessionId: sessions[0].id,
        role: 'assistant',
        content: '好的，以下是需要重点关注的风险点：\n\n1. 接口依赖风险：部分接口依赖第三方服务，存在响应不稳定的风险。\n2. 时间进度风险：部分模块开发进度略有延迟，可能影响整体上线时间。\n3. 测试覆盖风险：自动化测试用例覆盖率不足，可能导致回归问题。',
        sequence: 4,
        createdAt: '2026-05-10T14:34:00'
      },
      {
        id: 'chat-demo-msg-5',
        tenantId: 'demo',
        sessionId: sessions[0].id,
        role: 'user',
        content: '请把周报内容导出为 Markdown 格式。',
        sequence: 5,
        createdAt: '2026-05-10T14:35:00'
      },
      {
        id: 'chat-demo-msg-6',
        tenantId: 'demo',
        sessionId: sessions[0].id,
        role: 'assistant',
        content: '已生成并附上 Markdown 文件，请查看。',
        sequence: 6,
        createdAt: '2026-05-10T14:35:00',
        export: {
          id: 'asset-demo-markdown',
          url: '/storage/exports/demo/project-weekly-report.md',
          storageKey: 'exports/demo/project-weekly-report.md',
          fileName: '项目周报_2026-05-10.md',
          size: 12700
        }
      }
    ]
  };

  return {
    tenantId: 'demo',
    userId: 'demo-user',
    sessions,
    activeSession,
    models: [
      {
        id: 'model-general-text-default',
        modelKey: 'general_text_default',
        displayName: 'GPT-4.1',
        providerModel: 'demo-general-text',
        defaultPointCost: 10,
        channelKey: 'demo-general-text'
      }
    ]
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
      section('section-orders', 'home', 'order_center', '新商机 接单中心', 'order-grid', [
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
        item('workspace-00', 'tool', 'AI 工作台', '真实对话、图像、视频和音频任务统一入口', '应用工作台', 'LayoutGrid', '/workbench', false, 0),
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
      section('section-third-party-tools', 'home', 'third_party_tools', '第三方工具展示区', 'third-party-tools', [
        thirdPartyTool('third-tool-jianying', '剪映专业版', '视频剪辑与模板包装', '视频', 'JY', 'https://example.com/tools/jianying', 'https://example.com/downloads/jianying'),
        thirdPartyTool('third-tool-feishu', '飞书多维表格', '项目表格与团队协作', '办公', 'FS', 'https://example.com/tools/feishu-base', 'https://example.com/downloads/feishu'),
        thirdPartyTool('third-tool-meeting', '腾讯会议', '远程沟通与交付复盘', '协作', 'TX', 'https://example.com/tools/meeting', 'https://example.com/downloads/meeting'),
        thirdPartyTool('third-tool-apifox', 'Apifox', '接口调试与接口文档', '开发', 'AP', 'https://example.com/tools/apifox', 'https://example.com/downloads/apifox')
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
          : createGenericSections(pageSummary)
  };
}

export function createFallbackAudioWorkbenchPageConfig(): PortalPageConfig {
  return {
    tenantId: 'demo',
    page: page('workbench-audio', '音频生成', '音频生成工作台', '提示词、波形编辑、转写片段和导出设置', 'Headphones', 1),
    sections: createFallbackAudioSections()
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
  const normalizedPages = (payload.pages ?? []).map(normalizePageSummary);
  const normalizedChannels = Array.isArray(payload.channels)
    ? payload.channels.map(normalizePortalChannel)
    : normalizedPages.map((pageItem: PageConfigSummary) => ({ key: pageItem.pageKey, label: pageItem.label }));
  const shouldPatchCommunication = hasPortalKey(normalizedPages, normalizedChannels, WORKBENCH_PAGE_KEY);
  const pages = shouldPatchCommunication ? ensureCommunicationPage(normalizedPages) : normalizedPages;
  const channels = shouldPatchCommunication
    ? ensureCommunicationChannel(normalizedChannels.length > 0 ? normalizedChannels : pages.map((pageItem: PageConfigSummary) => ({ key: pageItem.pageKey, label: pageItem.label })))
    : normalizedChannels;
  return {
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    pages,
    channels,
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

export function normalizeHomeDashboard(payload: any): HomeDashboardModel {
  const fallback = createFallbackHomeDashboard();
  const normalized: HomeDashboardModel = {
    tenantId: payload.tenant_id ?? payload.tenantId ?? fallback.tenantId,
    page: normalizePageSummary(payload.page ?? fallback.page),
    sections: (payload.sections ?? []).map(normalizeSection),
    heroSlides: (payload.hero_slides ?? payload.heroSlides ?? []).map(normalizeHomeDashboardSlide),
    kpiCards: (payload.kpi_cards ?? payload.kpiCards ?? []).map(normalizeHomeDashboardKpiCard),
    workbenchShortcuts: (payload.workbench_shortcuts ?? payload.workbenchShortcuts ?? []).map(normalizePortalItem),
    communityCards: (payload.community_cards ?? payload.communityCards ?? []).map(normalizePortalItem),
    toolCards: (payload.tool_cards ?? payload.toolCards ?? []).map(normalizePortalItem)
  };
  return buildHomeDashboardModel(
    {
      tenantId: normalized.tenantId,
      page: normalized.page,
      sections: normalized.sections
    },
    normalized
  );
}

export function normalizeHomeDashboardSlide(payload: any): HomeDashboardSlide {
  return {
    id: payload.id ?? '',
    tenantId: payload.tenant_id ?? payload.tenantId,
    title: payload.title ?? '',
    subtitle: payload.subtitle ?? '',
    badge: payload.badge ?? '',
    ctaLabel: payload.cta_label ?? payload.ctaLabel ?? '立即查看',
    ctaSubtitle: payload.cta_subtitle ?? payload.ctaSubtitle ?? '',
    imageUrl: payload.image_url ?? payload.imageUrl ?? '',
    actionType: payload.action_type ?? payload.actionType ?? 'route',
    actionValue: payload.action_value ?? payload.actionValue ?? '',
    sortOrder: Number(payload.sort_order ?? payload.sortOrder ?? 100),
    enabled: Boolean(payload.enabled ?? true),
    metadata: normalizeMetadata(payload.metadata_json ?? payload.metadataJson ?? payload.metadata)
  };
}

export function normalizeHomeDashboardKpiCard(payload: any): HomeDashboardKpiCard {
  return {
    id: payload.id ?? '',
    label: payload.label ?? '',
    value: String(payload.value ?? ''),
    trend: payload.trend ?? '',
    icon: payload.icon ?? 'Sparkles',
    tone: payload.tone ?? 'blue',
    actionType: payload.action_type ?? payload.actionType ?? 'route',
    actionValue: payload.action_value ?? payload.actionValue ?? ''
  };
}

export function normalizeAssistantCenter(payload: any): AssistantCenter {
  const assistants = (payload.assistants ?? []).map(normalizeAssistant);
  return {
    categories: payload.categories ?? [],
    featured: (payload.featured ?? []).map(normalizeAssistant),
    assistants,
    ranking: (payload.ranking ?? buildAssistantRanking(assistants)).map(normalizeAssistant),
    promptTemplates: (payload.prompt_templates ?? payload.promptTemplates ?? []).map(normalizePromptTemplate)
  };
}

export function normalizeChatWorkbench(payload: any): ChatWorkbench {
  const activePayload = payload.active_session ?? payload.activeSession ?? null;
  const activeSession = activePayload ? normalizeChatActiveSession(activePayload) : null;
  const sessions = (payload.sessions ?? []).map(normalizeChatSessionSummary);
  return {
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    userId: payload.user_id ?? payload.userId ?? 'demo-user',
    sessions: sessions.length > 0 || !activeSession ? sessions : [activeSession],
    activeSession,
    models: (payload.models ?? []).map(normalizeChatModel)
  };
}

export function normalizeChatSessionSummary(payload: any): ChatSessionSummary {
  return {
    id: payload.id ?? '',
    tenantId: payload.tenant_id ?? payload.tenantId,
    userId: payload.user_id ?? payload.userId,
    title: payload.title || '新对话',
    preview: payload.preview ?? '',
    presetRole: payload.preset_role ?? payload.presetRole ?? 'assistant',
    modelKey: payload.model_key ?? payload.modelKey ?? 'general_text_default',
    status: payload.status ?? 'ACTIVE',
    messageCount: Number(payload.message_count ?? payload.messageCount ?? payload.messages?.length ?? 0),
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? payload.created_at ?? payload.createdAt ?? null
  };
}

export function normalizeChatActiveSession(payload: any): ChatActiveSession {
  const summary = normalizeChatSessionSummary(payload);
  return {
    ...summary,
    messages: (payload.messages ?? []).map(normalizeChatMessage)
  };
}

export function normalizeChatMessage(payload: any): ChatMessage {
  return {
    id: payload.id ?? '',
    tenantId: payload.tenant_id ?? payload.tenantId,
    sessionId: payload.session_id ?? payload.sessionId,
    role: payload.role ?? 'assistant',
    content: payload.content ?? '',
    sequence: Number(payload.sequence ?? 0),
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    export: normalizeChatExportFile(payload.export ?? payload.asset)
  };
}

export function normalizeChatSendResult(payload: any): ChatSendResult {
  return {
    session: normalizeChatActiveSession(payload.session ?? payload.active_session ?? {}),
    messagesCreated: (payload.messages_created ?? payload.messagesCreated ?? []).map(normalizeChatMessage)
  };
}

export function normalizeChatExportResult(payload: any): ChatExportResult {
  const asset = normalizeChatExportFile(payload.asset) ?? {
    url: '',
    storageKey: '',
    fileName: ''
  };
  return {
    asset,
    message: normalizeChatMessage({
      ...(payload.message ?? {}),
      export: payload.message?.export ?? asset
    })
  };
}

export function normalizeChatExportFile(payload: any): ChatExportFile | null {
  if (!payload) {
    return null;
  }
  return {
    id: payload.id,
    url: payload.url ?? '',
    storageKey: payload.storage_key ?? payload.storageKey ?? '',
    fileName: payload.file_name ?? payload.fileName ?? payload.title ?? '',
    size: payload.size == null ? undefined : Number(payload.size)
  };
}

function normalizeChatModel(payload: any): ChatModelSummary {
  return {
    id: payload.id ?? payload.model_key ?? payload.modelKey ?? '',
    modelKey: payload.model_key ?? payload.modelKey ?? 'general_text_default',
    displayName: payload.display_name ?? payload.displayName ?? 'GPT-4.1',
    providerModel: payload.provider_model ?? payload.providerModel,
    defaultPointCost: Number(payload.default_point_cost ?? payload.defaultPointCost ?? 0),
    channelKey: payload.channel_key ?? payload.channelKey
  };
}

export function normalizeVideoWorkbench(payload: any): VideoWorkbench {
  return {
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    userId: payload.user_id ?? payload.userId ?? 'demo-user',
    surface: normalizeGenerationSurface(payload.surface ?? payload.surfaceKey ?? 'portal'),
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
    surface: normalizeGenerationSurface(payload.surface ?? payload.surfaceKey ?? 'portal'),
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
    surface: normalizeGenerationSurface(payload.surface ?? payload.surfaceKey ?? 'portal'),
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

export function normalizeWorkbenchCapabilities(payload: any): WorkbenchCapabilitiesPayload {
  const capabilities = (payload.capabilities ?? []).map(normalizeWorkbenchCapability);
  const rawGroups = payload.groups ?? {};
  const groups: Record<string, WorkbenchCapability[]> = {};
  for (const [key, records] of Object.entries(rawGroups)) {
    groups[key] = Array.isArray(records) ? records.map(normalizeWorkbenchCapability) : [];
  }
  for (const capability of capabilities) {
    if (!groups[capability.group]) {
      groups[capability.group] = [];
    }
    if (!groups[capability.group].some((item) => item.id === capability.id)) {
      groups[capability.group].push(capability);
    }
  }
  return {
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    surface: normalizeGenerationSurface(payload.surface ?? payload.surfaceKey ?? 'workbench'),
    capabilities,
    groups: {
      chat: groups.chat ?? [],
      image: groups.image ?? [],
      video: groups.video ?? [],
      audio: groups.audio ?? [],
      ...groups
    }
  };
}

export function normalizeWorkbenchCapability(payload: any): WorkbenchCapability {
  return {
    id: payload.id ?? payload.target_key ?? payload.targetKey ?? '',
    group: payload.group ?? 'chat',
    targetType: payload.target_type ?? payload.targetType ?? '',
    targetKey: payload.target_key ?? payload.targetKey ?? '',
    title: payload.title ?? '',
    subtitle: payload.subtitle ?? '',
    category: payload.category ?? '',
    icon: payload.icon ?? 'Sparkles',
    actionType: payload.action_type ?? payload.actionType ?? 'workspace',
    actionValue: payload.action_value ?? payload.actionValue ?? '',
    sortOrder: Number(payload.sort_order ?? payload.sortOrder ?? 100),
    enabled: Boolean(payload.enabled ?? false),
    callable: Boolean(payload.callable ?? false),
    unavailableReason: payload.unavailable_reason ?? payload.unavailableReason ?? '',
    requiredMembership: Boolean(payload.required_membership ?? payload.requiredMembership ?? false),
    effectivePointCost: Number(payload.effective_point_cost ?? payload.effectivePointCost ?? 0),
    modelConfig: normalizeModelConfig(payload.model_config ?? payload.modelConfig)
  };
}

function homeSectionOrder(sectionItem: PortalSection, rule: HomeMenuRule): number {
  const index = rule.sectionKeys.indexOf(sectionItem.sectionKey);
  return index === -1 ? Number.MAX_SAFE_INTEGER : index;
}

export function normalizeAccountSummary(payload: any): AccountSummary {
  return {
    user: normalizeAccountUser(payload.user ?? {}),
    wallet: {
      balance: Number(payload.wallet?.balance ?? 0),
      frozenBalance: Number(payload.wallet?.frozen_balance ?? payload.wallet?.frozenBalance ?? 0),
      currency: payload.wallet?.currency ?? 'POINT'
    },
    membership: normalizeMembershipSummary(payload.membership ?? {})
  };
}

export function normalizeAccountUser(payload: any): AccountUser {
  return {
    id: payload.id ?? 'demo-user',
    tenantId: payload.tenant_id ?? payload.tenantId,
    phone: payload.phone ?? '',
    displayName: payload.display_name ?? payload.displayName ?? '演示用户',
    role: payload.role ?? 'USER',
    status: payload.status ?? 'ACTIVE'
  };
}

export function normalizeMembershipSummary(payload: any): MembershipSummary {
  const planPayload = payload.plan ?? null;
  return {
    active: Boolean(payload.active),
    plan: planPayload
      ? {
          id: planPayload.id ?? '',
          planKey: planPayload.plan_key ?? planPayload.planKey ?? '',
          name: planPayload.name ?? ''
        }
      : null,
    expiresAt: payload.expires_at ?? payload.expiresAt ?? null,
    entitlements: payload.entitlements ?? []
  };
}

export function normalizeRechargeOrder(payload: any): RechargeOrder {
  return {
    id: payload.id ?? '',
    tenantId: payload.tenant_id ?? payload.tenantId,
    userId: payload.user_id ?? payload.userId ?? 'demo-user',
    provider: payload.provider ?? '',
    providerOrderNo: payload.provider_order_no ?? payload.providerOrderNo ?? '',
    requestKey: payload.request_key ?? payload.requestKey ?? '',
    packageKey: payload.package_key ?? payload.packageKey ?? '',
    amountCents: Number(payload.amount_cents ?? payload.amountCents ?? 0),
    points: Number(payload.points ?? 0),
    status: payload.status ?? '',
    message: payload.message ?? '',
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    paidAt: payload.paid_at ?? payload.paidAt ?? null
  };
}

export function normalizePortalDetail(payload: any): PortalDetailPayload {
  const effectivePointCostValue = payload.effective_point_cost ?? payload.effectivePointCost;
  return {
    path: payload.path ?? '/',
    kind: payload.kind ?? 'single',
    title: payload.title ?? '',
    subtitle: payload.subtitle ?? '',
    icon: payload.icon ?? 'Sparkles',
    requiredMembership: Boolean(payload.required_membership ?? payload.requiredMembership),
    effectivePointCost: effectivePointCostValue == null ? 0 : Number(effectivePointCostValue),
    items: (payload.items ?? []).map(normalizePortalItem),
    detail: normalizePortalDetailContent(payload.detail ?? {}),
    userState: normalizePortalDetailUserState(payload.user_state ?? payload.userState ?? {}),
    permissions: normalizePortalDetailPermissions(payload.permissions ?? {})
  };
}

export function normalizePortalActionResult(payload: any): PortalActionResult {
  return {
    status: payload.status ?? '',
    message: payload.message ?? '',
    action: payload.action ? normalizePortalUserAction(payload.action) : null,
    download: normalizePortalDownload(payload.download),
    route: payload.route ?? null
  };
}

export function normalizePortalUserActions(payload: any): UserPortalAction[] {
  const records = Array.isArray(payload) ? payload : payload?.actions ?? [];
  return records.map(normalizePortalUserAction);
}

export function normalizePortalUserAction(payload: any): UserPortalAction {
  return {
    id: payload.id ?? '',
    tenantId: payload.tenant_id ?? payload.tenantId,
    userId: payload.user_id ?? payload.userId,
    detailPath: payload.detail_path ?? payload.detailPath ?? '',
    itemId: payload.item_id ?? payload.itemId ?? '',
    actionKey: payload.action_key ?? payload.actionKey ?? '',
    status: payload.status ?? '',
    message: payload.message ?? '',
    result: payload.result ?? payload.result_json ?? payload.resultJson ?? {},
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null
  };
}

export function normalizePortalSearchResult(payload: any): PortalSearchResult {
  return {
    id: payload.id ?? '',
    title: payload.title ?? '',
    subtitle: payload.subtitle ?? '',
    type: payload.type ?? payload.item_type ?? payload.itemType ?? 'item',
    pageKey: payload.page_key ?? payload.pageKey ?? '',
    path: payload.path ?? payload.action_value ?? payload.actionValue ?? '/',
    icon: payload.icon ?? 'Sparkles'
  };
}

export function loadWorkbenchDraft<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') {
    return fallback;
  }
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return fallback;
    }
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object' && fallback && typeof fallback === 'object') {
      return { ...fallback, ...parsed };
    }
    return parsed as T;
  } catch {
    return fallback;
  }
}

export function saveWorkbenchDraft(key: string, value: unknown) {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(key, JSON.stringify(value));
  }
}

function normalizePortalDetailContent(payload: any): PortalDetailContent {
  return {
    summary: payload.summary ?? '',
    highlights: normalizeStringList(payload.highlights),
    steps: normalizeStringList(payload.steps),
    deliverables: normalizeStringList(payload.deliverables),
    faqs: (payload.faqs ?? []).map(normalizePortalFaq).filter((faq: PortalDetailFaq) => faq.question || faq.answer),
    primaryAction: normalizePortalAction(payload.primary_action ?? payload.primaryAction, 'open', '立即查看'),
    secondaryActions: (payload.secondary_actions ?? payload.secondaryActions ?? []).map((action: any) =>
      normalizePortalAction(action, 'favorite', '收藏')
    ),
    download: normalizePortalDownload(payload.download),
    title: payload.title ?? '',
    bodyMarkdown: payload.body_markdown ?? payload.bodyMarkdown ?? '',
    tags: normalizeStringList(payload.tags),
    visibility: payload.visibility ?? 'community',
    authorUserId: payload.author_user_id ?? payload.authorUserId ?? '',
    currentVersion: Number(payload.current_version ?? payload.currentVersion ?? payload.version?.version ?? 1),
    version: normalizePortalDetailVersion(payload.version),
    versions: (payload.versions ?? []).map(normalizePortalDetailVersion).filter(Boolean) as PortalDetailVersion[],
    comments: (payload.comments ?? []).map(normalizePortalDetailComment),
    publishInfo: normalizePortalDetailPublishInfo(payload.publish_info ?? payload.publishInfo ?? {})
  };
}

function normalizePortalDetailUserState(payload: any): PortalDetailUserState {
  return {
    membershipActive: Boolean(payload.membership_active ?? payload.membershipActive),
    locked: Boolean(payload.locked),
    completedActions: normalizeStringList(payload.completed_actions ?? payload.completedActions)
  };
}

function normalizePortalAction(payload: any, fallbackKey: string, fallbackLabel: string): PortalDetailAction {
  return {
    key: payload?.key ?? payload?.action_key ?? payload?.actionKey ?? fallbackKey,
    label: payload?.label ?? fallbackLabel
  };
}

function normalizePortalDownload(payload: any): PortalDetailDownload | null {
  if (!payload) {
    return null;
  }
  return {
    fileName: payload.file_name ?? payload.fileName ?? payload.name ?? '',
    url: payload.url ?? '',
    storageKey: payload.storage_key ?? payload.storageKey
  };
}

function normalizePortalFaq(payload: any): PortalDetailFaq {
  return {
    question: payload.question ?? '',
    answer: payload.answer ?? ''
  };
}

function normalizePortalDetailVersion(payload: any): PortalDetailVersion | null {
  if (!payload) {
    return null;
  }
  return {
    id: payload.id ?? '',
    version: Number(payload.version ?? 1),
    title: payload.title ?? '',
    summary: payload.summary ?? '',
    bodyMarkdown: payload.body_markdown ?? payload.bodyMarkdown ?? '',
    tags: normalizeStringList(payload.tags),
    visibility: payload.visibility ?? 'community',
    releaseNote: payload.release_note ?? payload.releaseNote ?? '',
    authorUserId: payload.author_user_id ?? payload.authorUserId ?? '',
    createdAt: payload.created_at ?? payload.createdAt ?? null
  };
}

function normalizePortalDetailComment(payload: any): PortalDetailComment {
  return {
    id: payload.id ?? '',
    detailPath: payload.detail_path ?? payload.detailPath ?? '',
    userId: payload.user_id ?? payload.userId ?? '',
    authorName: payload.author_name ?? payload.authorName ?? '',
    content: payload.content ?? '',
    isAuthor: Boolean(payload.is_author ?? payload.isAuthor),
    createdAt: payload.created_at ?? payload.createdAt ?? null
  };
}

function normalizePortalDetailPublishInfo(payload: any): PortalDetailPublishInfo {
  return {
    typeLabel: payload.type_label ?? payload.typeLabel ?? '详情内容',
    typeHint: payload.type_hint ?? payload.typeHint ?? '',
    versionLabel: payload.version_label ?? payload.versionLabel ?? 'v1',
    versionHint: payload.version_hint ?? payload.versionHint ?? '',
    visibility: payload.visibility ?? 'community',
    visibilityLabel: payload.visibility_label ?? payload.visibilityLabel ?? '社区成员',
    visibilityHint: payload.visibility_hint ?? payload.visibilityHint ?? ''
  };
}

function normalizeStringList(value: any): string[] {
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof value === 'string') {
    return value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean);
  }
  return [];
}

function normalizeMetadata(value: any): Record<string, any> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
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

function normalizePortalChannel(payload: any): { key: string; label: string } {
  const key = payload.key ?? payload.page_key ?? payload.pageKey ?? '';
  return {
    key,
    label: payload.label ?? payload.title ?? key
  };
}

function hasPortalKey(
  pages: PageConfigSummary[],
  channels: Array<{ key: string; label: string }>,
  pageKey: string
): boolean {
  return pages.some((pageItem) => pageItem.pageKey === pageKey) || channels.some((channel) => channel.key === pageKey);
}

function ensureCommunicationPage(pages: PageConfigSummary[]): PageConfigSummary[] {
  if (pages.some((pageItem) => pageItem.pageKey === COMMUNICATION_PAGE_KEY)) {
    return pages;
  }
  const communicationPage = fallbackPages.find((pageItem) => pageItem.pageKey === COMMUNICATION_PAGE_KEY);
  if (!communicationPage) {
    return pages;
  }
  return insertAfterWorkbenchBeforeMarketing(pages, { ...communicationPage });
}

function ensureCommunicationChannel(channels: Array<{ key: string; label: string }>): Array<{ key: string; label: string }> {
  if (channels.some((channel) => channel.key === COMMUNICATION_PAGE_KEY)) {
    return channels;
  }
  return insertAfterWorkbenchBeforeMarketing(channels, { key: COMMUNICATION_PAGE_KEY, label: '沟通大厅' });
}

function insertAfterWorkbenchBeforeMarketing<T extends { key?: string; pageKey?: string }>(items: T[], item: T): T[] {
  const copy = [...items];
  const keyOf = (entry: T) => entry.pageKey ?? entry.key ?? '';
  const workbenchIndex = copy.findIndex((entry) => keyOf(entry) === WORKBENCH_PAGE_KEY);
  if (workbenchIndex >= 0) {
    copy.splice(workbenchIndex + 1, 0, item);
    return copy;
  }
  const marketingIndex = copy.findIndex((entry) => keyOf(entry) === MARKETING_PAGE_KEY);
  if (marketingIndex >= 0) {
    copy.splice(marketingIndex, 0, item);
    return copy;
  }
  copy.push(item);
  return copy;
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
  const pointCost = Number(payload.point_cost ?? payload.pointCost ?? 0);
  const effectivePointCostValue = payload.effective_point_cost ?? payload.effectivePointCost;
  const metadata = normalizeMetadata(payload.metadata_json ?? payload.metadataJson ?? payload.metadata);
  const menuKeys = normalizeStringList(payload.menu_keys ?? payload.menuKeys ?? metadata.menuKeys ?? metadata.menu_keys ?? []);
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
    pointCost,
    effectivePointCost: effectivePointCostValue == null ? pointCost : Number(effectivePointCostValue),
    modelConfig: normalizeModelConfig(payload.model_config ?? payload.modelConfig),
    metadata,
    menuKeys
  };
}

function normalizeAssistant(payload: any): AssistantCard {
  const usageCount = Number(payload.usage_count ?? payload.usageCount ?? 0);
  const pointCost = Number(payload.point_cost ?? payload.pointCost ?? 0);
  const effectivePointCostValue = payload.effective_point_cost ?? payload.effectivePointCost;
  return {
    id: payload.id,
    name: payload.name,
    category: payload.category,
    description: payload.description ?? '',
    icon: payload.icon ?? 'Bot',
    usageCount,
    usageCountLabel: payload.usage_count_label ?? payload.usageCountLabel ?? formatUsageCount(usageCount),
    pointCost,
    effectivePointCost: effectivePointCostValue == null ? pointCost : Number(effectivePointCostValue),
    requiredMembership: Boolean(payload.required_membership ?? payload.requiredMembership),
    actionValue: payload.action_value ?? payload.actionValue ?? '',
    modelConfig: normalizeModelConfig(payload.model_config ?? payload.modelConfig)
  };
}

function normalizePromptTemplate(payload: any): PromptTemplate {
  const effectivePointCostValue = payload.effective_point_cost ?? payload.effectivePointCost;
  return {
    id: payload.id,
    title: payload.title,
    category: payload.category,
    content: payload.content,
    requiredMembership: Boolean(payload.required_membership ?? payload.requiredMembership),
    effectivePointCost: effectivePointCostValue == null ? 0 : Number(effectivePointCostValue),
    modelConfig: normalizeModelConfig(payload.model_config ?? payload.modelConfig)
  };
}

export function normalizeModelConfig(payload: any): ModelConfigSummary | null {
  if (!payload) {
    return null;
  }
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    modelKey: payload.model_key ?? payload.modelKey,
    displayName: payload.display_name ?? payload.displayName ?? '',
    capability: payload.capability ?? '',
    channelId: payload.channel_id ?? payload.channelId,
    channelKey: payload.channel_key ?? payload.channelKey,
    channelName: payload.channel_name ?? payload.channelName,
    providerModel: payload.provider_model ?? payload.providerModel,
    defaultPointCost: Number(payload.default_point_cost ?? payload.defaultPointCost ?? 0),
    enabled: Boolean(payload.enabled ?? true),
    metadataJson: normalizeMetadata(payload.metadata_json ?? payload.metadataJson ?? payload.metadata)
  };
}

export function normalizeChatModelProfile(payload: any): ChatModelProfilePayload {
  const profilePayload = payload.profile ?? payload;
  const providerPayload = payload.provider ?? payload.provider_channel ?? payload.providerChannel ?? null;
  const profile: ChatModelProfileSummary = {
    channelKey: profilePayload.channel_key ?? profilePayload.channelKey ?? 'openai-chat-compatible',
    providerName: profilePayload.provider_name ?? profilePayload.providerName ?? '中转',
    note: profilePayload.note ?? '',
    officialUrl: profilePayload.official_url ?? profilePayload.officialUrl ?? '',
    baseUrl: profilePayload.base_url ?? profilePayload.baseUrl ?? '',
    apiKey: profilePayload.api_key ?? profilePayload.apiKey ?? '',
    modelName: profilePayload.model_name ?? profilePayload.modelName ?? '',
    modelKey: profilePayload.model_key ?? profilePayload.modelKey ?? 'general_text_default',
    displayName: profilePayload.display_name ?? profilePayload.displayName ?? '',
    modelReasoningEffort: profilePayload.model_reasoning_effort ?? profilePayload.modelReasoningEffort ?? 'high',
    providerReasoningEffort: profilePayload.provider_reasoning_effort ?? profilePayload.providerReasoningEffort ?? 'medium',
    serviceTier: profilePayload.service_tier ?? profilePayload.serviceTier ?? 'fast',
    contextWindow: Number(profilePayload.context_window ?? profilePayload.contextWindow ?? 1000000),
    autoCompactTokenLimit: Number(profilePayload.auto_compact_token_limit ?? profilePayload.autoCompactTokenLimit ?? 900000),
    disableResponseStorage: Boolean(profilePayload.disable_response_storage ?? profilePayload.disableResponseStorage ?? true),
    defaultPointCost: Number(profilePayload.default_point_cost ?? profilePayload.defaultPointCost ?? 0),
    timeoutSeconds: Number(profilePayload.timeout_seconds ?? profilePayload.timeoutSeconds ?? 60),
    enabled: Boolean(profilePayload.enabled ?? true)
  };
  return {
    profile,
    provider: providerPayload ? normalizeProviderChannel(providerPayload) : null,
    modelConfig: normalizeModelConfig(payload.model_config ?? payload.modelConfig),
    authJson: payload.auth_json ?? payload.authJson ?? '',
    configToml: payload.config_toml ?? payload.configToml ?? ''
  };
}

export function normalizeProviderChannel(payload: any): ProviderChannelSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    channelKey: payload.channel_key ?? payload.channelKey,
    displayName: payload.display_name ?? payload.displayName ?? '',
    baseUrl: payload.base_url ?? payload.baseUrl ?? '',
    apiKeyMask: payload.api_key_mask ?? payload.apiKeyMask ?? '',
    channelType: payload.channel_type ?? payload.channelType ?? '',
    adapterType: payload.adapter_type ?? payload.adapterType ?? 'custom_http',
    priority: Number(payload.priority ?? 100),
    enabled: Boolean(payload.enabled ?? true),
    healthStatus: payload.health_status ?? payload.healthStatus,
    timeoutSeconds: Number(payload.timeout_seconds ?? payload.timeoutSeconds ?? 60),
    metadataJson: normalizeMetadata(payload.metadata_json ?? payload.metadataJson ?? payload.metadata)
  };
}

function normalizePortalDetailPermissions(payload: any): PortalDetailPayload['permissions'] {
  return {
    canEdit: Boolean(payload.can_edit ?? payload.canEdit),
    canComment: Boolean(payload.can_comment ?? payload.canComment)
  };
}

export function normalizeToolModelBinding(payload: any): ToolModelBindingSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    targetType: payload.target_type ?? payload.targetType ?? '',
    targetKey: payload.target_key ?? payload.targetKey ?? '',
    modelConfigId: payload.model_config_id ?? payload.modelConfigId ?? '',
    pointCostOverride:
      payload.point_cost_override === undefined || payload.point_cost_override === null
        ? payload.pointCostOverride ?? null
        : Number(payload.point_cost_override),
    effectivePointCost:
      payload.effective_point_cost === undefined || payload.effective_point_cost === null
        ? payload.effectivePointCost ?? null
        : Number(payload.effective_point_cost),
    enabled: Boolean(payload.enabled ?? true),
    modelConfig: normalizeModelConfig(payload.model_config ?? payload.modelConfig)
  };
}

export function normalizeAdminOverview(payload: any): AdminOverviewSummary {
  return {
    tenantId: payload.tenant_id ?? payload.tenantId,
    users: {
      total: Number(payload.users?.total ?? 0),
      active: Number(payload.users?.active ?? 0),
      admins: Number(payload.users?.admins ?? 0)
    },
    membershipPlans: {
      total: Number(payload.membership_plans?.total ?? payload.membershipPlans?.total ?? 0),
      enabled: Number(payload.membership_plans?.enabled ?? payload.membershipPlans?.enabled ?? 0)
    },
    wallets: {
      totalBalance: Number(payload.wallets?.total_balance ?? payload.wallets?.totalBalance ?? 0),
      frozenBalance: Number(payload.wallets?.frozen_balance ?? payload.wallets?.frozenBalance ?? 0)
    },
    content: {
      pages: Number(payload.content?.pages ?? 0),
      sections: Number(payload.content?.sections ?? 0),
      items: Number(payload.content?.items ?? 0)
    },
    models: {
      channels: Number(payload.models?.channels ?? 0),
      modelConfigs: Number(payload.models?.model_configs ?? payload.models?.modelConfigs ?? 0),
      bindings: Number(payload.models?.bindings ?? 0)
    },
    recentLogs: (payload.recent_logs ?? payload.recentLogs ?? []).map(normalizeAdminAuditLog)
  };
}

export function normalizeAdminUser(payload: any): AdminUserSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    phone: payload.phone ?? '',
    displayName: payload.display_name ?? payload.displayName ?? '',
    role: payload.role ?? '',
    status: payload.status ?? '',
    balance: Number(payload.balance ?? 0),
    frozenBalance: Number(payload.frozen_balance ?? payload.frozenBalance ?? 0),
    currency: payload.currency ?? 'POINT',
    membershipPlanId: payload.membership_plan_id ?? payload.membershipPlanId ?? null,
    membershipPlanKey: payload.membership_plan_key ?? payload.membershipPlanKey ?? null,
    membershipPlanName: payload.membership_plan_name ?? payload.membershipPlanName ?? null,
    membershipStatus: payload.membership_status ?? payload.membershipStatus ?? null,
    membershipExpiresAt: payload.membership_expires_at ?? payload.membershipExpiresAt ?? null,
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null
  };
}

export function normalizeAdminMembershipPlan(payload: any): AdminMembershipPlanSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    planKey: payload.plan_key ?? payload.planKey ?? '',
    name: payload.name ?? '',
    priceCents: Number(payload.price_cents ?? payload.priceCents ?? 0),
    durationDays: Number(payload.duration_days ?? payload.durationDays ?? 0),
    entitlements: normalizeStringList(payload.entitlements),
    enabled: Boolean(payload.enabled ?? true),
    sortOrder: Number(payload.sort_order ?? payload.sortOrder ?? 100),
    activeUserCount: Number(payload.active_user_count ?? payload.activeUserCount ?? 0),
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null
  };
}

export function normalizeAdminUserMembership(payload: any): AdminUserMembershipSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    userId: payload.user_id ?? payload.userId ?? '',
    userDisplayName: payload.user_display_name ?? payload.userDisplayName ?? '',
    userPhone: payload.user_phone ?? payload.userPhone ?? '',
    plan: normalizeAdminMembershipPlan(payload.plan ?? payload.membership_plan ?? payload.membershipPlan ?? {}),
    status: payload.status ?? '',
    startedAt: payload.started_at ?? payload.startedAt ?? null,
    expiresAt: payload.expires_at ?? payload.expiresAt ?? null,
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null
  };
}

export function normalizeAdminWalletTransaction(payload: any): AdminWalletTransactionSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    userId: payload.user_id ?? payload.userId ?? '',
    userDisplayName: payload.user_display_name ?? payload.userDisplayName ?? '',
    requestKey: payload.request_key ?? payload.requestKey ?? '',
    amount: Number(payload.amount ?? 0),
    balanceAfter: Number(payload.balance_after ?? payload.balanceAfter ?? 0),
    type: payload.type ?? '',
    remark: payload.remark ?? '',
    relatedRef: payload.related_ref ?? payload.relatedRef ?? '',
    createdAt: payload.created_at ?? payload.createdAt ?? null
  };
}

export function normalizeAdminAuditLog(payload: any): AdminAuditLogSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    actorUserId: payload.actor_user_id ?? payload.actorUserId ?? '',
    actorDisplayName: payload.actor_display_name ?? payload.actorDisplayName ?? '',
    actorRole: payload.actor_role ?? payload.actorRole ?? '',
    action: payload.action ?? '',
    targetType: payload.target_type ?? payload.targetType ?? '',
    targetId: payload.target_id ?? payload.targetId ?? '',
    summary: payload.summary ?? '',
    createdAt: payload.created_at ?? payload.createdAt ?? null
  };
}

export function normalizeAdminRedemptionBatch(payload: any): AdminRedemptionBatchSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    name: payload.name ?? '',
    points: Number(payload.points ?? 0),
    membershipPlanId: payload.membership_plan_id ?? payload.membershipPlanId ?? null,
    membershipDays:
      payload.membership_days ?? payload.membershipDays ?? null,
    quantity: Number(payload.quantity ?? 0),
    status: payload.status ?? '',
    expiresAt: payload.expires_at ?? payload.expiresAt ?? null,
    generatedCount: Number(payload.generated_count ?? payload.generatedCount ?? 0),
    redeemedCount: Number(payload.redeemed_count ?? payload.redeemedCount ?? 0),
    createdAt: payload.created_at ?? payload.createdAt ?? null,
    updatedAt: payload.updated_at ?? payload.updatedAt ?? null
  };
}

export function normalizeAdminRedemptionCode(payload: any): AdminRedemptionCodeSummary {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId,
    batchId: payload.batch_id ?? payload.batchId ?? '',
    code: payload.code,
    maskedCode: payload.masked_code ?? payload.maskedCode ?? '',
    status: payload.status ?? '',
    redeemedByUserId: payload.redeemed_by_user_id ?? payload.redeemedByUserId ?? null,
    redeemedAt: payload.redeemed_at ?? payload.redeemedAt ?? null,
    createdAt: payload.created_at ?? payload.createdAt ?? null
  };
}

export function normalizeRedemptionResult(payload: any): RedemptionResult {
  const accountSummary = normalizeAccountSummary(payload.account_summary ?? payload.accountSummary ?? {});
  return {
    status: payload.status ?? '',
    pointsGranted: Number(payload.points_granted ?? payload.pointsGranted ?? 0),
    wallet: {
      balance: Number(payload.wallet?.balance ?? accountSummary.wallet.balance ?? 0),
      frozenBalance: Number(payload.wallet?.frozen_balance ?? payload.wallet?.frozenBalance ?? accountSummary.wallet.frozenBalance ?? 0),
      currency: payload.wallet?.currency ?? accountSummary.wallet.currency ?? 'POINT'
    },
    membership: normalizeMembershipSummary(payload.membership ?? accountSummary.membership ?? {}),
    accountSummary
  };
}

function normalizeGenerationSurface(value: any): GenerationSurface {
  return value === 'workbench' ? 'workbench' : 'portal';
}

function normalizeVideoTask(payload: any): VideoTask {
  return {
    id: payload.id,
    tenantId: payload.tenant_id ?? payload.tenantId ?? 'demo',
    userId: payload.user_id ?? payload.userId ?? 'demo-user',
    surface: normalizeGenerationSurface(payload.surface ?? payload.surfaceKey ?? 'portal'),
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
    surface: normalizeGenerationSurface(payload.surface ?? payload.surfaceKey ?? 'portal'),
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

function startOfDay(value: Date): Date {
  const date = new Date(value);
  date.setHours(0, 0, 0, 0);
  return date;
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
    tags: [],
    metadata: {}
  };
}

function thirdPartyTool(
  id: string,
  title: string,
  subtitle: string,
  category: string,
  brandMark: string,
  actionValue: string,
  downloadUrl: string
): PortalItem {
  return {
    id,
    itemType: 'third_party_tool',
    title,
    subtitle,
    category,
    icon: 'Download',
    actionType: 'external_link',
    actionValue,
    requiredMembership: false,
    pointCost: 0,
    effectivePointCost: 0,
    sortOrder: 100,
    enabled: true,
    tags: [category, '第三方工具'],
    metadata: {
      brandMark,
      detail: {
        summary: subtitle,
        primaryAction: { key: 'download', label: '下载客户端' },
        secondaryActions: [{ key: 'favorite', label: '收藏' }],
        download: {
          fileName: `${id}.url`,
          url: downloadUrl
        }
      }
    }
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

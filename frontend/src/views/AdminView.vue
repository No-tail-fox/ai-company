<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import type { Component } from 'vue';
import {
  ArrowLeft,
  BarChart3,
  Coins,
  Eye,
  EyeOff,
  FileText,
  ImagePlus,
  Layers3,
  Lock,
  Maximize2,
  Minus,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Ticket,
  Trash2,
  UserPlus,
  Users,
  Wallet,
  X
} from 'lucide-vue-next';
import {
  adminAdjustWallet,
  adminCreateHomeSlide,
  adminCreateItem,
  adminCreateMembershipPlan,
  adminCreateModelConfig,
  adminCreatePage,
  adminCreateProviderChannel,
  adminCreateRedemptionBatch,
  adminCreateSection,
  adminCreateToolModelBinding,
  adminCreateUser,
  adminCleanupCourses,
  adminDeleteHomeSlide,
  adminDeleteItem,
  adminDeleteMembershipPlan,
  adminDeletePage,
  adminDeleteSection,
  adminDeleteUser,
  adminDeleteUserMembership,
  adminDisableRedemptionCode,
  adminFetchPageContent,
  adminGetChatModelProfile,
  adminGrantMembership,
  adminListAuditLogs,
  adminListCourses,
  adminListHomeSlides,
  adminListMembershipPlans,
  adminListModelConfigs,
  adminListOverview,
  adminListPages,
  adminListProviderChannels,
  adminListRedemptionBatches,
  adminListRedemptionCodes,
  adminListToolModelBindings,
  adminListUserMemberships,
  adminListUsers,
  adminListWalletTransactions,
  adminListWorkbenchCapabilities,
  adminReorderHomeSlides,
  adminReorderItems,
  adminReorderPages,
  adminReorderSections,
  adminUpdateHomeSlide,
  adminUpdateItem,
  adminUpdateMembershipPlan,
  adminUpdateModelConfig,
  adminUpdatePage,
  adminUpdateProviderChannel,
  adminUpdateSection,
  adminUpdateToolModelBinding,
  adminUpdateUser,
  adminUpdateUserMembership,
  adminUpdateChatModelProfile,
  adminUpdateWorkbenchCapability,
  adminUploadImage,
  clearAdminToken,
  getAdminToken,
  loginAdmin
} from '../services/api';
import DynamicPage from '../components/DynamicPage.vue';
import AudioPage from '../components/AudioPage.vue';
import HomeDashboardPage from '../components/HomeDashboardPage.vue';
import MarketingPage from '../components/MarketingPage.vue';
import { clampPreviewScale, moveRecord, reorderByDrop } from '../services/adminInteractions';
import {
  buildHomeSlidePayload,
  buildItemPayload,
  buildCodexAuthJsonPreview,
  buildCodexConfigTomlPreview,
  buildChatModelProfilePayload,
  buildModelConfigPayload,
  buildPagePayload,
  buildProviderChannelPayload,
  buildReorderPayload,
  buildSectionPayload,
  buildToolModelBindingPayload
} from '../services/adminForms';
import {
  buildHomeDashboardModel,
  createFallbackPageConfig,
  shouldUseAudioPage,
  shouldUseHomeDashboardPage,
  shouldUseMarketingPage,
  type AdminAuditLogSummary,
  type AdminMembershipPlanSummary,
  type AdminOverviewSummary,
  type AdminRedemptionBatchSummary,
  type AdminRedemptionCodeSummary,
  type AdminUserMembershipSummary,
  type AdminUserSummary,
  type AdminWalletTransactionSummary,
  type ChatModelProfilePayload,
  type CourseCatalogItem,
  type CourseCatalogPayload,
  type HomeDashboardSlide,
  type ModelConfigSummary,
  type PageConfigSummary,
  type PortalItem,
  type PortalPageConfig,
  type PortalSection,
  type ProviderChannelSummary,
  type ToolModelBindingSummary,
  type WorkbenchCapability
} from '../services/viewModel';

type AdminModule = 'overview' | 'users' | 'memberships' | 'points' | 'redemptions' | 'content' | 'courses' | 'models' | 'audit';
type AdminPanel =
  | ''
  | 'home-slide'
  | 'user'
  | 'wallet'
  | 'redemption-batch'
  | 'membership-plan'
  | 'user-membership'
  | 'page'
  | 'section'
  | 'item'
  | 'provider-channel'
  | 'model-config'
  | 'tool-binding'
  | 'workbench-capability';
type LoginUser = {
  id: string;
  displayName: string;
  phone: string;
  role: string;
  status: string;
};

const router = useRouter();
const token = ref(getAdminToken());
const currentAdmin = ref<LoginUser | null>(null);
const errorMessage = ref('');
const notice = ref('');

const moduleStorageKey = 'opc_admin_active_module';
const pageStorageKey = 'opc_admin_selected_page';
const userStorageKey = 'opc_admin_selected_user';

const adminModules: Array<{ key: AdminModule; label: string; icon: Component; description: string }> = [
  { key: 'redemptions', label: '兑换码管理', icon: Ticket, description: '批量生成、售卖发放和兑换状态' },
  { key: 'overview', label: '总览', icon: BarChart3, description: '概览核心指标和最近操作' },
  { key: 'users', label: '人员管理', icon: Users, description: '新增、编辑、禁用人员' },
  { key: 'memberships', label: '会员管理', icon: UserPlus, description: '会员计划和开通记录' },
  { key: 'points', label: '积分管理', icon: Coins, description: '积分账户、流水和调账' },
  { key: 'content', label: '内容管理', icon: FileText, description: '页面、模块、卡片和预览' },
  { key: 'courses', label: '课程管理', icon: Sparkles, description: '飞书课程、格式清洗和批量导入' },
  { key: 'models', label: '模型中心', icon: Layers3, description: '渠道、模型和工具绑定' },
  { key: 'audit', label: '审计日志', icon: ShieldCheck, description: '查看关键管理操作' }
];

const activeModule = ref<AdminModule>(readStoredModule());

const loginForm = reactive({ phone: '13900000000', password: 'admin123456' });

const overview = ref<AdminOverviewSummary | null>(null);
const users = ref<AdminUserSummary[]>([]);
const membershipPlans = ref<AdminMembershipPlanSummary[]>([]);
const userMemberships = ref<AdminUserMembershipSummary[]>([]);
const walletTransactions = ref<AdminWalletTransactionSummary[]>([]);
const auditLogs = ref<AdminAuditLogSummary[]>([]);
const redemptionBatches = ref<AdminRedemptionBatchSummary[]>([]);
const redemptionCodes = ref<AdminRedemptionCodeSummary[]>([]);
const generatedRedemptionCodes = ref<AdminRedemptionCodeSummary[]>([]);
const courseCatalog = ref<CourseCatalogPayload>({
  tenantId: 'demo',
  total: 0,
  page: 1,
  pageSize: 50,
  categories: [],
  items: []
});
const courseQuery = ref('');
const courseCategory = ref('');
const coursePage = ref(1);
const courseCleanupBusy = ref(false);

const pages = ref<PageConfigSummary[]>([]);
const homeSlides = ref<HomeDashboardSlide[]>([]);
const providerChannels = ref<ProviderChannelSummary[]>([]);
const modelConfigs = ref<ModelConfigSummary[]>([]);
const toolModelBindings = ref<ToolModelBindingSummary[]>([]);
const workbenchCapabilities = ref<WorkbenchCapability[]>([]);
const chatModelProfile = ref<ChatModelProfilePayload | null>(null);
const pageConfig = ref<PortalPageConfig | null>(null);
const selectedPageKey = ref(readStoredPageKey());
const selectedUserId = ref(readStoredUserId());
const draggedPageId = ref('');
const draggedHomeSlideId = ref('');
const draggedSectionId = ref('');
const draggedItemId = ref('');
const activeDropPageId = ref('');
const activeDropHomeSlideId = ref('');
const activeDropSectionId = ref('');
const activeDropItemId = ref('');

const userQuery = ref('');
const userRoleFilter = ref('');
const userStatusFilter = ref('');
const walletUserFilterId = ref('');
const membershipUserFilterId = ref('');
const auditLimit = ref(50);

const activePanel = ref<AdminPanel>('');
const previewScale = ref(0.55);
const previewWidth = ref(580);

const userFormId = ref('');
const userForm = reactive({
  phone: '',
  displayName: '',
  role: 'USER',
  status: 'ACTIVE',
  password: ''
});

const walletAdjustForm = reactive({
  userId: '',
  amount: 100,
  reason: '手工调账',
  requestKey: ''
});

const redemptionBatchForm = reactive({
  name: '',
  quantity: 10,
  points: 0,
  membershipPlanId: '',
  membershipDays: 31,
  expiresAt: ''
});

const membershipPlanFormId = ref('');
const membershipPlanForm = reactive({
  planKey: '',
  name: '',
  priceCents: 0,
  durationDays: 31,
  entitlementsText: '',
  enabled: true,
  sortOrder: 100
});

const userMembershipFormId = ref('');
const userMembershipForm = reactive({
  userId: '',
  planId: '',
  durationDays: 31,
  status: 'ACTIVE',
  expiresAt: ''
});

const pageFormId = ref('');
const pageForm = reactive({
  pageKey: '',
  label: '',
  title: '',
  subtitle: '',
  icon: 'Sparkles',
  sortOrder: 100,
  enabled: true
});

const homeSlideFormId = ref('');
const homeSlideForm = reactive({
  title: '',
  subtitle: '',
  badge: '',
  ctaLabel: '立即查看',
  ctaSubtitle: '',
  imageUrl: '',
  actionType: 'route',
  actionValue: '/membership/benefits',
  sortOrder: 100,
  enabled: true,
  accent: 'gold'
});

const sectionFormId = ref('');
const sectionForm = reactive({
  pageKey: '',
  sectionKey: '',
  title: '',
  subtitle: '',
  layout: 'tool-grid',
  sortOrder: 100,
  enabled: true
});

const itemFormId = ref('');
const itemForm = reactive({
  sectionId: '',
  itemType: 'tool',
  title: '',
  subtitle: '',
  category: '',
  icon: 'Sparkles',
  imageUrl: '',
  badge: '',
  tagsText: '',
  sortOrder: 100,
  enabled: true,
  actionType: 'route',
  actionValue: '',
  requiredMembership: false,
  pointCost: 0,
  detailSummary: '',
  detailHighlightsText: '',
  detailStepsText: '',
  detailDeliverablesText: '',
  detailFaqsText: '',
  detailPrimaryActionKey: 'enroll',
  detailPrimaryActionLabel: '报名',
  detailSecondaryActionsText: 'favorite|收藏',
  detailDownloadFileName: '',
  detailDownloadUrl: ''
});

const providerChannelFormId = ref('');
const providerChannelForm = reactive({
  channelKey: '',
  displayName: '',
  baseUrl: '',
  apiKey: '',
  channelType: 'TEXT',
  adapterType: 'custom_http',
  priority: 100,
  enabled: true,
  timeoutSeconds: 60,
  presetKey: 'custom',
  remark: '',
  website: '',
  useFullUrl: false,
  authJsonText: '{\n  "OPENAI_API_KEY": ""\n}',
  configTomlText: '',
  writeCommonConfig: true,
  testConfigText: '',
  billingConfigText: '',
  metadataJson: {} as Record<string, unknown>
});

const chatModelProfileForm = reactive({
  channelKey: 'openai-chat-compatible',
  providerName: '中转',
  note: '',
  officialUrl: 'https://ai.input.im',
  baseUrl: 'https://ai.input.im',
  apiKey: '',
  savedApiKeyMask: '',
  modelName: 'gpt-5.5',
  modelKey: 'general_text_default',
  displayName: 'GPT-5.5',
  modelReasoningEffort: 'high',
  providerReasoningEffort: 'medium',
  serviceTier: 'fast',
  contextWindow: 1000000,
  autoCompactTokenLimit: 900000,
  disableResponseStorage: true,
  defaultPointCost: 0,
  timeoutSeconds: 60,
  enabled: true
});

const modelConfigFormId = ref('');
const modelConfigForm = reactive({
  modelKey: '',
  displayName: '',
  capability: 'TEXT',
  channelId: '',
  providerModel: '',
  defaultPointCost: 0,
  enabled: true,
  useMillionContextWindow: false,
  compressionThreshold: 900000,
  testConfigText: '',
  billingConfigText: '',
  metadataJson: {} as Record<string, unknown>
});

const toolBindingFormId = ref('');
const toolBindingForm = reactive({
  targetType: 'builtin',
  targetKey: '',
  modelConfigId: '',
  pointCostOverride: null as number | string | null,
  enabled: true
});

const workbenchCapabilityForm = reactive({
  targetType: '',
  targetKey: '',
  title: '',
  modelConfigId: '',
  pointCostOverride: null as number | string | null,
  enabled: true
});

type ProviderPresetOption = {
  key: string;
  label: string;
  hint: string;
  defaults: {
    channelType: string;
    adapterType: string;
    baseUrl: string;
    remark: string;
    website: string;
    useFullUrl: boolean;
    authJsonText: string;
    configTomlText: string;
    writeCommonConfig: boolean;
    testConfigText: string;
    billingConfigText: string;
  };
};

const defaultAuthJson = '{\n  "OPENAI_API_KEY": ""\n}';

function createPreset(
  key: string,
  label: string,
  hint: string,
  defaults: Partial<ProviderPresetOption['defaults']> = {}
): ProviderPresetOption {
  return {
    key,
    label,
    hint,
    defaults: {
      channelType: 'TEXT',
      adapterType: 'openai_compatible',
      baseUrl: 'https://api.example.com/v1',
      remark: `${label} 预设`,
      website: '',
      useFullUrl: true,
      authJsonText: defaultAuthJson,
      configTomlText: 'model_provider = "openai_compatible"',
      writeCommonConfig: true,
      testConfigText: '{"temperature":0.2}',
      billingConfigText: '{"mode":"point"}',
      ...defaults
    }
  };
}

const providerPresetOptions: ProviderPresetOption[] = [
  createPreset('custom', '自定义配置', '手动填写全部字段', {
    channelType: 'TEXT',
    adapterType: 'custom_http',
    baseUrl: '',
    remark: '',
    website: '',
    useFullUrl: false,
    configTomlText: '',
    testConfigText: '',
    billingConfigText: ''
  }),
  createPreset('openai_official', 'OpenAI Official', 'OpenAI 官方兼容端点', {
    baseUrl: 'https://api.openai.com/v1',
    website: 'https://openai.com',
    configTomlText: 'model_provider = "openai_compatible"'
  }),
  createPreset('anthropic', 'Anthropic', 'Claude 官方兼容端点'),
  createPreset('aihubmix', 'AiHubMix', '统一聚合路由端点'),
  createPreset('dmxapi', 'DMXAPI', '多供应商代理端点'),
  createPreset('youyun', '优云智算', '通用云模型端点'),
  createPreset('pipellm', 'PIPELLM', '管道式模型路由端点'),
  createPreset('openrouter', 'OpenRouter', 'OpenRouter 聚合端点', {
    baseUrl: 'https://openrouter.ai/api/v1',
    website: 'https://openrouter.ai'
  }),
  createPreset('therouter', 'TheRouter', 'TheRouter 聚合端点', {
    baseUrl: 'https://api.therouter.ai/v1'
  }),
  createPreset('azure_openai', 'Azure OpenAI', 'Azure OpenAI 资源端点', {
    baseUrl: 'https://{resource}.openai.azure.com/openai/deployments',
    website: 'https://azure.microsoft.com/products/ai-services/openai-service'
  }),
  createPreset('packycode', 'PackyCode', '编码模型服务端点'),
  createPreset('cubence', 'Cubence', '向量与推理服务端点'),
  createPreset('aigocode', 'AIGoCode', '代码生成服务端点'),
  createPreset('rightcode', 'RightCode', '代码助手服务端点'),
  createPreset('sssaicode', 'SSSAICode', '代码与对话服务端点'),
  createPreset('micu', 'Micu', '多用途推理端点'),
  createPreset('ctokai', 'CTok.ai', '模型路由与控制台'),
  createPreset('lionccapi', 'LionCCAPI', '兼容型聚合端点'),
  createPreset('ddshub', 'DDSHub', '数据与模型服务端点'),
  createPreset('e-flowcode', 'E-FlowCode', '工作流模型服务端点'),
  createPreset('lemondata', 'LemonData', '数据分析与模型端点'),
  createPreset('aicodemirror', 'AICodeMirror', '代码镜像服务端点'),
  createPreset('aicoding', 'AICoding', '通用编码端点'),
  createPreset('crazyrouter', 'CrazyRouter', '高并发路由端点')
];

function providerPresetByKey(key: string) {
  return providerPresetOptions.find((preset) => preset.key === key) ?? providerPresetOptions[0];
}

function metadataText(value: unknown) {
  if (value === undefined || value === null || value === '') {
    return '';
  }
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2);
}

function metadataBoolean(value: unknown, fallback = false) {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    return value.toLowerCase() === 'true';
  }
  return fallback;
}

function metadataNumber(value: unknown, fallback = 0) {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

const itemTypeOptions = [
  { value: 'tool', label: '工具' },
  { value: 'template', label: '模板' },
  { value: 'course', label: '课程' },
  { value: 'service', label: '服务' },
  { value: 'community', label: '社群' },
  { value: 'resource', label: '资源' },
  { value: 'ranking', label: '榜单' },
  { value: 'banner', label: '横幅' },
  { value: 'stat', label: '数据卡' },
  { value: 'task', label: '任务' },
  { value: 'voice', label: '音色' },
  { value: 'audio', label: '音频工具' },
  { value: 'workbench', label: '工作台入口' },
  { value: 'project', label: '项目' },
  { value: 'guide', label: '指南' },
  { value: 'case', label: '案例' },
  { value: 'third_party_tool', label: '第三方工具' }
] as const;

const actionTypeOptions = [
  { value: 'route', label: '路由跳转' },
  { value: 'workspace', label: '工作台跳转' },
  { value: 'external_link', label: '外部链接' }
] as const;

const selectedPage = computed(() => pages.value.find((page) => page.pageKey === selectedPageKey.value) ?? null);
const selectedSections = computed(() => pageConfig.value?.sections ?? []);
const selectedItems = computed(() =>
  selectedSections.value.flatMap((section) => section.items.map((item) => ({ ...item, sectionTitle: section.title })))
);
const filteredUsers = computed(() =>
  users.value.filter((user) => {
    const query = userQuery.value.trim().toLowerCase();
    const matchesQuery =
      !query ||
      user.phone.toLowerCase().includes(query) ||
      user.displayName.toLowerCase().includes(query);
    const matchesRole = !userRoleFilter.value || user.role === userRoleFilter.value;
    const matchesStatus = !userStatusFilter.value || user.status === userStatusFilter.value;
    return matchesQuery && matchesRole && matchesStatus;
  })
);
const filteredWalletTransactions = computed(() =>
  walletUserFilterId.value ? walletTransactions.value.filter((row) => row.userId === walletUserFilterId.value) : walletTransactions.value
);
const filteredUserMemberships = computed(() =>
  membershipUserFilterId.value ? userMemberships.value.filter((row) => row.userId === membershipUserFilterId.value) : userMemberships.value
);
const selectedUser = computed(() => users.value.find((user) => user.id === selectedUserId.value) ?? filteredUsers.value[0] ?? null);
const previewPageConfig = computed<PortalPageConfig | null>(() => {
  if (!pageConfig.value) {
    return null;
  }
  return {
    ...pageConfig.value,
    sections: pageConfig.value.sections
      .filter((section) => section.enabled)
      .map((section) => ({
        ...section,
        items: section.items.filter((item) => item.enabled)
      }))
  };
});
const previewUsesMarketingPage = computed(() => Boolean(previewPageConfig.value && shouldUseMarketingPage(previewPageConfig.value.page.pageKey)));
const previewUsesAudioPage = computed(() => Boolean(previewPageConfig.value && shouldUseAudioPage(previewPageConfig.value.page.pageKey)));
const previewUsesHomeDashboardPage = computed(() => Boolean(previewPageConfig.value && shouldUseHomeDashboardPage(previewPageConfig.value.page.pageKey)));
const previewHomeDashboardModel = computed(() =>
  buildHomeDashboardModel(previewPageConfig.value ?? createFallbackPageConfig('home'), null)
);
const previewPercent = computed(() => `${Math.round(previewScale.value * 100)}%`);
const previewPanelStyle = computed(() => ({ width: `${previewWidth.value}px` }));
const previewStageStyle = computed(() => ({
  width: '1120px',
  transform: `scale(${previewScale.value})`
}));
const chatAuthPreview = computed(() =>
  chatModelProfileForm.apiKey
    ? buildCodexAuthJsonPreview(chatModelProfileForm.apiKey)
    : chatModelProfile.value?.authJson ?? buildCodexAuthJsonPreview('')
);
const chatConfigPreview = computed(() => buildCodexConfigTomlPreview(chatModelProfileForm));
const chatRuntimeState = computed(() => {
  const provider = chatModelProfile.value?.provider;
  const model = chatModelProfile.value?.modelConfig;
  if (!provider || !model) {
    return '未写入';
  }
  if (!provider.enabled || !model.enabled || !chatModelProfileForm.enabled) {
    return '已停用';
  }
  return '可调用';
});
const itemActionValuePlaceholder = computed(() => {
  if (itemForm.actionType === 'workspace') {
    return '/workbench 或 /workbench/image';
  }
  if (itemForm.actionType === 'external_link') {
    return 'https://example.com';
  }
  return '/home /workbench/image';
});
const activeModuleMeta = computed(() => adminModules.find((module) => module.key === activeModule.value) ?? adminModules[0]);
const moduleDescription = computed(() => activeModuleMeta.value.description);
const panelTitle = computed(() => {
  if (activePanel.value === 'user') {
    return userFormId.value ? '编辑人员' : '新增人员';
  }
  if (activePanel.value === 'home-slide') {
    return homeSlideFormId.value ? '编辑首页轮播' : '新增首页轮播';
  }
  if (activePanel.value === 'wallet') {
    return '积分调整';
  }
  if (activePanel.value === 'redemption-batch') {
    return '批量生成兑换码';
  }
  if (activePanel.value === 'membership-plan') {
    return membershipPlanFormId.value ? '编辑会员计划' : '新增会员计划';
  }
  if (activePanel.value === 'user-membership') {
    return userMembershipFormId.value ? '编辑会员' : '新增会员';
  }
  if (activePanel.value === 'page') {
    return pageFormId.value ? '编辑页面' : '新增页面';
  }
  if (activePanel.value === 'section') {
    return sectionFormId.value ? '编辑模块' : '新增模块';
  }
  if (activePanel.value === 'item') {
    return itemFormId.value ? '编辑卡片' : '新增卡片';
  }
  if (activePanel.value === 'provider-channel') {
    return providerChannelFormId.value ? '编辑渠道' : '新增渠道';
  }
  if (activePanel.value === 'model-config') {
    return modelConfigFormId.value ? '编辑模型' : '新增模型';
  }
  if (activePanel.value === 'tool-binding') {
    return toolBindingFormId.value ? '编辑绑定' : '新增绑定';
  }
  if (activePanel.value === 'workbench-capability') {
    return '工作台能力筛选';
  }
  return '';
});

function labelForOption(options: readonly { value: string; label: string }[], value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function isKnownOption(options: readonly { value: string; label: string }[], value: string) {
  return options.some((option) => option.value === value);
}

function itemTypeLabel(value: string) {
  return labelForOption(itemTypeOptions, value);
}

function actionTypeLabel(value: string) {
  return labelForOption(actionTypeOptions, value);
}

function membershipPlanName(planId?: string | null) {
  if (!planId) {
    return '不赠送会员';
  }
  return membershipPlans.value.find((plan) => plan.id === planId)?.name ?? planId;
}

function userNameById(userId?: string | null) {
  if (!userId) {
    return '未兑换';
  }
  const user = users.value.find((item) => item.id === userId);
  return user?.displayName || user?.phone || userId;
}

function redemptionStatusLabel(status: string) {
  const labels: Record<string, string> = {
    ACTIVE: '未使用',
    REDEEMED: '已兑换',
    DISABLED: '已禁用',
    EXPIRED: '已过期'
  };
  return labels[status] ?? status;
}

const overviewCards = computed(() => {
  const current = overview.value;
  return [
    { label: '用户总数', value: current?.users.total ?? users.value.length, hint: `${current?.users.active ?? 0} 活跃` },
    { label: '会员计划', value: current?.membershipPlans.total ?? membershipPlans.value.length, hint: `${current?.membershipPlans.enabled ?? 0} 启用` },
    { label: '积分余额', value: formatPoints(current?.wallets.totalBalance ?? 0), hint: `冻结 ${formatPoints(current?.wallets.frozenBalance ?? 0)}` },
    { label: '内容资源', value: current ? `${current.content.pages}/${current.content.sections}/${current.content.items}` : '-', hint: '页 / 模块 / 卡片' },
    { label: '模型资源', value: current ? `${current.models.channels}/${current.models.modelConfigs}/${current.models.bindings}` : '-', hint: '渠道 / 模型 / 绑定' },
    { label: '审计日志', value: current?.recentLogs.length ?? auditLogs.value.length, hint: '最近操作' }
  ];
});

onMounted(async () => {
  if (token.value) {
    await run(refreshAdmin);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', resizePreview);
  window.removeEventListener('pointerup', stopPreviewResize);
});

function readStoredModule(): AdminModule {
  const stored = window.localStorage.getItem(moduleStorageKey);
  return adminModules.some((module) => module.key === stored) ? (stored as AdminModule) : 'overview';
}

function readStoredPageKey() {
  return window.localStorage.getItem(pageStorageKey) || 'home';
}

function readStoredUserId() {
  return window.localStorage.getItem(userStorageKey) || '';
}

function setActiveModule(moduleKey: AdminModule) {
  activeModule.value = moduleKey;
  window.localStorage.setItem(moduleStorageKey, moduleKey);
  if (moduleKey === 'courses') {
    void loadAdminCourses();
  }
}

function setSelectedPage(pageKey: string) {
  selectedPageKey.value = pageKey;
  window.localStorage.setItem(pageStorageKey, pageKey);
  void loadSelectedPage();
}

function setSelectedUser(userId: string) {
  selectedUserId.value = userId;
  window.localStorage.setItem(userStorageKey, userId);
}

async function submitLogin() {
  await run(async () => {
    const result = await loginAdmin(loginForm.phone, loginForm.password);
    token.value = result.accessToken;
    currentAdmin.value = result.user;
    notice.value = `已登录：${result.user.displayName || result.user.phone}`;
    await refreshAdmin();
  });
}

async function refreshAdmin() {
  const [
    overviewPayload,
    rawUsers,
    plans,
    memberships,
    transactions,
    logs,
    batches,
    codes,
    rawSlides,
    rawPages,
    chatProfile,
    channels,
    models,
    bindings,
    capabilityPayload
  ] = await Promise.all([
    adminListOverview(),
    adminListUsers({ limit: 500 }),
    adminListMembershipPlans(),
    adminListUserMemberships('', 500),
    adminListWalletTransactions('', 500),
    adminListAuditLogs(auditLimit.value),
    adminListRedemptionBatches(),
    adminListRedemptionCodes(),
    adminListHomeSlides(),
    adminListPages(),
    adminGetChatModelProfile(),
    adminListProviderChannels(),
    adminListModelConfigs(),
    adminListToolModelBindings(),
    adminListWorkbenchCapabilities()
  ]);
  overview.value = overviewPayload;
  users.value = rawUsers;
  membershipPlans.value = plans;
  userMemberships.value = memberships;
  walletTransactions.value = transactions;
  auditLogs.value = logs;
  redemptionBatches.value = batches;
  redemptionCodes.value = codes;
  homeSlides.value = rawSlides;
  pages.value = rawPages.map(normalizePageSummary);
  chatModelProfile.value = chatProfile;
  applyChatModelProfile(chatProfile);
  providerChannels.value = channels;
  modelConfigs.value = models;
  toolModelBindings.value = bindings;
  workbenchCapabilities.value = capabilityPayload.capabilities;

  if (!pages.value.some((page) => page.pageKey === selectedPageKey.value)) {
    selectedPageKey.value = pages.value[0]?.pageKey ?? 'home';
    window.localStorage.setItem(pageStorageKey, selectedPageKey.value);
  }
  if (!users.value.some((user) => user.id === selectedUserId.value)) {
    selectedUserId.value = users.value[0]?.id ?? '';
    if (selectedUserId.value) {
      window.localStorage.setItem(userStorageKey, selectedUserId.value);
    }
  }
  if (!walletUserFilterId.value) {
    walletUserFilterId.value = selectedUserId.value;
  }
  if (!membershipUserFilterId.value) {
    membershipUserFilterId.value = selectedUserId.value;
  }
  await loadSelectedPage();
  await loadAdminCourses();
}

async function loadAdminCourses() {
  courseCatalog.value = await adminListCourses({
    query: courseQuery.value.trim(),
    category: courseCategory.value,
    page: coursePage.value,
    pageSize: 50
  });
}

async function loadSelectedPage() {
  if (!selectedPageKey.value) {
    pageConfig.value = null;
    return;
  }
  const nextPageConfig = await adminFetchPageContent(selectedPageKey.value);
  pageConfig.value = nextPageConfig;
  sectionForm.pageKey = selectedPageKey.value;
  itemForm.sectionId = nextPageConfig.sections[0]?.id ?? '';
}

async function refreshWithNotice() {
  await run(async () => {
    await refreshAdmin();
    notice.value = '后台数据已刷新';
  });
}

async function searchAdminCourses() {
  await run(async () => {
    coursePage.value = 1;
    await loadAdminCourses();
  });
}

async function changeCoursePage(offset: number) {
  const totalPages = Math.max(1, Math.ceil(courseCatalog.value.total / courseCatalog.value.pageSize));
  const nextPage = Math.min(totalPages, Math.max(1, coursePage.value + offset));
  if (nextPage === coursePage.value) {
    return;
  }
  await run(async () => {
    coursePage.value = nextPage;
    await loadAdminCourses();
  });
}

async function cleanupAdminCourses() {
  await run(async () => {
    courseCleanupBusy.value = true;
    try {
      const result = await adminCleanupCourses();
      await loadAdminCourses();
      notice.value = `已清洗 ${result.changed} / ${result.scanned} 个课程，剩余异常 ${result.dirtyRemaining}`;
    } finally {
      courseCleanupBusy.value = false;
    }
  });
}

function openCourseDetail(course: CourseCatalogItem) {
  if (course.detailPath) {
    void router.push(course.detailPath);
  }
}

function openUserPanel(user?: AdminUserSummary) {
  userFormId.value = user?.id ?? '';
  userForm.phone = user?.phone ?? '';
  userForm.displayName = user?.displayName ?? '';
  userForm.role = user?.role ?? 'USER';
  userForm.status = user?.status ?? 'ACTIVE';
  userForm.password = '';
  activePanel.value = 'user';
}

function openWalletPanel(user?: AdminUserSummary) {
  walletAdjustForm.userId = user?.id ?? selectedUser.value?.id ?? users.value[0]?.id ?? '';
  walletAdjustForm.amount = 100;
  walletAdjustForm.reason = '手工调账';
  walletAdjustForm.requestKey = '';
  activePanel.value = 'wallet';
}

function openRedemptionBatchPanel() {
  redemptionBatchForm.name = `兑换码批次 ${redemptionBatches.value.length + 1}`;
  redemptionBatchForm.quantity = 10;
  redemptionBatchForm.points = 0;
  redemptionBatchForm.membershipPlanId = membershipPlans.value[0]?.id ?? '';
  redemptionBatchForm.membershipDays = membershipPlans.value[0]?.durationDays ?? 31;
  redemptionBatchForm.expiresAt = '';
  generatedRedemptionCodes.value = [];
  activePanel.value = 'redemption-batch';
}

function openMembershipPlanPanel(plan?: AdminMembershipPlanSummary) {
  membershipPlanFormId.value = plan?.id ?? '';
  membershipPlanForm.planKey = plan?.planKey ?? '';
  membershipPlanForm.name = plan?.name ?? '';
  membershipPlanForm.priceCents = plan?.priceCents ?? 0;
  membershipPlanForm.durationDays = plan?.durationDays ?? 31;
  membershipPlanForm.entitlementsText = (plan?.entitlements ?? []).join('\n');
  membershipPlanForm.enabled = plan?.enabled ?? true;
  membershipPlanForm.sortOrder = plan?.sortOrder ?? 100;
  activePanel.value = 'membership-plan';
}

function openUserMembershipPanel(membership?: AdminUserMembershipSummary, userId?: string) {
  userMembershipFormId.value = membership?.id ?? '';
  userMembershipForm.userId = userId ?? membership?.userId ?? selectedUser.value?.id ?? users.value[0]?.id ?? '';
  userMembershipForm.planId = membership?.plan.id ?? membershipPlans.value[0]?.id ?? '';
  userMembershipForm.durationDays = membership?.plan.durationDays ?? 31;
  userMembershipForm.status = membership?.status ?? 'ACTIVE';
  userMembershipForm.expiresAt = toDateInput(membership?.expiresAt ?? '');
  activePanel.value = 'user-membership';
}

function openHomeSlidePanel(slide?: HomeDashboardSlide) {
  homeSlideFormId.value = slide?.id ?? '';
  homeSlideForm.title = slide?.title ?? '';
  homeSlideForm.subtitle = slide?.subtitle ?? '';
  homeSlideForm.badge = slide?.badge ?? '';
  homeSlideForm.ctaLabel = slide?.ctaLabel ?? '立即查看';
  homeSlideForm.ctaSubtitle = slide?.ctaSubtitle ?? '';
  homeSlideForm.imageUrl = slide?.imageUrl ?? '';
  homeSlideForm.actionType = slide?.actionType ?? 'route';
  homeSlideForm.actionValue = slide?.actionValue ?? '/membership/benefits';
  homeSlideForm.sortOrder = slide?.sortOrder ?? (homeSlides.value.length + 1) * 10;
  homeSlideForm.enabled = slide?.enabled ?? true;
  homeSlideForm.accent = String(slide?.metadata?.accent ?? 'gold');
  activePanel.value = 'home-slide';
}

function openPagePanel(page?: PageConfigSummary) {
  pageFormId.value = page?.id ?? '';
  pageForm.pageKey = page?.pageKey ?? `page-${pages.value.length + 1}`;
  pageForm.label = page?.label ?? '';
  pageForm.title = page?.title ?? '';
  pageForm.subtitle = page?.subtitle ?? '';
  pageForm.icon = page?.icon ?? 'Sparkles';
  pageForm.sortOrder = page?.sortOrder ?? 100;
  pageForm.enabled = page?.enabled ?? true;
  activePanel.value = 'page';
}

function openSectionPanel(section?: PortalSection) {
  sectionFormId.value = section?.id ?? '';
  sectionForm.pageKey = selectedPageKey.value;
  sectionForm.sectionKey = section?.sectionKey ?? `section-${selectedSections.value.length + 1}`;
  sectionForm.title = section?.title ?? '';
  sectionForm.subtitle = section?.subtitle ?? '';
  sectionForm.layout = section?.layout ?? 'tool-grid';
  sectionForm.sortOrder = section?.sortOrder ?? 100;
  sectionForm.enabled = section?.enabled ?? true;
  activePanel.value = 'section';
}

function openItemPanel(item?: PortalItem, sectionId?: string) {
  itemFormId.value = item?.id ?? '';
  itemForm.sectionId = sectionId ?? item?.sectionId ?? selectedSections.value[0]?.id ?? '';
  itemForm.itemType = item?.itemType ?? 'tool';
  itemForm.title = item?.title ?? '';
  itemForm.subtitle = item?.subtitle ?? '';
  itemForm.category = item?.category ?? '';
  itemForm.icon = item?.icon ?? 'Sparkles';
  itemForm.imageUrl = item?.imageUrl ?? '';
  itemForm.badge = item?.badge ?? '';
  itemForm.tagsText = (item?.tags ?? []).join(', ');
  itemForm.sortOrder = item?.sortOrder ?? 100;
  itemForm.enabled = item?.enabled ?? true;
  itemForm.actionType = item?.actionType ?? 'route';
  itemForm.actionValue = item?.actionValue ?? '';
  itemForm.requiredMembership = item?.requiredMembership ?? false;
  itemForm.pointCost = item?.pointCost ?? 0;
  const detail = (item?.metadata?.detail ?? {}) as Record<string, any>;
  itemForm.detailSummary = detail.summary ?? '';
  itemForm.detailHighlightsText = joinLines(detail.highlights);
  itemForm.detailStepsText = joinLines(detail.steps);
  itemForm.detailDeliverablesText = joinLines(detail.deliverables);
  itemForm.detailFaqsText = joinFaqLines(detail.faqs);
  itemForm.detailPrimaryActionKey = detail.primaryAction?.key ?? 'enroll';
  itemForm.detailPrimaryActionLabel = detail.primaryAction?.label ?? '报名';
  itemForm.detailSecondaryActionsText = joinSecondaryActions(detail.secondaryActions);
  itemForm.detailDownloadFileName = detail.download?.fileName ?? '';
  itemForm.detailDownloadUrl = detail.download?.url ?? '';
  activePanel.value = 'item';
}

function applyProviderPreset(presetKey: string) {
  const preset = providerPresetByKey(presetKey);
  Object.assign(providerChannelForm, {
    displayName: preset.label,
    channelType: preset.defaults.channelType,
    adapterType: preset.defaults.adapterType,
    baseUrl: preset.defaults.baseUrl,
    remark: preset.defaults.remark,
    website: preset.defaults.website,
    useFullUrl: preset.defaults.useFullUrl,
    authJsonText: preset.defaults.authJsonText,
    configTomlText: preset.defaults.configTomlText,
    writeCommonConfig: preset.defaults.writeCommonConfig,
    testConfigText: preset.defaults.testConfigText,
    billingConfigText: preset.defaults.billingConfigText,
    presetKey: preset.key
  });
}

function openProviderChannelPanel(channel?: ProviderChannelSummary) {
  providerChannelFormId.value = channel?.id ?? '';
  const metadata = (channel?.metadataJson ?? {}) as Record<string, unknown>;
  const preset = providerPresetByKey(String(metadata.preset_key ?? 'custom'));
  applyProviderPreset(preset.key);
  providerChannelForm.channelKey = channel?.channelKey ?? '';
  providerChannelForm.displayName = channel?.displayName ?? preset.label;
  providerChannelForm.baseUrl = channel?.baseUrl ?? preset.defaults.baseUrl;
  providerChannelForm.apiKey = '';
  providerChannelForm.channelType = channel?.channelType ?? preset.defaults.channelType;
  providerChannelForm.adapterType = channel?.adapterType ?? preset.defaults.adapterType;
  providerChannelForm.priority = channel?.priority ?? 100;
  providerChannelForm.enabled = channel?.enabled ?? true;
  providerChannelForm.timeoutSeconds = channel?.timeoutSeconds ?? 60;
  providerChannelForm.presetKey = preset.key;
  providerChannelForm.remark = String(metadata.remark ?? preset.defaults.remark ?? '');
  providerChannelForm.website = String(metadata.website ?? preset.defaults.website ?? '');
  providerChannelForm.useFullUrl = metadataBoolean(metadata.use_full_url, preset.defaults.useFullUrl);
  providerChannelForm.authJsonText = metadataText(metadata.auth_json) || preset.defaults.authJsonText;
  providerChannelForm.configTomlText = String(metadata.config_toml ?? preset.defaults.configTomlText ?? '');
  providerChannelForm.writeCommonConfig = metadataBoolean(metadata.write_common_config, preset.defaults.writeCommonConfig);
  providerChannelForm.testConfigText = String(metadata.test_config ?? preset.defaults.testConfigText ?? '');
  providerChannelForm.billingConfigText = String(metadata.billing_config ?? preset.defaults.billingConfigText ?? '');
  providerChannelForm.metadataJson = metadata;
  activePanel.value = 'provider-channel';
}

function applyChatModelProfile(payload: ChatModelProfilePayload) {
  const profile = payload.profile;
  chatModelProfileForm.channelKey = profile.channelKey;
  chatModelProfileForm.providerName = profile.providerName || '中转';
  chatModelProfileForm.note = profile.note;
  chatModelProfileForm.officialUrl = profile.officialUrl;
  chatModelProfileForm.baseUrl = profile.baseUrl;
  chatModelProfileForm.apiKey = '';
  chatModelProfileForm.savedApiKeyMask = payload.provider?.apiKeyMask ?? '';
  chatModelProfileForm.modelName = profile.modelName;
  chatModelProfileForm.modelKey = profile.modelKey;
  chatModelProfileForm.displayName = profile.displayName || profile.modelName;
  chatModelProfileForm.modelReasoningEffort = profile.modelReasoningEffort;
  chatModelProfileForm.providerReasoningEffort = profile.providerReasoningEffort;
  chatModelProfileForm.serviceTier = profile.serviceTier;
  chatModelProfileForm.contextWindow = profile.contextWindow;
  chatModelProfileForm.autoCompactTokenLimit = profile.autoCompactTokenLimit;
  chatModelProfileForm.disableResponseStorage = profile.disableResponseStorage;
  chatModelProfileForm.defaultPointCost = profile.defaultPointCost;
  chatModelProfileForm.timeoutSeconds = profile.timeoutSeconds;
  chatModelProfileForm.enabled = profile.enabled;
}

function openModelConfigPanel(model?: ModelConfigSummary) {
  modelConfigFormId.value = model?.id ?? '';
  const metadata = model?.metadataJson ?? {};
  modelConfigForm.modelKey = model?.modelKey ?? '';
  modelConfigForm.displayName = model?.displayName ?? '';
  modelConfigForm.capability = model?.capability ?? 'TEXT';
  modelConfigForm.channelId = model?.channelId ?? providerChannels.value[0]?.id ?? '';
  modelConfigForm.providerModel = model?.providerModel ?? '';
  modelConfigForm.defaultPointCost = model?.defaultPointCost ?? 0;
  modelConfigForm.enabled = model?.enabled ?? true;
  modelConfigForm.useMillionContextWindow = metadataBoolean(metadata.use_million_context_window, false);
  modelConfigForm.compressionThreshold = metadataNumber(metadata.compression_threshold, 900000);
  modelConfigForm.testConfigText = String(metadata.test_config ?? '');
  modelConfigForm.billingConfigText = String(metadata.billing_config ?? '');
  modelConfigForm.metadataJson = metadata;
  activePanel.value = 'model-config';
}

function openToolBindingPanel(binding?: ToolModelBindingSummary) {
  toolBindingFormId.value = binding?.id ?? '';
  toolBindingForm.targetType = binding?.targetType ?? 'builtin';
  toolBindingForm.targetKey = binding?.targetKey ?? '';
  toolBindingForm.modelConfigId = binding?.modelConfigId ?? modelConfigs.value[0]?.id ?? '';
  toolBindingForm.pointCostOverride = binding?.pointCostOverride ?? null;
  toolBindingForm.enabled = binding?.enabled ?? true;
  activePanel.value = 'tool-binding';
}

function openWorkbenchCapabilityPanel(capability: WorkbenchCapability) {
  workbenchCapabilityForm.targetType = capability.targetType;
  workbenchCapabilityForm.targetKey = capability.targetKey;
  workbenchCapabilityForm.title = capability.title;
  workbenchCapabilityForm.modelConfigId = capability.modelConfig?.id ?? modelConfigs.value[0]?.id ?? '';
  workbenchCapabilityForm.pointCostOverride = capability.effectivePointCost;
  workbenchCapabilityForm.enabled = capability.enabled;
  activePanel.value = 'workbench-capability';
}

async function saveUser() {
  await run(async () => {
    const payload = {
      phone: userForm.phone.trim(),
      displayName: userForm.displayName.trim(),
      role: userForm.role,
      status: userForm.status,
      ...(userForm.password.trim() ? { password: userForm.password.trim() } : {})
    };
    if (userFormId.value) {
      await adminUpdateUser(userFormId.value, payload);
      notice.value = '人员信息已更新';
    } else {
      await adminCreateUser({ ...payload, password: userForm.password.trim() || 'admin123456' });
      notice.value = '人员已创建';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function disableUser(user: AdminUserSummary) {
  await run(async () => {
    await adminDeleteUser(user.id);
    notice.value = `已禁用 ${user.displayName || user.phone}`;
    await refreshAdmin();
  });
}

async function saveWalletAdjustment() {
  await run(async () => {
    await adminAdjustWallet(walletAdjustForm.userId, {
      amount: Number(walletAdjustForm.amount),
      reason: walletAdjustForm.reason.trim(),
      requestKey: walletAdjustForm.requestKey.trim() || undefined
    });
    notice.value = '积分已调整';
    closePanel();
    await refreshAdmin();
  });
}

async function saveRedemptionBatch() {
  await run(async () => {
    const result = await adminCreateRedemptionBatch({
      name: redemptionBatchForm.name.trim(),
      quantity: Number(redemptionBatchForm.quantity),
      points: Number(redemptionBatchForm.points),
      membershipPlanId: redemptionBatchForm.membershipPlanId || undefined,
      membershipDays: redemptionBatchForm.membershipDays ? Number(redemptionBatchForm.membershipDays) : undefined,
      expiresAt: redemptionBatchForm.expiresAt ? new Date(redemptionBatchForm.expiresAt).toISOString() : undefined
    });
    generatedRedemptionCodes.value = result.codes;
    notice.value = `已批量生成 ${result.codes.length} 个兑换码`;
    await refreshAdmin();
  });
}

async function disableRedemptionCode(code: AdminRedemptionCodeSummary) {
  await run(async () => {
    await adminDisableRedemptionCode(code.id);
    notice.value = '兑换码已禁用';
    await refreshAdmin();
  });
}

async function saveMembershipPlan() {
  await run(async () => {
    const payload = {
      planKey: membershipPlanForm.planKey.trim(),
      name: membershipPlanForm.name.trim(),
      priceCents: Number(membershipPlanForm.priceCents),
      durationDays: Number(membershipPlanForm.durationDays),
      entitlements: splitLines(membershipPlanForm.entitlementsText),
      enabled: membershipPlanForm.enabled,
      sortOrder: Number(membershipPlanForm.sortOrder)
    };
    if (membershipPlanFormId.value) {
      await adminUpdateMembershipPlan(membershipPlanFormId.value, payload);
      notice.value = '会员计划已更新';
    } else {
      await adminCreateMembershipPlan(payload);
      notice.value = '会员计划已创建';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function disableMembershipPlan(plan: AdminMembershipPlanSummary) {
  await run(async () => {
    await adminDeleteMembershipPlan(plan.id);
    notice.value = `已停用 ${plan.name}`;
    await refreshAdmin();
  });
}

async function saveUserMembership() {
  await run(async () => {
    if (userMembershipFormId.value) {
      await adminUpdateUserMembership(userMembershipFormId.value, {
        planId: userMembershipForm.planId,
        status: userMembershipForm.status,
        expiresAt: userMembershipForm.expiresAt || undefined
      });
      notice.value = '会员记录已更新';
    } else {
      await adminGrantMembership({
        userId: userMembershipForm.userId,
        planId: userMembershipForm.planId,
        durationDays: Number(userMembershipForm.durationDays),
        status: userMembershipForm.status
      });
      notice.value = '会员已开通';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function disableUserMembership(membership: AdminUserMembershipSummary) {
  await run(async () => {
    await adminDeleteUserMembership(membership.id);
    notice.value = '会员记录已停用';
    await refreshAdmin();
  });
}

async function saveHomeSlide() {
  await run(async () => {
    const current = homeSlides.value.find((slide) => slide.id === homeSlideFormId.value);
    const payload = buildHomeSlidePayload({
      title: homeSlideForm.title.trim(),
      subtitle: homeSlideForm.subtitle.trim(),
      badge: homeSlideForm.badge.trim(),
      ctaLabel: homeSlideForm.ctaLabel.trim(),
      ctaSubtitle: homeSlideForm.ctaSubtitle.trim(),
      imageUrl: homeSlideForm.imageUrl.trim(),
      actionType: homeSlideForm.actionType,
      actionValue: homeSlideForm.actionValue.trim(),
      sortOrder: Number(homeSlideForm.sortOrder),
      enabled: homeSlideForm.enabled,
      metadataJson: {
        ...(current?.metadata ?? {}),
        accent: homeSlideForm.accent
      }
    });
    if (homeSlideFormId.value) {
      await adminUpdateHomeSlide(homeSlideFormId.value, payload);
      notice.value = '首页轮播已更新';
    } else {
      await adminCreateHomeSlide(payload);
      notice.value = '首页轮播已创建';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function moveHomeSlide(slideId: string, direction: -1 | 1) {
  const nextSlides = moveRecord(homeSlides.value, slideId, direction);
  if (!nextSlides) {
    return;
  }
  await run(async () => {
    await adminReorderHomeSlides(nextSlides);
    notice.value = '首页轮播顺序已调整';
    await refreshAdmin();
  });
}

async function dropHomeSlide(targetId: string) {
  if (!draggedHomeSlideId.value || draggedHomeSlideId.value === targetId) {
    return;
  }
  const nextSlides = reorderByDrop(homeSlides.value, draggedHomeSlideId.value, targetId);
  draggedHomeSlideId.value = '';
  activeDropHomeSlideId.value = '';
  if (!nextSlides) {
    return;
  }
  await run(async () => {
    await adminReorderHomeSlides(nextSlides);
    notice.value = '首页轮播顺序已调整';
    await refreshAdmin();
  });
}

async function toggleHomeSlideVisibility(slide: HomeDashboardSlide) {
  await run(async () => {
    if (slide.enabled) {
      await adminDeleteHomeSlide(slide.id);
      notice.value = '首页轮播已停用';
    } else {
      await adminUpdateHomeSlide(slide.id, { enabled: true });
      notice.value = '首页轮播已启用';
    }
    await refreshAdmin();
  });
}

async function savePage() {
  await run(async () => {
    const payload = buildPagePayload(pageForm);
    if (pageFormId.value) {
      await adminUpdatePage(pageFormId.value, payload);
      notice.value = '页面已更新';
    } else {
      await adminCreatePage(payload);
      notice.value = '页面已创建';
      setSelectedPage(pageForm.pageKey);
    }
    closePanel();
    await refreshAdmin();
  });
}

async function disablePage(page: PageConfigSummary) {
  if (!page.id) {
    return;
  }
  await run(async () => {
    await adminDeletePage(page.id!);
    notice.value = '页面已停用';
    await refreshAdmin();
  });
}

async function saveSection() {
  await run(async () => {
    const payload = buildSectionPayload(sectionForm);
    if (sectionFormId.value) {
      await adminUpdateSection(sectionFormId.value, payload);
      notice.value = '模块已更新';
    } else {
      await adminCreateSection(payload);
      notice.value = '模块已创建';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function disableSection(section: PortalSection) {
  await run(async () => {
    await adminDeleteSection(section.id);
    notice.value = '模块已停用';
    await refreshAdmin();
  });
}

async function saveItem() {
  await run(async () => {
    const payload = buildItemPayload({
      ...itemForm,
      tags: splitLines(itemForm.tagsText)
    });
    if (itemFormId.value) {
      await adminUpdateItem(itemFormId.value, payload);
      notice.value = '卡片已更新';
    } else {
      await adminCreateItem(payload);
      notice.value = '卡片已创建';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function disableItem(item: PortalItem) {
  await run(async () => {
    await adminDeleteItem(item.id);
    notice.value = '卡片已停用';
    await refreshAdmin();
  });
}

async function saveProviderChannel() {
  await run(async () => {
    const payload = buildProviderChannelPayload(providerChannelForm);
    if (providerChannelFormId.value) {
      await adminUpdateProviderChannel(providerChannelFormId.value, payload);
      notice.value = '渠道已更新';
    } else {
      await adminCreateProviderChannel(payload);
      notice.value = '渠道已创建';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function saveChatModelProfile() {
  await run(async () => {
    const payload = buildChatModelProfilePayload({
      channelKey: chatModelProfileForm.channelKey.trim(),
      providerName: chatModelProfileForm.providerName.trim(),
      note: chatModelProfileForm.note.trim(),
      officialUrl: chatModelProfileForm.officialUrl.trim(),
      baseUrl: chatModelProfileForm.baseUrl.trim(),
      apiKey: chatModelProfileForm.apiKey.trim(),
      modelName: chatModelProfileForm.modelName.trim(),
      modelKey: chatModelProfileForm.modelKey.trim(),
      displayName: chatModelProfileForm.displayName.trim(),
      modelReasoningEffort: chatModelProfileForm.modelReasoningEffort,
      providerReasoningEffort: chatModelProfileForm.providerReasoningEffort,
      serviceTier: chatModelProfileForm.serviceTier,
      contextWindow: Number(chatModelProfileForm.contextWindow),
      autoCompactTokenLimit: Number(chatModelProfileForm.autoCompactTokenLimit),
      disableResponseStorage: chatModelProfileForm.disableResponseStorage,
      defaultPointCost: Number(chatModelProfileForm.defaultPointCost),
      timeoutSeconds: Number(chatModelProfileForm.timeoutSeconds),
      enabled: chatModelProfileForm.enabled
    });
    const saved = await adminUpdateChatModelProfile({
      channelKey: String(payload.channel_key),
      providerName: String(payload.provider_name),
      note: String(payload.note),
      officialUrl: String(payload.official_url),
      baseUrl: String(payload.base_url),
      apiKey: String(payload.api_key),
      modelName: String(payload.model_name),
      modelKey: String(payload.model_key),
      displayName: String(payload.display_name),
      modelReasoningEffort: String(payload.model_reasoning_effort),
      providerReasoningEffort: String(payload.provider_reasoning_effort),
      serviceTier: String(payload.service_tier),
      contextWindow: Number(payload.context_window),
      autoCompactTokenLimit: Number(payload.auto_compact_token_limit),
      disableResponseStorage: Boolean(payload.disable_response_storage),
      defaultPointCost: Number(payload.default_point_cost),
      timeoutSeconds: Number(payload.timeout_seconds),
      enabled: Boolean(payload.enabled)
    });
    chatModelProfile.value = saved;
    applyChatModelProfile(saved);
    notice.value = 'AI 对话模型配置已保存，工作台模型已同步';
    await refreshAdmin();
  });
}

async function saveModelConfig() {
  await run(async () => {
    const payload = buildModelConfigPayload(modelConfigForm);
    if (modelConfigFormId.value) {
      await adminUpdateModelConfig(modelConfigFormId.value, payload);
      notice.value = '模型已更新';
    } else {
      await adminCreateModelConfig(payload);
      notice.value = '模型已创建';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function saveToolBinding() {
  await run(async () => {
    const payload = buildToolModelBindingPayload(toolBindingForm);
    if (toolBindingFormId.value) {
      await adminUpdateToolModelBinding(toolBindingFormId.value, payload);
      notice.value = '绑定已更新';
    } else {
      await adminCreateToolModelBinding(payload);
      notice.value = '绑定已创建';
    }
    closePanel();
    await refreshAdmin();
  });
}

async function saveWorkbenchCapability() {
  await run(async () => {
    await adminUpdateWorkbenchCapability({
      targetType: workbenchCapabilityForm.targetType,
      targetKey: workbenchCapabilityForm.targetKey,
      modelConfigId: workbenchCapabilityForm.modelConfigId,
      pointCostOverride: workbenchCapabilityForm.pointCostOverride,
      enabled: workbenchCapabilityForm.enabled
    });
    notice.value = '工作台能力已更新';
    closePanel();
    await refreshAdmin();
  });
}

async function toggleWorkbenchCapability(capability: WorkbenchCapability) {
  await run(async () => {
    await adminUpdateWorkbenchCapability({
      targetType: capability.targetType,
      targetKey: capability.targetKey,
      modelConfigId: capability.modelConfig?.id ?? modelConfigs.value[0]?.id ?? '',
      pointCostOverride: capability.effectivePointCost,
      enabled: !capability.enabled
    });
    notice.value = capability.enabled ? '工作台能力已停用' : '工作台能力已启用';
    await refreshAdmin();
  });
}

async function togglePageVisibility(page: PageConfigSummary) {
  const pageId = page.id;
  if (!pageId) {
    return;
  }
  await run(async () => {
    await adminUpdatePage(pageId, { enabled: !page.enabled });
    notice.value = page.enabled ? '页面已停用' : '页面已启用';
    await refreshAdmin();
  });
}

async function toggleSectionVisibility(section: PortalSection) {
  await run(async () => {
    await adminUpdateSection(section.id, { enabled: !section.enabled });
    notice.value = section.enabled ? '模块已停用' : '模块已启用';
    await refreshAdmin();
  });
}

async function toggleItemVisibility(item: PortalItem) {
  await run(async () => {
    await adminUpdateItem(item.id, { enabled: !item.enabled });
    notice.value = item.enabled ? '卡片已停用' : '卡片已启用';
    await refreshAdmin();
  });
}

async function toggleProviderChannel(channel: ProviderChannelSummary) {
  await run(async () => {
    await adminUpdateProviderChannel(channel.id, { enabled: !channel.enabled });
    notice.value = channel.enabled ? '渠道已停用' : '渠道已启用';
    await refreshAdmin();
  });
}

async function toggleModelConfig(model: ModelConfigSummary) {
  await run(async () => {
    await adminUpdateModelConfig(model.id, { enabled: !model.enabled });
    notice.value = model.enabled ? '模型已停用' : '模型已启用';
    await refreshAdmin();
  });
}

async function toggleToolBinding(binding: ToolModelBindingSummary) {
  await run(async () => {
    await adminUpdateToolModelBinding(binding.id, { enabled: !binding.enabled });
    notice.value = binding.enabled ? '绑定已停用' : '绑定已启用';
    await refreshAdmin();
  });
}

async function movePage(pageId: string, direction: -1 | 1) {
  const nextPages = moveRecord(
    pages.value.filter((page): page is PageConfigSummary & { id: string } => Boolean(page.id)),
    pageId,
    direction
  );
  if (!nextPages) {
    return;
  }
  await savePageOrder(nextPages);
}

async function dropPage(targetPageId?: string) {
  if (!targetPageId) {
    return;
  }
  const nextPages = reorderByDrop(
    pages.value.filter((page): page is PageConfigSummary & { id: string } => Boolean(page.id)),
    draggedPageId.value,
    targetPageId
  );
  draggedPageId.value = '';
  activeDropPageId.value = '';
  if (!nextPages) {
    return;
  }
  await savePageOrder(nextPages);
}

async function savePageOrder(nextPages: Array<PageConfigSummary & { id: string }>) {
  await run(async () => {
    await adminReorderPages(buildReorderPayload(nextPages.map((page) => ({ id: page.id }))));
    notice.value = '页面顺序已保存';
    await refreshAdmin();
  });
}

async function moveSection(sectionId: string, direction: -1 | 1) {
  const nextSections = moveRecord(selectedSections.value, sectionId, direction);
  if (!nextSections) {
    return;
  }
  await saveSectionOrder(nextSections);
}

async function dropSection(targetSectionId: string) {
  const nextSections = reorderByDrop(selectedSections.value, draggedSectionId.value, targetSectionId);
  draggedSectionId.value = '';
  activeDropSectionId.value = '';
  if (!nextSections) {
    return;
  }
  await saveSectionOrder(nextSections);
}

async function saveSectionOrder(nextSections: PortalSection[]) {
  await run(async () => {
    await adminReorderSections(buildReorderPayload(nextSections));
    notice.value = '模块顺序已保存';
    await refreshAdmin();
  });
}

async function moveItem(itemId: string, direction: -1 | 1) {
  const section = selectedSections.value.find((candidate) => candidate.items.some((item) => item.id === itemId));
  if (!section) {
    return;
  }
  const nextItems = moveRecord(section.items, itemId, direction);
  if (!nextItems) {
    return;
  }
  await saveItemOrder(section.id, nextItems);
}

async function dropItem(section: PortalSection, targetItemId: string) {
  const nextItems = reorderByDrop(section.items, draggedItemId.value, targetItemId);
  draggedItemId.value = '';
  activeDropItemId.value = '';
  if (!nextItems) {
    return;
  }
  await saveItemOrder(section.id, nextItems);
}

async function saveItemOrder(sectionId: string, nextItems: PortalItem[]) {
  await run(async () => {
    await adminReorderItems(buildReorderPayload(nextItems, sectionId));
    notice.value = '卡片顺序已保存';
    await refreshAdmin();
  });
}

async function uploadImage(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }
  await run(async () => {
    const result = await adminUploadImage(file);
    itemForm.imageUrl = result.url;
    notice.value = '图片已上传';
  });
}

function closePanel() {
  activePanel.value = '';
  userFormId.value = '';
  walletAdjustForm.requestKey = '';
  membershipPlanFormId.value = '';
  userMembershipFormId.value = '';
  homeSlideFormId.value = '';
  pageFormId.value = '';
  sectionFormId.value = '';
  itemFormId.value = '';
  providerChannelFormId.value = '';
  modelConfigFormId.value = '';
  toolBindingFormId.value = '';
}

function logout() {
  clearAdminToken();
  token.value = '';
  currentAdmin.value = null;
  overview.value = null;
  users.value = [];
  membershipPlans.value = [];
  userMemberships.value = [];
  walletTransactions.value = [];
  auditLogs.value = [];
  homeSlides.value = [];
  pages.value = [];
  providerChannels.value = [];
  modelConfigs.value = [];
  toolModelBindings.value = [];
  workbenchCapabilities.value = [];
  pageConfig.value = null;
  notice.value = '';
  errorMessage.value = '';
}

function setPreviewScale(value: number) {
  previewScale.value = clampPreviewScale(value);
}

function nudgePreviewScale(delta: number) {
  setPreviewScale(previewScale.value + delta);
}

function startPreviewResize(event: PointerEvent) {
  event.preventDefault();
  resizeStartX = event.clientX;
  resizeStartWidth = previewWidth.value;
  window.addEventListener('pointermove', resizePreview);
  window.addEventListener('pointerup', stopPreviewResize);
}

let resizeStartX = 0;
let resizeStartWidth = 0;

function resizePreview(event: PointerEvent) {
  const delta = event.clientX - resizeStartX;
  previewWidth.value = Math.min(980, Math.max(380, resizeStartWidth - delta));
}

function stopPreviewResize() {
  window.removeEventListener('pointermove', resizePreview);
  window.removeEventListener('pointerup', stopPreviewResize);
}

function normalizePageSummary(page: any): PageConfigSummary {
  return {
    id: page.id,
    tenantId: page.tenant_id ?? page.tenantId,
    pageKey: page.page_key ?? page.pageKey,
    label: page.label ?? '',
    title: page.title ?? '',
    subtitle: page.subtitle ?? '',
    icon: page.icon ?? 'Sparkles',
    sortOrder: Number(page.sort_order ?? page.sortOrder ?? 100),
    enabled: Boolean(page.enabled ?? true)
  };
}

function splitLines(value?: string) {
  return String(value ?? '')
    .split(/[\n,，]/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function joinLines(value: unknown) {
  return Array.isArray(value) ? value.map((line) => String(line).trim()).filter(Boolean).join('\n') : '';
}

function joinFaqLines(value: unknown) {
  if (!Array.isArray(value)) {
    return '';
  }
  return value
    .map((item) => {
      const question = String(item?.question ?? '').trim();
      const answer = String(item?.answer ?? '').trim();
      return question || answer ? `${question}|${answer}` : '';
    })
    .filter(Boolean)
    .join('\n');
}

function joinSecondaryActions(value: unknown) {
  if (!Array.isArray(value)) {
    return '';
  }
  return value
    .map((item) => {
      const key = String(item?.key ?? '').trim();
      const label = String(item?.label ?? '').trim();
      return key || label ? `${key}|${label}` : '';
    })
    .filter(Boolean)
    .join('\n');
}

function parseMetadataJson(value?: string): Record<string, unknown> | undefined {
  const raw = String(value ?? '').trim();
  if (!raw) {
    return undefined;
  }
  const parsed = JSON.parse(raw);
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('渠道元数据必须是 JSON 对象');
  }
  return parsed as Record<string, unknown>;
}

function toDateInput(value?: string) {
  if (!value) {
    return '';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value.slice(0, 10);
  }
  return date.toISOString().slice(0, 10);
}

function formatPoints(value: number | string) {
  return Number(value || 0).toLocaleString('zh-CN');
}

function formatMoney(cents: number) {
  return `¥${(Number(cents || 0) / 100).toFixed(2)}`;
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return '未设置';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString('zh-CN', { hour12: false });
}

function formatDate(value?: string | null) {
  if (!value) {
    return '未设置';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString('zh-CN');
}

function roleLabel(role: string) {
  const labels: Record<string, string> = {
    SUPER_ADMIN: '超级管理员',
    ADMIN: '管理员',
    OPERATOR: '运营',
    CONTENT_EDITOR: '内容编辑',
    READ_ONLY: '只读',
    USER: '普通成员'
  };
  return labels[role] ?? role;
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    ACTIVE: '启用',
    INACTIVE: '停用',
    DISABLED: '停用',
    EXPIRED: '过期'
  };
  return labels[status] ?? status;
}

function membershipStatusLabel(status: string) {
  const labels: Record<string, string> = {
    ACTIVE: '生效',
    EXPIRED: '过期',
    CANCELLED: '取消',
    DISABLED: '停用'
  };
  return labels[status] ?? status;
}

function auditActionLabel(action: string) {
  const labels: Record<string, string> = {
    'user.create': '创建人员',
    'user.update': '更新人员',
    'user.disable': '停用人员',
    'wallet.adjust': '积分调账',
    'membership_plan.create': '创建会员计划',
    'membership_plan.update': '更新会员计划',
    'membership_plan.disable': '停用会员计划',
    'membership.grant': '开通会员',
    'membership.update': '更新会员',
    'membership.disable': '停用会员',
    'content.page.create': '创建页面',
    'content.section.create': '创建模块',
    'content.item.create': '创建卡片',
    'model.create': '创建模型',
    'model.update': '更新模型'
  };
  return labels[action] ?? action;
}

async function run(task: () => Promise<void>) {
  errorMessage.value = '';
  try {
    await task();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '操作失败';
  }
}
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <div class="admin-brand">
        <button class="back-link" type="button" @click="router.push('/home')">
          <ArrowLeft :size="18" />
          返回前台
        </button>
        <h1>新商机管理后台</h1>
        <p>人员、会员、积分、内容和模型统一管理。</p>
      </div>

      <nav class="admin-nav">
        <button
          v-for="module in adminModules"
          :key="module.key"
          type="button"
          :class="['admin-nav-item', { active: activeModule === module.key }]"
          @click="setActiveModule(module.key)"
        >
          <component :is="module.icon" :size="18" />
          <span>{{ module.label }}</span>
        </button>
      </nav>

      <div class="admin-sidebar-footer">
        <div class="admin-identity">
          <strong>{{ currentAdmin?.displayName ?? '管理员' }}</strong>
          <span>{{ roleLabel(currentAdmin?.role ?? 'ADMIN') }}</span>
        </div>
        <button v-if="token" class="ghost-btn" type="button" @click="logout">
          <Lock :size="18" />
          退出登录
        </button>
      </div>
    </aside>

    <main class="admin-main">
      <section v-if="!token" class="admin-login">
        <div class="admin-login-card">
          <h2>管理端登录</h2>
          <p>使用管理员账号进入运营控制台。</p>
          <label>手机号<input v-model="loginForm.phone" autocomplete="username" /></label>
          <label>密码<input v-model="loginForm.password" type="password" autocomplete="current-password" /></label>
          <button class="primary-btn" type="button" @click="submitLogin">登录管理端</button>
        </div>
      </section>

      <template v-else>
        <header class="admin-topbar">
          <div class="admin-topbar-title">
            <span>{{ activeModuleMeta.label }}</span>
            <h2>{{ moduleDescription }}</h2>
          </div>
          <div class="admin-topbar-actions">
            <button class="ghost-btn" type="button" @click="refreshWithNotice">
              <RefreshCw :size="18" />
              刷新
            </button>
            <button class="ghost-btn" type="button" @click="setPreviewScale(0.55)">
              <Maximize2 :size="18" />
              适配预览
            </button>
          </div>
        </header>

        <p v-if="notice" class="notice">{{ notice }}</p>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <section v-if="activeModule === 'overview'" class="admin-panel">
          <div class="admin-summary-grid">
            <article v-for="card in overviewCards" :key="card.label" class="admin-summary-card">
              <span>{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
              <small>{{ card.hint }}</small>
            </article>
          </div>

          <section class="admin-table-panel">
            <header class="panel-header">
              <div>
                <strong>最近审计</strong>
                <span>高风险操作和关键变更</span>
              </div>
              <button class="ghost-btn" type="button" @click="setActiveModule('audit')">查看全部</button>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>动作</th>
                  <th>对象</th>
                  <th>操作者</th>
                  <th>摘要</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in (overview?.recentLogs ?? auditLogs.slice(0, 5))" :key="log.id">
                  <td>{{ formatDateTime(log.createdAt) }}</td>
                  <td>{{ auditActionLabel(log.action) }}</td>
                  <td>{{ log.targetType }} / {{ log.targetId || '全部' }}</td>
                  <td>{{ log.actorDisplayName }} · {{ roleLabel(log.actorRole) }}</td>
                  <td>{{ log.summary }}</td>
                </tr>
              </tbody>
            </table>
          </section>
        </section>

        <section v-else-if="activeModule === 'users'" class="admin-panel">
          <header class="panel-header">
            <div>
              <strong>人员管理</strong>
              <span>新增、编辑、禁用和积分操作</span>
            </div>
            <button class="primary-btn" type="button" @click="openUserPanel()">
              <UserPlus :size="18" />
              新增人员
            </button>
          </header>

          <div class="admin-filters">
            <label class="search-field">
              <Search :size="16" />
              <input v-model="userQuery" placeholder="搜索手机号或昵称" />
            </label>
            <select v-model="userRoleFilter">
              <option value="">全部角色</option>
              <option value="USER">普通成员</option>
              <option value="READ_ONLY">只读</option>
              <option value="CONTENT_EDITOR">内容编辑</option>
              <option value="OPERATOR">运营</option>
              <option value="ADMIN">管理员</option>
              <option value="SUPER_ADMIN">超级管理员</option>
            </select>
            <select v-model="userStatusFilter">
              <option value="">全部状态</option>
              <option value="ACTIVE">启用</option>
              <option value="INACTIVE">停用</option>
            </select>
          </div>

          <table class="admin-table">
            <thead>
              <tr>
                <th>手机号</th>
                <th>名称</th>
                <th>角色</th>
                <th>状态</th>
                <th>积分</th>
                <th>会员</th>
                <th>更新时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in filteredUsers"
                :key="user.id"
                :class="{ selected: selectedUserId === user.id }"
                @click="setSelectedUser(user.id)"
              >
                <td>{{ user.phone }}</td>
                <td>
                  <strong>{{ user.displayName }}</strong>
                  <small>{{ user.id }}</small>
                </td>
                <td>{{ roleLabel(user.role) }}</td>
                <td><span :class="['status-pill', user.status.toLowerCase()]">{{ statusLabel(user.status) }}</span></td>
                <td>{{ formatPoints(user.balance) }}</td>
                <td>
                  <div class="stacked-text">
                    <strong>{{ user.membershipPlanName || '未开通' }}</strong>
                    <span>{{ user.membershipStatus ? membershipStatusLabel(user.membershipStatus) : '无记录' }}</span>
                  </div>
                </td>
                <td>{{ formatDateTime(user.updatedAt || user.createdAt) }}</td>
                <td>
                  <div class="row-actions">
                    <button class="icon-btn" type="button" title="编辑" @click.stop="openUserPanel(user)">
                      <Pencil :size="16" />
                    </button>
                    <button class="icon-btn" type="button" title="积分调整" @click.stop="openWalletPanel(user)">
                      <Coins :size="16" />
                    </button>
                    <button class="icon-btn" type="button" title="开通会员" @click.stop="openUserMembershipPanel(undefined, user.id)">
                      <UserPlus :size="16" />
                    </button>
                    <button class="icon-btn danger" type="button" title="停用" @click.stop="disableUser(user)">
                      <Trash2 :size="16" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <section v-else-if="activeModule === 'memberships'" class="admin-panel">
          <header class="panel-header">
            <div>
              <strong>会员管理</strong>
              <span>会员计划与开通记录</span>
            </div>
            <div class="panel-actions">
              <button class="ghost-btn" type="button" @click="openUserMembershipPanel(undefined, selectedUser?.id)">
                <UserPlus :size="18" />
                新增会员
              </button>
              <button class="primary-btn" type="button" @click="openMembershipPlanPanel()">
                <Plus :size="18" />
                新增会员计划
              </button>
            </div>
          </header>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>会员计划</strong>
                <span>软停用，不做硬删除</span>
              </div>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>名称</th>
                  <th>价格</th>
                  <th>周期</th>
                  <th>权益</th>
                  <th>激活用户</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="plan in membershipPlans" :key="plan.id">
                  <td>{{ plan.planKey }}</td>
                  <td>
                    <strong>{{ plan.name }}</strong>
                    <small>{{ plan.id }}</small>
                  </td>
                  <td>{{ formatMoney(plan.priceCents) }}</td>
                  <td>{{ plan.durationDays }} 天</td>
                  <td>{{ plan.entitlements.length ? plan.entitlements.join('、') : '无' }}</td>
                  <td>{{ plan.activeUserCount }}</td>
                  <td><span :class="['status-pill', plan.enabled ? 'active' : 'inactive']">{{ plan.enabled ? '启用' : '停用' }}</span></td>
                  <td>
                    <div class="row-actions">
                      <button class="icon-btn" type="button" title="编辑" @click="openMembershipPlanPanel(plan)">
                        <Pencil :size="16" />
                      </button>
                      <button class="icon-btn danger" type="button" title="停用" @click="disableMembershipPlan(plan)">
                        <Trash2 :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>会员记录</strong>
                <span>开通、续期和停用都留痕</span>
              </div>
              <select v-model="membershipUserFilterId">
                <option value="">全部用户</option>
                <option v-for="user in users" :key="user.id" :value="user.id">{{ user.displayName || user.phone }}</option>
              </select>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>用户</th>
                  <th>会员计划</th>
                  <th>状态</th>
                  <th>开始</th>
                  <th>到期</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="membership in filteredUserMemberships" :key="membership.id">
                  <td>
                    <strong>{{ membership.userDisplayName }}</strong>
                    <small>{{ membership.userPhone }}</small>
                  </td>
                  <td>{{ membership.plan.name }}</td>
                  <td><span class="status-pill active">{{ membershipStatusLabel(membership.status) }}</span></td>
                  <td>{{ formatDateTime(membership.startedAt) }}</td>
                  <td>{{ formatDateTime(membership.expiresAt) }}</td>
                  <td>{{ formatDateTime(membership.updatedAt || membership.createdAt) }}</td>
                  <td>
                    <div class="row-actions">
                      <button class="icon-btn" type="button" title="编辑" @click="openUserMembershipPanel(membership)">
                        <Pencil :size="16" />
                      </button>
                      <button class="icon-btn danger" type="button" title="停用" @click="disableUserMembership(membership)">
                        <Trash2 :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>
        </section>

        <section v-else-if="activeModule === 'points'" class="admin-panel">
          <header class="panel-header">
            <div>
              <strong>积分管理</strong>
              <span>账户余额和流水一体查看</span>
            </div>
            <button class="primary-btn" type="button" @click="openWalletPanel(selectedUser ?? users[0])">
              <Coins :size="18" />
              积分调整
            </button>
          </header>

          <div class="admin-filters">
            <select v-model="walletUserFilterId">
              <option value="">全部用户</option>
              <option v-for="user in users" :key="user.id" :value="user.id">{{ user.displayName || user.phone }}</option>
            </select>
          </div>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>积分账户</strong>
                <span>显示余额、冻结和会员状态</span>
              </div>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>用户</th>
                  <th>余额</th>
                  <th>冻结</th>
                  <th>会员</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.id">
                  <td>
                    <strong>{{ user.displayName }}</strong>
                    <small>{{ user.phone }}</small>
                  </td>
                  <td>{{ formatPoints(user.balance) }}</td>
                  <td>{{ formatPoints(user.frozenBalance) }}</td>
                  <td>{{ user.membershipPlanName || '未开通' }}</td>
                  <td>{{ statusLabel(user.status) }}</td>
                  <td>
                    <div class="row-actions">
                      <button class="icon-btn" type="button" title="调账" @click="openWalletPanel(user)">
                        <Wallet :size="16" />
                      </button>
                      <button class="icon-btn" type="button" title="开通会员" @click="openUserMembershipPanel(undefined, user.id)">
                        <UserPlus :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>积分流水</strong>
                <span>调账、充值和扣减都可追踪</span>
              </div>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>用户</th>
                  <th>金额</th>
                  <th>结果余额</th>
                  <th>类型</th>
                  <th>原因</th>
                  <th>请求Key</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="transaction in filteredWalletTransactions" :key="transaction.id">
                  <td>{{ formatDateTime(transaction.createdAt) }}</td>
                  <td>{{ transaction.userDisplayName }}</td>
                  <td :class="['amount-cell', transaction.amount >= 0 ? 'positive' : 'negative']">
                    {{ transaction.amount >= 0 ? '+' : '' }}{{ formatPoints(transaction.amount) }}
                  </td>
                  <td>{{ formatPoints(transaction.balanceAfter) }}</td>
                  <td>{{ transaction.type }}</td>
                  <td>{{ transaction.remark }}</td>
                  <td>{{ transaction.requestKey }}</td>
                </tr>
              </tbody>
            </table>
          </section>
        </section>

        <section v-else-if="activeModule === 'redemptions'" class="admin-panel">
          <header class="panel-header">
            <div>
              <strong>兑换码管理</strong>
              <span>批量生成外部售卖兑换码，兑换后自动发积分和会员</span>
            </div>
            <button class="primary-btn" type="button" @click="openRedemptionBatchPanel">
              <Ticket :size="18" />
              批量生成
            </button>
          </header>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>兑换码批次</strong>
                <span>按批次查看发放内容、数量和兑换进度</span>
              </div>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>批次</th>
                  <th>积分</th>
                  <th>会员</th>
                  <th>数量</th>
                  <th>已兑换</th>
                  <th>有效期</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="batch in redemptionBatches" :key="batch.id">
                  <td>
                    <strong>{{ batch.name }}</strong>
                    <small>{{ formatDateTime(batch.createdAt) }}</small>
                  </td>
                  <td>{{ formatPoints(batch.points) }}</td>
                  <td>
                    <div class="stacked-text">
                      <strong>{{ membershipPlanName(batch.membershipPlanId) }}</strong>
                      <span>{{ batch.membershipDays ? `${batch.membershipDays} 天` : '不赠送时长' }}</span>
                    </div>
                  </td>
                  <td>{{ batch.generatedCount || batch.quantity }}</td>
                  <td>{{ batch.redeemedCount }}</td>
                  <td>{{ formatDateTime(batch.expiresAt) }}</td>
                  <td><span :class="['status-pill', batch.status.toLowerCase()]">{{ statusLabel(batch.status) }}</span></td>
                </tr>
              </tbody>
            </table>
          </section>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>兑换码列表</strong>
                <span>明文只在生成后展示；列表页仅显示脱敏码和兑换状态</span>
              </div>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>兑换码</th>
                  <th>状态</th>
                  <th>兑换人</th>
                  <th>兑换时间</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="code in redemptionCodes" :key="code.id">
                  <td>{{ code.maskedCode || code.code }}</td>
                  <td><span :class="['status-pill', code.status.toLowerCase()]">{{ redemptionStatusLabel(code.status) }}</span></td>
                  <td>{{ userNameById(code.redeemedByUserId) }}</td>
                  <td>{{ formatDateTime(code.redeemedAt) }}</td>
                  <td>{{ formatDateTime(code.createdAt) }}</td>
                  <td>
                    <div class="row-actions">
                      <button
                        class="icon-btn danger"
                        :disabled="code.status !== 'ACTIVE'"
                        type="button"
                        title="禁用"
                        @click="disableRedemptionCode(code)"
                      >
                        <Trash2 :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>
        </section>

        <section v-else-if="activeModule === 'content'" class="admin-panel content-layout">
          <div class="content-main">
            <header class="panel-header">
              <div>
                <strong>内容管理</strong>
                <span>页面、模块和卡片表格化维护</span>
              </div>
              <div class="panel-actions">
                <button class="ghost-btn" type="button" @click="openHomeSlidePanel()">
                  <Plus :size="18" />
                  新增首页轮播
                </button>
                <button class="ghost-btn" type="button" @click="openPagePanel()">
                  <Plus :size="18" />
                  新增页面
                </button>
                <button class="ghost-btn" type="button" @click="openSectionPanel()">
                  <Plus :size="18" />
                  新增模块
                </button>
                <button class="primary-btn" type="button" @click="openItemPanel(undefined, selectedSections[0]?.id)">
                  <Plus :size="18" />
                  新增卡片
                </button>
              </div>
            </header>

            <section class="admin-table-panel home-slide-panel">
              <header class="panel-header compact">
                <div>
                  <strong>首页轮播</strong>
                  <span>会员活动、模板上新和社群入口独立管理</span>
                </div>
                <button class="primary-btn" type="button" @click="openHomeSlidePanel()">
                  <Plus :size="18" />
                  新增轮播
                </button>
              </header>
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>标题</th>
                    <th>文案</th>
                    <th>CTA</th>
                    <th>跳转</th>
                    <th>排序</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="slide in homeSlides"
                    :key="slide.id"
                    :class="{ hidden: !slide.enabled }"
                    draggable="true"
                    @dragstart="draggedHomeSlideId = slide.id"
                    @dragend="draggedHomeSlideId = ''; activeDropHomeSlideId = ''"
                    @dragenter.prevent="activeDropHomeSlideId = slide.id"
                    @dragover.prevent
                    @drop="dropHomeSlide(slide.id)"
                  >
                    <td>
                      <strong>{{ slide.title }}</strong>
                      <small>{{ slide.badge }}</small>
                    </td>
                    <td>
                      <strong>{{ slide.subtitle }}</strong>
                      <small>{{ slide.ctaSubtitle }}</small>
                    </td>
                    <td>{{ slide.ctaLabel }}</td>
                    <td>{{ slide.actionValue }}</td>
                    <td>{{ slide.sortOrder }}</td>
                    <td><span :class="['status-pill', slide.enabled ? 'active' : 'inactive']">{{ slide.enabled ? '启用' : '停用' }}</span></td>
                    <td>
                      <div class="row-actions">
                        <button class="mini-btn" type="button" @click.stop="moveHomeSlide(slide.id, -1)">
                          <Minus :size="14" />
                        </button>
                        <button class="mini-btn" type="button" @click.stop="moveHomeSlide(slide.id, 1)">
                          <Plus :size="14" />
                        </button>
                        <button class="icon-btn" type="button" title="编辑" @click.stop="openHomeSlidePanel(slide)">
                          <Pencil :size="16" />
                        </button>
                        <button class="icon-btn" type="button" :title="slide.enabled ? '停用' : '启用'" @click.stop="toggleHomeSlideVisibility(slide)">
                          <EyeOff v-if="slide.enabled" :size="16" />
                          <Eye v-else :size="16" />
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </section>

            <section class="admin-table-panel">
              <header class="panel-header compact">
                <div>
                  <strong>页面列表</strong>
                  <span>点击行切换右侧预览</span>
                </div>
              </header>
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>页面Key</th>
                    <th>名称</th>
                    <th>标题</th>
                    <th>排序</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="page in pages"
                    :key="page.pageKey"
                    :class="[{ selected: selectedPageKey === page.pageKey }, { hidden: !page.enabled }]"
                    draggable="true"
                    @click="setSelectedPage(page.pageKey)"
                    @dragstart="draggedPageId = page.id || ''"
                    @dragend="draggedPageId = ''; activeDropPageId = ''"
                    @dragenter.prevent="activeDropPageId = page.id || ''"
                    @dragover.prevent
                    @drop="dropPage(page.id)"
                  >
                    <td>{{ page.pageKey }}</td>
                    <td>{{ page.label }}</td>
                    <td>{{ page.title }}</td>
                    <td>{{ page.sortOrder }}</td>
                    <td><span :class="['status-pill', page.enabled ? 'active' : 'inactive']">{{ page.enabled ? '启用' : '停用' }}</span></td>
                    <td>
                      <div class="row-actions">
                        <button class="mini-btn" type="button" @click.stop="movePage(page.id || '', -1)">
                          <Minus :size="14" />
                        </button>
                        <button class="mini-btn" type="button" @click.stop="movePage(page.id || '', 1)">
                          <Plus :size="14" />
                        </button>
                        <button class="icon-btn" type="button" title="编辑" @click.stop="openPagePanel(page)">
                          <Pencil :size="16" />
                        </button>
                        <button class="icon-btn" type="button" title="停用" @click.stop="togglePageVisibility(page)">
                          <EyeOff :size="16" />
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </section>

            <section class="admin-table-panel">
              <header class="panel-header compact">
                <div>
                  <strong>模块列表</strong>
                  <span>页面内模块可单独编辑和禁用</span>
                </div>
              </header>
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>模块Key</th>
                    <th>标题</th>
                    <th>布局</th>
                    <th>排序</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="section in selectedSections"
                    :key="section.id"
                    :class="{ hidden: !section.enabled }"
                    draggable="true"
                    @dragstart="draggedSectionId = section.id"
                    @dragend="draggedSectionId = ''; activeDropSectionId = ''"
                    @dragenter.prevent="activeDropSectionId = section.id"
                    @dragover.prevent
                    @drop="dropSection(section.id)"
                  >
                    <td>{{ section.sectionKey }}</td>
                    <td>
                      <strong>{{ section.title }}</strong>
                      <small>{{ section.subtitle }}</small>
                    </td>
                    <td>{{ section.layout }}</td>
                    <td>{{ section.sortOrder }}</td>
                    <td><span :class="['status-pill', section.enabled ? 'active' : 'inactive']">{{ section.enabled ? '启用' : '停用' }}</span></td>
                    <td>
                      <div class="row-actions">
                        <button class="mini-btn" type="button" @click.stop="moveSection(section.id, -1)">
                          <Minus :size="14" />
                        </button>
                        <button class="mini-btn" type="button" @click.stop="moveSection(section.id, 1)">
                          <Plus :size="14" />
                        </button>
                        <button class="icon-btn" type="button" title="编辑" @click.stop="openSectionPanel(section)">
                          <Pencil :size="16" />
                        </button>
                        <button class="icon-btn" type="button" title="停用" @click.stop="toggleSectionVisibility(section)">
                          <EyeOff :size="16" />
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </section>

            <section class="admin-table-panel">
              <header class="panel-header compact">
                <div>
                  <strong>卡片列表</strong>
                  <span>按模块分组展示和编辑</span>
                </div>
              </header>
              <div v-for="section in selectedSections" :key="section.id" class="section-group">
                <header class="section-group-head">
                  <div>
                    <strong>{{ section.title }}</strong>
                    <span>{{ section.sectionKey }} / {{ section.layout }}</span>
                  </div>
                  <button class="ghost-btn" type="button" @click="openItemPanel(undefined, section.id)">
                    <Plus :size="16" />
                    新增卡片
                  </button>
                </header>
                <table class="admin-table compact-table">
                  <thead>
                    <tr>
                      <th>标题</th>
                      <th>分类</th>
                      <th>类型</th>
                      <th>积分</th>
                      <th>状态</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="item in section.items"
                      :key="item.id"
                      :class="{ hidden: !item.enabled }"
                      draggable="true"
                      @dragstart="draggedItemId = item.id"
                      @dragend="draggedItemId = ''; activeDropItemId = ''"
                      @dragenter.prevent="activeDropItemId = item.id"
                      @dragover.prevent
                      @drop="dropItem(section, item.id)"
                    >
                      <td>
                        <strong>{{ item.title }}</strong>
                        <small>{{ item.subtitle }}</small>
                      </td>
                      <td>{{ item.category }}</td>
                      <td>{{ itemTypeLabel(item.itemType) }}</td>
                      <td>{{ item.pointCost }}</td>
                      <td><span :class="['status-pill', item.enabled ? 'active' : 'inactive']">{{ item.enabled ? '启用' : '停用' }}</span></td>
                      <td>
                        <div class="row-actions">
                          <button class="mini-btn" type="button" @click.stop="moveItem(item.id, -1)">
                            <Minus :size="14" />
                          </button>
                          <button class="mini-btn" type="button" @click.stop="moveItem(item.id, 1)">
                            <Plus :size="14" />
                          </button>
                          <button class="icon-btn" type="button" title="编辑" @click.stop="openItemPanel(item, section.id)">
                            <Pencil :size="16" />
                          </button>
                          <button class="icon-btn" type="button" title="停用" @click.stop="toggleItemVisibility(item)">
                            <EyeOff :size="16" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <aside class="admin-preview-panel" :style="previewPanelStyle">
            <span class="preview-resize-handle" @pointerdown="startPreviewResize"></span>
            <header>
              <div>
                <span>内容预览</span>
                <strong>{{ selectedPage?.title || '未选择页面' }}</strong>
              </div>
              <div class="preview-actions">
                <button class="ghost-btn" type="button" @click="setPreviewScale(0.55)">适配</button>
                <button class="ghost-btn" type="button" @click="router.push(`/${selectedPageKey}`)">打开页面</button>
              </div>
            </header>
            <header class="preview-toolbar">
              <button class="mini-btn" type="button" @click="nudgePreviewScale(-0.05)"><Minus :size="14" /></button>
              <input
                :value="previewScale"
                type="range"
                min="0.3"
                max="1.2"
                step="0.05"
                @input="setPreviewScale(Number(($event.target as HTMLInputElement).value))"
              />
              <button class="mini-btn" type="button" @click="nudgePreviewScale(0.05)"><Plus :size="14" /></button>
              <button class="ghost-btn" type="button" @click="setPreviewScale(1)"><Maximize2 :size="16" />{{ previewPercent }}</button>
            </header>
            <div class="preview-canvas">
              <div class="preview-stage" :style="previewStageStyle">
                <HomeDashboardPage
                  v-if="previewPageConfig && previewUsesHomeDashboardPage"
                  :model="previewHomeDashboardModel"
                  @open-item="() => undefined"
                />
                <MarketingPage
                  v-else-if="previewPageConfig && previewUsesMarketingPage"
                  :page-config="previewPageConfig"
                  @open-item="() => undefined"
                />
                <AudioPage
                  v-else-if="previewPageConfig && previewUsesAudioPage"
                  :page-config="previewPageConfig"
                  @open-item="() => undefined"
                />
                <DynamicPage v-else-if="previewPageConfig" :page-config="previewPageConfig" @open-item="() => undefined" />
              </div>
            </div>
          </aside>
        </section>

        <section v-else-if="activeModule === 'courses'" class="admin-panel">
          <header class="panel-header">
            <div>
              <strong>课程管理</strong>
              <span>管理飞书导入课程、查看格式异常并批量清洗 Markdown</span>
            </div>
            <div class="panel-actions">
              <button class="ghost-btn" type="button" @click="loadAdminCourses">
                <RefreshCw :size="18" />
                刷新课程
              </button>
              <button class="primary-btn" type="button" :disabled="courseCleanupBusy" @click="cleanupAdminCourses">
                <Sparkles :size="18" />
                {{ courseCleanupBusy ? '清洗中' : '批量清洗' }}
              </button>
            </div>
          </header>

          <div class="admin-filters">
            <label class="search-field">
              <Search :size="16" />
              <input v-model="courseQuery" placeholder="搜索课程标题、摘要或分类" @keyup.enter="searchAdminCourses" />
            </label>
            <select v-model="courseCategory" @change="searchAdminCourses">
              <option value="">全部分类</option>
              <option v-for="category in courseCatalog.categories" :key="category" :value="category">{{ category }}</option>
            </select>
            <button class="ghost-btn" type="button" @click="searchAdminCourses">搜索</button>
          </div>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>{{ courseCatalog.total }} 个课程</strong>
                <span>当前第 {{ courseCatalog.page }} 页，每页 {{ courseCatalog.pageSize }} 条</span>
              </div>
              <div class="panel-actions">
                <button class="ghost-btn" type="button" :disabled="courseCatalog.page <= 1" @click="changeCoursePage(-1)">上一页</button>
                <button
                  class="ghost-btn"
                  type="button"
                  :disabled="courseCatalog.page >= Math.max(1, Math.ceil(courseCatalog.total / courseCatalog.pageSize))"
                  @click="changeCoursePage(1)"
                >
                  下一页
                </button>
              </div>
            </header>

            <table class="admin-table">
              <thead>
                <tr>
                  <th>课程</th>
                  <th>分类</th>
                  <th>来源路径</th>
                  <th>权限</th>
                  <th>格式</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="course in courseCatalog.items" :key="course.id">
                  <td>
                    <strong>{{ course.title }}</strong>
                    <small>{{ course.subtitle }}</small>
                  </td>
                  <td>{{ course.category || '未分类' }}</td>
                  <td class="path-cell">{{ course.sourcePath.join(' / ') || course.detailPath }}</td>
                  <td>{{ course.requiredMembership ? '会员' : '公开' }}</td>
                  <td>
                    <span :class="['status-pill', course.dirty ? 'inactive' : 'active']">
                      {{ course.dirty ? '待清洗' : '正常' }}
                    </span>
                  </td>
                  <td>{{ formatDateTime(course.updatedAt) }}</td>
                  <td>
                    <button class="ghost-btn" type="button" @click="openCourseDetail(course)">打开</button>
                  </td>
                </tr>
                <tr v-if="courseCatalog.items.length === 0">
                  <td colspan="7">暂无课程，完成飞书导入后会显示在这里。</td>
                </tr>
              </tbody>
            </table>
          </section>
        </section>

        <section v-else-if="activeModule === 'models'" class="admin-panel">
          <header class="panel-header">
            <div>
              <strong>模型中心</strong>
              <span>AI 对话模型优先配置，渠道、模型与绑定作为高级维护项</span>
            </div>
          </header>

          <section class="admin-table-panel chat-profile-panel">
            <header class="panel-header compact">
              <div>
                <strong>AI 对话模型配置</strong>
                <span>保存后会同步 TEXT 渠道、默认对话模型和工作台可调用路由</span>
              </div>
              <span :class="['status-pill', chatRuntimeState === '可调用' ? 'active' : 'inactive']">{{ chatRuntimeState }}</span>
            </header>
            <div class="chat-profile-grid">
              <form class="form-card chat-profile-form" @submit.prevent="saveChatModelProfile">
                <label>渠道Key<input v-model="chatModelProfileForm.channelKey" /></label>
                <label>服务商名称<input v-model="chatModelProfileForm.providerName" placeholder="中转" /></label>
                <label>官网地址<input v-model="chatModelProfileForm.officialUrl" placeholder="https://ai.input.im" /></label>
                <label>API 请求地址<input v-model="chatModelProfileForm.baseUrl" placeholder="https://ai.input.im" /></label>
                <label>API Key<input v-model="chatModelProfileForm.apiKey" type="password" :placeholder="chatModelProfileForm.savedApiKeyMask ? `已保存 ${chatModelProfileForm.savedApiKeyMask}，留空保持不变` : '首次配置必须填写'" /></label>
                <label>模型名称<input v-model="chatModelProfileForm.modelName" placeholder="gpt-5.5" /></label>
                <label>工作台模型Key<input v-model="chatModelProfileForm.modelKey" disabled /></label>
                <label>展示名称<input v-model="chatModelProfileForm.displayName" placeholder="GPT-5.5" /></label>
                <label>
                  模型推理强度
                  <select v-model="chatModelProfileForm.modelReasoningEffort">
                    <option value="minimal">minimal</option>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                    <option value="xhigh">xhigh</option>
                  </select>
                </label>
                <label>
                  服务商推理强度
                  <select v-model="chatModelProfileForm.providerReasoningEffort">
                    <option value="minimal">minimal</option>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                    <option value="xhigh">xhigh</option>
                  </select>
                </label>
                <label>
                  service_tier
                  <select v-model="chatModelProfileForm.serviceTier">
                    <option value="auto">auto</option>
                    <option value="default">default</option>
                    <option value="fast">fast</option>
                  </select>
                </label>
                <label>超时秒数<input v-model.number="chatModelProfileForm.timeoutSeconds" min="1" type="number" /></label>
                <label>上下文窗口<input v-model.number="chatModelProfileForm.contextWindow" min="1" type="number" /></label>
                <label>自动压缩阈值<input v-model.number="chatModelProfileForm.autoCompactTokenLimit" min="1" type="number" /></label>
                <label>默认积分<input v-model.number="chatModelProfileForm.defaultPointCost" min="0" type="number" /></label>
                <label class="field-span-2">备注<textarea v-model="chatModelProfileForm.note" rows="2" placeholder="账号来源、适用范围或运维说明" /></label>
                <label class="check-label"><input v-model="chatModelProfileForm.disableResponseStorage" type="checkbox" />disable_response_storage</label>
                <label class="check-label"><input v-model="chatModelProfileForm.enabled" type="checkbox" />启用对话模型</label>
                <button class="primary-btn" type="submit">保存并同步到工作台</button>
              </form>

              <aside class="chat-profile-preview">
                <section>
                  <header>
                    <strong>auth.json</strong>
                    <span>{{ chatModelProfileForm.apiKey ? '当前输入预览' : '已保存配置预览' }}</span>
                  </header>
                  <pre>{{ chatAuthPreview }}</pre>
                </section>
                <section>
                  <header>
                    <strong>config.toml</strong>
                    <span>OpenAI Responses</span>
                  </header>
                  <pre>{{ chatConfigPreview }}</pre>
                </section>
              </aside>
            </div>
          </section>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>供应商渠道</strong>
                <span>展示、编辑和启停</span>
              </div>
              <button class="primary-btn" type="button" @click="openProviderChannelPanel()">
                <Plus :size="18" />
                新增渠道
              </button>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>名称</th>
                  <th>类型</th>
                  <th>地址</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="channel in providerChannels" :key="channel.id">
                  <td>{{ channel.channelKey }}</td>
                  <td>
                    <strong>{{ channel.displayName }}</strong>
                    <small>{{ channel.apiKeyMask || '未设置密钥' }}</small>
                  </td>
                  <td>{{ channel.channelType }}</td>
                  <td>{{ channel.baseUrl }}</td>
                  <td><span :class="['status-pill', channel.enabled ? 'active' : 'inactive']">{{ channel.enabled ? '启用' : '停用' }}</span></td>
                  <td>
                    <div class="row-actions">
                      <button class="icon-btn" type="button" title="编辑" @click="openProviderChannelPanel(channel)">
                        <Pencil :size="16" />
                      </button>
                      <button class="icon-btn" type="button" title="启停" @click="toggleProviderChannel(channel)">
                        <EyeOff :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>模型列表</strong>
                <span>模型和默认积分配置</span>
              </div>
              <button class="primary-btn" type="button" @click="openModelConfigPanel()">
                <Plus :size="18" />
                新增模型
              </button>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Key</th>
                  <th>名称</th>
                  <th>能力</th>
                  <th>渠道</th>
                  <th>模型名</th>
                  <th>默认积分</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="model in modelConfigs" :key="model.id">
                  <td>{{ model.modelKey }}</td>
                  <td>{{ model.displayName }}</td>
                  <td>{{ model.capability }}</td>
                  <td>{{ model.channelName || model.channelKey || model.channelId }}</td>
                  <td>{{ model.providerModel }}</td>
                  <td>{{ model.defaultPointCost }}</td>
                  <td><span :class="['status-pill', model.enabled ? 'active' : 'inactive']">{{ model.enabled ? '启用' : '停用' }}</span></td>
                  <td>
                    <div class="row-actions">
                      <button class="icon-btn" type="button" title="编辑" @click="openModelConfigPanel(model)">
                        <Pencil :size="16" />
                      </button>
                      <button class="icon-btn" type="button" title="启停" @click="toggleModelConfig(model)">
                        <EyeOff :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>工作台能力筛选</strong>
                <span>控制对话、图像、视频和音频工作台的显示、模型和积分</span>
              </div>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>能力</th>
                  <th>分组</th>
                  <th>模型</th>
                  <th>积分</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="capability in workbenchCapabilities" :key="capability.targetType + capability.targetKey">
                  <td>
                    <strong>{{ capability.title }}</strong>
                    <small>{{ capability.targetType }} / {{ capability.targetKey }}</small>
                  </td>
                  <td>{{ capability.group }}</td>
                  <td>{{ capability.modelConfig?.displayName || capability.modelConfig?.modelKey || '未绑定' }}</td>
                  <td>{{ capability.effectivePointCost }}</td>
                  <td>
                    <span :class="['status-pill', capability.callable ? 'active' : 'inactive']">
                      {{ capability.callable ? '可调用' : capability.unavailableReason || '停用' }}
                    </span>
                  </td>
                  <td>
                    <div class="row-actions">
                      <button class="icon-btn" type="button" title="编辑" @click="openWorkbenchCapabilityPanel(capability)">
                        <Pencil :size="16" />
                      </button>
                      <button class="icon-btn" type="button" title="启停" @click="toggleWorkbenchCapability(capability)">
                        <EyeOff :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>

          <section class="admin-table-panel">
            <header class="panel-header compact">
              <div>
                <strong>工具绑定列表</strong>
                <span>把工具、模板和内容对象接到模型上</span>
              </div>
              <button class="primary-btn" type="button" @click="openToolBindingPanel()">
                <Plus :size="18" />
                新增绑定
              </button>
            </header>
            <table class="admin-table">
              <thead>
                <tr>
                  <th>目标</th>
                  <th>模型</th>
                  <th>覆盖积分</th>
                  <th>生效积分</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="binding in toolModelBindings" :key="binding.id">
                  <td>{{ binding.targetType }} / {{ binding.targetKey }}</td>
                  <td>{{ binding.modelConfig?.displayName || binding.modelConfig?.modelKey || binding.modelConfigId }}</td>
                  <td>{{ binding.pointCostOverride ?? '默认' }}</td>
                  <td>{{ binding.effectivePointCost ?? binding.pointCostOverride ?? 0 }}</td>
                  <td><span :class="['status-pill', binding.enabled ? 'active' : 'inactive']">{{ binding.enabled ? '启用' : '停用' }}</span></td>
                  <td>
                    <div class="row-actions">
                      <button class="icon-btn" type="button" title="编辑" @click="openToolBindingPanel(binding)">
                        <Pencil :size="16" />
                      </button>
                      <button class="icon-btn" type="button" title="启停" @click="toggleToolBinding(binding)">
                        <EyeOff :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>
        </section>

        <section v-else-if="activeModule === 'audit'" class="admin-panel">
          <header class="panel-header">
            <div>
              <strong>审计日志</strong>
              <span>记录关键管理动作和变更摘要</span>
            </div>
            <select v-model.number="auditLimit" @change="refreshWithNotice">
              <option :value="20">最近 20 条</option>
              <option :value="50">最近 50 条</option>
              <option :value="100">最近 100 条</option>
            </select>
          </header>

          <table class="admin-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>动作</th>
                <th>对象</th>
                <th>操作者</th>
                <th>摘要</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in auditLogs" :key="log.id">
                <td>{{ formatDateTime(log.createdAt) }}</td>
                <td>{{ auditActionLabel(log.action) }}</td>
                <td>{{ log.targetType }} / {{ log.targetId || '全部' }}</td>
                <td>{{ log.actorDisplayName }} · {{ roleLabel(log.actorRole) }}</td>
                <td>{{ log.summary }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </template>
    </main>

    <div
      v-if="activePanel"
      class="modal-backdrop modal-backdrop-center"
      @click.self="closePanel"
    >
      <section
        :class="[
          'modal-panel',
          'admin-modal-shell',
          { 'admin-card-modal': activePanel === 'item' || activePanel === 'provider-channel' || activePanel === 'model-config' }
        ]"
      >
        <header>
          <div>
            <span>管理操作</span>
            <strong>{{ panelTitle }}</strong>
          </div>
          <button class="icon-btn" type="button" @click="closePanel"><X :size="16" /></button>
        </header>

        <form v-if="activePanel === 'home-slide'" class="form-card" @submit.prevent="saveHomeSlide">
          <label>标题<input v-model="homeSlideForm.title" /></label>
          <label>副标题<textarea v-model="homeSlideForm.subtitle" rows="3" /></label>
          <label>角标<input v-model="homeSlideForm.badge" /></label>
          <label>CTA 文案<input v-model="homeSlideForm.ctaLabel" /></label>
          <label>CTA 副文案<input v-model="homeSlideForm.ctaSubtitle" /></label>
          <label>图片地址<input v-model="homeSlideForm.imageUrl" placeholder="/storage/home/xxx.png" /></label>
          <label>动作类型<input v-model="homeSlideForm.actionType" /></label>
          <label>跳转地址<input v-model="homeSlideForm.actionValue" /></label>
          <label>排序<input v-model.number="homeSlideForm.sortOrder" type="number" /></label>
          <label>
            主题色
            <select v-model="homeSlideForm.accent">
              <option value="gold">gold</option>
              <option value="blue">blue</option>
              <option value="green">green</option>
              <option value="violet">violet</option>
            </select>
          </label>
          <label class="check-label"><input v-model="homeSlideForm.enabled" type="checkbox" />启用</label>
          <button class="primary-btn" type="submit">{{ homeSlideFormId ? '更新轮播' : '创建轮播' }}</button>
        </form>

        <form v-else-if="activePanel === 'user'" class="form-card" @submit.prevent="saveUser">
          <label>手机号<input v-model="userForm.phone" /></label>
          <label>名称<input v-model="userForm.displayName" /></label>
          <label>
            角色
            <select v-model="userForm.role">
              <option value="USER">普通成员</option>
              <option value="READ_ONLY">只读</option>
              <option value="CONTENT_EDITOR">内容编辑</option>
              <option value="OPERATOR">运营</option>
              <option value="ADMIN">管理员</option>
              <option value="SUPER_ADMIN">超级管理员</option>
            </select>
          </label>
          <label>
            状态
            <select v-model="userForm.status">
              <option value="ACTIVE">启用</option>
              <option value="INACTIVE">停用</option>
            </select>
          </label>
          <label>密码<input v-model="userForm.password" type="password" placeholder="留空则不修改" /></label>
          <button class="primary-btn" type="submit">{{ userFormId ? '更新人员' : '新增人员' }}</button>
        </form>

        <form v-else-if="activePanel === 'wallet'" class="form-card" @submit.prevent="saveWalletAdjustment">
          <label>
            用户
            <select v-model="walletAdjustForm.userId">
              <option v-for="user in users" :key="user.id" :value="user.id">{{ user.displayName || user.phone }}</option>
            </select>
          </label>
          <label>积分变动<input v-model.number="walletAdjustForm.amount" type="number" /></label>
          <label>原因<textarea v-model="walletAdjustForm.reason" rows="3" /></label>
          <label>请求Key<input v-model="walletAdjustForm.requestKey" placeholder="留空自动生成" /></label>
          <button class="primary-btn" type="submit">提交调账</button>
        </form>

        <form v-else-if="activePanel === 'redemption-batch'" class="form-card" @submit.prevent="saveRedemptionBatch">
          <label>批次名称<input v-model="redemptionBatchForm.name" /></label>
          <label>生成数量<input v-model.number="redemptionBatchForm.quantity" min="1" max="1000" type="number" /></label>
          <label>赠送积分<input v-model.number="redemptionBatchForm.points" min="0" type="number" /></label>
          <label>
            会员套餐
            <select v-model="redemptionBatchForm.membershipPlanId">
              <option value="">不赠送会员</option>
              <option v-for="plan in membershipPlans" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
            </select>
          </label>
          <label>会员天数<input v-model.number="redemptionBatchForm.membershipDays" min="0" type="number" /></label>
          <label>过期时间<input v-model="redemptionBatchForm.expiresAt" type="date" /></label>
          <button class="primary-btn" type="submit">批量生成</button>
          <section v-if="generatedRedemptionCodes.length > 0" class="generated-code-list field-span-2">
            <strong>本次生成的兑换码</strong>
            <textarea
              readonly
              rows="8"
              :value="generatedRedemptionCodes.map((code) => code.code || code.maskedCode).join('\n')"
            />
          </section>
        </form>

        <form v-else-if="activePanel === 'membership-plan'" class="form-card" @submit.prevent="saveMembershipPlan">
          <label>计划Key<input v-model="membershipPlanForm.planKey" /></label>
          <label>名称<input v-model="membershipPlanForm.name" /></label>
          <label>价格（分）<input v-model.number="membershipPlanForm.priceCents" type="number" /></label>
          <label>周期（天）<input v-model.number="membershipPlanForm.durationDays" type="number" /></label>
          <label>权益<textarea v-model="membershipPlanForm.entitlementsText" rows="3" placeholder="每行一条权益" /></label>
          <label>排序<input v-model.number="membershipPlanForm.sortOrder" type="number" /></label>
          <label class="check-label"><input v-model="membershipPlanForm.enabled" type="checkbox" />启用</label>
          <button class="primary-btn" type="submit">{{ membershipPlanFormId ? '更新计划' : '创建计划' }}</button>
        </form>

        <form v-else-if="activePanel === 'user-membership'" class="form-card" @submit.prevent="saveUserMembership">
          <label>
            用户
            <select v-model="userMembershipForm.userId">
              <option v-for="user in users" :key="user.id" :value="user.id">{{ user.displayName || user.phone }}</option>
            </select>
          </label>
          <label>
            会员计划
            <select v-model="userMembershipForm.planId">
              <option v-for="plan in membershipPlans" :key="plan.id" :value="plan.id">{{ plan.name }}</option>
            </select>
          </label>
          <label v-if="!userMembershipFormId">持续天数<input v-model.number="userMembershipForm.durationDays" type="number" /></label>
          <label v-if="userMembershipFormId">到期时间<input v-model="userMembershipForm.expiresAt" type="date" /></label>
          <label>
            状态
            <select v-model="userMembershipForm.status">
              <option value="ACTIVE">生效</option>
              <option value="EXPIRED">过期</option>
              <option value="CANCELLED">取消</option>
            </select>
          </label>
          <button class="primary-btn" type="submit">{{ userMembershipFormId ? '更新会员' : '新增会员' }}</button>
        </form>

        <form v-else-if="activePanel === 'page'" class="form-card" @submit.prevent="savePage">
          <label>页面Key<input v-model="pageForm.pageKey" :disabled="Boolean(pageFormId)" /></label>
          <label>导航名称<input v-model="pageForm.label" /></label>
          <label>页面标题<input v-model="pageForm.title" /></label>
          <label>副标题<input v-model="pageForm.subtitle" /></label>
          <label>图标<input v-model="pageForm.icon" /></label>
          <label>排序<input v-model.number="pageForm.sortOrder" type="number" /></label>
          <label class="check-label"><input v-model="pageForm.enabled" type="checkbox" />启用</label>
          <button class="primary-btn" type="submit">{{ pageFormId ? '更新页面' : '创建页面' }}</button>
        </form>

        <form v-else-if="activePanel === 'section'" class="form-card" @submit.prevent="saveSection">
          <label>模块Key<input v-model="sectionForm.sectionKey" :disabled="Boolean(sectionFormId)" /></label>
          <label>标题<input v-model="sectionForm.title" /></label>
          <label>副标题<input v-model="sectionForm.subtitle" /></label>
          <label>
            页面
            <select v-model="sectionForm.pageKey">
              <option v-for="page in pages" :key="page.pageKey" :value="page.pageKey">{{ page.label }}</option>
            </select>
          </label>
          <label>
            布局
            <select v-model="sectionForm.layout">
              <option value="stat-strip">stat-strip</option>
              <option value="tool-grid">tool-grid</option>
              <option value="learning-grid">learning-grid</option>
              <option value="order-grid">order-grid</option>
              <option value="banner-row">banner-row</option>
              <option value="promo-carousel">promo-carousel</option>
              <option value="template-list">template-list</option>
              <option value="third-party-tools">third-party-tools</option>
              <option value="ranking-list">ranking-list</option>
              <option value="audio-workbench">audio-workbench</option>
              <option value="audio-stats">audio-stats</option>
              <option value="audio-tools">audio-tools</option>
              <option value="audio-voices">audio-voices</option>
              <option value="audio-table">audio-table</option>
              <option value="audio-queue">audio-queue</option>
              <option value="audio-resources">audio-resources</option>
              <option value="audio-guides">audio-guides</option>
            </select>
          </label>
          <label>排序<input v-model.number="sectionForm.sortOrder" type="number" /></label>
          <label class="check-label"><input v-model="sectionForm.enabled" type="checkbox" />启用</label>
          <button class="primary-btn" type="submit">{{ sectionFormId ? '更新模块' : '创建模块' }}</button>
        </form>

        <form v-else-if="activePanel === 'item'" class="form-card card-editor-form" @submit.prevent="saveItem">
          <section class="card-form-section">
            <div class="card-form-section__head">
              <strong>基础信息</strong>
              <span>卡片在列表和入口中的展示内容</span>
            </div>
            <label class="field-span-2">
              所属模块
              <select v-model="itemForm.sectionId">
                <option v-for="section in selectedSections" :key="section.id" :value="section.id">{{ section.title }}</option>
              </select>
            </label>
            <label>
              卡片类型
              <select v-model="itemForm.itemType">
                <option
                  v-if="itemForm.itemType && !isKnownOption(itemTypeOptions, itemForm.itemType)"
                  :value="itemForm.itemType"
                >
                  {{ itemTypeLabel(itemForm.itemType) }}
                </option>
                <option v-for="option in itemTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </label>
            <label>标题<input v-model="itemForm.title" /></label>
            <label>说明<input v-model="itemForm.subtitle" /></label>
            <label>分类<input v-model="itemForm.category" /></label>
            <label>图标<input v-model="itemForm.icon" /></label>
            <label>图片地址<input v-model="itemForm.imageUrl" placeholder="/storage/items/xxx.png" /></label>
            <label class="field-span-2">标签<textarea v-model="itemForm.tagsText" rows="2" placeholder="每行或逗号分隔" /></label>
            <label>排序<input v-model.number="itemForm.sortOrder" type="number" /></label>
            <label class="check-label"><input v-model="itemForm.enabled" type="checkbox" />启用</label>
          </section>

          <section class="card-form-section">
            <div class="card-form-section__head">
              <strong>动作配置</strong>
              <span>卡片点击后的跳转和积分消耗</span>
            </div>
            <label>
              动作类型
              <select v-model="itemForm.actionType">
                <option
                  v-if="itemForm.actionType && !isKnownOption(actionTypeOptions, itemForm.actionType)"
                  :value="itemForm.actionType"
                >
                  {{ actionTypeLabel(itemForm.actionType) }}
                </option>
                <option v-for="option in actionTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
              </select>
            </label>
            <label>跳转值<input v-model="itemForm.actionValue" :placeholder="itemActionValuePlaceholder" /></label>
            <label>积分<input v-model.number="itemForm.pointCost" type="number" /></label>
            <label class="check-label"><input v-model="itemForm.requiredMembership" type="checkbox" />会员可用</label>
            <label class="upload-line field-span-2">
              <ImagePlus :size="18" />
              上传图片
              <input type="file" accept="image/*" @change="uploadImage" />
            </label>
          </section>

          <section class="card-form-section">
            <div class="card-form-section__head">
              <strong>详情配置</strong>
              <span>详情页内容、按钮和下载信息</span>
            </div>
            <label class="field-span-2">详情摘要<textarea v-model="itemForm.detailSummary" rows="3" /></label>
            <label class="field-span-2">详情亮点<textarea v-model="itemForm.detailHighlightsText" rows="3" /></label>
            <label class="field-span-2">步骤/目录<textarea v-model="itemForm.detailStepsText" rows="4" /></label>
            <label class="field-span-2">交付物<textarea v-model="itemForm.detailDeliverablesText" rows="3" /></label>
            <label class="field-span-2">FAQ<textarea v-model="itemForm.detailFaqsText" rows="3" placeholder="问题|答案，每行一条" /></label>
            <label>主按钮 Key<input v-model="itemForm.detailPrimaryActionKey" /></label>
            <label>主按钮文案<input v-model="itemForm.detailPrimaryActionLabel" /></label>
            <label class="field-span-2">次按钮<textarea v-model="itemForm.detailSecondaryActionsText" rows="2" placeholder="favorite|收藏" /></label>
            <label>下载文件名<input v-model="itemForm.detailDownloadFileName" /></label>
            <label>下载URL<input v-model="itemForm.detailDownloadUrl" /></label>
          </section>

          <div class="card-editor-footer">
            <button class="ghost-btn" type="button" @click="closePanel">取消</button>
            <button class="primary-btn" type="submit">{{ itemFormId ? '更新卡片' : '创建卡片' }}</button>
          </div>
        </form>

        <form v-else-if="activePanel === 'provider-channel'" class="form-card card-editor-form" @submit.prevent="saveProviderChannel">
          <section class="card-form-section">
            <div class="card-form-section__head">
              <strong>供应商预设</strong>
              <span>选择预设只会填默认值，所有字段都还能继续改</span>
            </div>
            <div class="provider-preset-row field-span-2">
              <button
                v-for="preset in providerPresetOptions"
                :key="preset.key"
                :class="['provider-preset-chip', { active: providerChannelForm.presetKey === preset.key }]"
                type="button"
                @click="applyProviderPreset(preset.key)"
              >
                <strong>{{ preset.label }}</strong>
                <small>{{ preset.hint }}</small>
              </button>
            </div>
            <label>供应商名称<input v-model="providerChannelForm.displayName" /></label>
            <label>备注<input v-model="providerChannelForm.remark" /></label>
            <label>官网<input v-model="providerChannelForm.website" placeholder="https://example.com" /></label>
            <label>渠道 Key<input v-model="providerChannelForm.channelKey" /></label>
            <label>
              渠道类型
              <select v-model="providerChannelForm.channelType">
                <option value="TEXT">TEXT</option>
                <option value="IMAGE">IMAGE</option>
                <option value="VIDEO">VIDEO</option>
                <option value="AUDIO">AUDIO</option>
              </select>
            </label>
            <label>
              适配器
              <select v-model="providerChannelForm.adapterType">
                <option value="openai_compatible">openai_compatible</option>
                <option value="custom_http">custom_http</option>
              </select>
            </label>
            <label>API 请求地址<input v-model="providerChannelForm.baseUrl" placeholder="https://api.example.com/v1" /></label>
            <label>API Key<input v-model="providerChannelForm.apiKey" type="password" placeholder="留空则保持原值" /></label>
            <label>优先级<input v-model.number="providerChannelForm.priority" type="number" /></label>
            <label>超时秒数<input v-model.number="providerChannelForm.timeoutSeconds" type="number" /></label>
            <label class="check-label"><input v-model="providerChannelForm.useFullUrl" type="checkbox" />完整 URL</label>
            <label class="check-label"><input v-model="providerChannelForm.enabled" type="checkbox" />启用</label>
          </section>

          <section class="card-form-section">
            <div class="card-form-section__head">
              <strong>auth.json / config.toml</strong>
              <span>这里只保存模板文本，不会写回本地文件</span>
            </div>
            <label class="field-span-2">auth.json<textarea v-model="providerChannelForm.authJsonText" rows="4" placeholder='{"OPENAI_API_KEY": ""}' /></label>
            <label class="field-span-2">config.toml<textarea v-model="providerChannelForm.configTomlText" rows="4" placeholder='model_provider = "openai_compatible"' /></label>
            <label class="check-label"><input v-model="providerChannelForm.writeCommonConfig" type="checkbox" />写入公共配置</label>
          </section>

          <section class="card-form-section">
            <div class="card-form-section__head">
              <strong>测试配置 / 计费配置</strong>
              <span>这些内容会进 metadata_json，后续可再接入运行时</span>
            </div>
            <label class="field-span-2">测试配置<textarea v-model="providerChannelForm.testConfigText" rows="3" placeholder='{"temperature":0.2}' /></label>
            <label class="field-span-2">计费配置<textarea v-model="providerChannelForm.billingConfigText" rows="3" placeholder='{"mode":"point"}' /></label>
          </section>

          <div class="card-editor-footer">
            <button class="ghost-btn" type="button" @click="closePanel">取消</button>
            <button class="primary-btn" type="submit">{{ providerChannelFormId ? '更新渠道' : '创建渠道' }}</button>
          </div>
        </form>

        <form v-else-if="activePanel === 'model-config'" class="form-card card-editor-form" @submit.prevent="saveModelConfig">
          <section class="card-form-section">
            <div class="card-form-section__head">
              <strong>基础信息</strong>
              <span>模型仍沿用现有渠道和绑定主链路</span>
            </div>
            <label>模型 Key<input v-model="modelConfigForm.modelKey" /></label>
            <label>模型名称<input v-model="modelConfigForm.displayName" /></label>
            <label>
              能力类型
              <select v-model="modelConfigForm.capability">
                <option value="TEXT">TEXT</option>
                <option value="IMAGE">IMAGE</option>
                <option value="VIDEO">VIDEO</option>
                <option value="AUDIO">AUDIO</option>
              </select>
            </label>
            <label>
              绑定渠道
              <select v-model="modelConfigForm.channelId">
                <option v-for="channel in providerChannels" :key="channel.id" :value="channel.id">{{ channel.displayName }}</option>
              </select>
            </label>
            <label>供应商模型<input v-model="modelConfigForm.providerModel" /></label>
            <label>默认积分<input v-model.number="modelConfigForm.defaultPointCost" type="number" /></label>
            <label class="check-label"><input v-model="modelConfigForm.enabled" type="checkbox" />启用</label>
          </section>

          <section class="card-form-section">
            <div class="card-form-section__head">
              <strong>运行配置</strong>
              <span>1M 上下文和压缩阈值会写入 metadata_json</span>
            </div>
            <label class="check-label"><input v-model="modelConfigForm.useMillionContextWindow" type="checkbox" />1M 上下文窗口</label>
            <label>压缩阈值<input v-model.number="modelConfigForm.compressionThreshold" min="0" type="number" /></label>
            <label class="field-span-2">测试配置<textarea v-model="modelConfigForm.testConfigText" rows="3" placeholder='{"temperature":0.2}' /></label>
            <label class="field-span-2">计费配置<textarea v-model="modelConfigForm.billingConfigText" rows="3" placeholder='{"mode":"tiered","unit_cost":120}' /></label>
          </section>

          <div class="card-editor-footer">
            <button class="ghost-btn" type="button" @click="closePanel">取消</button>
            <button class="primary-btn" type="submit">{{ modelConfigFormId ? '更新模型' : '创建模型' }}</button>
          </div>
        </form>

        <form v-else-if="activePanel === 'tool-binding'" class="form-card" @submit.prevent="saveToolBinding">
          <label>
            目标类型
            <select v-model="toolBindingForm.targetType">
              <option value="builtin">builtin</option>
              <option value="assistant">assistant</option>
              <option value="content_item">content_item</option>
              <option value="prompt_template">prompt_template</option>
            </select>
          </label>
          <label>目标ID<input v-model="toolBindingForm.targetKey" /></label>
          <label>
            绑定模型
            <select v-model="toolBindingForm.modelConfigId">
              <option v-for="model in modelConfigs" :key="model.id" :value="model.id">{{ model.displayName }} ({{ model.modelKey }})</option>
            </select>
          </label>
          <label>覆盖积分<input v-model="toolBindingForm.pointCostOverride" type="number" placeholder="留空则使用模型默认积分" /></label>
          <label class="check-label"><input v-model="toolBindingForm.enabled" type="checkbox" />启用</label>
          <button class="primary-btn" type="submit">{{ toolBindingFormId ? '更新绑定' : '创建绑定' }}</button>
        </form>

        <form v-else-if="activePanel === 'workbench-capability'" class="form-card" @submit.prevent="saveWorkbenchCapability">
          <label>能力名称<input v-model="workbenchCapabilityForm.title" disabled /></label>
          <label>目标类型<input v-model="workbenchCapabilityForm.targetType" disabled /></label>
          <label class="field-span-2">目标ID<input v-model="workbenchCapabilityForm.targetKey" disabled /></label>
          <label>
            绑定模型
            <select v-model="workbenchCapabilityForm.modelConfigId">
              <option v-for="model in modelConfigs" :key="model.id" :value="model.id">{{ model.displayName }} ({{ model.modelKey }})</option>
            </select>
          </label>
          <label>覆盖积分<input v-model="workbenchCapabilityForm.pointCostOverride" type="number" placeholder="留空则使用模型默认积分" /></label>
          <label class="check-label"><input v-model="workbenchCapabilityForm.enabled" type="checkbox" />启用</label>
          <button class="primary-btn" type="submit">更新工作台能力</button>
        </form>
      </section>
    </div>
  </div>
</template>

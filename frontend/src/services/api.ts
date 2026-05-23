import {
  createFallbackAssistantCenter,
  createFallbackImageWorkbench,
  createFallbackPageConfig,
  createFallbackPortalConfig,
  createFallbackVideoWorkbench,
  buildAudioTaskPayload,
  normalizeAccountSummary,
  normalizeAccountUser,
  normalizeAdminAuditLog,
  normalizeAdminMembershipPlan,
  normalizeAdminOverview,
  normalizeAdminRedemptionBatch,
  normalizeAdminRedemptionCode,
  normalizeAdminUser,
  normalizeAdminUserMembership,
  normalizeAdminWalletTransaction,
  normalizeRedemptionResult,
  normalizeRechargeOrder,
  normalizeHomeDashboard,
  normalizeHomeDashboardSlide,
  normalizeModelConfig,
  normalizeProviderChannel,
  normalizeToolModelBinding,
  normalizeWorkbenchCapabilities,
  normalizeAssistantCenter,
  normalizeAudioTask,
  normalizeChatActiveSession,
  normalizeChatExportResult,
  normalizeChatModelProfile,
  normalizeChatSendResult,
  normalizeChatWorkbench,
  normalizeCourseCatalog,
  normalizeImageWorkbench,
  normalizePageConfig,
  normalizePortalActionResult,
  normalizePortalConfig,
  normalizePortalDetail,
  normalizePortalSearchResult,
  normalizePortalUserActions,
  normalizeVideoWorkbench,
  type ModelConfigSummary,
  type AssistantCenter,
  type AccountSummary,
  type AccountUser,
  type AdminAuditLogSummary,
  type AdminMembershipPlanSummary,
  type AdminOverviewSummary,
  type AdminRedemptionBatchSummary,
  type AdminRedemptionCodeSummary,
  type AdminUserMembershipSummary,
  type AdminUserSummary,
  type AdminWalletTransactionSummary,
  type AudioTask,
  type AudioTaskPayload,
  type ChatActiveSession,
  type ChatExportResult,
  type ChatModelProfilePayload,
  type ChatSendResult,
  type ChatWorkbench,
  type CourseCatalogPayload,
  type GenerationSurface,
  type HomeDashboardModel,
  type HomeDashboardSlide,
  type ImageTask,
  type ImageWorkbench,
  type ProviderChannelSummary,
  type PortalActionRequest,
  type PortalActionResult,
  type PortalConfig,
  type PortalDetailPayload,
  type PortalItem,
  type PortalPageConfig,
  type PortalSearchResult,
  type RedemptionResult,
  type RechargeOrder,
  type ToolModelBindingSummary,
  type UserPortalAction,
  type VideoTask,
  type VideoWorkbench,
  type WorkbenchCapabilitiesPayload
} from './viewModel';
import {
  createFallbackCommunicationHallPayload,
  normalizeCommunicationHallPayload,
  normalizeCommunicationHallPost,
  type CommunicationHallPayload,
  type CommunicationHallPostCreateRequest,
  type CommunicationHallPostResponse
} from './communicationHall';

const tenantId = 'demo';
const tokenKey = 'opc_admin_token';
const userSessionKey = 'opc_user_session';
export const userSessionChangedEvent = 'opc:user-session-changed';
const DEFAULT_IMAGE_ROUTE_KEY = 'image_text_to_image';
const DEFAULT_VIDEO_ROUTE_KEY = 'video_text_to_video';

export interface GenerationRequestOptions {
  requestKey?: string;
  targetType?: string;
  targetId?: string;
  routeKey?: string;
  surface?: GenerationSurface;
  options?: Record<string, unknown>;
}

export interface WorkbenchCapabilityRequest {
  targetType: string;
  targetKey: string;
  modelConfigId?: string;
  pointCostOverride?: number | string | null;
  enabled?: boolean;
}

export interface ChatModelProfileRequest {
  channelKey?: string;
  providerName: string;
  note?: string;
  officialUrl?: string;
  baseUrl: string;
  apiKey?: string;
  modelName: string;
  modelKey?: string;
  displayName?: string;
  modelReasoningEffort?: string;
  providerReasoningEffort?: string;
  serviceTier?: string;
  contextWindow?: number;
  autoCompactTokenLimit?: number;
  disableResponseStorage?: boolean;
  defaultPointCost?: number;
  timeoutSeconds?: number;
  enabled?: boolean;
}

export interface PortalDetailUpdateRequest {
  title?: string;
  summary?: string;
  bodyMarkdown?: string;
  tags?: string[];
  visibility?: string;
}

export interface ChatSessionRequest {
  title?: string;
  userId?: string;
  modelKey?: string;
  presetRole?: string;
  status?: string;
}

export interface ChatMessageRequest {
  content: string;
  modelKey?: string;
}

export interface LoginResult {
  accessToken: string;
  tokenType: string;
  user: {
    id: string;
    tenantId: string;
    phone: string;
    displayName: string;
    role: string;
    status: string;
  };
}

export type UserSession = LoginResult;

export interface VerificationCodeRequest {
  phone: string;
  purpose: 'REGISTER' | 'LOGIN' | 'RESET_PASSWORD';
}

export interface RegisterUserRequest {
  phone: string;
  password: string;
  displayName: string;
  verificationCode: string;
}

export interface LoginUserRequest {
  phone: string;
  password?: string;
  verificationCode?: string;
  loginMethod?: 'PASSWORD' | 'CODE';
}

export interface PasswordResetRequest {
  phone: string;
  verificationCode: string;
  newPassword: string;
}

export interface PasswordChangeRequest {
  currentPassword: string;
  newPassword: string;
}

export interface AccountProfileUpdateRequest {
  userId: string;
  displayName: string;
}

export interface RechargeOrderRequest {
  userId: string;
  packageKey: string;
}

export interface CourseCatalogRequest {
  query?: string;
  category?: string;
  page?: number;
  pageSize?: number;
}

export interface AdminUserRequest {
  phone: string;
  displayName: string;
  role?: string;
  status?: string;
  password?: string;
}

export interface AdminUserUpdateRequest {
  phone?: string;
  displayName?: string;
  role?: string;
  status?: string;
  password?: string;
}

export interface WalletAdjustmentRequest {
  amount: number;
  reason?: string;
  requestKey?: string;
}

export interface MembershipPlanRequest {
  planKey: string;
  name: string;
  priceCents?: number;
  durationDays?: number;
  entitlements?: string[];
  enabled?: boolean;
  sortOrder?: number;
}

export interface MembershipPlanUpdateRequest {
  planKey?: string;
  name?: string;
  priceCents?: number;
  durationDays?: number;
  entitlements?: string[];
  enabled?: boolean;
  sortOrder?: number;
}

export interface UserMembershipRequest {
  userId: string;
  planId: string;
  durationDays?: number;
  status?: string;
}

export interface UserMembershipUpdateRequest {
  planId?: string;
  status?: string;
  expiresAt?: string;
}

export interface RedemptionBatchRequest {
  name: string;
  quantity: number;
  points: number;
  membershipPlanId?: string;
  membershipDays?: number;
  expiresAt?: string;
}

export function getAdminToken(): string {
  return getStorageItem(tokenKey);
}

export function setAdminToken(token: string) {
  setStorageItem(tokenKey, token);
}

export function clearAdminToken() {
  removeStorageItem(tokenKey);
}

export function getUserSession(): UserSession | null {
  const raw = getStorageItem(userSessionKey);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as UserSession;
  } catch {
    removeStorageItem(userSessionKey);
    return null;
  }
}

export function setUserSession(session: UserSession) {
  setStorageItem(userSessionKey, JSON.stringify(session));
  dispatchUserSessionChanged();
}

export function clearUserSession() {
  removeStorageItem(userSessionKey);
  dispatchUserSessionChanged();
}

export function getCurrentUserId(fallback = 'demo-user'): string {
  return getUserSession()?.user.id || fallback;
}

export async function requestVerificationCode(payload: VerificationCodeRequest): Promise<{ phone: string; purpose: string; devCode?: string; message?: string }> {
  const response = await request('/api/v1/auth/verification-codes', {
    method: 'POST',
    body: JSON.stringify({
      phone: payload.phone,
      purpose: payload.purpose
    })
  });
  return {
    phone: response.phone ?? payload.phone,
    purpose: response.purpose ?? payload.purpose,
    devCode: response.dev_code ?? response.devCode,
    message: response.message
  };
}

export async function registerUser(payload: RegisterUserRequest): Promise<LoginResult> {
  const result = normalizeLoginResult(
    await request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        phone: payload.phone,
        password: payload.password,
        display_name: payload.displayName,
        verification_code: payload.verificationCode
      })
    })
  );
  setUserSession(result);
  return result;
}

export async function loginUser(payload: LoginUserRequest): Promise<LoginResult> {
  const body: Record<string, string> = {
    phone: payload.phone,
    login_method: payload.loginMethod ?? 'PASSWORD'
  };
  if (payload.password) {
    body.password = payload.password;
  }
  if (payload.verificationCode) {
    body.verification_code = payload.verificationCode;
  }
  const result = normalizeLoginResult(
    await request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(body)
    })
  );
  setUserSession(result);
  return result;
}

export async function resetPassword(payload: PasswordResetRequest): Promise<{ status: string }> {
  return request('/api/v1/auth/password/reset', {
    method: 'POST',
    body: JSON.stringify({
      phone: payload.phone,
      verification_code: payload.verificationCode,
      new_password: payload.newPassword
    })
  });
}

export async function changePassword(payload: PasswordChangeRequest): Promise<{ status: string }> {
  return request('/api/v1/auth/password/change', {
    method: 'POST',
    body: JSON.stringify({
      current_password: payload.currentPassword,
      new_password: payload.newPassword
    }),
    userAuth: true
  });
}

export async function loginAdmin(phone: string, password: string): Promise<LoginResult> {
  const result = normalizeLoginResult(await request('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone, password })
  }));
  setAdminToken(result.accessToken);
  return result;
}

export async function fetchAccountSummary(userId = getCurrentUserId()): Promise<AccountSummary> {
  const params = new URLSearchParams({ user_id: userId });
  return normalizeAccountSummary(await request(`/api/v1/account/summary?${params.toString()}`));
}

export async function updateAccountProfile(payload: AccountProfileUpdateRequest): Promise<AccountUser> {
  const response = await request('/api/v1/account/profile', {
    method: 'PATCH',
    body: JSON.stringify({
      user_id: payload.userId,
      display_name: payload.displayName
    })
  });
  return normalizeAccountUser(response.user ?? response);
}

export async function createRechargeOrder(payload: RechargeOrderRequest): Promise<RechargeOrder> {
  return normalizeRechargeOrder(
    await request('/api/v1/payments/recharge-orders', {
      method: 'POST',
      body: JSON.stringify({
        user_id: payload.userId,
        package_key: payload.packageKey
      })
    })
  );
}

export async function fetchPortalConfig(): Promise<PortalConfig> {
  try {
    return normalizePortalConfig(await request('/api/v1/portal/config'));
  } catch {
    return createFallbackPortalConfig();
  }
}

export async function fetchPortalPage(pageKey: string): Promise<PortalPageConfig> {
  try {
    return normalizePageConfig(await request(`/api/v1/portal/pages/${encodeURIComponent(pageKey)}`));
  } catch {
    return createFallbackPageConfig(pageKey);
  }
}

export async function fetchHomeDashboard(): Promise<HomeDashboardModel> {
  try {
    return normalizeHomeDashboard(await request('/api/v1/home/dashboard'));
  } catch {
    return normalizeHomeDashboard({});
  }
}

export async function fetchPortalDetail(detailPath: string, userId = 'demo-user'): Promise<PortalDetailPayload> {
  const normalizedPath = encodeDetailPath(detailPath);
  const params = new URLSearchParams({ user_id: userId });
  return normalizePortalDetail(
    await request(`/api/v1/portal/details/${normalizedPath}?${params.toString()}`, portalAuthOptions())
  );
}

export async function searchPortal(query: string, pageKey = '', limit = 8): Promise<PortalSearchResult[]> {
  const params = new URLSearchParams({ q: query });
  if (pageKey) {
    params.set('page_key', pageKey);
  }
  params.set('limit', String(limit));
  const payload = await request(`/api/v1/portal/search?${params.toString()}`);
  return (payload.results ?? []).map(normalizePortalSearchResult);
}

export async function runPortalAction(payload: PortalActionRequest): Promise<PortalActionResult> {
  return normalizePortalActionResult(
    await request('/api/v1/portal/actions', {
      method: 'POST',
      body: JSON.stringify({
        user_id: payload.userId,
        detail_path: payload.detailPath,
        item_id: payload.itemId,
        action_key: payload.actionKey
      })
    })
  );
}

export async function fetchPortalUserActions(userId = 'demo-user', kind = 'all'): Promise<UserPortalAction[]> {
  const params = new URLSearchParams({ user_id: userId, kind });
  const payload = await request(`/api/v1/portal/user-actions?${params.toString()}`);
  return normalizePortalUserActions(payload);
}

export async function fetchCourses(options: CourseCatalogRequest = {}): Promise<CourseCatalogPayload> {
  const params = new URLSearchParams();
  params.set('q', options.query ?? '');
  params.set('category', options.category ?? '');
  params.set('page', String(options.page ?? 1));
  params.set('page_size', String(options.pageSize ?? 20));
  return normalizeCourseCatalog(await request(`/api/v1/courses?${params.toString()}`));
}

export async function adminListCourses(options: CourseCatalogRequest = {}): Promise<CourseCatalogPayload> {
  const params = new URLSearchParams();
  if (options.query) {
    params.set('q', options.query);
  }
  if (options.category) {
    params.set('category', options.category);
  }
  params.set('page', String(options.page ?? 1));
  params.set('page_size', String(options.pageSize ?? 50));
  return normalizeCourseCatalog(await request(`/api/v1/admin/courses?${params.toString()}`, { auth: true }));
}

export async function adminCleanupCourses(): Promise<{ scanned: number; changed: number; dirtyRemaining: number }> {
  const payload = await request('/api/v1/admin/courses/cleanup', { method: 'POST', body: JSON.stringify({}), auth: true });
  return {
    scanned: Number(payload.scanned ?? 0),
    changed: Number(payload.changed ?? 0),
    dirtyRemaining: Number(payload.dirty_remaining ?? payload.dirtyRemaining ?? 0)
  };
}

export async function fetchCommunicationHall(userId = getCurrentUserId('demo-user')): Promise<CommunicationHallPayload> {
  const params = new URLSearchParams({ user_id: userId });
  try {
    return normalizeCommunicationHallPayload(await request(`/api/v1/communication/posts?${params.toString()}`, portalAuthOptions()));
  } catch {
    return createFallbackCommunicationHallPayload();
  }
}

export async function createCommunicationHallPost(payload: CommunicationHallPostCreateRequest): Promise<CommunicationHallPostResponse> {
  const response = await request('/api/v1/communication/posts', {
    method: 'POST',
    body: JSON.stringify({
      category_key: payload.categoryKey,
      title: payload.title,
      body_markdown: payload.bodyMarkdown
    }),
    userAuth: true
  });
  const post = normalizeCommunicationHallPost(response.post ?? response);
  return {
    post,
    detailPath: String(response.detail_path ?? response.detailPath ?? post.detailPath ?? '')
  };
}

export async function fetchMembershipStatus(userId = 'demo-user') {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/api/v1/memberships/status?${params.toString()}`);
}

export async function fetchAssistantCenter(): Promise<AssistantCenter> {
  try {
    return normalizeAssistantCenter(await request('/api/v1/assistants'));
  } catch {
    return createFallbackAssistantCenter();
  }
}

export async function fetchChatWorkbench(sessionId?: string): Promise<ChatWorkbench> {
  const params = new URLSearchParams({ user_id: getCurrentUserId() });
  if (sessionId) {
    params.set('session_id', sessionId);
  }
  return normalizeChatWorkbench(await request(`/api/v1/chat/workbench?${params.toString()}`));
}

export async function createChatSession(payload: ChatSessionRequest = {}): Promise<ChatActiveSession> {
  return normalizeChatActiveSession(
    await request('/api/v1/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({
        title: payload.title ?? '',
        user_id: payload.userId ?? getCurrentUserId(),
        model_key: payload.modelKey ?? 'general_text_default',
        preset_role: payload.presetRole ?? 'assistant'
      })
    })
  );
}

export async function fetchChatSession(sessionId: string): Promise<ChatActiveSession> {
  return normalizeChatActiveSession(await request(`/api/v1/chat/sessions/${encodeURIComponent(sessionId)}`));
}

export async function updateChatSession(sessionId: string, payload: ChatSessionRequest): Promise<ChatActiveSession> {
  return normalizeChatActiveSession(
    await request(`/api/v1/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'PATCH',
      body: JSON.stringify({
        title: payload.title,
        model_key: payload.modelKey,
        preset_role: payload.presetRole,
        status: payload.status
      })
    })
  );
}

export async function sendChatMessage(sessionId: string, payload: ChatMessageRequest): Promise<ChatSendResult> {
  return normalizeChatSendResult(
    await request(`/api/v1/chat/sessions/${encodeURIComponent(sessionId)}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        content: payload.content,
        model_key: payload.modelKey
      })
    })
  );
}

export async function exportChatSession(sessionId: string): Promise<ChatExportResult> {
  return normalizeChatExportResult(
    await request(`/api/v1/chat/sessions/${encodeURIComponent(sessionId)}/export`, {
      method: 'POST',
      body: JSON.stringify({ format: 'markdown' })
    })
  );
}

export async function fetchVideoWorkbench(surface: GenerationSurface = 'portal'): Promise<VideoWorkbench> {
  const params = new URLSearchParams({ user_id: getCurrentUserId(), surface });
  return normalizeVideoWorkbench(await request(`/api/v1/video/workbench?${params.toString()}`));
}

export async function createVideoGeneration(
  prompt: string,
  requestKeyOrOptions?: string | GenerationRequestOptions
): Promise<VideoTask> {
  const options = normalizeGenerationRequestOptions(requestKeyOrOptions);
  const payload = await request('/api/v1/video/generations', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      user_id: getCurrentUserId(),
      route_key: options.routeKey ?? DEFAULT_VIDEO_ROUTE_KEY,
      request_key: options.requestKey,
      target_type: options.targetType,
      target_id: options.targetId,
      surface: options.surface ?? 'portal',
      options: options.options ?? {}
    })
  });
  return normalizeVideoWorkbench({
    tenant_id: 'demo',
    user_id: 'demo-user',
    wallet: {},
    route: {},
    tasks: [payload]
  }).tasks[0];
}

export async function fetchImageWorkbench(surface: GenerationSurface = 'portal'): Promise<ImageWorkbench> {
  const params = new URLSearchParams({ user_id: getCurrentUserId(), surface });
  return normalizeImageWorkbench(await request(`/api/v1/image/workbench?${params.toString()}`));
}

export async function createImageGeneration(
  prompt: string,
  requestKeyOrOptions?: string | GenerationRequestOptions
): Promise<ImageTask> {
  const options = normalizeGenerationRequestOptions(requestKeyOrOptions);
  const payload = await request('/api/v1/image/generations', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      user_id: getCurrentUserId(),
      route_key: options.routeKey ?? DEFAULT_IMAGE_ROUTE_KEY,
      request_key: options.requestKey,
      target_type: options.targetType,
      target_id: options.targetId,
      surface: options.surface ?? 'portal',
      options: options.options ?? {}
    })
  });
  return normalizeImageWorkbench({
    tenant_id: 'demo',
    user_id: 'demo-user',
    wallet: {},
    route: {},
    tasks: [payload]
  }).tasks[0];
}

export async function fetchAudioTasks(surface: GenerationSurface = 'portal'): Promise<AudioTask[]> {
  const params = new URLSearchParams({ surface });
  const payload = await request(`/api/v1/audio/tasks?${params.toString()}`);
  return (payload.tasks ?? []).map(normalizeAudioTask);
}

export async function fetchWorkbenchCapabilities(surface: GenerationSurface = 'workbench'): Promise<WorkbenchCapabilitiesPayload> {
  const params = new URLSearchParams({ surface });
  return normalizeWorkbenchCapabilities(await request(`/api/v1/workbench/capabilities?${params.toString()}`));
}

export async function createAudioTask(payload: AudioTaskPayload): Promise<AudioTask> {
  return normalizeAudioTask(
    await request('/api/v1/audio/tasks', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  );
}

export async function createAudioTaskForTool(tool: PortalItem, prompt: string, voice?: PortalItem, sourceUrl = ''): Promise<AudioTask> {
  return createAudioTask(buildAudioTaskPayload(tool, prompt, voice, sourceUrl));
}

export async function adminListOverview(): Promise<AdminOverviewSummary> {
  return normalizeAdminOverview(await request('/api/v1/admin/overview', { auth: true }));
}

export async function adminListUsers(params: { query?: string; role?: string; status?: string; limit?: number } = {}): Promise<AdminUserSummary[]> {
  const search = new URLSearchParams();
  if (params.query) {
    search.set('query', params.query);
  }
  if (params.role) {
    search.set('role', params.role);
  }
  if (params.status) {
    search.set('status', params.status);
  }
  if (params.limit !== undefined) {
    search.set('limit', String(params.limit));
  }
  const suffix = search.toString();
  const payload = await request(`/api/v1/admin/users${suffix ? `?${suffix}` : ''}`, { auth: true });
  return (payload.users ?? payload ?? []).map(normalizeAdminUser);
}

export async function adminCreateUser(payload: AdminUserRequest): Promise<AdminUserSummary> {
  return normalizeAdminUser(
    await request('/api/v1/admin/users', {
      method: 'POST',
      body: JSON.stringify({
        phone: payload.phone,
        display_name: payload.displayName,
        role: payload.role ?? 'USER',
        status: payload.status ?? 'ACTIVE',
        password: payload.password ?? ''
      }),
      auth: true
    })
  );
}

export async function adminUpdateUser(userId: string, payload: AdminUserUpdateRequest): Promise<AdminUserSummary> {
  return normalizeAdminUser(
    await request(`/api/v1/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({
        phone: payload.phone,
        display_name: payload.displayName,
        role: payload.role,
        status: payload.status,
        password: payload.password
      }),
      auth: true
    })
  );
}

export async function adminDeleteUser(userId: string): Promise<AdminUserSummary> {
  return normalizeAdminUser(await request(`/api/v1/admin/users/${userId}`, { method: 'DELETE', auth: true }));
}

export async function adminAdjustWallet(
  userId: string,
  payload: WalletAdjustmentRequest
): Promise<{ balance: number; frozenBalance: number; currency: string; transaction: AdminWalletTransactionSummary }> {
  const response = await request(`/api/v1/admin/wallets/${userId}/adjust`, {
    method: 'POST',
    body: JSON.stringify({
      amount: payload.amount,
      reason: payload.reason ?? '',
      request_key: payload.requestKey
    }),
    auth: true
  });
  return {
    balance: Number(response.balance ?? 0),
    frozenBalance: Number(response.frozen_balance ?? response.frozenBalance ?? 0),
    currency: response.currency ?? 'POINT',
    transaction: normalizeAdminWalletTransaction(response.transaction ?? response)
  };
}

export async function adminListWalletTransactions(userId = '', limit = 100): Promise<AdminWalletTransactionSummary[]> {
  const params = new URLSearchParams();
  if (userId) {
    params.set('user_id', userId);
  }
  params.set('limit', String(limit));
  const payload = await request(`/api/v1/admin/wallet-transactions?${params.toString()}`, { auth: true });
  return (payload.transactions ?? payload ?? []).map(normalizeAdminWalletTransaction);
}

export async function adminListMembershipPlans(): Promise<AdminMembershipPlanSummary[]> {
  const payload = await request('/api/v1/admin/membership-plans', { auth: true });
  return (payload.plans ?? payload ?? []).map(normalizeAdminMembershipPlan);
}

export async function adminCreateMembershipPlan(payload: MembershipPlanRequest): Promise<AdminMembershipPlanSummary> {
  return normalizeAdminMembershipPlan(
    await request('/api/v1/admin/membership-plans', {
      method: 'POST',
      body: JSON.stringify({
        plan_key: payload.planKey,
        name: payload.name,
        price_cents: payload.priceCents ?? 0,
        duration_days: payload.durationDays ?? 31,
        entitlements: payload.entitlements ?? [],
        enabled: payload.enabled ?? true,
        sort_order: payload.sortOrder ?? 100
      }),
      auth: true
    })
  );
}

export async function adminUpdateMembershipPlan(planId: string, payload: MembershipPlanUpdateRequest): Promise<AdminMembershipPlanSummary> {
  return normalizeAdminMembershipPlan(
    await request(`/api/v1/admin/membership-plans/${planId}`, {
      method: 'PUT',
      body: JSON.stringify({
        plan_key: payload.planKey,
        name: payload.name,
        price_cents: payload.priceCents,
        duration_days: payload.durationDays,
        entitlements: payload.entitlements,
        enabled: payload.enabled,
        sort_order: payload.sortOrder
      }),
      auth: true
    })
  );
}

export async function adminDeleteMembershipPlan(planId: string): Promise<AdminMembershipPlanSummary> {
  return normalizeAdminMembershipPlan(await request(`/api/v1/admin/membership-plans/${planId}`, { method: 'DELETE', auth: true }));
}

export async function adminListUserMemberships(userId = '', limit = 100): Promise<AdminUserMembershipSummary[]> {
  const params = new URLSearchParams();
  if (userId) {
    params.set('user_id', userId);
  }
  params.set('limit', String(limit));
  const payload = await request(`/api/v1/admin/user-memberships?${params.toString()}`, { auth: true });
  return (payload.memberships ?? payload ?? []).map(normalizeAdminUserMembership);
}

export async function adminGrantMembership(payload: UserMembershipRequest): Promise<AdminUserMembershipSummary> {
  const body: Record<string, unknown> = {
    user_id: payload.userId,
    plan_id: payload.planId,
    duration_days: payload.durationDays
  };
  if (payload.status) {
    body.status = payload.status;
  }
  return normalizeAdminUserMembership(
    await request('/api/v1/admin/user-memberships', {
      method: 'POST',
      body: JSON.stringify(body),
      auth: true
    })
  );
}

export async function adminUpdateUserMembership(membershipId: string, payload: UserMembershipUpdateRequest): Promise<AdminUserMembershipSummary> {
  return normalizeAdminUserMembership(
    await request(`/api/v1/admin/user-memberships/${membershipId}`, {
      method: 'PUT',
      body: JSON.stringify({
        plan_id: payload.planId,
        status: payload.status,
        expires_at: payload.expiresAt
      }),
      auth: true
    })
  );
}

export async function adminDeleteUserMembership(membershipId: string): Promise<AdminUserMembershipSummary> {
  return normalizeAdminUserMembership(await request(`/api/v1/admin/user-memberships/${membershipId}`, { method: 'DELETE', auth: true }));
}

export async function adminListAuditLogs(limit = 50): Promise<AdminAuditLogSummary[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  const payload = await request(`/api/v1/admin/audit-logs?${params.toString()}`, { auth: true });
  return (payload.logs ?? payload ?? []).map(normalizeAdminAuditLog);
}

export async function redeemCode(code: string): Promise<RedemptionResult> {
  return normalizeRedemptionResult(
    await request('/api/v1/redemptions/redeem', {
      method: 'POST',
      body: JSON.stringify({ code }),
      userAuth: true
    })
  );
}

export async function adminListRedemptionBatches(limit = 100): Promise<AdminRedemptionBatchSummary[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  const payload = await request(`/api/v1/admin/redemption-batches?${params.toString()}`, { auth: true });
  return (payload.batches ?? payload ?? []).map(normalizeAdminRedemptionBatch);
}

export async function adminListRedemptionCodes(batchId = '', limit = 200): Promise<AdminRedemptionCodeSummary[]> {
  const params = new URLSearchParams();
  if (batchId) {
    params.set('batch_id', batchId);
  }
  params.set('limit', String(limit));
  const payload = await request(`/api/v1/admin/redemption-codes?${params.toString()}`, { auth: true });
  return (payload.codes ?? payload ?? []).map(normalizeAdminRedemptionCode);
}

export async function adminCreateRedemptionBatch(payload: RedemptionBatchRequest): Promise<{ batch: AdminRedemptionBatchSummary; codes: AdminRedemptionCodeSummary[] }> {
  const response = await request('/api/v1/admin/redemption-batches', {
    method: 'POST',
    body: JSON.stringify({
      name: payload.name,
      quantity: payload.quantity,
      points: payload.points,
      membership_plan_id: payload.membershipPlanId,
      membership_days: payload.membershipDays,
      expires_at: payload.expiresAt
    }),
    auth: true
  });
  return {
    batch: normalizeAdminRedemptionBatch(response.batch ?? response),
    codes: (response.codes ?? []).map(normalizeAdminRedemptionCode)
  };
}

export async function adminDisableRedemptionCode(codeId: string): Promise<AdminRedemptionCodeSummary> {
  return normalizeAdminRedemptionCode(
    await request(`/api/v1/admin/redemption-codes/${codeId}`, {
      method: 'DELETE',
      auth: true
    })
  );
}

export async function adminListProviderChannels(): Promise<ProviderChannelSummary[]> {
  const payload = await request('/api/v1/admin/provider-channels', { auth: true });
  return (payload.channels ?? payload ?? []).map(normalizeProviderChannel);
}

export async function adminGetChatModelProfile(): Promise<ChatModelProfilePayload> {
  return normalizeChatModelProfile(await request('/api/v1/admin/chat-model-profile', { auth: true }));
}

export async function adminUpdateChatModelProfile(payload: ChatModelProfileRequest): Promise<ChatModelProfilePayload> {
  return normalizeChatModelProfile(
    await request('/api/v1/admin/chat-model-profile', {
      method: 'PUT',
      body: JSON.stringify({
        channel_key: payload.channelKey,
        provider_name: payload.providerName,
        note: payload.note ?? '',
        official_url: payload.officialUrl ?? '',
        base_url: payload.baseUrl,
        api_key: payload.apiKey ?? '',
        model_name: payload.modelName,
        model_key: 'general_text_default',
        display_name: payload.displayName ?? '',
        model_reasoning_effort: payload.modelReasoningEffort ?? 'high',
        provider_reasoning_effort: payload.providerReasoningEffort ?? 'medium',
        service_tier: payload.serviceTier ?? 'fast',
        context_window: payload.contextWindow ?? 1000000,
        auto_compact_token_limit: payload.autoCompactTokenLimit ?? 900000,
        disable_response_storage: payload.disableResponseStorage ?? true,
        default_point_cost: payload.defaultPointCost ?? 0,
        timeout_seconds: payload.timeoutSeconds ?? 60,
        enabled: payload.enabled ?? true
      }),
      auth: true
    })
  );
}

export async function adminCreateProviderChannel(payload: Record<string, unknown>): Promise<ProviderChannelSummary> {
  return normalizeProviderChannel(
    await request('/api/v1/admin/provider-channels', {
      method: 'POST',
      body: JSON.stringify(payload),
      auth: true
    })
  );
}

export async function adminUpdateProviderChannel(channelId: string, payload: Record<string, unknown>): Promise<ProviderChannelSummary> {
  return normalizeProviderChannel(
    await request(`/api/v1/admin/provider-channels/${channelId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
      auth: true
    })
  );
}

export async function adminListModelConfigs(): Promise<ModelConfigSummary[]> {
  const payload = await request('/api/v1/admin/model-configs', { auth: true });
  const records = (payload.model_configs ?? payload.models ?? payload ?? []) as any[];
  return records
    .map((record) => normalizeModelConfig(record))
    .filter((record): record is ModelConfigSummary => Boolean(record));
}

export async function adminCreateModelConfig(payload: Record<string, unknown>): Promise<ModelConfigSummary> {
  return normalizeModelConfig(
    await request('/api/v1/admin/model-configs', {
      method: 'POST',
      body: JSON.stringify(payload),
      auth: true
    })
  ) as ModelConfigSummary;
}

export async function adminUpdateModelConfig(modelConfigId: string, payload: Record<string, unknown>): Promise<ModelConfigSummary> {
  return normalizeModelConfig(
    await request(`/api/v1/admin/model-configs/${modelConfigId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
      auth: true
    })
  ) as ModelConfigSummary;
}

export async function adminListToolModelBindings(): Promise<ToolModelBindingSummary[]> {
  const payload = await request('/api/v1/admin/tool-model-bindings', { auth: true });
  return (payload.bindings ?? payload ?? []).map(normalizeToolModelBinding);
}

export async function adminListWorkbenchCapabilities(): Promise<WorkbenchCapabilitiesPayload> {
  return normalizeWorkbenchCapabilities(await request('/api/v1/admin/workbench-capabilities', { auth: true }));
}

export async function adminUpdateWorkbenchCapability(payload: WorkbenchCapabilityRequest): Promise<ToolModelBindingSummary> {
  const pointCostOverride =
    payload.pointCostOverride === undefined ||
    payload.pointCostOverride === null ||
    payload.pointCostOverride === ''
      ? null
      : Number(payload.pointCostOverride);
  return normalizeToolModelBinding(
    await request('/api/v1/admin/workbench-capabilities', {
      method: 'PATCH',
      body: JSON.stringify({
        target_type: payload.targetType,
        target_key: payload.targetKey,
        model_config_id: payload.modelConfigId,
        point_cost_override: pointCostOverride,
        enabled: payload.enabled
      }),
      auth: true
    })
  );
}

export async function updatePortalDetail(detailPath: string, payload: PortalDetailUpdateRequest): Promise<PortalDetailPayload> {
  const normalizedPath = encodeDetailPath(detailPath);
  return normalizePortalDetail(
    await request(`/api/v1/portal/details/${normalizedPath}`, {
      ...portalAuthOptions(),
      method: 'PATCH',
      body: JSON.stringify({
        title: payload.title,
        summary: payload.summary,
        body_markdown: payload.bodyMarkdown,
        tags: payload.tags,
        visibility: payload.visibility
      })
    })
  );
}

export async function publishPortalDetail(detailPath: string, releaseNote = ''): Promise<PortalDetailPayload> {
  const normalizedPath = encodeDetailPath(detailPath);
  return normalizePortalDetail(
    await request(`/api/v1/portal/details/${normalizedPath}/versions`, {
      ...portalAuthOptions(),
      method: 'POST',
      body: JSON.stringify({ release_note: releaseNote })
    })
  );
}

export async function rollbackPortalDetailVersion(detailPath: string, versionId: string, releaseNote = ''): Promise<PortalDetailPayload> {
  const normalizedPath = encodeDetailPath(detailPath);
  return normalizePortalDetail(
    await request(`/api/v1/portal/details/${normalizedPath}/versions/${encodeURIComponent(versionId)}/rollback`, {
      ...portalAuthOptions(),
      method: 'POST',
      body: JSON.stringify({ release_note: releaseNote })
    })
  );
}

export async function createPortalDetailComment(detailPath: string, content: string) {
  const normalizedPath = encodeDetailPath(detailPath);
  const payload = await request(`/api/v1/portal/details/${normalizedPath}/comments`, {
    ...portalAuthOptions(),
    method: 'POST',
    body: JSON.stringify({ content })
  });
  return {
    comment: payload.comment,
    detail: normalizePortalDetail({ detail: payload.detail }).detail
  };
}

export async function adminCreateToolModelBinding(payload: Record<string, unknown>): Promise<ToolModelBindingSummary> {
  return normalizeToolModelBinding(
    await request('/api/v1/admin/tool-model-bindings', {
      method: 'POST',
      body: JSON.stringify(payload),
      auth: true
    })
  );
}

export async function adminUpdateToolModelBinding(bindingId: string, payload: Record<string, unknown>): Promise<ToolModelBindingSummary> {
  return normalizeToolModelBinding(
    await request(`/api/v1/admin/tool-model-bindings/${bindingId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
      auth: true
    })
  );
}

export async function adminListHomeSlides(): Promise<HomeDashboardSlide[]> {
  const payload = await request('/api/v1/admin/home-slides', { auth: true });
  return (payload.slides ?? payload ?? []).map(normalizeHomeDashboardSlide);
}

export async function adminCreateHomeSlide(payload: Record<string, unknown>): Promise<HomeDashboardSlide> {
  return normalizeHomeDashboardSlide(
    await request('/api/v1/admin/home-slides', {
      method: 'POST',
      body: JSON.stringify(payload),
      auth: true
    })
  );
}

export async function adminUpdateHomeSlide(slideId: string, payload: Record<string, unknown>): Promise<HomeDashboardSlide> {
  return normalizeHomeDashboardSlide(
    await request(`/api/v1/admin/home-slides/${slideId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
      auth: true
    })
  );
}

export async function adminReorderHomeSlides(slides: Array<{ id: string }>): Promise<HomeDashboardSlide[]> {
  const payload = await request('/api/v1/admin/home-slides/reorder', {
    method: 'POST',
    body: JSON.stringify({ ordered_ids: slides.map((slide) => slide.id) }),
    auth: true
  });
  return (payload.slides ?? payload ?? []).map(normalizeHomeDashboardSlide);
}

export async function adminDeleteHomeSlide(slideId: string): Promise<HomeDashboardSlide> {
  return normalizeHomeDashboardSlide(await request(`/api/v1/admin/home-slides/${slideId}`, { method: 'DELETE', auth: true }));
}

export async function uploadAudio(file: File) {
  const form = new FormData();
  form.append('file', file);
  return request('/api/v1/audio/uploads', { method: 'POST', body: form, isForm: true });
}

export async function adminListPages() {
  return request('/api/v1/admin/pages', { auth: true });
}

export async function adminFetchPageContent(pageKey: string) {
  return normalizePageConfig(await request(`/api/v1/admin/page-content/${encodeURIComponent(pageKey)}`, { auth: true }));
}

export async function adminCreatePage(payload: Record<string, unknown>) {
  return request('/api/v1/admin/pages', { method: 'POST', body: JSON.stringify(payload), auth: true });
}

export async function adminUpdatePage(pageId: string, payload: Record<string, unknown>) {
  return request(`/api/v1/admin/pages/${pageId}`, { method: 'PUT', body: JSON.stringify(payload), auth: true });
}

export async function adminReorderPages(payload: Record<string, unknown>) {
  return request('/api/v1/admin/pages/reorder', { method: 'POST', body: JSON.stringify(payload), auth: true });
}

export async function adminDeletePage(pageId: string) {
  return request(`/api/v1/admin/pages/${pageId}`, { method: 'DELETE', auth: true });
}

export async function adminCreateSection(payload: Record<string, unknown>) {
  return request('/api/v1/admin/sections', { method: 'POST', body: JSON.stringify(payload), auth: true });
}

export async function adminUpdateSection(sectionId: string, payload: Record<string, unknown>) {
  return request(`/api/v1/admin/sections/${sectionId}`, { method: 'PUT', body: JSON.stringify(payload), auth: true });
}

export async function adminReorderSections(payload: Record<string, unknown>) {
  return request('/api/v1/admin/sections/reorder', { method: 'POST', body: JSON.stringify(payload), auth: true });
}

export async function adminDeleteSection(sectionId: string) {
  return request(`/api/v1/admin/sections/${sectionId}`, { method: 'DELETE', auth: true });
}

export async function adminCreateItem(payload: Record<string, unknown>) {
  return request('/api/v1/admin/items', { method: 'POST', body: JSON.stringify(payload), auth: true });
}

export async function adminUpdateItem(itemId: string, payload: Record<string, unknown>) {
  return request(`/api/v1/admin/items/${itemId}`, { method: 'PUT', body: JSON.stringify(payload), auth: true });
}

export async function adminReorderItems(payload: Record<string, unknown>) {
  return request('/api/v1/admin/items/reorder', { method: 'POST', body: JSON.stringify(payload), auth: true });
}

export async function adminDeleteItem(itemId: string) {
  return request(`/api/v1/admin/items/${itemId}`, { method: 'DELETE', auth: true });
}

export async function adminUploadImage(file: File) {
  const form = new FormData();
  form.append('file', file);
  return request('/api/v1/admin/uploads', { method: 'POST', body: form, auth: true, isForm: true });
}

async function request(path: string, options: RequestInit & { auth?: boolean; userAuth?: boolean; isForm?: boolean } = {}) {
  const headers = new Headers(options.headers);
  headers.set('X-Tenant-ID', tenantId);
  if (!options.isForm) {
    headers.set('Content-Type', 'application/json');
  }
  if (options.auth) {
    const token = getAdminToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }
  if (options.userAuth) {
    const session = getUserSession();
    if (session?.accessToken) {
      headers.set('Authorization', `Bearer ${session.accessToken}`);
    } else if (!headers.has('Authorization')) {
      const token = getAdminToken();
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
    }
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    throw new Error(`request failed: ${response.status}`);
  }
  return response.json();
}

function portalAuthOptions(): { auth?: boolean; userAuth?: boolean } {
  return getUserSession()?.accessToken || getAdminToken()
    ? { auth: true, userAuth: true }
    : {};
}

function normalizeLoginResult(payload: any): LoginResult {
  return {
    accessToken: payload.access_token ?? payload.accessToken ?? '',
    tokenType: payload.token_type ?? payload.tokenType ?? 'bearer',
    user: {
      id: payload.user?.id ?? '',
      tenantId: payload.user?.tenant_id ?? payload.user?.tenantId ?? tenantId,
      phone: payload.user?.phone ?? '',
      displayName: payload.user?.display_name ?? payload.user?.displayName ?? '',
      role: payload.user?.role ?? 'USER',
      status: payload.user?.status ?? 'ACTIVE'
    }
  };
}

function getStorageItem(key: string): string {
  if (typeof window === 'undefined' || !window.localStorage) {
    return '';
  }
  return window.localStorage.getItem(key) ?? '';
}

function setStorageItem(key: string, value: string) {
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.setItem(key, value);
  }
}

function removeStorageItem(key: string) {
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.removeItem(key);
  }
}

function dispatchUserSessionChanged() {
  if (typeof window === 'undefined' || typeof window.dispatchEvent !== 'function') {
    return;
  }
  const event = typeof CustomEvent === 'function'
    ? new CustomEvent(userSessionChangedEvent)
    : ({ type: userSessionChangedEvent } as Event);
  window.dispatchEvent(event);
}

function normalizeGenerationRequestOptions(requestKeyOrOptions?: string | GenerationRequestOptions): GenerationRequestOptions {
  if (!requestKeyOrOptions) {
    return {};
  }
  if (typeof requestKeyOrOptions === 'string') {
    return { requestKey: requestKeyOrOptions };
  }
  return requestKeyOrOptions;
}

function encodeDetailPath(detailPath: string): string {
  return detailPath
    .replace(/^\/+/, '')
    .split('/')
    .filter(Boolean)
    .map((segment) => encodeURIComponent(segment))
    .join('/');
}

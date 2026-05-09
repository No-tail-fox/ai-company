import {
  createFallbackAssistantCenter,
  createFallbackImageWorkbench,
  createFallbackPageConfig,
  createFallbackPortalConfig,
  createFallbackVideoWorkbench,
  buildAudioTaskPayload,
  normalizeAssistantCenter,
  normalizeAudioTask,
  normalizeImageWorkbench,
  normalizePageConfig,
  normalizePortalConfig,
  normalizeVideoWorkbench,
  type AssistantCenter,
  type AudioTask,
  type AudioTaskPayload,
  type ImageTask,
  type ImageWorkbench,
  type PortalConfig,
  type PortalItem,
  type PortalPageConfig,
  type VideoTask,
  type VideoWorkbench
} from './viewModel';

const tenantId = 'demo';
const tokenKey = 'opc_admin_token';

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

export function getAdminToken(): string {
  return window.localStorage.getItem(tokenKey) ?? '';
}

export function setAdminToken(token: string) {
  window.localStorage.setItem(tokenKey, token);
}

export function clearAdminToken() {
  window.localStorage.removeItem(tokenKey);
}

export async function loginAdmin(phone: string, password: string): Promise<LoginResult> {
  const payload = await request('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ phone, password })
  });
  const result = {
    accessToken: payload.access_token,
    tokenType: payload.token_type,
    user: {
      id: payload.user.id,
      tenantId: payload.user.tenant_id ?? payload.user.tenantId,
      phone: payload.user.phone,
      displayName: payload.user.display_name ?? payload.user.displayName,
      role: payload.user.role,
      status: payload.user.status
    }
  };
  setAdminToken(result.accessToken);
  return result;
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

export async function fetchAssistantCenter(): Promise<AssistantCenter> {
  try {
    return normalizeAssistantCenter(await request('/api/v1/assistants'));
  } catch {
    return createFallbackAssistantCenter();
  }
}

export async function fetchVideoWorkbench(): Promise<VideoWorkbench> {
  try {
    return normalizeVideoWorkbench(await request('/api/v1/video/workbench?user_id=demo-user'));
  } catch {
    return createFallbackVideoWorkbench();
  }
}

export async function createVideoGeneration(prompt: string, requestKey?: string): Promise<VideoTask> {
  const payload = await request('/api/v1/video/generations', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      user_id: 'demo-user',
      route_key: 'video_text_to_video',
      request_key: requestKey
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

export async function fetchImageWorkbench(): Promise<ImageWorkbench> {
  try {
    return normalizeImageWorkbench(await request('/api/v1/image/workbench?user_id=demo-user'));
  } catch {
    return createFallbackImageWorkbench();
  }
}

export async function createImageGeneration(prompt: string, requestKey?: string): Promise<ImageTask> {
  const payload = await request('/api/v1/image/generations', {
    method: 'POST',
    body: JSON.stringify({
      prompt,
      user_id: 'demo-user',
      route_key: 'image_text_to_image',
      request_key: requestKey
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

export async function fetchAudioTasks(): Promise<AudioTask[]> {
  try {
    const payload = await request('/api/v1/audio/tasks');
    return (payload.tasks ?? []).map(normalizeAudioTask);
  } catch {
    return [];
  }
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

export async function uploadAudio(file: File) {
  const form = new FormData();
  form.append('file', file);
  return request('/api/v1/audio/uploads', { method: 'POST', body: form, isForm: true });
}

export async function adminListPages() {
  return request('/api/v1/admin/pages', { auth: true });
}

export async function adminFetchPageContent(pageKey: string) {
  return request(`/api/v1/admin/page-content/${encodeURIComponent(pageKey)}`, { auth: true });
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

async function request(path: string, options: RequestInit & { auth?: boolean; isForm?: boolean } = {}) {
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
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    throw new Error(`request failed: ${response.status}`);
  }
  return response.json();
}

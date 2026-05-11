<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  AlertCircle,
  Bot,
  ChevronRight,
  Circle,
  FileDown,
  FileText,
  Folder,
  Image as ImageIcon,
  Loader2,
  MessageSquare,
  Music,
  Paperclip,
  Plus,
  RefreshCw,
  Search,
  Send,
  Settings,
  Sparkles,
  UploadCloud,
  UserRound,
} from 'lucide-vue-next';
import WorkspaceShell from './WorkspaceShell.vue';
import {
  createChatSession,
  exportChatSession,
  fetchChatWorkbench,
  sendChatMessage,
  updateChatSession
} from '../services/api';
import {
  createFallbackChatWorkbench,
  groupChatSessionsByRecency,
  type ChatActiveSession,
  type ChatExportFile,
  type ChatMessage,
  type ChatModelSummary,
  type ChatSessionSummary,
  type ChatWorkbench
} from '../services/viewModel';

interface WorkbenchSettings {
  autoSave: boolean;
  codeHighlight: boolean;
  streaming: boolean;
  fontSize: number;
  themeMode: string;
}

const SETTINGS_KEY = 'opc_workbench_settings';
const EXPORT_CACHE_KEY = 'opc_workbench_exports';
const DEFAULT_MODEL_KEY = 'general_text_default';

const fallbackWorkbench = createFallbackChatWorkbench();
const route = useRoute();
const router = useRouter();
const workbench = ref<ChatWorkbench>(fallbackWorkbench);
const threadRef = ref<HTMLElement | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const isLoading = ref(false);
const isSending = ref(false);
const isExporting = ref(false);
const searchQuery = ref('');
const draft = ref('');
const errorMessage = ref('');
const selectedModelKey = ref(DEFAULT_MODEL_KEY);
const selectedRole = ref('通用助手');
const uploadedFileName = ref('');
const settings = ref<WorkbenchSettings>(loadSettings());

const roleOptions = ['通用助手', '产品经理', '文案顾问', '技术顾问'];

const activeSession = computed(() => workbench.value.activeSession);
const availableModels = computed<ChatModelSummary[]>(() =>
  workbench.value.models.length > 0 ? workbench.value.models : fallbackWorkbench.models
);
const activeModel = computed(() =>
  availableModels.value.find((model) => model.modelKey === selectedModelKey.value) ?? availableModels.value[0]
);
const filteredSessions = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase();
  if (!keyword) {
    return workbench.value.sessions;
  }
  return workbench.value.sessions.filter((session) =>
    `${session.title} ${session.preview}`.toLowerCase().includes(keyword)
  );
});
const sessionGroups = computed(() => groupChatSessionsByRecency(filteredSessions.value));
const modelConfigNotice = computed(() =>
  workbench.value.models.length === 0
    ? '后台尚未启用可用 TEXT 模型渠道，发送时会返回配置提示。'
    : ''
);
const threadStyle = computed(() => ({
  fontSize: `${settings.value.fontSize}px`
}));
const queueItems = computed(() => [
  {
    id: 'chat-active',
    title: '对话任务 #1024',
    subtitle: activeSession.value?.title || '等待新对话',
    status: isSending.value ? '生成中' : '排队中',
    tone: isSending.value ? 'blue' : 'orange',
    time: '刚刚',
    icon: MessageSquare
  },
  {
    id: 'export-active',
    title: '导出任务 #1025',
    subtitle: 'Markdown 文件生成',
    status: isExporting.value ? '生成中' : '就绪',
    tone: isExporting.value ? 'blue' : 'green',
    time: isExporting.value ? '刚刚' : '待触发',
    icon: FileText
  },
  {
    id: 'image-link',
    title: '图像生成 #1023',
    subtitle: '跳转到图像工作台',
    status: '可用',
    tone: 'blue',
    time: '3 分钟前',
    icon: ImageIcon
  }
]);
const recentRuns = computed(() =>
  workbench.value.sessions.slice(0, 4).map((session, index) => ({
    id: session.id,
    title: session.title || '未命名对话',
    meta: formatDateTime(session.updatedAt ?? session.createdAt),
    icon: index % 3 === 0 ? MessageSquare : index % 3 === 1 ? ImageIcon : Music
  }))
);

onMounted(async () => {
  await loadWorkbench(currentRouteSessionId());
});

watch(
  () => route.query.session,
  async () => {
    await loadWorkbench(currentRouteSessionId(), false);
  }
);

watch(
  settings,
  (value) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(value));
    }
  },
  { deep: true }
);

async function loadWorkbench(sessionId = '', syncQuery = true) {
  isLoading.value = true;
  try {
    const payload = applyCachedExports(await fetchChatWorkbench(sessionId || undefined));
    workbench.value = payload;
    if (payload.activeSession) {
      selectedModelKey.value = payload.activeSession.modelKey || DEFAULT_MODEL_KEY;
      selectedRole.value = payload.activeSession.presetRole || selectedRole.value;
      if (syncQuery && !sessionId) {
        await router.replace({ path: '/workbench', query: { ...route.query, session: payload.activeSession.id } });
      }
    } else if (availableModels.value[0]) {
      selectedModelKey.value = availableModels.value[0].modelKey;
    }
    errorMessage.value = '';
    await nextTick(scrollThreadToBottom);
  } finally {
    isLoading.value = false;
  }
}

async function createNewChat() {
  errorMessage.value = '';
  try {
    const session = await createChatSession({
      title: '',
      modelKey: selectedModelKey.value || DEFAULT_MODEL_KEY,
      presetRole: selectedRole.value
    });
    applyActiveSession(session);
    await router.push({ path: '/workbench', query: { session: session.id } });
    draft.value = '';
    await nextTick(scrollThreadToBottom);
    return session;
  } catch (error) {
    errorMessage.value = friendlyError(error);
    return null;
  }
}

async function selectSession(session: ChatSessionSummary) {
  if (session.id === activeSession.value?.id) {
    return;
  }
  await router.push({ path: '/workbench', query: { session: session.id } });
}

async function saveSessionPreferences() {
  const session = activeSession.value;
  if (!session) {
    return;
  }
  try {
    const updated = await updateChatSession(session.id, {
      modelKey: selectedModelKey.value,
      presetRole: selectedRole.value
    });
    applyActiveSession(updated);
  } catch (error) {
    errorMessage.value = friendlyError(error);
  }
}

async function sendDraft() {
  const content = draft.value.trim();
  if (!content || isSending.value) {
    return;
  }
  let session = activeSession.value;
  if (!session) {
    session = await createNewChat();
  }
  if (!session) {
    return;
  }
  const shouldExport = /导出|markdown|md/i.test(content);
  draft.value = '';
  isSending.value = true;
  errorMessage.value = '';
  try {
    const result = await sendChatMessage(session.id, {
      content,
      modelKey: selectedModelKey.value || DEFAULT_MODEL_KEY
    });
    applyActiveSession(result.session);
    await nextTick(scrollThreadToBottom);
    if (shouldExport) {
      await exportCurrentSession();
    }
  } catch (error) {
    draft.value = content;
    errorMessage.value = friendlyError(error);
  } finally {
    isSending.value = false;
  }
}

async function exportCurrentSession() {
  const session = activeSession.value;
  if (!session || isExporting.value) {
    return;
  }
  isExporting.value = true;
  errorMessage.value = '';
  try {
    const result = await exportChatSession(session.id);
    const message = {
      ...result.message,
      export: result.message.export ?? result.asset
    };
    rememberExport(message);
    appendMessage(message);
    await nextTick(scrollThreadToBottom);
  } catch (error) {
    errorMessage.value = friendlyError(error);
  } finally {
    isExporting.value = false;
  }
}

function handleComposerKey(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    void sendDraft();
  }
}

function openFilePicker() {
  fileInput.value?.click();
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  uploadedFileName.value = input.files?.[0]?.name ?? '';
}

function toggleSetting(key: 'autoSave' | 'codeHighlight' | 'streaming') {
  settings.value[key] = !settings.value[key];
}

function applyActiveSession(session: ChatActiveSession) {
  const cached = applyCachedExportsToSession(session);
  const summary = sessionToSummary(cached);
  const sessions = workbench.value.sessions.filter((item) => item.id !== cached.id);
  workbench.value = {
    ...workbench.value,
    activeSession: cached,
    sessions: [summary, ...sessions].sort((left, right) =>
      String(right.updatedAt ?? '').localeCompare(String(left.updatedAt ?? ''))
    )
  };
}

function appendMessage(message: ChatMessage) {
  const session = activeSession.value;
  if (!session) {
    return;
  }
  const exists = session.messages.some((item) => item.id === message.id);
  const messages = exists
    ? session.messages.map((item) => (item.id === message.id ? message : item))
    : [...session.messages, message];
  applyActiveSession({
    ...session,
    messages,
    messageCount: messages.length,
    preview: message.content,
    updatedAt: message.createdAt ?? new Date().toISOString()
  });
}

function sessionToSummary(session: ChatActiveSession): ChatSessionSummary {
  const lastMessage = session.messages[session.messages.length - 1];
  return {
    id: session.id,
    tenantId: session.tenantId,
    userId: session.userId,
    title: session.title || '新对话',
    preview: lastMessage?.content ?? session.preview ?? '',
    presetRole: session.presetRole,
    modelKey: session.modelKey,
    status: session.status,
    messageCount: session.messages.length,
    createdAt: session.createdAt,
    updatedAt: lastMessage?.createdAt ?? session.updatedAt
  };
}

function currentRouteSessionId(): string {
  const value = route.query.session;
  if (Array.isArray(value)) {
    return value[0] ?? '';
  }
  return value ? String(value) : '';
}

function applyCachedExports(payload: ChatWorkbench): ChatWorkbench {
  if (!payload.activeSession) {
    return payload;
  }
  return {
    ...payload,
    activeSession: applyCachedExportsToSession(payload.activeSession)
  };
}

function applyCachedExportsToSession(session: ChatActiveSession): ChatActiveSession {
  const cache = loadExportCache();
  return {
    ...session,
    messages: session.messages.map((message) => ({
      ...message,
      export: message.export ?? cache[message.id] ?? null
    }))
  };
}

function rememberExport(message: ChatMessage) {
  if (!message.export || typeof window === 'undefined') {
    return;
  }
  const cache = loadExportCache();
  cache[message.id] = message.export;
  window.localStorage.setItem(EXPORT_CACHE_KEY, JSON.stringify(cache));
}

function loadExportCache(): Record<string, ChatExportFile> {
  if (typeof window === 'undefined') {
    return {};
  }
  try {
    return JSON.parse(window.localStorage.getItem(EXPORT_CACHE_KEY) ?? '{}');
  } catch {
    return {};
  }
}

function scrollThreadToBottom() {
  const element = threadRef.value;
  if (element) {
    element.scrollTop = element.scrollHeight;
  }
}

function loadSettings(): WorkbenchSettings {
  if (typeof window === 'undefined') {
    return defaultSettings();
  }
  try {
    return { ...defaultSettings(), ...JSON.parse(window.localStorage.getItem(SETTINGS_KEY) ?? '{}') };
  } catch {
    return defaultSettings();
  }
}

function defaultSettings(): WorkbenchSettings {
  return {
    autoSave: true,
    codeHighlight: true,
    streaming: true,
    fontSize: 14,
    themeMode: 'system'
  };
}

function friendlyError(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  if (message.includes('TEXT') || message.includes('text') || message.includes('400') || message.includes('502')) {
    return '发送失败：请先在后台启用可用的 TEXT 模型渠道，再重新发送。';
  }
  return `发送失败：${message}`;
}

function formatSessionTime(value?: string | null): string {
  if (!value) {
    return '刚刚';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '刚刚';
  }
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

function formatDateTime(value?: string | null): string {
  if (!value) {
    return '刚刚';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '刚刚';
  }
  return `${date.toLocaleDateString('zh-CN')} ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`;
}

function formatFileSize(size?: number): string {
  if (!size) {
    return 'Markdown';
  }
  if (size < 1024) {
    return `${size} B`;
  }
  return `${(size / 1024).toFixed(1)} KB`;
}

</script>

<template>
  <WorkspaceShell
    active-module-key="chat"
    page-title="AI 工作台"
    page-subtitle="真实对话、队列和快捷操作的统一工作区"
    page-icon="Sparkles"
    variant="chat"
  >
    <template #headerActions>
      <button class="workspace-icon-action" aria-label="刷新" @click="loadWorkbench(currentRouteSessionId())">
        <RefreshCw :size="20" />
      </button>
      <button class="workspace-icon-action" aria-label="文件">
        <Folder :size="20" />
      </button>
      <button class="workspace-icon-action" aria-label="设置">
        <Settings :size="20" />
      </button>
    </template>

    <template #leftFooter>
      <div class="workbench-left-selects">
        <label>
          <span>角色：</span>
          <select v-model="selectedRole" @change="saveSessionPreferences">
            <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
          </select>
        </label>
        <label>
          <span>模型：</span>
          <select v-model="selectedModelKey" @change="saveSessionPreferences">
            <option v-for="model in availableModels" :key="model.modelKey" :value="model.modelKey">
              {{ model.displayName }}
            </option>
          </select>
        </label>
      </div>
    </template>

    <template #main>
        <section class="workbench-chat-card">
          <div class="workbench-toolbar">
            <label>
              <span>模型选择</span>
              <select v-model="selectedModelKey" @change="saveSessionPreferences">
                <option v-for="model in availableModels" :key="model.modelKey" :value="model.modelKey">
                  {{ model.displayName }}
                </option>
              </select>
            </label>
            <label>
              <span>人设选择</span>
              <select v-model="selectedRole" @change="saveSessionPreferences">
                <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
              </select>
            </label>
            <button class="workbench-new-chat" @click="createNewChat">
              <Plus :size="18" />
              新建对话
            </button>
          </div>

          <div v-if="modelConfigNotice" class="workbench-config-alert">
            <AlertCircle :size="17" />
            <span>{{ modelConfigNotice }}</span>
          </div>
          <div v-if="errorMessage" class="workbench-error-alert">
            <AlertCircle :size="17" />
            <span>{{ errorMessage }}</span>
          </div>

          <div class="workbench-chat-layout">
            <aside class="workbench-session-menu">
              <label class="workbench-session-search">
                <Search :size="17" />
                <input v-model="searchQuery" placeholder="搜索对话..." />
              </label>

              <div v-if="isLoading" class="workbench-loading">
                <Loader2 :size="18" />
                <span>加载会话...</span>
              </div>

              <template v-for="group in sessionGroups" :key="group.key">
                <h2>{{ group.label }}</h2>
                <button
                  v-for="session in group.sessions"
                  :key="session.id"
                  :class="{ active: session.id === activeSession?.id }"
                  class="workbench-session-item"
                  @click="selectSession(session)"
                >
                  <Circle v-if="session.id !== activeSession?.id" :size="15" />
                  <span v-else class="workbench-active-dot"></span>
                  <strong>{{ session.title || '新对话' }}</strong>
                  <em>{{ formatSessionTime(session.updatedAt ?? session.createdAt) }}</em>
                </button>
              </template>

              <button class="workbench-all-sessions" @click="searchQuery = ''">
                查看全部对话
                <ChevronRight :size="17" />
              </button>
            </aside>

            <section class="workbench-thread-panel">
              <div ref="threadRef" class="workbench-thread" :style="threadStyle">
                <article
                  v-for="message in activeSession?.messages ?? []"
                  :key="message.id"
                  :class="['workbench-message', message.role === 'user' ? 'from-user' : 'from-assistant']"
                >
                  <span class="workbench-avatar">
                    <UserRound v-if="message.role === 'user'" :size="20" />
                    <Sparkles v-else :size="20" />
                  </span>
                  <div class="workbench-message-body">
                    <p v-if="!message.export">{{ message.content }}</p>
                    <a
                      v-else
                      class="workbench-file-card"
                      :href="message.export.url"
                      target="_blank"
                      rel="noreferrer"
                    >
                      <span class="workbench-file-icon">
                        <FileText :size="30" />
                        <b>MD</b>
                      </span>
                      <span>
                        <strong>{{ message.export.fileName || 'Markdown 文件.md' }}</strong>
                        <small>{{ formatFileSize(message.export.size) }}</small>
                        <em>{{ message.content }}</em>
                      </span>
                    </a>
                    <time>{{ formatSessionTime(message.createdAt) }}</time>
                  </div>
                </article>

                <div v-if="!activeSession?.messages.length" class="workbench-empty-thread">
                  <Bot :size="36" />
                  <strong>新对话已就绪</strong>
                  <span>输入任务后会保存为真实会话，并调用已配置的 TEXT 模型。</span>
                </div>
              </div>

              <footer class="workbench-composer">
                <button aria-label="添加附件" @click="openFilePicker">
                  <Paperclip :size="25" />
                </button>
                <textarea
                  v-model="draft"
                  rows="2"
                  placeholder="输入消息，Enter 发送"
                  @keydown="handleComposerKey"
                />
                <select v-model="selectedModelKey" @change="saveSessionPreferences">
                  <option v-for="model in availableModels" :key="model.modelKey" :value="model.modelKey">
                    {{ model.displayName }}
                  </option>
                </select>
                <button class="workbench-send" :disabled="isSending || !draft.trim()" @click="sendDraft">
                  <Loader2 v-if="isSending" :size="21" />
                  <Send v-else :size="21" />
                  发送
                </button>
                <input ref="fileInput" type="file" hidden @change="handleFileChange" />
                <span v-if="uploadedFileName" class="workbench-uploaded">已选择：{{ uploadedFileName }}</span>
              </footer>
            </section>
          </div>
        </section>
    </template>

    <template #side>
        <section class="workbench-side-card">
          <header>
            <h2>任务队列</h2>
            <button>查看全部</button>
          </header>
          <article v-for="item in queueItems" :key="item.id" class="workbench-queue-item">
            <span :class="['workbench-queue-icon', item.tone]">
              <component :is="item.icon" :size="21" />
            </span>
            <div>
              <strong>{{ item.title }}</strong>
              <small>{{ item.subtitle }}</small>
            </div>
            <em :class="item.tone">{{ item.status }}</em>
            <time>{{ item.time }}</time>
          </article>
        </section>

        <section class="workbench-side-card">
          <header>
            <h2>最近运行</h2>
            <button @click="searchQuery = ''">查看全部</button>
          </header>
          <article v-for="item in recentRuns" :key="item.id" class="workbench-run-item">
            <component :is="item.icon" :size="21" />
            <span>
              <strong>{{ item.title }}</strong>
              <small>{{ item.meta }}</small>
            </span>
          </article>
        </section>

        <section class="workbench-side-card">
          <header>
            <h2>快捷操作</h2>
          </header>
          <div class="workbench-quick-actions">
            <button @click="createNewChat">
              <Plus :size="29" />
              <span>新建任务</span>
            </button>
            <button @click="openFilePicker">
              <UploadCloud :size="29" />
              <span>导入素材</span>
            </button>
            <button :disabled="isExporting" @click="exportCurrentSession">
              <FileDown :size="29" />
              <span>下载结果</span>
            </button>
          </div>
        </section>

        <section class="workbench-side-card settings-card">
          <header>
            <h2>设置</h2>
          </header>
          <label class="workbench-setting-row">
            <span>自动保存对话</span>
            <button :class="{ active: settings.autoSave }" role="switch" @click="toggleSetting('autoSave')">
              <i></i>
            </button>
          </label>
          <label class="workbench-setting-row">
            <span>代码块语法高亮</span>
            <button :class="{ active: settings.codeHighlight }" role="switch" @click="toggleSetting('codeHighlight')">
              <i></i>
            </button>
          </label>
          <label class="workbench-setting-row">
            <span>流式输出</span>
            <button :class="{ active: settings.streaming }" role="switch" @click="toggleSetting('streaming')">
              <i></i>
            </button>
          </label>
          <label class="workbench-slider-row">
            <span>字体大小</span>
            <input v-model.number="settings.fontSize" type="range" min="12" max="18" />
            <em>{{ settings.fontSize }}px</em>
          </label>
          <label class="workbench-theme-row">
            <span>主题模式</span>
            <select v-model="settings.themeMode">
              <option value="system">跟随系统</option>
              <option value="light">明亮模式</option>
              <option value="focus">专注模式</option>
            </select>
          </label>
        </section>
    </template>
  </WorkspaceShell>
</template>

<style scoped>
.workbench-composer button,
.workbench-side-card button {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.workbench-left-selects {
  display: grid;
  gap: 12px;
}

.workbench-left-selects label,
.workbench-toolbar label {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #4b5563;
}

.workbench-left-selects label {
  justify-content: space-between;
  min-height: 52px;
  padding: 0 14px;
  border: 1px solid #dce3ee;
  border-radius: 12px;
  background: #fff;
}

.workbench-left-selects select,
.workbench-toolbar select,
.workbench-composer select,
.workbench-theme-row select {
  min-width: 110px;
  border: 0;
  background: transparent;
  color: #111827;
  font: inherit;
  outline: none;
}

.workbench-chat-card {
  min-height: 620px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
  overflow: visible;
}

.workbench-toolbar {
  min-height: 72px;
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  align-items: center;
  gap: 28px;
  padding: 14px 18px;
  border-bottom: 1px solid #e4e9f1;
}

.workbench-toolbar label select {
  height: 42px;
  min-width: 160px;
  padding: 0 18px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: #fff;
}

.workbench-new-chat,
.workbench-send {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 18px;
  border: 1px solid #7068ff !important;
  border-radius: 8px;
  color: #5146e8 !important;
  background: #fff !important;
}

.workbench-config-alert,
.workbench-error-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 18px 0;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
}

.workbench-config-alert {
  color: #9a5b00;
  background: #fff8e6;
}

.workbench-error-alert {
  color: #b42318;
  background: #fff1f0;
}

.workbench-chat-layout {
  min-height: 560px;
  display: grid;
  grid-template-columns: 255px minmax(0, 1fr);
}

.workbench-session-menu {
  padding: 16px 12px;
  border-right: 1px solid #e4e9f1;
}

.workbench-session-search {
  height: 40px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  color: #8992a4;
  background: #fff;
}

.workbench-session-search input {
  width: 100%;
  border: 0;
  outline: none;
  font: inherit;
}

.workbench-session-menu h2 {
  margin: 24px 10px 10px;
  color: #4b5563;
  font-size: 14px;
}

.workbench-session-item {
  width: 100%;
  min-height: 46px;
  display: grid;
  grid-template-columns: 18px 1fr auto;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding: 0 10px;
  border: 1px solid #e1e7f0;
  border-radius: 8px;
  background: #fff;
  color: #111827;
  cursor: pointer;
}

.workbench-session-item.active {
  border-color: #6d63ff;
  background: #fbfbff;
}

.workbench-session-item strong {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-weight: 600;
}

.workbench-session-item em {
  color: #8b95a7;
  font-size: 12px;
  font-style: normal;
}

.workbench-active-dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: #5f62f5;
}

.workbench-all-sessions {
  width: 100%;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18px;
  padding: 0 12px;
  border: 0;
  border-top: 1px solid #edf1f6;
  background: transparent;
  color: #4b5563;
  cursor: pointer;
}

.workbench-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px 10px;
  color: #6b7280;
}

.workbench-loading svg,
.workbench-send svg:first-child {
  animation: workbench-spin 0.8s linear infinite;
}

.workbench-thread-panel {
  min-width: 0;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
}

.workbench-thread {
  min-height: 0;
  padding: 24px 28px;
}

.workbench-message {
  display: grid;
  grid-template-columns: 42px minmax(160px, 1fr);
  gap: 14px;
  margin-bottom: 22px;
}

.workbench-message.from-user {
  grid-template-columns: minmax(160px, 1fr) 42px;
}

.workbench-message.from-user .workbench-avatar {
  grid-column: 2;
  grid-row: 1;
}

.workbench-message.from-user .workbench-message-body {
  grid-column: 1;
  justify-self: end;
}

.workbench-avatar {
  width: 34px;
  height: 34px;
  display: inline-grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, #5f62f5, #7c6ff6);
}

.workbench-message.from-user .workbench-avatar {
  color: #4f46e5;
  background: #eef1ff;
}

.workbench-message-body {
  max-width: min(680px, 86%);
}

.workbench-message-body p {
  margin: 0;
  padding: 18px 20px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: #fff;
  line-height: 1.75;
  white-space: pre-wrap;
}

.workbench-message.from-user .workbench-message-body p {
  border-color: #cfd4ff;
  background: #fbfbff;
}

.workbench-message-body time {
  display: block;
  margin-top: 8px;
  color: #8b95a7;
  font-size: 12px;
}

.workbench-file-card {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  gap: 14px;
  width: min(380px, 100%);
  padding: 14px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: #fff;
  color: #111827;
  text-decoration: none;
}

.workbench-file-icon {
  width: 50px;
  height: 50px;
  display: grid;
  place-items: center;
  border: 1px solid #cfd4ff;
  border-radius: 8px;
  color: #5b54f2;
  background: #f1f0ff;
}

.workbench-file-icon b {
  font-size: 11px;
}

.workbench-file-card span:last-child {
  display: grid;
  gap: 4px;
}

.workbench-file-card small,
.workbench-file-card em {
  color: #8b95a7;
  font-style: normal;
}

.workbench-empty-thread {
  min-height: 320px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  color: #6b7280;
  text-align: center;
}

.workbench-empty-thread strong {
  color: #111827;
  font-size: 18px;
}

.workbench-composer {
  position: relative;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 120px 118px;
  align-items: end;
  gap: 12px;
  margin: 0 20px 18px;
  padding: 12px 14px;
  border: 1px solid #aeaaff;
  border-radius: 12px;
  background: #fff;
}

.workbench-composer > button:first-child {
  width: 38px;
  height: 38px;
  color: #4b5563;
}

.workbench-composer textarea {
  resize: none;
  min-height: 42px;
  max-height: 130px;
  border: 0;
  outline: none;
  color: #111827;
  font: inherit;
  line-height: 1.6;
}

.workbench-composer select {
  height: 38px;
  padding: 0 10px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
}

.workbench-send {
  min-height: 46px;
  color: #fff !important;
  border: 0 !important;
  background: linear-gradient(135deg, #625cf6, #7b65f5) !important;
}

.workbench-send:disabled,
.workbench-quick-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.workbench-uploaded {
  position: absolute;
  left: 58px;
  bottom: -22px;
  color: #64748b;
  font-size: 12px;
}

.workbench-side-card {
  padding: 18px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
}

.workbench-side-card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.workbench-side-card h2 {
  margin: 0;
  font-size: 18px;
}

.workbench-side-card header button {
  color: #4f46e5;
  font-size: 13px;
}

.workbench-queue-item {
  min-height: 66px;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e9f1;
  border-radius: 8px;
}

.workbench-queue-item + .workbench-queue-item,
.workbench-run-item + .workbench-run-item {
  margin-top: 10px;
}

.workbench-queue-icon {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 50%;
}

.workbench-queue-icon.blue {
  color: #4f46e5;
  background: #eef1ff;
}

.workbench-queue-icon.green {
  color: #11a66a;
  background: #eafaf3;
}

.workbench-queue-icon.orange {
  color: #d97800;
  background: #fff6e8;
}

.workbench-queue-item div,
.workbench-run-item span {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.workbench-queue-item strong,
.workbench-run-item strong {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.workbench-queue-item small,
.workbench-queue-item time,
.workbench-run-item small {
  color: #8b95a7;
}

.workbench-queue-item em {
  grid-column: 3;
  padding: 5px 10px;
  border-radius: 8px;
  font-style: normal;
  font-size: 12px;
}

.workbench-queue-item em.blue {
  color: #4f46e5;
  background: #eef1ff;
}

.workbench-queue-item em.green {
  color: #0f8a58;
  background: #eafaf3;
}

.workbench-queue-item em.orange {
  color: #b76300;
  background: #fff3dd;
}

.workbench-queue-item time {
  grid-column: 3;
  font-size: 12px;
}

.workbench-run-item {
  min-height: 54px;
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #e4e9f1;
  border-radius: 8px;
}

.workbench-run-item svg {
  color: #4f46e5;
}

.workbench-quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.workbench-quick-actions button {
  min-height: 96px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  border: 1px solid #dfe5ef !important;
  border-radius: 8px;
  color: #4f46e5;
  background: #fff !important;
}

.workbench-quick-actions span {
  color: #111827;
}

.settings-card {
  display: grid;
  gap: 14px;
}

.workbench-setting-row,
.workbench-slider-row,
.workbench-theme-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  color: #374151;
}

.workbench-setting-row button {
  width: 46px;
  height: 26px;
  padding: 3px;
  border-radius: 999px;
  background: #d8dee9;
}

.workbench-setting-row button i {
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.18s ease;
}

.workbench-setting-row button.active {
  background: #5f62f5;
}

.workbench-setting-row button.active i {
  transform: translateX(20px);
}

.workbench-slider-row {
  grid-template-columns: auto minmax(0, 1fr) auto;
}

.workbench-slider-row input {
  width: 100%;
  accent-color: #5f62f5;
}

.workbench-theme-row select {
  height: 38px;
  min-width: 140px;
  padding: 0 12px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: #fff;
}

@keyframes workbench-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1280px) {
  .workbench-toolbar {
    gap: 16px;
  }
}
</style>

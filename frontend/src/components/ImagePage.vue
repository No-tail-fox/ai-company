<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  Download,
  Expand,
  Image as ImageIcon,
  List,
  Search,
  Sparkles
} from 'lucide-vue-next';
import { createImageGeneration, fetchImageWorkbench, fetchWorkbenchCapabilities } from '../services/api';
import {
  getImageStatusMeta,
  loadWorkbenchDraft,
  saveWorkbenchDraft,
  type ImageTask,
  type ImageWorkbench,
  type WorkbenchCapability
} from '../services/viewModel';
import WorkspaceShell from './WorkspaceShell.vue';

interface ImageDraft {
  model: string;
  size: string;
  ratio: string;
  style: string;
  prompt: string;
  quality: string;
  count: string;
  seed: string;
  autoSave: boolean;
  codeHighlight: boolean;
  streaming: boolean;
}

interface PreviewCard {
  id: string;
  title: string;
  label: string;
  url?: string | null;
  accent: string;
  featured?: boolean;
}

const SURFACE = 'workbench';
const DRAFT_KEY = 'opc_workbench_image_draft';

const emptyImageWorkbench: ImageWorkbench = {
  tenantId: '',
  userId: '',
  surface: SURFACE,
  wallet: { balance: 0, frozenBalance: 0 },
  route: { routeKey: '', unitCost: 0 },
  tasks: []
};

const defaultDraft: ImageDraft = {
  model: '通用绘图',
  size: '1024 x 1024',
  ratio: '1:1',
  style: '写实',
  prompt: '',
  quality: '高（推荐）',
  count: '4 张',
  seed: '',
  autoSave: true,
  codeHighlight: true,
  streaming: true
};

const workbench = ref<ImageWorkbench>(emptyImageWorkbench);
const draft = ref<ImageDraft>(loadWorkbenchDraft(DRAFT_KEY, defaultDraft));
const capabilities = ref<WorkbenchCapability[]>([]);
const selectedCapabilityKey = ref('');
const isCreating = ref(false);
const createError = ref('');
const activeHistoryId = ref('');
const historyQuery = ref('');
const pollTimer = ref<number | null>(null);

const modelOptions = ['通用绘图', '商品摄影', '海报设计', '国风插画'];
const sizeOptions = ['1024 x 1024', '1344 x 768', '768 x 1344', '1536 x 1024'];
const ratioOptions = ['1:1', '3:4', '4:3', '16:9', '9:16'];
const styleOptions = ['写实', '插画', '国风', '赛博', '极简', '3D', '产品图', '海报'];

const historyRows = computed(() => {
  const keyword = historyQuery.value.trim().toLowerCase();
  const taskRows = workbench.value.tasks.slice(0, 4).map((task) => ({
    id: task.id,
    title: compact(task.prompt, 14),
    time: formatTime(task.createdAt),
    group: task.status === 'FAILED' ? '失败' : '任务'
  }));
  return keyword ? taskRows.filter((row) => row.title.toLowerCase().includes(keyword)) : taskRows;
});

const groupedHistory = computed(() => {
  const groups: Array<{ key: string; rows: typeof historyRows.value }> = [];
  for (const row of historyRows.value) {
    const group = groups.find((item) => item.key === row.group);
    if (group) {
      group.rows.push(row);
    } else {
      groups.push({ key: row.group, rows: [row] });
    }
  }
  return groups;
});

const previewCards = computed<PreviewCard[]>(() => {
  const successfulTasks = workbench.value.tasks
    .filter((task) => task.status === 'SUCCESS' && task.resultUrl)
    .slice(0, 2)
    .map((task, index) => ({
      id: task.id,
      title: compact(task.prompt, 18),
      label: `方案 ${String.fromCharCode(65 + index)}`,
      url: task.resultUrl,
      accent: index % 2 === 0 ? 'city' : 'moon',
      featured: index === 0
    }));
  return successfulTasks;
});

const queueRows = computed(() => {
  const taskRows = workbench.value.tasks.slice(0, 4).map((task, index) => ({
    id: task.id,
    title: `图像生成 #${1024 - index}`,
    subtitle: compact(task.prompt, 10),
    status: statusMeta(task.status).label,
    tone: statusMeta(task.status).tone,
    time: task.status === 'PENDING' ? '刚刚' : formatTime(task.createdAt),
    progress: statusMeta(task.status).progress,
    errorMessage: task.errorMessage
  }));
  return taskRows;
});

const recentRuns = computed(() =>
  historyRows.value.slice(3, 8).map((row, index) => ({
    ...row,
    icon: index % 3 === 0 ? 'MessageCircle' : index % 3 === 1 ? 'Image' : 'Headphones'
  }))
);
const latestImageResult = computed(() =>
  workbench.value.tasks.find((task) => task.status === 'SUCCESS' && task.resultUrl) ?? null
);
const callableCapabilities = computed(() => capabilities.value.filter((capability) => capability.callable));
const selectedCapability = computed(
  () =>
    callableCapabilities.value.find((capability) => capability.targetKey === selectedCapabilityKey.value) ??
    callableCapabilities.value[0] ??
    null
);
const hasActiveTasks = computed(() => workbench.value.tasks.some(isActiveTask));

watch(
  draft,
  (value) => saveWorkbenchDraft(DRAFT_KEY, value),
  { deep: true }
);

onMounted(async () => {
  await Promise.all([loadWorkbench(), loadCapabilities()]);
  startTaskPolling();
});

onBeforeUnmount(stopTaskPolling);

watch(hasActiveTasks, (active) => {
  if (active) {
    startTaskPolling();
  } else {
    stopTaskPolling();
  }
});

async function loadWorkbench(silent = false) {
  try {
    workbench.value = await fetchImageWorkbench(SURFACE);
    if (!silent) {
      createError.value = '';
    }
  } catch (error) {
    if (!silent) {
      createError.value = error instanceof Error ? error.message : '图像任务加载失败';
    }
  }
}

async function loadCapabilities(silent = false) {
  try {
    const payload = await fetchWorkbenchCapabilities(SURFACE);
    capabilities.value = payload.groups.image ?? [];
    if (!selectedCapabilityKey.value && callableCapabilities.value[0]) {
      selectedCapabilityKey.value = callableCapabilities.value[0].targetKey;
    }
  } catch (error) {
    capabilities.value = [];
    if (!silent) {
      createError.value = error instanceof Error ? error.message : '图像能力加载失败';
    }
  }
}

async function createFromPrompt() {
  const prompt = draft.value.prompt.trim();
  if (!prompt) {
    createError.value = '请输入图像提示词';
    return;
  }
  const capability = selectedCapability.value;
  if (!capability) {
    createError.value = '后台未启用可调用的图像能力';
    return;
  }
  isCreating.value = true;
  createError.value = '';
  try {
    const enrichedPrompt = `${prompt}；模型：${draft.value.model}；尺寸：${draft.value.size}；比例：${draft.value.ratio}；风格：${draft.value.style}`;
    const created = await createImageGeneration(enrichedPrompt, {
      targetType: capability.targetType,
      targetId: capability.targetKey,
      routeKey: capability.modelConfig?.modelKey ?? capability.actionValue ?? workbench.value.route.routeKey,
      surface: SURFACE,
      options: imageGenerationOptions()
    });
    const refreshed = await fetchImageWorkbench(SURFACE);
    if (!refreshed.tasks.some((task) => task.id === created.id)) {
      refreshed.tasks = [created, ...refreshed.tasks];
    }
    workbench.value = refreshed;
    activeHistoryId.value = created.id;
    startTaskPolling();
  } catch (error) {
    createError.value = error instanceof Error ? error.message : '图像任务创建失败';
  } finally {
    isCreating.value = false;
  }
}

function imageGenerationOptions() {
  return {
    size: draft.value.size.replace(/\s*x\s*/i, 'x'),
    quality: draft.value.quality.includes('高') ? 'high' : 'standard',
    n: Number.parseInt(draft.value.count, 10) || 1,
    ratio: draft.value.ratio,
    style: draft.value.style,
    seed: draft.value.seed.trim() || undefined
  };
}

function resetImageDraft() {
  draft.value.prompt = '';
  activeHistoryId.value = '';
  createError.value = '';
}

function startTaskPolling() {
  if (!hasActiveTasks.value || pollTimer.value !== null || typeof window === 'undefined') {
    return;
  }
  pollTimer.value = window.setInterval(() => {
    void loadWorkbench(true).then(() => {
      if (!hasActiveTasks.value) {
        stopTaskPolling();
      }
    });
  }, 3000);
}

function stopTaskPolling() {
  if (pollTimer.value !== null && typeof window !== 'undefined') {
    window.clearInterval(pollTimer.value);
  }
  pollTimer.value = null;
}

function isActiveTask(task: ImageTask): boolean {
  return task.status === 'PENDING' || task.status === 'PROCESSING';
}

function statusMeta(status: string) {
  return getImageStatusMeta(status);
}

function formatTime(value?: string | null) {
  if (!value) {
    return '刚刚';
  }
  return value.replace('T', ' ').slice(11, 16) || value.slice(0, 10);
}

function compact(value: string, max = 18) {
  return value.length > max ? `${value.slice(0, max)}...` : value;
}
</script>

<template>
  <WorkspaceShell
    active-module-key="image"
    page-title="AI 图像工作台"
    page-subtitle="模型、尺寸、历史、预览和队列在同一处完成"
    page-icon="Sparkles"
    variant="image"
  >
    <template #leftFooter>
      <div class="wb-left-selects">
        <label>
          <span>能力：</span>
          <select v-model="selectedCapabilityKey" :disabled="!callableCapabilities.length">
            <option v-for="capability in callableCapabilities" :key="capability.targetKey" :value="capability.targetKey">
              {{ capability.title }}
            </option>
          </select>
        </label>
        <label>
          <span>模型：</span>
          <strong class="wb-managed-model">{{ selectedCapability?.modelConfig?.displayName ?? '后台未启用' }}</strong>
        </label>
      </div>
    </template>

    <template #main>
      <section class="wb-image">
        <section class="wb-image-config">
          <label>
            <span>模型</span>
            <select v-model="draft.model">
              <option v-for="model in modelOptions" :key="model">{{ model }}</option>
            </select>
          </label>
          <label>
            <span>尺寸</span>
            <select v-model="draft.size">
              <option v-for="size in sizeOptions" :key="size">{{ size }}</option>
            </select>
          </label>
          <div class="wb-ratio-group" role="group" aria-label="图像比例">
            <span>比例</span>
            <button
              v-for="ratio in ratioOptions"
              :key="ratio"
              :class="{ active: draft.ratio === ratio }"
              type="button"
              @click="draft.ratio = ratio"
            >
              {{ ratio }}
            </button>
          </div>
          <div class="wb-style-group" role="group" aria-label="图像风格">
            <span>风格</span>
            <button
              v-for="style in styleOptions"
              :key="style"
              :class="{ active: draft.style === style }"
              type="button"
              @click="draft.style = style"
            >
              {{ style }}
            </button>
          </div>
        </section>

        <div class="wb-image-body">
          <aside class="wb-history-panel">
            <header>
              <h2>历史记录</h2>
              <label class="wb-search">
                <Search :size="18" />
                <input v-model="historyQuery" placeholder="搜索提示词..." />
              </label>
            </header>
            <div v-for="group in groupedHistory" :key="group.key" class="wb-history-group">
              <h3>{{ group.key }}</h3>
              <button
                v-for="row in group.rows"
                :key="row.id"
                :class="{ active: activeHistoryId === row.id }"
                type="button"
                @click="activeHistoryId = row.id"
              >
                <i></i>
                <span>{{ row.title }}</span>
                <time>{{ row.time }}</time>
              </button>
            </div>
            <button class="wb-link-button" type="button" @click="historyQuery = ''">
              查看全部记录
              <List :size="16" />
            </button>
          </aside>

          <section class="wb-preview-panel">
            <header>
              <h2>生成预览</h2>
            </header>
            <div v-if="previewCards.length" class="wb-preview-grid">
              <article
                v-for="card in previewCards"
                :key="card.id"
                :class="['wb-preview-card', card.accent, { featured: card.featured }]"
              >
                <img :src="card.url || ''" :alt="card.title" />
                <footer>
                  <strong>{{ card.label }}</strong>
                  <a class="wb-card-action" :href="card.url || '#'" download aria-label="下载">
                    <Download :size="18" />
                  </a>
                  <a class="wb-card-action" :href="card.url || '#'" target="_blank" rel="noreferrer" aria-label="打开">
                    <Expand :size="18" />
                  </a>
                </footer>
              </article>
            </div>
            <div v-else class="wb-empty-state">
              <ImageIcon :size="34" />
              <strong>还没有完成的图像</strong>
              <span>提交任务后，成功结果会在这里显示真实图片。</span>
            </div>
          </section>
        </div>

        <section class="wb-prompt-composer">
          <label>
            <span>提示词</span>
            <textarea v-model="draft.prompt" maxlength="1000" placeholder="描述你想生成的画面、光线、材质与风格..." />
            <small>{{ draft.prompt.length }} / 1000</small>
          </label>
          <button class="wb-generate-button" :disabled="isCreating || !selectedCapability" type="button" @click="createFromPrompt">
            <Sparkles :size="24" />
            {{ isCreating ? '生成中' : '生成图像' }}
          </button>
          <p v-if="createError" class="wb-error">{{ createError }}</p>
        </section>
      </section>
    </template>

    <template #side>
      <section class="wb-side-panel">
        <header>
          <h2>任务队列</h2>
          <button type="button">查看全部</button>
        </header>
        <article v-for="task in queueRows" :key="task.id" class="wb-task-row">
          <span :class="['wb-task-icon', task.tone]"><ImageIcon :size="20" /></span>
          <div>
            <strong>{{ task.title }}</strong>
            <small>{{ task.subtitle }}</small>
            <small v-if="task.errorMessage" class="wb-task-error">{{ task.errorMessage }}</small>
            <div v-if="task.progress < 100" class="wb-progress">
              <i :style="{ width: `${task.progress}%` }"></i>
            </div>
          </div>
          <em :class="task.tone">{{ task.status }}</em>
          <time>{{ task.time }}</time>
        </article>
      </section>

      <section class="wb-side-panel">
        <header>
          <h2>最近运行</h2>
          <button type="button">查看全部</button>
        </header>
        <article v-for="run in recentRuns" :key="run.id" class="wb-run-row">
          <span><ImageIcon :size="18" /></span>
          <div>
            <strong>{{ run.title }}</strong>
            <small>{{ run.time }}</small>
          </div>
        </article>
      </section>

      <section class="wb-side-panel">
        <header>
          <h2>快捷操作</h2>
        </header>
        <div class="wb-quick-grid">
          <button type="button" @click="resetImageDraft"><Sparkles :size="24" />新建图像</button>
          <a v-if="latestImageResult" :href="latestImageResult.resultUrl || '#'" download>
            <Download :size="24" />
            下载结果
          </a>
          <button v-else type="button" disabled><Download :size="24" />下载结果</button>
        </div>
      </section>

      <section class="wb-side-panel wb-settings-panel">
        <header>
          <h2>设置</h2>
        </header>
        <label><span>自动保存任务</span><input v-model="draft.autoSave" type="checkbox" /></label>
        <label><span>代码块语法高亮</span><input v-model="draft.codeHighlight" type="checkbox" /></label>
        <label><span>流式输出</span><input v-model="draft.streaming" type="checkbox" /></label>
        <label>
          <span>图片质量</span>
          <select v-model="draft.quality">
            <option>高（推荐）</option>
            <option>标准</option>
          </select>
        </label>
        <label>
          <span>每次生成数量</span>
          <select v-model="draft.count">
            <option>1 张</option>
            <option>2 张</option>
            <option>4 张</option>
          </select>
        </label>
        <label>
          <span>随机种子（可选）</span>
          <input v-model="draft.seed" placeholder="请输入种子值" />
        </label>
      </section>
    </template>
  </WorkspaceShell>
</template>

<style scoped>
.wb-left-selects,
.wb-left-selects label,
.wb-image,
.wb-image-config,
.wb-history-panel,
.wb-preview-panel,
.wb-prompt-composer,
.wb-side-panel {
  min-width: 0;
}

.wb-left-selects {
  display: grid;
  gap: 12px;
}

.wb-left-selects label {
  min-height: 56px;
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 8px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 0 14px;
  background: #fff;
}

.wb-left-selects span {
  color: #1f2937;
  font-weight: 800;
}

.wb-left-selects select,
.wb-image-config select,
.wb-settings-panel select,
.wb-settings-panel input:not([type='checkbox']) {
  width: 100%;
  height: 40px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 0 12px;
  color: #172033;
  background: #fff;
  font: inherit;
}

.wb-managed-model {
  overflow: hidden;
  color: #172033;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-image {
  display: grid;
  gap: 18px;
}

.wb-image-config,
.wb-history-panel,
.wb-preview-panel,
.wb-prompt-composer,
.wb-side-panel {
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 24px rgba(38, 50, 84, 0.04);
}

.wb-image-config {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(180px, 1fr) minmax(360px, 1.7fr);
  gap: 18px 24px;
  padding: 20px 22px;
}

.wb-image-config label,
.wb-ratio-group,
.wb-style-group {
  display: grid;
  gap: 10px;
}

.wb-image-config span,
.wb-prompt-composer span {
  color: #5c667a;
  font-weight: 800;
}

.wb-style-group {
  grid-column: 1 / -1;
}

.wb-ratio-group,
.wb-style-group {
  grid-template-columns: repeat(8, max-content);
  align-items: end;
  gap: 10px 14px;
}

.wb-ratio-group > span,
.wb-style-group > span {
  grid-column: 1 / -1;
}

.wb-ratio-group button,
.wb-style-group button,
.wb-link-button,
.wb-task-row button,
.wb-quick-grid button,
.wb-quick-grid a,
.wb-side-panel header button {
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  color: #273044;
  background: #fff;
  font: inherit;
}

.wb-ratio-group button,
.wb-style-group button {
  min-width: 72px;
  min-height: 42px;
  padding: 0 16px;
}

.wb-ratio-group button.active,
.wb-style-group button.active {
  border-color: #5964ff;
  color: #4f5cff;
  background: #f4f5ff;
}

.wb-image-body {
  display: grid;
  grid-template-columns: 290px minmax(0, 1fr);
  gap: 18px;
}

.wb-history-panel,
.wb-preview-panel,
.wb-side-panel {
  padding: 18px;
}

.wb-history-panel h2,
.wb-preview-panel h2,
.wb-side-panel h2 {
  margin: 0;
  color: #111827;
  font-size: 20px;
  line-height: 1.2;
}

.wb-history-panel header,
.wb-preview-panel header,
.wb-side-panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.wb-search {
  height: 42px;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 0 12px;
  color: #7a8496;
}

.wb-search input {
  width: 100%;
  border: 0;
  outline: none;
  color: #172033;
  background: transparent;
}

.wb-history-group {
  display: grid;
  gap: 8px;
  border-bottom: 1px solid #edf1f7;
  padding: 8px 0 14px;
}

.wb-history-group h3 {
  margin: 0 0 4px;
  color: #7a8496;
  font-size: 14px;
  font-weight: 800;
}

.wb-history-group button {
  min-height: 42px;
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0 10px;
  color: #2b3448;
  background: transparent;
  text-align: left;
}

.wb-history-group button.active {
  border-color: #5d68ff;
  background: #f7f8ff;
}

.wb-history-group i {
  width: 10px;
  height: 10px;
  border: 1px solid #a8b0c0;
  border-radius: 50%;
}

.wb-history-group button.active i {
  border-color: #5d68ff;
  background: #5d68ff;
}

.wb-history-group span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-history-group time {
  color: #98a1b3;
}

.wb-link-button {
  width: 100%;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 14px;
  color: #6b7280;
}

.wb-preview-grid {
  display: grid;
  grid-template-columns: minmax(280px, 1.35fr) repeat(2, minmax(150px, 0.65fr));
  gap: 16px;
}

.wb-empty-state {
  min-height: 320px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  color: #64748b;
  text-align: center;
}

.wb-empty-state strong {
  color: #172033;
  font-size: 18px;
}

.wb-preview-card {
  min-height: 218px;
  display: grid;
  grid-template-rows: minmax(0, 1fr) 50px;
  overflow: hidden;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: #fff;
}

.wb-preview-card.featured {
  grid-row: span 2;
  min-height: 500px;
}

.wb-preview-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.wb-preview-card footer {
  display: grid;
  grid-template-columns: 1fr repeat(2, 34px);
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  color: #6b7280;
}

.wb-card-action {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 8px;
  color: #5f6778;
  background: transparent;
}

.wb-prompt-composer {
  position: sticky;
  bottom: 0;
  z-index: 2;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 18px;
  padding: 18px;
}

.wb-prompt-composer label {
  position: relative;
  display: grid;
  gap: 8px;
}

.wb-prompt-composer textarea {
  min-height: 122px;
  resize: vertical;
  border: 1px solid #cdd4ff;
  border-radius: 8px;
  padding: 16px;
  outline: none;
  color: #172033;
  font: inherit;
}

.wb-prompt-composer small {
  position: absolute;
  left: 16px;
  bottom: 12px;
  color: #9aa3b4;
}

.wb-generate-button {
  align-self: end;
  min-height: 100px;
  display: grid;
  place-items: center;
  gap: 8px;
  border: 0;
  border-radius: 8px;
  color: #fff;
  background: linear-gradient(135deg, #5264ff, #7a3ff2);
  font-size: 20px;
  font-weight: 900;
}

.wb-generate-button:disabled {
  opacity: 0.68;
}

.wb-error {
  grid-column: 1 / -1;
  margin: 0;
  color: #d92d20;
  font-weight: 800;
}

.wb-side-panel header button {
  border: 0;
  color: #4f5cff;
  background: transparent;
  font-weight: 800;
}

.wb-task-row,
.wb-run-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  border: 1px solid #edf1f7;
  border-radius: 8px;
  padding: 12px;
}

.wb-task-row + .wb-task-row,
.wb-run-row + .wb-run-row {
  margin-top: 10px;
}

.wb-task-icon,
.wb-run-row > span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #5264ff;
  background: #f1f3ff;
}

.wb-task-icon.success {
  color: #0c9f61;
  background: #eaf8f1;
}

.wb-task-icon.pending {
  color: #f08a00;
  background: #fff5e5;
}

.wb-task-row strong,
.wb-run-row strong {
  display: block;
  overflow: hidden;
  color: #172033;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-task-row small,
.wb-run-row small,
.wb-task-row time {
  color: #8791a3;
}

.wb-task-error {
  color: #d92d20 !important;
}

.wb-task-row em {
  grid-column: 3;
  border-radius: 8px;
  padding: 5px 10px;
  font-style: normal;
  font-weight: 800;
}

.wb-task-row em.processing {
  color: #3567ff;
  background: #eef3ff;
}

.wb-task-row em.pending {
  color: #f08a00;
  background: #fff5e5;
}

.wb-task-row em.success {
  color: #0c9f61;
  background: #eaf8f1;
}

.wb-task-row time {
  grid-column: 3;
  justify-self: end;
}

.wb-progress {
  height: 5px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf1f7;
}

.wb-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #5264ff;
}

.wb-quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.wb-quick-grid button,
.wb-quick-grid a {
  min-height: 92px;
  display: grid;
  place-items: center;
  gap: 8px;
  color: #5264ff;
  text-decoration: none;
}

.wb-quick-grid button:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.wb-settings-panel {
  display: grid;
  gap: 14px;
}

.wb-settings-panel label {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px;
  align-items: center;
  gap: 12px;
  color: #5c667a;
}

.wb-settings-panel input[type='checkbox'] {
  justify-self: end;
  width: 46px;
  height: 26px;
  accent-color: #5264ff;
}

@media (max-width: 1180px) {
  .wb-image-config,
  .wb-image-body,
  .wb-prompt-composer {
    grid-template-columns: 1fr;
  }

  .wb-preview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .wb-preview-card.featured {
    min-height: 340px;
  }
}
</style>

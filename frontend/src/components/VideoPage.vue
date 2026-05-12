<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  Clapperboard,
  Download,
  Sparkles,
  Video
} from 'lucide-vue-next';
import { createVideoGeneration, fetchVideoWorkbench, fetchWorkbenchCapabilities } from '../services/api';
import {
  getVideoStatusMeta,
  loadWorkbenchDraft,
  saveWorkbenchDraft,
  type VideoTask,
  type VideoWorkbench,
  type WorkbenchCapability
} from '../services/viewModel';
import WorkspaceShell from './WorkspaceShell.vue';

interface VideoDraft {
  prompt: string;
  duration: string;
  ratio: string;
  resolution: string;
  frameRate: string;
  format: string;
  bitrate: string;
  watermark: boolean;
}

const SURFACE = 'workbench';
const DRAFT_KEY = 'opc_workbench_video_draft';

const emptyVideoWorkbench: VideoWorkbench = {
  tenantId: '',
  userId: '',
  surface: SURFACE,
  wallet: { balance: 0, frozenBalance: 0 },
  route: { routeKey: '', unitCost: 0 },
  tasks: []
};

const defaultDraft: VideoDraft = {
  prompt: '',
  duration: '10s',
  ratio: '16:9',
  resolution: '1080p',
  frameRate: '30',
  format: 'MP4',
  bitrate: '推荐（10Mbps）',
  watermark: false
};

const workbench = ref<VideoWorkbench>(emptyVideoWorkbench);
const draft = ref<VideoDraft>(loadWorkbenchDraft(DRAFT_KEY, defaultDraft));
const capabilities = ref<WorkbenchCapability[]>([]);
const selectedCapabilityKey = ref('');
const isCreating = ref(false);
const createError = ref('');
const pollTimer = ref<number | null>(null);

const durationOptions = ['10s', '15s', '30s', '45s', '60s'];
const ratioOptions = ['16:9', '9:16', '1:1', '21:9'];
const resolutionOptions = ['720p', '1080p', '2K', '4K'];
const frameRateOptions = ['24', '30', '60'];

const queueRows = computed(() => {
  const taskRows = workbench.value.tasks.slice(0, 4).map((task, index) => ({
    id: task.id,
    title: `视频生成 #${2048 - index}`,
    subtitle: statusMeta(task.status).tone === 'processing' ? `生成中 ${statusMeta(task.status).progress}%` : compact(task.prompt, 12),
    status: statusMeta(task.status).label,
    tone: statusMeta(task.status).tone,
    time: task.status === 'PROCESSING' ? '剩余 00:32' : formatDate(task.createdAt),
    progress: statusMeta(task.status).progress,
    errorMessage: task.errorMessage
  }));
  return taskRows;
});

const recentRuns = computed(() => {
  const taskRows = workbench.value.tasks.slice(0, 5).map((task, index) => ({
    id: task.id,
    title: `${task.routeKey === 'video_text_to_video' ? '视频生成' : task.routeKey} #${2045 - index}`,
    date: formatDate(task.createdAt)
  }));
  return taskRows;
});

const latestVideoResult = computed(() =>
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
    workbench.value = await fetchVideoWorkbench(SURFACE);
    if (!silent) {
      createError.value = '';
    }
  } catch (error) {
    if (!silent) {
      createError.value = error instanceof Error ? error.message : '视频任务加载失败';
    }
  }
}

async function loadCapabilities(silent = false) {
  try {
    const payload = await fetchWorkbenchCapabilities(SURFACE);
    capabilities.value = payload.groups.video ?? [];
    if (!selectedCapabilityKey.value && callableCapabilities.value[0]) {
      selectedCapabilityKey.value = callableCapabilities.value[0].targetKey;
    }
  } catch (error) {
    capabilities.value = [];
    if (!silent) {
      createError.value = error instanceof Error ? error.message : '视频能力加载失败';
    }
  }
}

async function createFromPrompt() {
  const prompt = draft.value.prompt.trim();
  if (!prompt) {
    createError.value = '请输入视频脚本或提示词';
    return;
  }
  const capability = selectedCapability.value;
  if (!capability) {
    createError.value = '后台未启用可调用的视频能力';
    return;
  }
  isCreating.value = true;
  createError.value = '';
  try {
    const enrichedPrompt = `${prompt}；时长：${draft.value.duration}；比例：${draft.value.ratio}；分辨率：${draft.value.resolution}；帧率：${draft.value.frameRate}`;
    const created = await createVideoGeneration(enrichedPrompt, {
      targetType: capability.targetType,
      targetId: capability.targetKey,
      routeKey: capability.modelConfig?.modelKey ?? capability.actionValue ?? workbench.value.route.routeKey,
      surface: SURFACE,
      options: videoGenerationOptions()
    });
    const refreshed = await fetchVideoWorkbench(SURFACE);
    if (!refreshed.tasks.some((task) => task.id === created.id)) {
      refreshed.tasks = [created, ...refreshed.tasks];
    }
    workbench.value = refreshed;
    startTaskPolling();
  } catch (error) {
    createError.value = error instanceof Error ? error.message : '视频任务创建失败';
  } finally {
    isCreating.value = false;
  }
}

function videoGenerationOptions() {
  return {
    seconds: Number.parseInt(draft.value.duration, 10) || 10,
    ratio: draft.value.ratio,
    size: resolutionToSize(draft.value.resolution, draft.value.ratio),
    frame_rate: Number.parseInt(draft.value.frameRate, 10) || 30,
    format: draft.value.format.toLowerCase(),
    bitrate: draft.value.bitrate,
    watermark: draft.value.watermark
  };
}

function resolutionToSize(resolution: string, ratio: string): string {
  const landscapeSizes: Record<string, string> = {
    '720p': '1280x720',
    '1080p': '1920x1080',
    '2K': '2560x1440',
    '4K': '3840x2160'
  };
  const portraitSizes: Record<string, string> = {
    '720p': '720x1280',
    '1080p': '1080x1920',
    '2K': '1440x2560',
    '4K': '2160x3840'
  };
  const squareSizes: Record<string, string> = {
    '720p': '1024x1024',
    '1080p': '1080x1080',
    '2K': '2048x2048',
    '4K': '4096x4096'
  };
  if (ratio === '9:16') {
    return portraitSizes[resolution] ?? '1080x1920';
  }
  if (ratio === '1:1') {
    return squareSizes[resolution] ?? '1080x1080';
  }
  return landscapeSizes[resolution] ?? '1920x1080';
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

function isActiveTask(task: VideoTask): boolean {
  return task.status === 'PENDING' || task.status === 'PROCESSING';
}

function statusMeta(status: string) {
  return getVideoStatusMeta(status);
}

function formatDate(value?: string | null) {
  if (!value) {
    return '刚刚';
  }
  return value.replace('T', ' ').slice(0, 16);
}

function compact(value: string, max = 18) {
  return value.length > max ? `${value.slice(0, max)}...` : value;
}
</script>

<template>
  <WorkspaceShell
    active-module-key="video"
    page-title="视频生成工作台"
    page-subtitle="脚本、故事板、预览、时间线和导出集中处理"
    page-icon="FileVideo"
    variant="video"
  >
    <template #leftFooter>
      <div class="video-left-selects">
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
          <strong class="video-managed-model">{{ selectedCapability?.modelConfig?.displayName ?? '后台未启用' }}</strong>
        </label>
      </div>
    </template>

    <template #main>
      <section class="wb-video">
        <section class="video-composer-grid">
          <article class="video-script-panel">
            <h2>脚本 / 提示词</h2>
            <label>
              <textarea v-model="draft.prompt" maxlength="5000" placeholder="请输入视频脚本或提示词..." />
              <small>{{ draft.prompt.length }} / 5000</small>
            </label>
          </article>

          <article class="video-config-panel">
            <label>
              <span>时长</span>
              <select v-model="draft.duration">
                <option v-for="duration in durationOptions" :key="duration">{{ duration }}</option>
              </select>
            </label>
            <div class="video-ratio-row" role="group" aria-label="画面比例">
              <span>画面比例</span>
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
            <label>
              <span>分辨率</span>
              <select v-model="draft.resolution">
                <option v-for="resolution in resolutionOptions" :key="resolution">{{ resolution }}</option>
              </select>
            </label>
            <label>
              <span>帧率</span>
              <select v-model="draft.frameRate">
                <option v-for="rate in frameRateOptions" :key="rate">{{ rate }}</option>
              </select>
            </label>
            <button class="video-generate-preview" :disabled="isCreating || !selectedCapability" type="button" @click="createFromPrompt">
              <Sparkles :size="22" />
              {{ isCreating ? '生成中' : '生成视频' }}
            </button>
            <p v-if="createError" class="video-error">{{ createError }}</p>
          </article>
        </section>

        <section class="video-player-panel">
          <header>
            <h2>生成结果</h2>
          </header>
          <div v-if="latestVideoResult" class="video-preview-frame">
            <video class="video-result-player" :src="latestVideoResult.resultUrl || ''" controls />
          </div>
          <div v-else class="video-empty-result">
            <Video :size="34" />
            <strong>还没有完成的视频</strong>
            <span>提交任务后，真实供应商返回的视频会在这里播放。</span>
          </div>
        </section>
      </section>
    </template>

    <template #side>
      <section class="video-side-panel">
        <header>
          <h2>任务队列</h2>
          <button type="button" @click="loadWorkbench(true)">刷新</button>
        </header>
        <article v-for="task in queueRows" :key="task.id" class="video-task-row">
          <span :class="task.tone"><Clapperboard :size="20" /></span>
          <div>
            <strong>{{ task.title }}</strong>
            <small>{{ task.subtitle }}</small>
            <small v-if="task.errorMessage" class="video-task-error">{{ task.errorMessage }}</small>
            <div v-if="task.progress > 0 && task.progress < 100" class="video-progress">
              <i :style="{ width: `${task.progress}%` }"></i>
            </div>
          </div>
          <em :class="task.tone">{{ task.status }}</em>
          <time>{{ task.time }}</time>
        </article>
      </section>

      <section class="video-side-panel">
        <header>
          <h2>最近运行</h2>
          <button type="button" @click="loadWorkbench(true)">刷新</button>
        </header>
        <article v-for="run in recentRuns" :key="run.id" class="video-run-row">
          <span><Video :size="18" /></span>
          <div>
            <strong>{{ run.title }}</strong>
            <small>{{ run.date }}</small>
          </div>
        </article>
      </section>

      <section class="video-side-panel video-export-panel">
        <header><h2>导出</h2></header>
        <label>
          <span>格式</span>
          <select v-model="draft.format">
            <option>MP4</option>
            <option>MOV</option>
            <option>WebM</option>
          </select>
        </label>
        <label>
          <span>码率</span>
          <select v-model="draft.bitrate">
            <option>推荐（10Mbps）</option>
            <option>高（20Mbps）</option>
          </select>
        </label>
        <label class="video-watermark">
          <span>水印</span>
          <input v-model="draft.watermark" type="checkbox" />
        </label>
        <a v-if="latestVideoResult" class="video-export-button" :href="latestVideoResult.resultUrl || '#'" download>
          <Download :size="22" />
          下载视频
        </a>
        <button v-else class="video-export-button" type="button" disabled><Download :size="22" />下载视频</button>
      </section>
    </template>
  </WorkspaceShell>
</template>

<style scoped>
.video-left-selects label,
.video-composer-grid,
.video-script-panel,
.video-config-panel,
.video-player-panel,
.video-side-panel {
  min-width: 0;
}

.video-left-selects {
  display: grid;
  gap: 12px;
}

.video-left-selects label {
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

.video-left-selects select,
.video-config-panel select,
.video-export-panel select {
  width: 100%;
  height: 42px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 0 12px;
  color: #172033;
  background: #fff;
  font: inherit;
}

.video-managed-model {
  overflow: hidden;
  color: #172033;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-video {
  display: grid;
  gap: 18px;
}

.video-composer-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.95fr);
  gap: 18px;
}

.video-script-panel,
.video-config-panel,
.video-player-panel,
.video-side-panel {
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 24px rgba(38, 50, 84, 0.04);
}

.video-script-panel,
.video-config-panel,
.video-player-panel,
.video-side-panel {
  padding: 18px;
}

.video-script-panel h2,
.video-player-panel h2,
.video-side-panel h2 {
  margin: 0;
  color: #111827;
  font-size: 20px;
  line-height: 1.2;
}

.video-script-panel {
  display: grid;
  gap: 14px;
}

.video-script-panel label {
  position: relative;
  display: block;
}

.video-script-panel textarea {
  width: 100%;
  min-height: 220px;
  resize: vertical;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 18px;
  color: #172033;
  outline: none;
  font: inherit;
}

.video-script-panel small {
  position: absolute;
  right: 18px;
  bottom: 14px;
  color: #8791a3;
}

.video-config-panel {
  display: grid;
  gap: 16px;
}

.video-config-panel label,
.video-ratio-row {
  display: grid;
  grid-template-columns: 94px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.video-config-panel span,
.video-export-panel span {
  color: #273044;
  font-weight: 800;
}

.video-ratio-row {
  grid-template-columns: 94px repeat(4, max-content);
}

.video-ratio-row button {
  min-width: 58px;
  height: 42px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  color: #172033;
  background: #fff;
  font: inherit;
}

.video-ratio-row button.active {
  border-color: #5964ff;
  color: #4f5cff;
  background: #f4f5ff;
}

.video-generate-preview,
.video-export-button {
  min-height: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 8px;
  font: inherit;
  font-weight: 900;
}

.video-generate-preview,
.video-export-button {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #5264ff, #7a3ff2);
}

.video-generate-preview:disabled,
.video-export-button:disabled {
  opacity: 0.68;
}

.video-error {
  margin: 0;
  color: #d92d20;
  font-weight: 800;
}

.video-player-panel header,
.video-side-panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.video-side-panel header button {
  min-height: 38px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 0 12px;
  color: #4f5cff;
  background: #fff;
  font: inherit;
  font-weight: 800;
}

.video-player-panel {
  display: grid;
  gap: 12px;
}

.video-preview-frame {
  overflow: hidden;
  border-radius: 8px;
  background: #111827;
}

.video-result-player {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #111827;
}

.video-empty-result {
  min-height: 260px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  color: #667085;
  text-align: center;
}

.video-empty-result strong {
  color: #172033;
  font-size: 18px;
}

.video-side-panel + .video-side-panel {
  margin-top: 0;
}

.video-task-row,
.video-run-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  border: 1px solid #edf1f7;
  border-radius: 8px;
  padding: 12px;
}

.video-task-row + .video-task-row,
.video-run-row + .video-run-row {
  margin-top: 10px;
}

.video-task-row > span,
.video-run-row > span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #5264ff;
  background: #f1f3ff;
}

.video-task-row > span.success {
  color: #0c9f61;
  background: #eaf8f1;
}

.video-task-row > span.pending {
  color: #f08a00;
  background: #fff5e5;
}

.video-task-row strong,
.video-run-row strong {
  display: block;
  overflow: hidden;
  color: #172033;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-task-row small,
.video-run-row small,
.video-task-row time {
  color: #8791a3;
}

.video-task-error {
  color: #d92d20 !important;
}

.video-task-row em {
  grid-column: 3;
  border-radius: 8px;
  padding: 5px 10px;
  font-style: normal;
  font-weight: 800;
}

.video-task-row em.processing {
  color: #3567ff;
  background: #eef3ff;
}

.video-task-row em.pending {
  color: #f08a00;
  background: #fff5e5;
}

.video-task-row em.success {
  color: #0c9f61;
  background: #eaf8f1;
}

.video-task-row time {
  grid-column: 3;
  justify-self: end;
}

.video-progress {
  height: 5px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf1f7;
}

.video-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #5264ff;
}

.video-export-panel {
  display: grid;
  gap: 16px;
}

.video-export-panel label {
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.video-watermark input {
  justify-self: end;
  width: 46px;
  height: 26px;
  accent-color: #5264ff;
}

.video-export-button {
  width: 100%;
  text-decoration: none;
}

@media (max-width: 1180px) {
  .video-composer-grid {
    grid-template-columns: 1fr;
  }
}
</style>

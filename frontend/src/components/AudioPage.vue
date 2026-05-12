<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  Download,
  Link,
  Music,
  Trash2,
  UploadCloud,
  Waves
} from 'lucide-vue-next';
import { createAudioTask, fetchAudioTasks, fetchWorkbenchCapabilities, uploadAudio } from '../services/api';
import {
  buildAudioTaskPayload,
  loadWorkbenchDraft,
  saveWorkbenchDraft,
  type AudioTask,
  type PortalItem,
  type WorkbenchCapability
} from '../services/viewModel';
import WorkspaceShell from './WorkspaceShell.vue';

interface AudioDraft {
  prompt: string;
  mode: string;
  duration: number;
  speed: number;
  mood: string;
  style: string;
  exportFormat: string;
  sampleRate: string;
  autoSave: boolean;
  notify: boolean;
  streaming: boolean;
  themeMode: string;
}

const SURFACE = 'workbench';
const DRAFT_KEY = 'opc_workbench_audio_draft';

const defaultDraft: AudioDraft = {
  prompt: '',
  mode: '旁白',
  duration: 60,
  speed: 1,
  mood: '平静',
  style: '自然',
  exportFormat: 'WAV',
  sampleRate: '44.1k Hz',
  autoSave: true,
  notify: true,
  streaming: true,
  themeMode: '跟随系统'
};

const providerVoiceOptions = [
  { label: 'Alloy', value: 'alloy' },
  { label: 'Ash', value: 'ash' },
  { label: 'Ballad', value: 'ballad' },
  { label: 'Coral', value: 'coral' },
  { label: 'Echo', value: 'echo' },
  { label: 'Fable', value: 'fable' },
  { label: 'Nova', value: 'nova' },
  { label: 'Onyx', value: 'onyx' },
  { label: 'Sage', value: 'sage' },
  { label: 'Shimmer', value: 'shimmer' }
];

const draft = ref<AudioDraft>(loadWorkbenchDraft(DRAFT_KEY, defaultDraft));
const capabilities = ref<WorkbenchCapability[]>([]);
const selectedTool = ref<PortalItem | null>(null);
const selectedVoiceKey = ref(providerVoiceOptions[0].value);
const sourceUrl = ref('');
const tasks = ref<AudioTask[]>([]);
const isSubmitting = ref(false);
const isLoadingTasks = ref(false);
const notice = ref('');
const pollTimer = ref<number | null>(null);

const managedAudioTools = computed<PortalItem[]>(() =>
  capabilities.value.filter((capability) => capability.callable).map(capabilityToPortalItem)
);
const audioTools = computed(() => managedAudioTools.value);
const selectedVoiceLabel = computed(
  () => providerVoiceOptions.find((voice) => voice.value === selectedVoiceKey.value)?.label ?? selectedVoiceKey.value
);

const modeOptions = ['旁白', '播客', '广告', 'ASMR'];
const moodOptions = ['平静', '开心', '激昂', '悲伤'];
const styleOptions = ['自然', '广播腔', 'ASMR'];

const queueRows = computed(() => {
  const rows = tasks.value.slice(0, 3).map((task, index) => ({
    id: task.id,
    title: `${task.taskType === 'TTS' ? '音频生成' : task.taskType} #${2048 - index}`,
    subtitle: `${selectedVoiceLabel.value} · ${draft.value.mode}`,
    status: statusLabel(task.status),
    tone: statusTone(task.status),
    time: task.status === 'PROCESSING' ? '剩余 00:12' : formatDate(task.createdAt),
    progress: progressForStatus(task.status),
    errorMessage: task.errorMessage
  }));
  return rows;
});

const recentRuns = computed(() => {
  const rows = tasks.value.slice(0, 5).map((task, index) => ({
    id: task.id,
    title: `${task.taskType === 'TTS' ? '音频生成' : task.taskType} #${2045 - index}`,
    subtitle: task.prompt ? compact(task.prompt, 18) : `${selectedVoiceLabel.value} · ${draft.value.mode}`,
    date: formatDate(task.createdAt)
  }));
  return rows;
});
const latestAudioResult = computed(() => tasks.value.find((task) => task.status === 'SUCCESS' && task.resultUrl) ?? null);
const hasActiveTasks = computed(() => tasks.value.some(isActiveTask));

watch(managedAudioTools, () => selectDefaults());

watch(
  draft,
  (value) => saveWorkbenchDraft(DRAFT_KEY, value),
  { deep: true }
);

onMounted(async () => {
  await Promise.all([loadTasks(), loadCapabilities()]);
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

function selectDefaults() {
  selectedTool.value =
    selectedTool.value && audioTools.value.some((tool) => tool.id === selectedTool.value?.id)
      ? selectedTool.value
      : audioTools.value[0] ?? null;
}

async function submitAudioTask() {
  const tool = selectedTool.value ?? audioTools.value[0];
  if (!tool) {
    notice.value = '后台未启用可调用的音频能力';
    return;
  }
  if (!draft.value.prompt.trim()) {
    notice.value = '请先输入音频提示词';
    return;
  }
  isSubmitting.value = true;
  notice.value = '';
  try {
    const payload = buildAudioTaskPayload(tool, draft.value.prompt.trim(), selectedVoiceItem(), sourceUrl.value, SURFACE);
    payload.options = {
      ...(payload.options ?? {}),
      voice: selectedVoiceKey.value,
      duration: draft.value.duration,
      speed: draft.value.speed,
      mood: draft.value.mood,
      style: draft.value.style,
      mode: draft.value.mode,
      format: draft.value.exportFormat.toLowerCase(),
      sample_rate: draft.value.sampleRate
    };
    const task = await createAudioTask(
      payload
    );
    tasks.value = [task, ...tasks.value.filter((existing) => existing.id !== task.id)];
    notice.value = task.status === 'SUCCESS' ? '音频任务已完成，可在最近运行中查看。' : '音频任务已提交。';
    startTaskPolling();
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '音频任务提交失败';
  } finally {
    isSubmitting.value = false;
  }
}

async function loadTasks() {
  isLoadingTasks.value = true;
  try {
    tasks.value = await fetchAudioTasks(SURFACE);
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '音频任务加载失败';
  } finally {
    isLoadingTasks.value = false;
  }
}

async function loadCapabilities() {
  try {
    const payload = await fetchWorkbenchCapabilities(SURFACE);
    capabilities.value = payload.groups.audio ?? [];
    selectDefaults();
  } catch (error) {
    capabilities.value = [];
    notice.value = error instanceof Error ? error.message : '音频能力加载失败';
  }
}

function capabilityToPortalItem(capability: WorkbenchCapability): PortalItem {
  return {
    id: capability.id || capability.targetKey,
    itemType: 'tool',
    title: capability.title,
    subtitle: capability.subtitle,
    category: capability.category,
    icon: capability.icon,
    actionType: capability.actionType || 'workspace',
    actionValue: capability.modelConfig?.modelKey ?? capability.actionValue ?? capability.targetKey,
    requiredMembership: capability.requiredMembership,
    pointCost: capability.effectivePointCost,
    effectivePointCost: capability.effectivePointCost,
    sortOrder: capability.sortOrder,
    enabled: capability.enabled,
    modelConfig: capability.modelConfig,
    metadata: {
      targetType: capability.targetType,
      targetKey: capability.targetKey,
      routeKey: capability.modelConfig?.modelKey ?? capability.actionValue ?? capability.targetKey
    }
  };
}

function selectedVoiceItem(): PortalItem {
  return {
    id: `provider-voice-${selectedVoiceKey.value}`,
    itemType: 'voice',
    title: selectedVoiceLabel.value,
    subtitle: '',
    category: 'provider',
    icon: 'Mic',
    actionType: 'audio_voice',
    actionValue: selectedVoiceKey.value,
    requiredMembership: false,
    pointCost: 0,
    sortOrder: 0,
    enabled: true,
    metadata: {}
  };
}

function startTaskPolling() {
  if (!hasActiveTasks.value || pollTimer.value !== null || typeof window === 'undefined') {
    return;
  }
  pollTimer.value = window.setInterval(() => {
    void loadTasks().then(() => {
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

function isActiveTask(task: AudioTask): boolean {
  return task.status === 'PENDING' || task.status === 'PROCESSING';
}

async function handleAudioUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }
  try {
    const result = await uploadAudio(file);
    sourceUrl.value = result.url;
    notice.value = '音频素材已上传';
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '音频上传失败';
  } finally {
    input.value = '';
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    PENDING: '排队中',
    PROCESSING: '生成中',
    SUCCESS: '已完成',
    FAILED: '失败'
  };
  return labels[status] ?? status;
}

function statusTone(status: string) {
  if (status === 'SUCCESS') {
    return 'success';
  }
  if (status === 'PROCESSING') {
    return 'processing';
  }
  if (status === 'FAILED') {
    return 'failed';
  }
  return 'pending';
}

function progressForStatus(status: string): number {
  if (status === 'SUCCESS') {
    return 100;
  }
  if (status === 'PROCESSING') {
    return 62;
  }
  if (status === 'FAILED') {
    return 100;
  }
  return 12;
}

function formatDate(value?: string | null): string {
  if (!value) {
    return '刚刚';
  }
  return value.replace('T', ' ').slice(0, 16);
}

function compact(value: string, max = 18) {
  return value.length > max ? `${value.slice(0, max)}...` : value;
}

function resetAudioDraft() {
  draft.value.prompt = '';
  sourceUrl.value = '';
  notice.value = '';
}

async function copyLatestAudioLink() {
  const url = latestAudioResult.value?.resultUrl;
  if (!url) {
    notice.value = '暂无可复制的音频结果';
    return;
  }
  try {
    await navigator.clipboard.writeText(url);
    notice.value = '下载链接已复制';
  } catch {
    notice.value = url;
  }
}
</script>

<template>
  <WorkspaceShell
    active-module-key="audio"
    page-title="音频生成工作台"
    page-subtitle="音色、提示词、波形编辑、转写片段和导出设置集中处理"
    page-icon="Sparkles"
    variant="audio"
  >
    <template #leftFooter>
      <div class="audio-left-selects">
        <label>
          <span>能力：</span>
          <select v-model="selectedTool" :disabled="!audioTools.length">
            <option v-for="tool in audioTools" :key="tool.id" :value="tool">
              {{ tool.title }}
            </option>
          </select>
        </label>
        <label>
          <span>模型：</span>
          <strong class="audio-managed-model">{{ selectedTool?.modelConfig?.displayName ?? '后台未启用' }}</strong>
        </label>
      </div>
    </template>

    <template #main>
      <section class="wb-audio">
        <section class="audio-control-strip">
          <label>
            <span>声音：</span>
            <select v-model="selectedVoiceKey">
              <option v-for="voice in providerVoiceOptions" :key="voice.value" :value="voice.value">
                {{ voice.label }}
              </option>
            </select>
          </label>
          <label>
            <span>模式：</span>
            <select v-model="draft.mode">
              <option v-for="mode in modeOptions" :key="mode">{{ mode }}</option>
            </select>
          </label>
          <button :disabled="isSubmitting || !selectedTool" type="button" @click="submitAudioTask">
            <Waves :size="20" />
            {{ isSubmitting ? '生成中' : '生成预览' }}
          </button>
        </section>

        <section class="audio-prompt-panel">
          <header>
            <h2>提示词（Prompt）</h2>
            <div>
              <button type="button" @click="draft.prompt = ''"><Trash2 :size="18" />清空</button>
            </div>
          </header>
          <textarea
            v-model="draft.prompt"
            maxlength="1000"
            placeholder="描述你想要的音色、语速、情绪与内容。例如：用温柔的女声，读一段 30 秒的产品介绍，语速中等，带轻微微笑。"
          />
          <small>{{ draft.prompt.length }} / 1000</small>
        </section>

        <section class="audio-param-grid">
          <article>
            <header>
              <h2>时长</h2>
              <strong>{{ draft.duration }}</strong>
              <span>秒</span>
            </header>
            <input v-model.number="draft.duration" type="range" min="5" max="180" aria-label="音频时长" />
            <footer><span>5s</span><span>180s</span></footer>
          </article>
          <article>
            <h2>情绪</h2>
            <div class="audio-pill-row">
              <button
                v-for="mood in moodOptions"
                :key="mood"
                :class="{ active: draft.mood === mood }"
                type="button"
                @click="draft.mood = mood"
              >
                {{ mood }}
              </button>
            </div>
          </article>
          <article>
            <header>
              <h2>语速</h2>
              <strong>{{ draft.speed.toFixed(1) }}x</strong>
            </header>
            <input v-model.number="draft.speed" type="range" min="0.8" max="1.3" step="0.1" aria-label="语速" />
            <footer><span>0.8x</span><span>1.3x</span></footer>
          </article>
          <article>
            <h2>风格</h2>
            <div class="audio-pill-row">
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
          </article>
        </section>

        <section class="audio-bottom-grid">
          <article class="audio-playback-panel">
            <h2>播放控制</h2>
            <audio v-if="latestAudioResult" class="audio-result-player" :src="latestAudioResult.resultUrl || ''" controls />
            <div v-else class="audio-empty-result">
              <Music :size="34" />
              <strong>还没有完成的音频</strong>
              <span>提交任务后，真实音频文件会在这里播放。</span>
            </div>
          </article>

          <article class="audio-export-card">
            <h2>导出</h2>
            <div class="audio-format-row">
              <button
                v-for="format in ['WAV', 'MP3', 'M4A']"
                :key="format"
                :class="{ active: draft.exportFormat === format }"
                type="button"
                @click="draft.exportFormat = format"
              >
                {{ format }}
              </button>
            </div>
            <label>
              <span>采样率</span>
              <select v-model="draft.sampleRate">
                <option>44.1k Hz</option>
                <option>48k Hz</option>
              </select>
            </label>
            <div class="audio-export-actions">
              <a v-if="latestAudioResult" :href="latestAudioResult.resultUrl || '#'" download>
                <Download :size="20" />
                导出文件
              </a>
              <button v-else type="button" disabled><Download :size="20" />导出文件</button>
              <button type="button" :disabled="!latestAudioResult" @click="copyLatestAudioLink">
                <Link :size="20" />
                复制下载链接
              </button>
            </div>
          </article>
        </section>

        <p v-if="notice" class="audio-notice">{{ notice }}</p>
      </section>
    </template>

    <template #side>
      <section class="audio-side-panel">
        <header>
          <h2>任务队列</h2>
          <button type="button" @click="loadTasks">{{ isLoadingTasks ? '刷新中' : '查看全部' }}</button>
        </header>
        <article v-for="task in queueRows" :key="task.id" class="audio-task-row">
          <span :class="task.tone"><Music :size="20" /></span>
          <div>
            <strong>{{ task.title }}</strong>
            <small>{{ task.subtitle }}</small>
            <small v-if="task.errorMessage" class="audio-task-error">{{ task.errorMessage }}</small>
            <div v-if="task.progress < 100" class="audio-progress">
              <i :style="{ width: `${task.progress}%` }"></i>
            </div>
          </div>
          <em :class="task.tone">{{ task.status }}</em>
          <time>{{ task.time }}</time>
        </article>
      </section>

      <section class="audio-side-panel">
        <header>
          <h2>最近运行</h2>
          <button type="button" @click="loadTasks">刷新</button>
        </header>
        <article v-for="run in recentRuns" :key="run.id" class="audio-run-row">
          <span><Music :size="18" /></span>
          <div>
            <strong>{{ run.title }}</strong>
            <small>{{ run.subtitle }}<br />{{ run.date }}</small>
          </div>
        </article>
      </section>

      <section class="audio-side-panel">
        <header><h2>快捷操作</h2></header>
        <div class="audio-quick-grid">
          <button type="button" @click="resetAudioDraft"><Music :size="26" />新建音频</button>
          <label>
            <UploadCloud :size="26" />
            导入音频
            <input type="file" accept="audio/*" @change="handleAudioUpload" />
          </label>
        </div>
      </section>

      <section class="audio-side-panel audio-settings-panel">
        <header><h2>设置</h2></header>
        <label><span>自动保存</span><input v-model="draft.autoSave" type="checkbox" /></label>
        <label><span>生成完成通知</span><input v-model="draft.notify" type="checkbox" /></label>
        <label><span>流式输出</span><input v-model="draft.streaming" type="checkbox" /></label>
        <label>
          <span>主题模式</span>
          <select v-model="draft.themeMode">
            <option>跟随系统</option>
            <option>浅色</option>
            <option>深色</option>
          </select>
        </label>
      </section>
    </template>
  </WorkspaceShell>
</template>

<style scoped>
.audio-left-selects label,
.audio-control-strip,
.audio-prompt-panel,
.audio-playback-panel,
.audio-export-card,
.audio-side-panel {
  min-width: 0;
}

.audio-left-selects {
  display: grid;
  gap: 12px;
}

.audio-left-selects label {
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

.audio-left-selects select,
.audio-control-strip select,
.audio-export-card select,
.audio-settings-panel select {
  width: 100%;
  height: 42px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 0 12px;
  color: #172033;
  background: #fff;
  font: inherit;
}

.audio-managed-model {
  overflow: hidden;
  color: #172033;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-audio {
  display: grid;
  gap: 18px;
}

.audio-control-strip,
.audio-prompt-panel,
.audio-param-grid article,
.audio-playback-panel,
.audio-export-card,
.audio-side-panel {
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 24px rgba(38, 50, 84, 0.04);
}

.audio-control-strip {
  display: grid;
  grid-template-columns: minmax(190px, 1fr) minmax(170px, 0.8fr) 168px;
  align-items: center;
  gap: 18px;
  padding: 18px 22px;
}

.audio-control-strip label {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 10px;
}

.audio-control-strip button,
.audio-prompt-panel button,
.audio-playback-panel button,
.audio-export-card button,
.audio-export-actions a,
.audio-side-panel header button,
.audio-quick-grid button,
.audio-quick-grid label {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 0 14px;
  color: #273044;
  background: #fff;
  font: inherit;
  font-weight: 800;
}

.audio-control-strip button:nth-of-type(1) {
  border-color: #5964ff;
  color: #4f5cff;
}

.audio-control-strip button:disabled {
  opacity: 0.68;
}

.audio-prompt-panel,
.audio-playback-panel,
.audio-export-card,
.audio-side-panel {
  padding: 18px;
}

.audio-prompt-panel header,
.audio-side-panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.audio-prompt-panel h2,
.audio-param-grid h2,
.audio-playback-panel h2,
.audio-export-card h2,
.audio-side-panel h2 {
  margin: 0;
  color: #111827;
  font-size: 20px;
}

.audio-prompt-panel header div {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.audio-prompt-panel {
  position: relative;
}

.audio-prompt-panel textarea {
  width: 100%;
  min-height: 180px;
  resize: vertical;
  border: 0;
  outline: none;
  color: #172033;
  background: transparent;
  font: inherit;
  line-height: 1.7;
}

.audio-prompt-panel small {
  position: absolute;
  right: 18px;
  bottom: 14px;
  color: #8791a3;
}

.audio-param-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.audio-param-grid article {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.audio-param-grid header {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.audio-param-grid strong {
  margin-left: auto;
  color: #5264ff;
  font-size: 24px;
}

.audio-param-grid input {
  width: 100%;
  accent-color: #5964ff;
}

.audio-param-grid footer {
  display: flex;
  justify-content: space-between;
  color: #667085;
}

.audio-pill-row {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.audio-pill-row button,
.audio-format-row button {
  min-width: 96px;
  min-height: 42px;
  border: 1px solid #dfe5ef;
  border-radius: 999px;
  color: #273044;
  background: #fff;
  font: inherit;
}

.audio-pill-row button.active,
.audio-format-row button.active {
  border-color: #5964ff;
  color: #fff;
  background: linear-gradient(135deg, #5264ff, #6c4cf5);
}

.audio-bottom-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18px;
}

.audio-playback-panel,
.audio-export-card {
  display: grid;
  gap: 18px;
}

.audio-result-player {
  width: 100%;
}

.audio-empty-result {
  min-height: 180px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  color: #667085;
  text-align: center;
}

.audio-empty-result strong {
  color: #172033;
  font-size: 18px;
}

.audio-format-row,
.audio-export-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.audio-export-card label {
  display: grid;
  grid-template-columns: 72px 190px;
  align-items: center;
  gap: 10px;
}

.audio-export-actions a:first-child {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #5264ff, #6c4cf5);
  text-decoration: none;
}

.audio-notice {
  margin: 0;
  border-radius: 8px;
  padding: 12px 14px;
  color: #245b45;
  background: #eaf8f1;
  font-weight: 800;
}

.audio-task-row,
.audio-run-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  border: 1px solid #edf1f7;
  border-radius: 8px;
  padding: 12px;
}

.audio-task-row + .audio-task-row,
.audio-run-row + .audio-run-row {
  margin-top: 10px;
}

.audio-task-row > span,
.audio-run-row > span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #5264ff;
  background: #f1f3ff;
}

.audio-task-row > span.success {
  color: #0c9f61;
  background: #eaf8f1;
}

.audio-task-row > span.pending {
  color: #f08a00;
  background: #fff5e5;
}

.audio-task-row strong,
.audio-run-row strong {
  display: block;
  overflow: hidden;
  color: #172033;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audio-task-row small,
.audio-run-row small,
.audio-task-row time {
  color: #8791a3;
}

.audio-task-error {
  color: #d92d20 !important;
}

.audio-task-row em {
  grid-column: 3;
  border-radius: 8px;
  padding: 5px 10px;
  font-style: normal;
  font-weight: 800;
}

.audio-task-row em.processing {
  color: #3567ff;
  background: #eef3ff;
}

.audio-task-row em.pending {
  color: #f08a00;
  background: #fff5e5;
}

.audio-task-row em.success {
  color: #0c9f61;
  background: #eaf8f1;
}

.audio-task-row time {
  grid-column: 3;
  justify-self: end;
}

.audio-progress {
  height: 5px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf1f7;
}

.audio-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #5264ff;
}

.audio-quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.audio-quick-grid button,
.audio-quick-grid label {
  position: relative;
  min-height: 92px;
  display: grid;
  place-items: center;
  gap: 8px;
  color: #5264ff;
  text-align: center;
}

.audio-quick-grid input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.audio-settings-panel {
  display: grid;
  gap: 14px;
}

.audio-settings-panel label {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px;
  align-items: center;
  gap: 12px;
  color: #5c667a;
}

.audio-settings-panel input[type='checkbox'] {
  justify-self: end;
  width: 46px;
  height: 26px;
  accent-color: #5264ff;
}

@media (max-width: 1180px) {
  .audio-control-strip,
  .audio-param-grid,
  .audio-bottom-grid {
    grid-template-columns: 1fr;
  }
}
</style>

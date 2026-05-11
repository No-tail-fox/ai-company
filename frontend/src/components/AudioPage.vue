<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  Bookmark,
  CircleHelp,
  Clock3,
  Download,
  Folder,
  Link,
  Mic,
  Music,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  Scissors,
  Send,
  Settings,
  SlidersHorizontal,
  Sparkles,
  Split,
  Trash2,
  UploadCloud,
  Volume2,
  Waves
} from 'lucide-vue-next';
import { createAudioTask, fetchAudioTasks, uploadAudio } from '../services/api';
import {
  buildAudioTaskPayload,
  createFallbackAudioWorkbenchPageConfig,
  getAudioSection,
  loadWorkbenchDraft,
  saveWorkbenchDraft,
  type AudioTask,
  type PortalItem,
  type PortalPageConfig
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

const props = defineProps<{
  pageConfig?: PortalPageConfig;
}>();

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

const pageConfig = computed(() => props.pageConfig ?? createFallbackAudioWorkbenchPageConfig());
const workbenchSection = computed(() => getAudioSection(pageConfig.value, 'audio-workbench'));
const toolsSection = computed(() => getAudioSection(pageConfig.value, 'audio-tools'));
const voicesSection = computed(() => getAudioSection(pageConfig.value, 'audio-voices'));

const draft = ref<AudioDraft>(loadWorkbenchDraft(DRAFT_KEY, defaultDraft));
const selectedTool = ref<PortalItem | null>(null);
const selectedVoice = ref<PortalItem | null>(null);
const sourceUrl = ref('');
const tasks = ref<AudioTask[]>([]);
const isSubmitting = ref(false);
const isLoadingTasks = ref(false);
const notice = ref('');
const playingId = ref('');
const pollTimer = ref<number | null>(null);

const voiceItems = computed(() => voicesSection.value?.items ?? []);
const audioTools = computed(() => toolsSection.value?.items ?? []);

const voiceOptions = computed(() => {
  const labels = voiceItems.value.map((voice) => voice.title);
  return labels.length > 0 ? labels : ['女声·清澈', '男声·磁性', '活力女声'];
});

const selectedVoiceTitle = computed({
  get: () => selectedVoice.value?.title ?? voiceOptions.value[0],
  set: (title: string) => {
    selectedVoice.value = voiceItems.value.find((voice) => voice.title === title) ?? selectedVoice.value;
  }
});

const modeOptions = ['旁白', '播客', '广告', 'ASMR'];
const moodOptions = ['平静', '开心', '激昂', '悲伤'];
const styleOptions = ['自然', '广播腔', 'ASMR'];

const queueRows = computed(() => {
  const rows = tasks.value.slice(0, 3).map((task, index) => ({
    id: task.id,
    title: `${task.taskType === 'TTS' ? '音频生成' : task.taskType} #${2048 - index}`,
    subtitle: `${selectedVoiceTitle.value} · ${draft.value.mode}`,
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
    subtitle: task.prompt ? compact(task.prompt, 18) : `${selectedVoiceTitle.value} · ${draft.value.mode}`,
    date: formatDate(task.createdAt)
  }));
  return rows;
});
const latestAudioResult = computed(() => tasks.value.find((task) => task.status === 'SUCCESS' && task.resultUrl) ?? null);
const hasActiveTasks = computed(() => tasks.value.some(isActiveTask));

const transcriptRows = [
  ['00:00 - 00:10', '欢迎收听本期节目，我们今天聊聊如何提升专注力。'],
  ['00:10 - 00:20', '首先，找到一个安静的环境，减少外界干扰非常重要。'],
  ['00:20 - 00:30', '其次，使用番茄工作法，把时间划分为 25 分钟专注 + 5 分钟休息。'],
  ['00:30 - 00:40', '第三，设定明确的小目标，完成后给自己一些正向反馈。'],
  ['00:40 - 00:50', '最后，保持规律的作息和适度运动，帮助大脑维持高效状态。'],
  ['00:50 - 01:00', '感谢收听，我们下期再见！']
];

watch(
  pageConfig,
  () => selectDefaults(),
  { immediate: true }
);

watch(
  draft,
  (value) => saveWorkbenchDraft(DRAFT_KEY, value),
  { deep: true }
);

onMounted(async () => {
  await loadTasks();
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
  selectedTool.value = selectedTool.value ?? audioTools.value[0] ?? workbenchSection.value?.items[0] ?? null;
  selectedVoice.value = selectedVoice.value ?? voiceItems.value[0] ?? null;
}

async function submitAudioTask() {
  const tool = selectedTool.value ?? audioTools.value[0] ?? workbenchSection.value?.items[0];
  if (!tool || !draft.value.prompt.trim()) {
    notice.value = '请先输入音频提示词';
    return;
  }
  isSubmitting.value = true;
  notice.value = '';
  try {
    const task = await createAudioTask(
      buildAudioTaskPayload(tool, draft.value.prompt.trim(), selectedVoice.value ?? undefined, sourceUrl.value, SURFACE)
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

function togglePlay(rowId: string) {
  playingId.value = playingId.value === rowId ? '' : rowId;
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
</script>

<template>
  <WorkspaceShell
    active-module-key="audio"
    page-title="音频生成工作台"
    page-subtitle="音色、提示词、波形编辑、转写片段和导出设置集中处理"
    page-icon="Sparkles"
    variant="audio"
  >
    <template #headerActions>
      <button class="audio-top-button" type="button"><Clock3 :size="20" />历史</button>
      <button class="audio-top-button" type="button"><Settings :size="20" />设置</button>
      <button class="audio-top-button" type="button"><CircleHelp :size="20" />帮助</button>
    </template>

    <template #leftFooter>
      <div class="audio-left-selects">
        <label>
          <span>角色：</span>
          <select>
            <option>通用助手</option>
            <option>音频导演</option>
          </select>
        </label>
        <label>
          <span>模型：</span>
          <select>
            <option>GPT-4.1</option>
            <option>Audio Studio</option>
          </select>
        </label>
      </div>
    </template>

    <template #main>
      <section class="wb-audio">
        <section class="audio-control-strip">
          <label>
            <span>声音：</span>
            <select v-model="selectedVoiceTitle">
              <option v-for="voice in voiceOptions" :key="voice">{{ voice }}</option>
            </select>
          </label>
          <label>
            <span>模式：</span>
            <select v-model="draft.mode">
              <option v-for="mode in modeOptions" :key="mode">{{ mode }}</option>
            </select>
          </label>
          <button :disabled="isSubmitting" type="button" @click="submitAudioTask">
            <Waves :size="20" />
            {{ isSubmitting ? '生成中' : '生成预览' }}
          </button>
          <button type="button"><SlidersHorizontal :size="20" />高级参数</button>
        </section>

        <section class="audio-prompt-panel">
          <header>
            <h2>提示词（Prompt）</h2>
            <div>
              <button type="button"><Bookmark :size="18" />插入模板</button>
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

        <section class="audio-wave-editor">
          <header>
            <h2>波形编辑</h2>
            <div>
              <button type="button"><Scissors :size="18" />剪切</button>
              <button type="button"><Split :size="18" />分割</button>
              <button type="button"><Waves :size="18" />淡入</button>
              <button type="button"><Waves :size="18" />淡出</button>
              <button type="button"><Volume2 :size="18" />降噪</button>
            </div>
          </header>
          <div class="audio-waveform" aria-hidden="true">
            <span v-for="index in 150" :key="index" :style="{ height: `${18 + ((index * 19) % 58)}px` }"></span>
            <i></i>
          </div>
          <footer>
            <span>00:00</span>
            <span>00:10</span>
            <span>00:20</span>
            <span>00:30</span>
            <span>00:40</span>
            <span>00:50</span>
            <span>01:00</span>
          </footer>
        </section>

        <section class="audio-bottom-grid">
          <article class="audio-playback-panel">
            <h2>播放控制</h2>
            <audio v-if="latestAudioResult" class="audio-result-player" :src="latestAudioResult.resultUrl || ''" controls />
            <div class="audio-player-buttons">
              <button type="button" aria-label="上一段"><RefreshCw :size="22" /></button>
              <button class="primary" type="button" @click="togglePlay('main')">
                <PauseCircle v-if="playingId === 'main'" :size="32" />
                <PlayCircle v-else :size="32" />
              </button>
              <button type="button" aria-label="下一段"><RefreshCw :size="22" /></button>
              <button type="button" aria-label="循环"><RefreshCw :size="22" /></button>
            </div>
            <div class="audio-volume-row">
              <Volume2 :size="20" />
              <input type="range" min="0" max="100" value="58" aria-label="音量" />
              <span>00:12 / 01:00</span>
            </div>
            <button type="button"><Bookmark :size="18" />标记片段</button>
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
              <button type="button"><Download :size="20" />导出文件</button>
              <button type="button"><Link :size="20" />复制下载链接</button>
            </div>
          </article>
        </section>

        <section class="audio-transcript-panel">
          <header>
            <h2>转写与片段</h2>
            <nav>
              <button class="active" type="button">转写</button>
              <button type="button">片段</button>
            </nav>
          </header>
          <div class="audio-transcript-table">
            <div v-for="(row, index) in transcriptRows" :key="row[0]" class="audio-transcript-row">
              <span>{{ index + 1 }}</span>
              <time>{{ row[0] }}</time>
              <p>{{ row[1] }}</p>
              <button type="button" aria-label="静音"><Volume2 :size="18" /></button>
              <button type="button" aria-label="播放"><Volume2 :size="18" /></button>
            </div>
          </div>
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
          <button type="button">查看全部</button>
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
          <button type="button"><Music :size="26" />新建音频</button>
          <label>
            <UploadCloud :size="26" />
            导入音频
            <input type="file" accept="audio/*" @change="handleAudioUpload" />
          </label>
          <button type="button"><Folder :size="26" />我的素材</button>
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
.audio-top-button,
.audio-left-selects label,
.audio-control-strip,
.audio-prompt-panel,
.audio-wave-editor,
.audio-playback-panel,
.audio-export-card,
.audio-transcript-panel,
.audio-side-panel {
  min-width: 0;
}

.audio-top-button {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  border-radius: 8px;
  padding: 0 12px;
  color: #273044;
  background: transparent;
  font-weight: 800;
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

.wb-audio {
  display: grid;
  gap: 18px;
}

.audio-control-strip,
.audio-prompt-panel,
.audio-param-grid article,
.audio-wave-editor,
.audio-playback-panel,
.audio-export-card,
.audio-transcript-panel,
.audio-side-panel {
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 24px rgba(38, 50, 84, 0.04);
}

.audio-control-strip {
  display: grid;
  grid-template-columns: minmax(190px, 1fr) minmax(170px, 0.8fr) 168px 168px;
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
.audio-wave-editor button,
.audio-playback-panel button,
.audio-export-card button,
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
.audio-wave-editor,
.audio-playback-panel,
.audio-export-card,
.audio-transcript-panel,
.audio-side-panel {
  padding: 18px;
}

.audio-prompt-panel header,
.audio-wave-editor header,
.audio-transcript-panel header,
.audio-side-panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.audio-prompt-panel h2,
.audio-param-grid h2,
.audio-wave-editor h2,
.audio-playback-panel h2,
.audio-export-card h2,
.audio-transcript-panel h2,
.audio-side-panel h2 {
  margin: 0;
  color: #111827;
  font-size: 20px;
}

.audio-prompt-panel header div,
.audio-wave-editor header div {
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

.audio-wave-editor {
  display: grid;
  gap: 12px;
}

.audio-waveform {
  position: relative;
  height: 138px;
  display: flex;
  align-items: center;
  gap: 3px;
  overflow: hidden;
}

.audio-waveform span {
  width: 4px;
  flex: 0 0 4px;
  border-radius: 999px;
  background: #5964ff;
}

.audio-waveform i {
  position: absolute;
  left: 24%;
  top: 8px;
  width: 23%;
  height: calc(100% - 16px);
  border: 2px solid #5964ff;
  border-radius: 8px;
  background: rgba(89, 100, 255, 0.08);
}

.audio-wave-editor footer {
  display: flex;
  justify-content: space-between;
  color: #667085;
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

.audio-player-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 26px;
}

.audio-result-player {
  width: 100%;
}

.audio-player-buttons .primary {
  width: 58px;
  height: 58px;
  border: 0;
  border-radius: 50%;
  color: #fff;
  background: linear-gradient(135deg, #5264ff, #6c4cf5);
}

.audio-volume-row {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  color: #667085;
}

.audio-volume-row input {
  accent-color: #5964ff;
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

.audio-export-actions button:first-child {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #5264ff, #6c4cf5);
}

.audio-transcript-panel nav {
  display: flex;
  gap: 24px;
}

.audio-transcript-panel nav button {
  min-height: 34px;
  border: 0;
  border-bottom: 2px solid transparent;
  color: #667085;
  background: transparent;
  font: inherit;
  font-weight: 800;
}

.audio-transcript-panel nav button.active {
  border-color: #5964ff;
  color: #4f5cff;
}

.audio-transcript-table {
  border: 1px solid #edf1f7;
  border-radius: 8px;
  overflow: hidden;
}

.audio-transcript-row {
  min-height: 48px;
  display: grid;
  grid-template-columns: 44px 140px minmax(0, 1fr) 40px 40px;
  align-items: center;
  border-top: 1px solid #edf1f7;
  color: #273044;
}

.audio-transcript-row:first-child {
  border-top: 0;
}

.audio-transcript-row span,
.audio-transcript-row time,
.audio-transcript-row button {
  height: 100%;
  display: grid;
  place-items: center;
  border-right: 1px solid #edf1f7;
}

.audio-transcript-row p {
  margin: 0;
  padding: 0 14px;
}

.audio-transcript-row button {
  border-width: 0 0 0 1px;
  color: #5264ff;
  background: #fff;
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

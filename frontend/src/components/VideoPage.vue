<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import {
  Clapperboard,
  Download,
  FileText,
  Folder,
  Grid3X3,
  Mic,
  Plus,
  Scissors,
  Settings,
  Sparkles,
  Trash2,
  Undo2,
  Redo2,
  Video,
  Volume2,
  ZoomIn,
  ZoomOut
} from 'lucide-vue-next';
import { createVideoGeneration, fetchVideoWorkbench } from '../services/api';
import {
  createFallbackVideoWorkbench,
  getVideoStatusMeta,
  loadWorkbenchDraft,
  saveWorkbenchDraft,
  type VideoTask,
  type VideoWorkbench
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
  styleOpen: boolean;
  lensOpen: boolean;
  negativeOpen: boolean;
}

interface SceneItem {
  id: string;
  title: string;
  copy: string;
  duration: string;
  accent: string;
}

const SURFACE = 'workbench';
const DRAFT_KEY = 'opc_workbench_video_draft';

const defaultDraft: VideoDraft = {
  prompt: '',
  duration: '10s',
  ratio: '16:9',
  resolution: '1080p',
  frameRate: '30',
  format: 'MP4',
  bitrate: '推荐（10Mbps）',
  watermark: false,
  styleOpen: false,
  lensOpen: false,
  negativeOpen: false
};

const workbench = ref<VideoWorkbench>({ ...createFallbackVideoWorkbench(), tasks: [] });
const draft = ref<VideoDraft>(loadWorkbenchDraft(DRAFT_KEY, defaultDraft));
const selectedSceneId = ref('scene-02');
const isCreating = ref(false);
const createError = ref('');
const pollTimer = ref<number | null>(null);

const durationOptions = ['10s', '15s', '30s', '45s', '60s'];
const ratioOptions = ['16:9', '9:16', '1:1', '21:9'];
const resolutionOptions = ['720p', '1080p', '2K', '4K'];
const frameRateOptions = ['24', '30', '60'];

const scenes: SceneItem[] = [
  { id: 'scene-01', title: '场景 01', copy: '清晨的城市，阳光洒在高楼之间。', duration: '00:04', accent: 'sunrise' },
  { id: 'scene-02', title: '场景 02', copy: '主角走在街道上，目光坚定。', duration: '00:06', accent: 'walk' },
  { id: 'scene-03', title: '场景 03', copy: '咖啡馆内，主角思考未来。', duration: '00:05', accent: 'cafe' },
  { id: 'scene-04', title: '场景 04', copy: '夜晚的天台，城市灯光璀璨。', duration: '00:05', accent: 'night' },
  { id: 'scene-05', title: '场景 05', copy: '主角回头微笑，充满希望。', duration: '00:05', accent: 'portrait' }
];

const storyboard = computed(() => [
  ...scenes,
  { id: 'add-shot', title: '添加镜头', copy: '', duration: '', accent: 'add' }
]);

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

const totalDuration = computed(() => {
  const seconds = scenes.reduce((sum, scene) => sum + Number(scene.duration.slice(-2)), 0);
  return `00:${String(seconds).padStart(2, '0')}`;
});
const latestVideoResult = computed(() =>
  workbench.value.tasks.find((task) => task.status === 'SUCCESS' && task.resultUrl) ?? null
);
const hasActiveTasks = computed(() => workbench.value.tasks.some(isActiveTask));

watch(
  draft,
  (value) => saveWorkbenchDraft(DRAFT_KEY, value),
  { deep: true }
);

onMounted(async () => {
  await loadWorkbench();
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

async function createFromPrompt() {
  const prompt = draft.value.prompt.trim();
  if (!prompt) {
    createError.value = '请输入视频脚本或提示词';
    return;
  }
  isCreating.value = true;
  createError.value = '';
  try {
    const enrichedPrompt = `${prompt}；时长：${draft.value.duration}；比例：${draft.value.ratio}；分辨率：${draft.value.resolution}；帧率：${draft.value.frameRate}`;
    const created = await createVideoGeneration(enrichedPrompt, {
      targetType: 'builtin',
      targetId: 'video_text_to_video',
      routeKey: 'video_text_to_video',
      surface: SURFACE
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
    <template #headerActions>
      <button class="video-top-button" type="button"><Folder :size="20" />素材库</button>
      <button class="video-top-button" type="button"><Grid3X3 :size="20" />模板</button>
      <button class="video-top-button" type="button"><Settings :size="20" />设置</button>
    </template>

    <template #leftFooter>
      <div class="video-left-selects">
        <label>
          <span>角色：</span>
          <select>
            <option>通用助手</option>
            <option>视频导演</option>
          </select>
        </label>
        <label>
          <span>模型：</span>
          <select>
            <option>GPT-4.1</option>
            <option>Video Render</option>
          </select>
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
            <button type="button" @click="draft.styleOpen = !draft.styleOpen">
              风格参考
              <span>⌄</span>
            </button>
            <button type="button" @click="draft.lensOpen = !draft.lensOpen">
              镜头语言
              <span>⌄</span>
            </button>
            <button type="button" @click="draft.negativeOpen = !draft.negativeOpen">
              负面提示词
              <span>⌄</span>
            </button>
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
            <button class="video-generate-preview" :disabled="isCreating" type="button" @click="createFromPrompt">
              <Sparkles :size="22" />
              {{ isCreating ? '生成中' : '生成预览' }}
            </button>
            <button class="video-generate-full" :disabled="isCreating" type="button" @click="createFromPrompt">生成全片</button>
            <p v-if="createError" class="video-error">{{ createError }}</p>
          </article>
        </section>

        <section class="video-edit-grid">
          <aside class="video-scene-list">
            <header>
              <h2>场景列表</h2>
              <button type="button"><Plus :size="18" />新增场景</button>
            </header>
            <button
              v-for="scene in scenes"
              :key="scene.id"
              :class="{ active: selectedSceneId === scene.id }"
              type="button"
              @click="selectedSceneId = scene.id"
            >
              <strong>{{ scene.title }}</strong>
              <time>{{ scene.duration }}</time>
              <span>{{ scene.copy }}</span>
            </button>
            <footer>总时长 {{ totalDuration }}</footer>
          </aside>

          <div class="video-main-canvas">
            <section class="video-storyboard-panel">
              <h2>故事板</h2>
              <div class="video-storyboard-grid">
                <button
                  v-for="shot in storyboard"
                  :key="shot.id"
                  :class="['video-shot', shot.accent, { active: selectedSceneId === shot.id, add: shot.id === 'add-shot' }]"
                  type="button"
                  @click="shot.id !== 'add-shot' && (selectedSceneId = shot.id)"
                >
                  <span v-if="shot.id !== 'add-shot'">{{ shot.title.replace('场景 ', '') }}</span>
                  <em v-if="shot.duration">{{ shot.duration }}</em>
                  <template v-if="shot.id === 'add-shot'"><Plus :size="20" />添加镜头</template>
                </button>
              </div>
            </section>

            <section class="video-player-panel">
              <header>
                <h2>预览</h2>
                <select v-model="draft.ratio">
                  <option v-for="ratio in ratioOptions" :key="ratio">{{ ratio }}</option>
                </select>
              </header>
              <div class="video-preview-frame">
                <video v-if="latestVideoResult" class="video-result-player" :src="latestVideoResult.resultUrl || ''" controls />
                <div v-else class="video-preview-scene walk"></div>
              </div>
              <div class="video-player-controls">
                <Video :size="22" />
                <span>00:02 / 00:06</span>
                <input type="range" min="0" max="100" value="42" aria-label="预览进度" />
                <Volume2 :size="20" />
                <input type="range" min="0" max="100" value="62" aria-label="音量" />
              </div>
              <small>当前镜头：场景 02 - 镜头 03</small>
            </section>
          </div>
        </section>

        <section class="video-timeline-panel">
          <header>
            <h2>时间线</h2>
            <div>
              <button type="button" aria-label="撤销"><Undo2 :size="18" /></button>
              <button type="button" aria-label="重做"><Redo2 :size="18" /></button>
              <button type="button" aria-label="剪切"><Scissors :size="18" /></button>
              <button type="button" aria-label="删除"><Trash2 :size="18" /></button>
            </div>
            <div>
              <ZoomOut :size="18" />
              <input type="range" min="0" max="100" value="62" aria-label="时间线缩放" />
              <ZoomIn :size="18" />
            </div>
          </header>
          <div class="video-timeline">
            <span>00:00</span>
            <span>00:05</span>
            <span>00:10</span>
            <span>00:15</span>
            <span>00:20</span>
            <span>00:25</span>
            <div class="track-label"><Video :size="20" />视频</div>
            <div class="track video-track">
              <button v-for="scene in scenes" :key="scene.id" :class="{ active: scene.id === selectedSceneId }" type="button">
                {{ scene.title }}<small>{{ scene.duration }}</small>
              </button>
            </div>
            <div class="track-label"><Mic :size="20" />旁白</div>
            <div class="track audio-track"></div>
            <div class="track-label"><Volume2 :size="20" />音乐</div>
            <div class="track music-track"></div>
            <div class="track-label"><FileText :size="20" />字幕</div>
            <div class="track subtitle-track">
              <span v-for="scene in scenes" :key="scene.id">{{ scene.copy }}</span>
            </div>
          </div>
        </section>
      </section>
    </template>

    <template #side>
      <section class="video-side-panel">
        <header>
          <h2>任务队列</h2>
          <button type="button">查看全部</button>
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
          <button type="button">查看全部</button>
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
        <button class="video-export-button" type="button"><Download :size="22" />导出视频</button>
        <button class="video-download-button" type="button"><Download :size="22" />下载项目</button>
      </section>
    </template>
  </WorkspaceShell>
</template>

<style scoped>
.video-top-button,
.video-left-selects label,
.video-composer-grid,
.video-script-panel,
.video-config-panel,
.video-scene-list,
.video-storyboard-panel,
.video-player-panel,
.video-timeline-panel,
.video-side-panel {
  min-width: 0;
}

.video-top-button {
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  padding: 0 16px;
  color: #172033;
  background: #fff;
  font-weight: 800;
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
.video-player-panel select,
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
.video-scene-list,
.video-storyboard-panel,
.video-player-panel,
.video-timeline-panel,
.video-side-panel {
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 24px rgba(38, 50, 84, 0.04);
}

.video-script-panel,
.video-config-panel,
.video-scene-list,
.video-storyboard-panel,
.video-player-panel,
.video-timeline-panel,
.video-side-panel {
  padding: 18px;
}

.video-script-panel h2,
.video-scene-list h2,
.video-storyboard-panel h2,
.video-player-panel h2,
.video-timeline-panel h2,
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

.video-script-panel > button {
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 0;
  border-top: 1px solid #edf1f7;
  color: #273044;
  background: transparent;
  font: inherit;
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
.video-generate-full,
.video-export-button,
.video-download-button {
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

.video-generate-full,
.video-download-button {
  border: 1px solid #98a2ff;
  color: #4f5cff;
  background: #fff;
}

.video-generate-preview:disabled,
.video-generate-full:disabled {
  opacity: 0.68;
}

.video-error {
  margin: 0;
  color: #d92d20;
  font-weight: 800;
}

.video-edit-grid {
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr);
  gap: 18px;
}

.video-scene-list {
  display: grid;
  gap: 14px;
}

.video-scene-list header,
.video-storyboard-panel header,
.video-player-panel header,
.video-timeline-panel header,
.video-side-panel header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.video-scene-list header button,
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

.video-scene-list > button {
  min-height: 88px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  border: 1px solid #edf1f7;
  border-radius: 8px;
  padding: 14px;
  color: #172033;
  background: #fff;
  text-align: left;
}

.video-scene-list > button.active {
  border-color: #5964ff;
  background: #f7f8ff;
}

.video-scene-list span {
  grid-column: 1 / -1;
  color: #6b7280;
}

.video-scene-list time,
.video-scene-list footer {
  color: #667085;
}

.video-main-canvas {
  display: grid;
  gap: 18px;
}

.video-storyboard-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.video-shot {
  position: relative;
  min-height: 124px;
  overflow: hidden;
  border: 2px solid transparent;
  border-radius: 8px;
  color: #fff;
  background: #edf1f7;
  font: inherit;
  text-align: left;
}

.video-shot.active {
  border-color: #5964ff;
}

.video-shot.add {
  display: grid;
  place-items: center;
  gap: 8px;
  border: 1px dashed #c7cfdd;
  color: #5f6778;
  background: #fff;
  text-align: center;
}

.video-shot:not(.add)::before,
.video-preview-scene::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 28%, rgba(0, 0, 0, 0.58));
}

.video-shot.sunrise,
.video-preview-scene.sunrise {
  background: linear-gradient(135deg, #516b83, #f2b76a 58%, #38465d);
}

.video-shot.walk,
.video-preview-scene.walk {
  background: linear-gradient(135deg, #2c3440, #d39c62 48%, #192535);
}

.video-shot.cafe,
.video-preview-scene.cafe {
  background: linear-gradient(135deg, #30251c, #b47b45 54%, #1c1714);
}

.video-shot.night,
.video-preview-scene.night {
  background: linear-gradient(135deg, #111827, #2d5d92 58%, #050816);
}

.video-shot.portrait,
.video-preview-scene.portrait {
  background: linear-gradient(135deg, #3d2f2a, #d8a16d 56%, #1e252f);
}

.video-shot span,
.video-shot em {
  position: absolute;
  z-index: 1;
  font-style: normal;
  font-weight: 900;
}

.video-shot span {
  left: 12px;
  bottom: 12px;
}

.video-shot em {
  right: 12px;
  bottom: 12px;
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

.video-preview-scene {
  position: relative;
  aspect-ratio: 16 / 9;
}

.video-result-player {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #111827;
}

.video-player-controls {
  display: grid;
  grid-template-columns: 24px auto minmax(0, 1fr) 22px 120px;
  align-items: center;
  gap: 12px;
  color: #5f6778;
}

.video-player-controls input,
.video-timeline-panel input {
  accent-color: #5964ff;
}

.video-player-panel small {
  color: #5f6778;
}

.video-timeline-panel header > div {
  display: flex;
  align-items: center;
  gap: 10px;
}

.video-timeline-panel button {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 8px;
  color: #3f485c;
  background: #fff;
}

.video-timeline {
  display: grid;
  grid-template-columns: 126px repeat(5, minmax(0, 1fr));
  border: 1px solid #edf1f7;
  border-radius: 8px;
  overflow: hidden;
}

.video-timeline > span {
  min-height: 34px;
  display: grid;
  place-items: center;
  color: #5f6778;
  border-bottom: 1px solid #edf1f7;
}

.video-timeline > span:first-child {
  grid-column: 2;
}

.track-label {
  min-height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-top: 1px solid #edf1f7;
  padding: 0 16px;
  color: #273044;
  font-weight: 800;
}

.track {
  grid-column: 2 / -1;
  min-height: 56px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-top: 1px solid #edf1f7;
  padding: 8px;
}

.video-track button,
.subtitle-track span {
  min-width: 132px;
  height: 38px;
  border: 1px solid #d7cdfd;
  border-radius: 8px;
  color: #4f3fb8;
  background: #f1edff;
  font: inherit;
}

.video-track button.active {
  border-color: #5964ff;
  box-shadow: 0 0 0 2px rgba(89, 100, 255, 0.12);
}

.video-track small {
  display: block;
}

.audio-track,
.music-track {
  min-height: 50px;
  background:
    repeating-linear-gradient(90deg, rgba(31, 188, 125, 0.35) 0 2px, transparent 2px 7px),
    linear-gradient(180deg, #f1fbf5, #ffffff);
}

.music-track {
  background:
    repeating-linear-gradient(90deg, rgba(111, 174, 255, 0.25) 0 2px, transparent 2px 7px),
    linear-gradient(180deg, #f2f8ff, #ffffff);
}

.subtitle-track span {
  display: inline-grid;
  place-items: center;
  min-width: 150px;
  padding: 0 10px;
  overflow: hidden;
  color: #7a4c18;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: #fff3df;
  border-color: #f3d6a8;
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

.video-export-button,
.video-download-button {
  width: 100%;
}

@media (max-width: 1180px) {
  .video-composer-grid,
  .video-edit-grid {
    grid-template-columns: 1fr;
  }

  .video-storyboard-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { Download, PauseCircle, PlayCircle, RefreshCw, Send, UploadCloud } from 'lucide-vue-next';
import { createAudioTask, fetchAudioTasks, uploadAudio } from '../services/api';
import { getIcon } from '../services/icons';
import {
  buildAudioTaskPayload,
  getAudioSection,
  type AudioTask,
  type PortalItem,
  type PortalPageConfig
} from '../services/viewModel';

const props = defineProps<{
  pageConfig: PortalPageConfig;
}>();

const emit = defineEmits<{
  openItem: [item: PortalItem];
}>();

const promptText = ref('欢迎使用 AI 音频工作台，让声音创作更简单高效！');
const selectedTool = ref<PortalItem | null>(null);
const selectedVoice = ref<PortalItem | null>(null);
const activeVoiceCategory = ref('全部');
const playingId = ref('');
const tasks = ref<AudioTask[]>([]);
const notice = ref('');
const isSubmitting = ref(false);
const isLoadingTasks = ref(false);
const sourceUrl = ref('');

const workbenchSection = computed(() => getAudioSection(props.pageConfig, 'audio-workbench'));
const statsSection = computed(() => getAudioSection(props.pageConfig, 'audio-stats'));
const toolsSection = computed(() => getAudioSection(props.pageConfig, 'audio-tools'));
const voicesSection = computed(() => getAudioSection(props.pageConfig, 'audio-voices'));
const tableSection = computed(() => getAudioSection(props.pageConfig, 'audio-table'));
const queueSection = computed(() => getAudioSection(props.pageConfig, 'audio-queue'));
const resourcesSection = computed(() => getAudioSection(props.pageConfig, 'audio-resources'));
const guidesSection = computed(() => getAudioSection(props.pageConfig, 'audio-guides'));

const audioTools = computed(() => toolsSection.value?.items ?? []);
const voiceItems = computed(() => voicesSection.value?.items ?? []);
const voiceCategories = computed(() => ['全部', ...Array.from(new Set(voiceItems.value.map((voice) => voice.category).filter(Boolean)))]);
const visibleVoices = computed(() =>
  activeVoiceCategory.value === '全部'
    ? voiceItems.value
    : voiceItems.value.filter((voice) => voice.category === activeVoiceCategory.value)
);
const recentRows = computed(() => {
  if (tasks.value.length > 0) {
    return tasks.value.slice(0, 5).map(taskToRow);
  }
  return (tableSection.value?.items ?? []).map(itemToRow);
});
const queueRows = computed(() => {
  if (tasks.value.length > 0) {
    return tasks.value.slice(0, 5).map(taskToQueueRow);
  }
  return (queueSection.value?.items ?? []).map(itemToQueueRow);
});

watch(
  () => props.pageConfig,
  () => selectDefaults(),
  { immediate: true }
);

onMounted(loadTasks);

function selectDefaults() {
  selectedTool.value = selectedTool.value ?? audioTools.value[0] ?? workbenchSection.value?.items[0] ?? null;
  selectedVoice.value = selectedVoice.value ?? voiceItems.value[0] ?? null;
}

function selectTool(tool: PortalItem) {
  selectedTool.value = tool;
  emit('openItem', tool);
}

function selectVoice(voice: PortalItem) {
  selectedVoice.value = voice;
}

async function submitAudioTask() {
  if (!selectedTool.value || !promptText.value.trim()) {
    notice.value = '请先选择工具并输入要生成的内容。';
    return;
  }
  isSubmitting.value = true;
  notice.value = '';
  try {
    const task = await createAudioTask(buildAudioTaskPayload(selectedTool.value, promptText.value.trim(), selectedVoice.value ?? undefined, sourceUrl.value));
    tasks.value = [task, ...tasks.value.filter((existing) => existing.id !== task.id)];
    notice.value = task.status === 'SUCCESS' ? '音频任务已完成，可在最近音频中查看。' : '音频任务已提交。';
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '音频任务提交失败';
  } finally {
    isSubmitting.value = false;
  }
}

async function loadTasks() {
  isLoadingTasks.value = true;
  try {
    tasks.value = await fetchAudioTasks();
  } finally {
    isLoadingTasks.value = false;
  }
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
    notice.value = '音频素材已上传，可用于转写、降噪或剪辑任务。';
  } catch (error) {
    notice.value = error instanceof Error ? error.message : '音频上传失败';
  } finally {
    input.value = '';
  }
}

function togglePlay(rowId: string) {
  playingId.value = playingId.value === rowId ? '' : rowId;
}

function taskToRow(task: AudioTask) {
  return {
    id: task.id,
    title: task.prompt.slice(0, 18) || task.taskType,
    type: task.taskType,
    duration: task.status === 'SUCCESS' ? '已生成' : statusLabel(task.status),
    voice: task.routeKey,
    createdAt: shortDate(task.createdAt),
    status: statusLabel(task.status),
    progress: progressForStatus(task.status),
    resultUrl: task.resultUrl ?? ''
  };
}

function itemToRow(item: PortalItem) {
  const [duration = '--', voice = item.category] = item.subtitle.split(' · ');
  return {
    id: item.id,
    title: item.title,
    type: item.itemType,
    duration,
    voice,
    createdAt: '2026-05-09',
    status: item.category,
    progress: item.category === '已完成' ? 100 : progressFromText(item.subtitle),
    resultUrl: item.actionValue
  };
}

function taskToQueueRow(task: AudioTask) {
  return {
    id: task.id,
    title: task.prompt.slice(0, 14) || task.taskType,
    time: task.status === 'SUCCESS' ? '已完成' : statusLabel(task.status),
    status: statusLabel(task.status),
    progress: progressForStatus(task.status),
    icon: task.status === 'SUCCESS' ? 'Headphones' : 'AudioWaveform'
  };
}

function itemToQueueRow(item: PortalItem) {
  return {
    id: item.id,
    title: item.title,
    time: item.subtitle.split(' · ')[0] ?? '--',
    status: item.category,
    progress: progressFromText(item.subtitle),
    icon: item.icon
  };
}

function progressFromText(text: string): number {
  const match = text.match(/(\d+)%/);
  return match ? Number(match[1]) : 0;
}

function progressForStatus(status: string): number {
  if (status === 'SUCCESS') {
    return 100;
  }
  if (status === 'PROCESSING') {
    return 65;
  }
  if (status === 'FAILED') {
    return 100;
  }
  return 12;
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    PENDING: '排队中',
    PROCESSING: '处理中',
    SUCCESS: '已完成',
    FAILED: '失败'
  };
  return labels[status] ?? status;
}

function shortDate(value?: string | null): string {
  if (!value) {
    return '刚刚';
  }
  return value.slice(0, 10);
}
</script>

<template>
  <section class="audio-page">
    <div class="audio-layout">
      <div class="audio-main">
        <header class="audio-head">
          <div>
            <h1>{{ pageConfig.page.title }}</h1>
            <p>{{ pageConfig.page.subtitle }}</p>
          </div>
          <button class="audio-primary-action" :disabled="isSubmitting" @click="submitAudioTask">
            <Send :size="18" />{{ isSubmitting ? '生成中' : '新建音频项目' }}
          </button>
        </header>

        <section class="audio-workbench">
          <div class="audio-generator-copy">
            <strong>{{ selectedTool?.title || '文本转语音' }}</strong>
            <span>{{ selectedTool?.subtitle || '输入文字，选择音色与情感，一键生成自然流畅的语音。' }}</span>
            <button @click="submitAudioTask">立即生成</button>
          </div>
          <div class="audio-wave-panel">
            <div class="audio-prompt-line">
              <span>{{ promptText }}</span>
              <small>{{ promptText.length }}/200</small>
            </div>
            <div class="waveform" aria-hidden="true">
              <span v-for="index in 72" :key="index" :style="{ height: `${18 + ((index * 17) % 42)}px` }"></span>
            </div>
            <div class="audio-control-row">
              <button class="audio-play" @click="togglePlay('workbench')">
                <PauseCircle v-if="playingId === 'workbench'" :size="24" />
                <PlayCircle v-else :size="24" />
              </button>
              <small>00:00 / 00:18</small>
              <select v-model="selectedVoice">
                <option v-for="voice in voiceItems" :key="voice.id" :value="voice">{{ voice.title }}</option>
              </select>
              <label class="audio-upload">
                <UploadCloud :size="16" />上传音频
                <input type="file" accept="audio/*" @change="handleAudioUpload" />
              </label>
            </div>
            <textarea v-model="promptText" maxlength="200" rows="3" />
          </div>
        </section>

        <p v-if="notice" class="audio-notice">{{ notice }}</p>

        <section class="audio-stats">
          <article v-for="stat in statsSection?.items ?? []" :key="stat.id">
            <span>{{ stat.title }}</span>
            <strong>{{ stat.subtitle }}</strong>
            <small>{{ stat.category }}</small>
          </article>
        </section>

        <section class="audio-module">
          <div class="audio-section-title">
            <h2>{{ toolsSection?.title || '音频工具中心' }}</h2>
          </div>
          <div class="audio-tools-grid">
            <button
              v-for="tool in audioTools"
              :key="tool.id"
              :class="{ active: selectedTool?.id === tool.id }"
              @click="selectTool(tool)"
            >
              <span><component :is="getIcon(tool.icon)" :size="28" /></span>
              <strong>{{ tool.title }}</strong>
              <small>{{ tool.subtitle }}</small>
              <em>立即使用</em>
            </button>
          </div>
        </section>

        <section class="audio-module">
          <div class="audio-section-title">
            <h2>{{ voicesSection?.title || '音色库' }}</h2>
            <div class="voice-tabs">
              <button
                v-for="category in voiceCategories"
                :key="category"
                :class="{ active: activeVoiceCategory === category }"
                @click="activeVoiceCategory = category"
              >
                {{ category }}
              </button>
            </div>
          </div>
          <div class="voice-strip">
            <button
              v-for="voice in visibleVoices"
              :key="voice.id"
              :class="{ active: selectedVoice?.id === voice.id }"
              @click="selectVoice(voice)"
            >
              <span><component :is="getIcon(voice.icon)" :size="24" /></span>
              <strong>{{ voice.title }}</strong>
              <small>{{ voice.subtitle }}</small>
              <PlayCircle :size="18" />
            </button>
          </div>
        </section>

        <section class="audio-module audio-table-card">
          <div class="audio-section-title">
            <h2>{{ tableSection?.title || '最近音频' }}</h2>
            <button class="audio-link" @click="loadTasks"><RefreshCw :size="15" />{{ isLoadingTasks ? '刷新中' : '刷新' }}</button>
          </div>
          <div class="audio-table">
            <div class="audio-table-head">
              <span>项目名称</span><span>类型</span><span>时长</span><span>音色 / 声源</span><span>状态</span><span>操作</span>
            </div>
            <div v-for="row in recentRows" :key="row.id" class="audio-table-row">
              <strong>{{ row.title }}</strong>
              <span>{{ row.type }}</span>
              <span>{{ row.duration }}</span>
              <span>{{ row.voice }}</span>
              <span class="audio-status">
                <i :class="row.status"></i>{{ row.status }}
              </span>
              <span class="audio-row-actions">
                <button @click="togglePlay(row.id)">播放</button>
                <a v-if="row.resultUrl" :href="row.resultUrl" target="_blank" rel="noreferrer"><Download :size="15" />下载</a>
              </span>
            </div>
          </div>
        </section>
      </div>

      <aside class="audio-side">
        <section class="audio-side-box">
          <header>
            <strong>{{ queueSection?.title || '音频任务队列' }}</strong>
            <button @click="loadTasks">全部任务</button>
          </header>
          <div class="audio-queue-list">
            <article v-for="row in queueRows" :key="row.id">
              <span><component :is="getIcon(row.icon)" :size="22" /></span>
              <div>
                <strong>{{ row.title }}</strong>
                <i><b :style="{ width: `${row.progress}%` }"></b></i>
              </div>
              <small>{{ row.time }}</small>
              <em>{{ row.status }}</em>
            </article>
          </div>
        </section>

        <section class="audio-side-box">
          <header><strong>{{ resourcesSection?.title || '音频资源库' }}</strong></header>
          <button v-for="resource in resourcesSection?.items ?? []" :key="resource.id" class="audio-resource-row">
            <component :is="getIcon(resource.icon)" :size="18" />
            <strong>{{ resource.title }}</strong>
            <span>{{ resource.subtitle }}</span>
          </button>
        </section>

        <section class="audio-side-box">
          <header><strong>{{ guidesSection?.title || '音频创作指南' }}</strong></header>
          <button v-for="guide in guidesSection?.items ?? []" :key="guide.id" class="audio-guide-row">
            <component :is="getIcon(guide.icon)" :size="18" />
            <strong>{{ guide.title }}</strong>
            <span>查看</span>
          </button>
        </section>
      </aside>
    </div>
  </section>
</template>

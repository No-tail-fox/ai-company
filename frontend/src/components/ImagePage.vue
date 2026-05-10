<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import {
  Download,
  Expand,
  Folder,
  Grid3X3,
  Heart,
  Image as ImageIcon,
  List,
  Plus,
  Search,
  Settings,
  Sparkles,
  UploadCloud,
  WandSparkles
} from 'lucide-vue-next';
import { createImageGeneration, fetchImageWorkbench } from '../services/api';
import {
  createFallbackImageWorkbench,
  getImageStatusMeta,
  loadWorkbenchDraft,
  saveWorkbenchDraft,
  type ImageTask,
  type ImageWorkbench
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

const workbench = ref<ImageWorkbench>(createFallbackImageWorkbench());
const draft = ref<ImageDraft>(loadWorkbenchDraft(DRAFT_KEY, defaultDraft));
const isCreating = ref(false);
const createError = ref('');
const activeHistoryId = ref('history-city');
const viewMode = ref<'grid' | 'list'>('grid');

const modelOptions = ['通用绘图', '商品摄影', '海报设计', '国风插画'];
const sizeOptions = ['1024 x 1024', '1344 x 768', '768 x 1344', '1536 x 1024'];
const ratioOptions = ['1:1', '3:4', '4:3', '16:9', '9:16'];
const styleOptions = ['写实', '插画', '国风', '赛博', '极简', '3D', '产品图', '海报'];

const historyRows = computed(() => {
  const taskRows = workbench.value.tasks.slice(0, 4).map((task) => ({
    id: task.id,
    title: compact(task.prompt, 14),
    time: formatTime(task.createdAt),
    group: '今天'
  }));
  return [
    ...taskRows,
    { id: 'history-city', title: '霓虹城市夜景', time: '14:35', group: '今天' },
    { id: 'history-product', title: '极简产品海报', time: '11:20', group: '今天' },
    { id: 'history-toy', title: '毛绒玩具电商图', time: '09:47', group: '今天' },
    { id: 'history-landscape', title: '中国风山水', time: '昨天 16:42', group: '昨天' },
    { id: 'history-room', title: '现代客厅室内设计', time: '昨天 10:18', group: '昨天' },
    { id: 'history-earphone', title: '科技感耳机渲染', time: '周二 15:30', group: '本周' },
    { id: 'history-shoes', title: '运动鞋产品图', time: '周二 11:05', group: '本周' },
    { id: 'history-cafe', title: '咖啡店海报设计', time: '周一 18:22', group: '本周' }
  ];
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
    .filter((task) => task.resultUrl)
    .slice(0, 2)
    .map((task, index) => ({
      id: task.id,
      title: compact(task.prompt, 18),
      label: `方案 ${String.fromCharCode(65 + index)}`,
      url: task.resultUrl,
      accent: index % 2 === 0 ? 'city' : 'moon',
      featured: index === 0
    }));
  return [
    ...successfulTasks,
    { id: 'preview-a', title: '霓虹城市夜景', label: '方案 A', accent: 'city', featured: successfulTasks.length === 0 },
    { id: 'preview-b', title: '雨夜街道', label: '方案 B', accent: 'street' },
    { id: 'preview-c', title: '月色天际线', label: '方案 C', accent: 'moon' },
    { id: 'preview-d', title: '窄巷霓虹', label: '方案 D', accent: 'alley' },
    { id: 'preview-e', title: '跑车街景', label: '方案 E', accent: 'car' }
  ].slice(0, 5);
});

const queueRows = computed(() => {
  const taskRows = workbench.value.tasks.slice(0, 4).map((task, index) => ({
    id: task.id,
    title: `图像生成 #${1024 - index}`,
    subtitle: compact(task.prompt, 10),
    status: statusMeta(task.status).label,
    tone: statusMeta(task.status).tone,
    time: task.status === 'PENDING' ? '刚刚' : formatTime(task.createdAt),
    progress: statusMeta(task.status).progress
  }));
  return taskRows.length > 0
    ? taskRows
    : [
        { id: 'queue-1', title: '图像生成 #1024', subtitle: '霓虹城市夜景', status: '排队中', tone: 'pending', time: '刚刚', progress: 12 },
        { id: 'queue-2', title: '图像生成 #1023', subtitle: '极简产品海报', status: '生成中', tone: 'processing', time: '2 分钟前', progress: 65 },
        { id: 'queue-3', title: '图像生成 #1022', subtitle: '毛绒玩具电商图', status: '已完成', tone: 'success', time: '8 分钟前', progress: 100 }
      ];
});

const recentRuns = computed(() =>
  historyRows.value.slice(3, 8).map((row, index) => ({
    ...row,
    icon: index % 3 === 0 ? 'MessageCircle' : index % 3 === 1 ? 'Image' : 'Headphones'
  }))
);

watch(
  draft,
  (value) => saveWorkbenchDraft(DRAFT_KEY, value),
  { deep: true }
);

onMounted(loadWorkbench);

async function loadWorkbench() {
  workbench.value = await fetchImageWorkbench(SURFACE);
}

async function createFromPrompt() {
  const prompt = draft.value.prompt.trim();
  if (!prompt) {
    createError.value = '请输入图像提示词';
    return;
  }
  isCreating.value = true;
  createError.value = '';
  try {
    const enrichedPrompt = `${prompt}；模型：${draft.value.model}；尺寸：${draft.value.size}；比例：${draft.value.ratio}；风格：${draft.value.style}`;
    const created = await createImageGeneration(enrichedPrompt, {
      targetType: 'builtin',
      targetId: 'image_text_to_image',
      routeKey: 'image_text_to_image',
      surface: SURFACE
    });
    const refreshed = await fetchImageWorkbench(SURFACE);
    if (!refreshed.tasks.some((task) => task.id === created.id)) {
      refreshed.tasks = [created, ...refreshed.tasks];
    }
    workbench.value = refreshed;
    activeHistoryId.value = created.id;
  } catch (error) {
    createError.value = error instanceof Error ? error.message : '图像任务创建失败';
  } finally {
    isCreating.value = false;
  }
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
    <template #headerActions>
      <button class="workspace-icon-action" aria-label="素材库" title="素材库">
        <Folder :size="20" />
      </button>
      <button class="workspace-icon-action" aria-label="设置" title="设置">
        <Settings :size="20" />
      </button>
    </template>

    <template #leftFooter>
      <div class="wb-left-selects">
        <label>
          <span>角色：</span>
          <select>
            <option>通用助手</option>
            <option>品牌设计师</option>
          </select>
        </label>
        <label>
          <span>模型：</span>
          <select>
            <option>GPT-4.1</option>
            <option>GPT Image</option>
          </select>
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
                <input placeholder="搜索提示词..." />
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
            <button class="wb-link-button" type="button">
              查看全部记录
              <List :size="16" />
            </button>
          </aside>

          <section class="wb-preview-panel">
            <header>
              <h2>生成预览</h2>
              <div class="wb-view-toggle">
                <button :class="{ active: viewMode === 'grid' }" type="button" aria-label="宫格视图" @click="viewMode = 'grid'">
                  <Grid3X3 :size="18" />
                </button>
                <button :class="{ active: viewMode === 'list' }" type="button" aria-label="列表视图" @click="viewMode = 'list'">
                  <List :size="18" />
                </button>
              </div>
            </header>
            <div class="wb-preview-grid">
              <article
                v-for="card in previewCards"
                :key="card.id"
                :class="['wb-preview-card', card.accent, { featured: card.featured }]"
              >
                <img v-if="card.url" :src="card.url" :alt="card.title" />
                <div v-else class="wb-generated-scene" aria-hidden="true">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <footer>
                  <strong>{{ card.label }}</strong>
                  <button type="button" aria-label="收藏"><Heart :size="18" /></button>
                  <button type="button" aria-label="下载"><Download :size="18" /></button>
                  <button type="button" aria-label="放大"><Expand :size="18" /></button>
                </footer>
              </article>
            </div>
          </section>
        </div>

        <section class="wb-reference-panel">
          <header>
            <h2>参考图（可选）</h2>
          </header>
          <div class="wb-reference-list">
            <div class="wb-reference-thumb city">
              <button type="button" aria-label="移除参考图">×</button>
            </div>
            <button v-for="index in 3" :key="index" class="wb-reference-add" type="button">
              <Plus :size="20" />
            </button>
          </div>
        </section>

        <section class="wb-prompt-composer">
          <label>
            <span>提示词</span>
            <textarea v-model="draft.prompt" maxlength="1000" placeholder="描述你想生成的画面、光线、材质与风格..." />
            <small>{{ draft.prompt.length }} / 1000</small>
          </label>
          <button class="wb-generate-button" :disabled="isCreating" type="button" @click="createFromPrompt">
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
          <button type="button"><Plus :size="24" />新建图像</button>
          <button type="button"><UploadCloud :size="24" />导入参考</button>
          <button type="button"><Download :size="24" />下载结果</button>
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
.wb-reference-panel,
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

.wb-image {
  display: grid;
  gap: 18px;
}

.wb-image-config,
.wb-history-panel,
.wb-preview-panel,
.wb-reference-panel,
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
.wb-view-toggle button,
.wb-link-button,
.wb-reference-add,
.wb-task-row button,
.wb-quick-grid button,
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
.wb-style-group button.active,
.wb-view-toggle button.active {
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
.wb-reference-panel,
.wb-side-panel {
  padding: 18px;
}

.wb-history-panel h2,
.wb-preview-panel h2,
.wb-reference-panel h2,
.wb-side-panel h2 {
  margin: 0;
  color: #111827;
  font-size: 20px;
  line-height: 1.2;
}

.wb-history-panel header,
.wb-preview-panel header,
.wb-reference-panel header,
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

.wb-view-toggle {
  display: flex;
  gap: 6px;
}

.wb-view-toggle button {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
}

.wb-preview-grid {
  display: grid;
  grid-template-columns: minmax(280px, 1.35fr) repeat(2, minmax(150px, 0.65fr));
  gap: 16px;
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

.wb-preview-card img,
.wb-generated-scene {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.wb-generated-scene {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(9, 22, 58, 0.2), rgba(5, 11, 28, 0.55)),
    linear-gradient(135deg, #061833, #0f5e9c 42%, #fd3fa4 80%, #121a3d);
}

.wb-preview-card.street .wb-generated-scene {
  background:
    linear-gradient(180deg, rgba(9, 22, 58, 0.12), rgba(5, 11, 28, 0.55)),
    linear-gradient(135deg, #153456, #1676b9 42%, #ff4e8f 78%, #111827);
}

.wb-preview-card.moon .wb-generated-scene {
  background:
    radial-gradient(circle at 72% 24%, #f8fbff 0 22px, transparent 23px),
    linear-gradient(160deg, #10294a, #081426 62%, #07111f);
}

.wb-preview-card.alley .wb-generated-scene {
  background: linear-gradient(135deg, #08233e, #065d7c 38%, #8a2df4 72%, #101827);
}

.wb-preview-card.car .wb-generated-scene {
  background: linear-gradient(135deg, #081525, #0e4f87 42%, #df2f84 78%, #090e19);
}

.wb-generated-scene span {
  position: absolute;
  bottom: 0;
  width: 16%;
  border-radius: 8px 8px 0 0;
  background: rgba(4, 12, 30, 0.68);
  box-shadow: inset 0 18px 0 rgba(255, 255, 255, 0.08);
}

.wb-generated-scene span:nth-child(1) {
  left: 8%;
  height: 72%;
}

.wb-generated-scene span:nth-child(2) {
  left: 35%;
  height: 92%;
}

.wb-generated-scene span:nth-child(3) {
  right: 12%;
  height: 62%;
}

.wb-preview-card footer {
  display: grid;
  grid-template-columns: 1fr repeat(3, 34px);
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  color: #6b7280;
}

.wb-preview-card footer button {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 8px;
  color: #5f6778;
  background: transparent;
}

.wb-reference-panel {
  display: grid;
}

.wb-reference-list {
  display: flex;
  gap: 18px;
  align-items: center;
}

.wb-reference-thumb,
.wb-reference-add {
  width: 92px;
  height: 92px;
  border-radius: 8px;
}

.wb-reference-thumb {
  position: relative;
  background: linear-gradient(135deg, #08233e, #0e6eb0 48%, #ca2cff);
}

.wb-reference-thumb button {
  position: absolute;
  right: -8px;
  top: -8px;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 50%;
  color: #fff;
  background: #1f2937;
}

.wb-reference-add {
  display: grid;
  place-items: center;
  border-style: dashed;
  color: #667085;
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

.wb-quick-grid button {
  min-height: 92px;
  display: grid;
  place-items: center;
  gap: 8px;
  color: #5264ff;
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

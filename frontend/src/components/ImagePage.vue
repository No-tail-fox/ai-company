<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { createImageGeneration, fetchImageWorkbench } from '../services/api';
import { getIcon } from '../services/icons';
import {
  createFallbackImageWorkbench,
  getImageStatusMeta,
  type ImageTask,
  type ImageWorkbench
} from '../services/viewModel';

interface ImageAction {
  title: string;
  subtitle: string;
  icon: string;
  prompt: string;
}

interface ImageTemplate {
  title: string;
  category: string;
  ratio: string;
  badge?: string;
  prompt: string;
}

interface ProjectRow {
  id: string;
  name: string;
  type: string;
  size: string;
  ratio: string;
  updatedAt: string;
  status: string;
}

const workbench = ref<ImageWorkbench>(createFallbackImageWorkbench());
const promptText = ref('请生成一张夏季新品推广海报，画面清爽高级，突出产品质感，适合社媒和电商投放。');
const activeStyle = ref('商业海报');
const activeRatio = ref('1:1');
const isCreating = ref(false);
const createError = ref('');

const styleOptions = ['商业海报', '写实摄影', '国潮插画', '3D质感', '极简高级'];
const ratioOptions = ['1:1', '4:3', '16:9', '3:4'];

const actions: ImageAction[] = [
  { title: '商品图生成', subtitle: '电商主图、场景图和细节图', icon: 'Gift', prompt: '请生成一张电商商品主图，白色背景，突出产品质感、核心卖点和高级光影。' },
  { title: '人像写真', subtitle: '头像、证件照和风格写真', icon: 'UserRound', prompt: '请生成一张自然光人像写真，干净背景，专业但亲和，适合个人品牌头像。' },
  { title: '风格迁移', subtitle: '参考风格快速统一视觉', icon: 'WandSparkles', prompt: '请生成一组统一品牌风格的社媒配图，柔和渐变、清晰主体、视觉一致。' },
  { title: '智能抠图', subtitle: '主体分离、换背景和透明图', icon: 'ScanSearch', prompt: '请生成一个产品主体清晰、边缘干净、适合后续抠图换背景的商品图。' },
  { title: '电商海报', subtitle: '促销活动和详情页素材', icon: 'Megaphone', prompt: '请生成一张618电商促销海报，红橙氛围，突出限时优惠和产品卖点。' },
  { title: '批量出图', subtitle: '多尺寸多风格批量生成', icon: 'LayoutGrid', prompt: '请为同一产品生成三种投放素材方向：高级质感、节日促销、生活方式场景。' }
];

const templates: ImageTemplate[] = [
  { title: '产品海报', category: '产品宣传', ratio: '1:1', prompt: '请生成一张产品宣传海报，突出品牌感、产品质感和简洁卖点。' },
  { title: '社媒配图', category: '社媒运营', ratio: '4:3', badge: 'NEW', prompt: '请生成一张小红书风格社媒配图，清新明亮，适合种草笔记封面。' },
  { title: '电商主图', category: '电商素材', ratio: '1:1', prompt: '请生成一张电商主图，干净背景、产品居中、卖点视觉明确。' },
  { title: '头像写真', category: '人像写真', ratio: '3:4', prompt: '请生成一张专业头像写真，柔和光线，背景简洁，适合个人主页。' },
  { title: '节日营销', category: '节日热点', ratio: '16:9', prompt: '请生成一张节日营销视觉图，喜庆但高级，适合活动横幅。' },
  { title: '室内设计', category: '空间方案', ratio: '16:9', prompt: '请生成一张现代室内设计效果图，温暖灯光、简洁高级、空间层次清晰。' }
];

const tips = [
  { icon: 'FileText', title: '描述越具体，图像越稳定', text: '建议写清主体、场景、光线和用途。' },
  { icon: 'LayoutGrid', title: '先选比例再写提示词', text: '头像、主图、横幅适合不同画幅。' },
  { icon: 'Sparkles', title: '保留品牌关键词', text: '统一色彩、材质和构图能形成系列感。' }
];

const recentProjects = computed<ProjectRow[]>(() => {
  const fromTasks = workbench.value.tasks.map((task) => ({
    id: task.id,
    name: task.prompt,
    type: task.routeKey === 'image_text_to_image' ? '文生图' : task.routeKey,
    size: task.status === 'SUCCESS' ? '2048px' : '--',
    ratio: activeRatio.value,
    updatedAt: formatDateTime(task.createdAt),
    status: task.status
  }));
  const fallbackRows: ProjectRow[] = [
    { id: 'image-project-a', name: '夏季新品推广海报', type: '商品海报', size: '2048px', ratio: '1:1', updatedAt: '2026-05-09 14:30', status: 'PROCESSING' },
    { id: 'image-project-b', name: '企业品牌宣传配图', type: '品牌视觉', size: '1920px', ratio: '16:9', updatedAt: '2026-05-09 11:22', status: 'SUCCESS' },
    { id: 'image-project-c', name: '知识科普：AI入门指南', type: '封面图', size: '1080px', ratio: '4:3', updatedAt: '2026-05-08 18:05', status: 'SUCCESS' },
    { id: 'image-project-d', name: '618促销电商主图', type: '电商主图', size: '--', ratio: '1:1', updatedAt: '2026-05-08 09:40', status: 'PENDING' }
  ];
  return [...fromTasks, ...fallbackRows].slice(0, 5);
});

const queueTasks = computed(() => workbench.value.tasks.slice(0, 5));
const walletLabel = computed(() => `${workbench.value.wallet.balance.toLocaleString()} 积分`);
const frozenLabel = computed(() => `${workbench.value.wallet.frozenBalance.toLocaleString()} 冻结`);

onMounted(async () => {
  workbench.value = await fetchImageWorkbench();
});

async function createFromPrompt(prompt = promptText.value) {
  const cleaned = prompt.trim();
  if (!cleaned) {
    createError.value = '请输入图片创作需求';
    return;
  }
  isCreating.value = true;
  createError.value = '';
  try {
    const enrichedPrompt = `${cleaned}；风格：${activeStyle.value}；比例：${activeRatio.value}`;
    const created = await createImageGeneration(enrichedPrompt);
    const refreshed = await fetchImageWorkbench();
    if (!refreshed.tasks.some((task) => task.id === created.id)) {
      refreshed.tasks = [created, ...refreshed.tasks];
    }
    workbench.value = refreshed;
    promptText.value = cleaned;
  } catch (error) {
    createError.value = error instanceof Error ? error.message : '创建图片任务失败';
  } finally {
    isCreating.value = false;
  }
}

function useAction(action: ImageAction) {
  promptText.value = action.prompt;
  createFromPrompt(action.prompt);
}

function useTemplate(template: ImageTemplate) {
  promptText.value = template.prompt;
  activeRatio.value = template.ratio;
  activeStyle.value = template.category;
  createFromPrompt(template.prompt);
}

function statusMeta(status: string) {
  return getImageStatusMeta(status);
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return '刚刚';
  }
  return value.replace('T', ' ').slice(0, 16);
}

function compactPrompt(task: ImageTask) {
  return task.prompt.length > 15 ? `${task.prompt.slice(0, 15)}...` : task.prompt;
}
</script>

<template>
  <section class="image-page">
    <div class="image-layout">
      <div class="image-main">
        <header class="image-head">
          <div>
            <h1>AI图片创作中心</h1>
            <p>提示词、模板、批量出图和生成队列，一站式完成图片素材生产</p>
          </div>
          <button class="image-create-btn" :disabled="isCreating" @click="createFromPrompt()">
            <component :is="getIcon('Sparkles')" :size="18" />
            {{ isCreating ? '创建中' : '立即创作' }}
          </button>
        </header>

        <section class="image-creation-grid">
          <article class="image-primary-tool">
            <div class="image-tool-copy">
              <h2>一句话生成图片</h2>
              <p>输入画面需求，选择风格与比例，自动进入图片生成队列。</p>
              <textarea v-model="promptText" rows="4" aria-label="图片创作需求"></textarea>
              <div class="image-option-row">
                <span>风格</span>
                <button v-for="style in styleOptions" :key="style" :class="{ active: activeStyle === style }" @click="activeStyle = style">
                  {{ style }}
                </button>
              </div>
              <div class="image-option-row">
                <span>比例</span>
                <button v-for="ratio in ratioOptions" :key="ratio" :class="{ active: activeRatio === ratio }" @click="activeRatio = ratio">
                  {{ ratio }}
                </button>
              </div>
              <button class="image-submit" :disabled="isCreating" @click="createFromPrompt()">
                去创作
                <component :is="getIcon('Sparkles')" :size="17" />
              </button>
              <span v-if="createError" class="image-error">{{ createError }}</span>
            </div>
            <div class="image-preview-card" aria-hidden="true">
              <div class="image-preview-window">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div class="image-preview-scene">
                <div class="image-sun"></div>
                <div class="image-mountain left"></div>
                <div class="image-mountain right"></div>
                <div class="image-product">
                  <component :is="getIcon('Image')" :size="34" />
                </div>
              </div>
              <div class="image-prompt-chip">高清商业海报</div>
              <div class="image-swatch-row">
                <span></span><span></span><span></span><span></span>
              </div>
            </div>
          </article>

          <button v-for="action in actions" :key="action.title" class="image-action-card" @click="useAction(action)">
            <span><component :is="getIcon(action.icon)" :size="30" /></span>
            <strong>{{ action.title }}</strong>
            <p>{{ action.subtitle }}</p>
          </button>
        </section>

        <section class="image-panel">
          <div class="image-section-title">
            <div>
              <h2>图片模板库</h2>
              <nav aria-label="图片模板分类">
                <span>全部</span>
                <span>产品宣传</span>
                <span>社媒运营</span>
                <span>电商素材</span>
                <span>人像写真</span>
                <span>空间方案</span>
              </nav>
            </div>
            <button>更多模板 <component :is="getIcon('ChevronRight')" :size="18" /></button>
          </div>
          <div class="image-template-strip">
            <button v-for="template in templates" :key="template.title" class="image-template" @click="useTemplate(template)">
              <span v-if="template.badge" class="template-badge">{{ template.badge }}</span>
              <strong>{{ template.title }}</strong>
              <small>{{ template.category }}</small>
              <em>{{ template.ratio }}</em>
            </button>
          </div>
        </section>

        <section class="image-panel">
          <div class="image-section-title compact">
            <h2>最近项目</h2>
            <button>查看全部项目 <component :is="getIcon('ChevronRight')" :size="18" /></button>
          </div>
          <div class="image-project-table">
            <div class="image-project-row image-project-head">
              <span>项目名称</span>
              <span>类型</span>
              <span>尺寸</span>
              <span>比例</span>
              <span>更新于</span>
              <span>状态</span>
              <span>操作</span>
            </div>
            <div v-for="project in recentProjects" :key="project.id" class="image-project-row">
              <strong>{{ project.name }}</strong>
              <span>{{ project.type }}</span>
              <span>{{ project.size }}</span>
              <span>{{ project.ratio }}</span>
              <span>{{ project.updatedAt }}</span>
              <span :class="['image-project-status', statusMeta(project.status).tone]">
                {{ statusMeta(project.status).label }}
              </span>
              <span class="image-project-actions">查看 · 继续编辑</span>
            </div>
          </div>
        </section>
      </div>

      <aside class="image-side">
        <section class="image-side-box">
          <header>
            <strong>生成队列</strong>
            <span>{{ walletLabel }} · {{ frozenLabel }}</span>
          </header>
          <div class="image-queue-list">
            <article v-for="task in queueTasks" :key="task.id" class="image-queue-item">
              <div class="image-queue-thumb"><component :is="getIcon('Image')" :size="24" /></div>
              <div>
                <strong>{{ compactPrompt(task) }}</strong>
                <span>{{ statusMeta(task.status).label }} · {{ task.estimatedCost }} 积分</span>
                <div class="image-queue-progress">
                  <i :style="{ width: `${statusMeta(task.status).progress}%` }"></i>
                </div>
              </div>
              <em>{{ statusMeta(task.status).progress }}%</em>
            </article>
          </div>
          <p v-if="queueTasks.length === 0" class="image-queue-empty">暂无生成任务</p>
        </section>

        <section class="image-vip-panel">
          <div>
            <strong>开通会员，解锁更多AI图片特权</strong>
            <span>高清无水印导出、批量出图、商用模板和优先队列</span>
          </div>
          <button>立即开通</button>
        </section>

        <section class="image-side-box">
          <header>
            <strong>创作小贴士</strong>
            <span>更多</span>
          </header>
          <button v-for="tip in tips" :key="tip.title" class="image-tip">
            <component :is="getIcon(tip.icon)" :size="22" />
            <span>
              <strong>{{ tip.title }}</strong>
              <small>{{ tip.text }}</small>
            </span>
          </button>
        </section>
      </aside>
    </div>
  </section>
</template>

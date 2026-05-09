<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { createVideoGeneration, fetchVideoWorkbench } from '../services/api';
import { getIcon } from '../services/icons';
import {
  createFallbackVideoWorkbench,
  getVideoStatusMeta,
  type VideoTask,
  type VideoWorkbench
} from '../services/viewModel';

interface VideoAction {
  title: string;
  subtitle: string;
  icon: string;
  prompt: string;
}

interface VideoTemplate {
  title: string;
  category: string;
  duration: string;
  badge?: string;
  prompt: string;
}

const workbench = ref<VideoWorkbench>(createFallbackVideoWorkbench());
const promptText = ref('请生成一条 45 秒新品上市推广视频，包含开场钩子、产品卖点、使用场景和结尾行动号召。');
const isCreating = ref(false);
const createError = ref('');

const actions: VideoAction[] = [
  {
    title: '数字人讲解',
    subtitle: 'AI数字人，多种形象自动口播',
    icon: 'UserRound',
    prompt: '请生成一条 60 秒数字人讲解视频，主题是企业 AI 培训课程介绍。'
  },
  {
    title: '商品短视频',
    subtitle: '一键生成电商展示视频',
    icon: 'Gift',
    prompt: '请生成一条商品短视频，突出产品质感、核心卖点和限时优惠。'
  },
  {
    title: '批量剪辑',
    subtitle: '批量处理视频，高效剪辑统一风格',
    icon: 'FileVideo',
    prompt: '请把一组素材规划成 5 条同风格短视频，分别给出剪辑节奏和字幕方向。'
  },
  {
    title: '智能字幕',
    subtitle: '自动识别语音，生成精准字幕',
    icon: 'NotebookTabs',
    prompt: '请为知识讲解视频生成精准字幕和适合竖屏展示的字幕样式建议。'
  },
  {
    title: '配音换声',
    subtitle: '多种音色，情绪表达一键配置',
    icon: 'Headphones',
    prompt: '请为品牌宣传视频生成温暖自然的配音脚本，并标注语速和情绪。'
  }
];

const templates: VideoTemplate[] = [
  { title: '产品介绍', category: '产品介绍', duration: '01:02', prompt: '请生成一条产品介绍视频，结构包含痛点、方案、亮点和购买引导。' },
  { title: '新品上市推广', category: '营销推广', duration: '00:45', badge: 'NEW', prompt: '请生成一条新品上市推广短视频，适合社媒信息流投放。' },
  { title: '知识科普讲解', category: '知识讲解', duration: '01:15', prompt: '请生成一条知识科普视频，用通俗语言解释 AI 自动化。' },
  { title: '企业宣传片', category: '企业宣传', duration: '01:35', prompt: '请生成一条企业宣传片，突出团队实力、服务案例和品牌信任感。' },
  { title: '节日祝福视频', category: '节日热点', duration: '00:30', prompt: '请生成一条节日祝福视频，语气真诚、节奏轻快。' },
  { title: '生活Vlog', category: '生活娱乐', duration: '00:50', prompt: '请生成一条生活 Vlog 视频脚本，画面自然、有轻松旁白。' }
];

const tips = [
  { icon: 'FileText', title: '文案越清晰，生成效果越好', text: '建议分段描述画面、卖点和情绪。' },
  { icon: 'LayoutGrid', title: '选好模板，提升效率', text: '模板可快速匹配场景和风格。' },
  { icon: 'Sparkles', title: '配音与字幕可提升完整度', text: '注意语速、字幕层级和重点突出。' }
];

const recentProjects = computed(() => {
  const fromTasks = workbench.value.tasks.map((task) => ({
    id: task.id,
    name: task.prompt,
    type: task.routeKey === 'video_text_to_video' ? '文案生成' : task.routeKey,
    duration: task.status === 'SUCCESS' ? '00:45' : '--',
    resolution: '1080P',
    updatedAt: formatDateTime(task.createdAt),
    status: task.status
  }));
  const fallbackRows = [
    { id: 'project-demo-a', name: '夏季新品推广视频', type: '营销推广', duration: '00:45', resolution: '1080P', updatedAt: '2026-05-09 14:30', status: 'PROCESSING' },
    { id: 'project-demo-b', name: '企业介绍宣传片', type: '企业宣传', duration: '02:10', resolution: '4K', updatedAt: '2026-05-09 11:22', status: 'SUCCESS' },
    { id: 'project-demo-c', name: '知识科普：AI入门指南', type: '知识讲解', duration: '03:18', resolution: '1080P', updatedAt: '2026-05-08 18:05', status: 'SUCCESS' },
    { id: 'project-demo-d', name: '618促销带货视频', type: '电商带货', duration: '00:38', resolution: '1080P', updatedAt: '2026-05-08 09:40', status: 'PENDING' }
  ];
  return [...fromTasks, ...fallbackRows].slice(0, 4);
});

const queueTasks = computed(() => workbench.value.tasks.slice(0, 5));
const walletLabel = computed(() => `${workbench.value.wallet.balance.toLocaleString()} 积分`);
const frozenLabel = computed(() => `${workbench.value.wallet.frozenBalance.toLocaleString()} 冻结`);

onMounted(async () => {
  workbench.value = await fetchVideoWorkbench();
});

async function createFromPrompt(prompt = promptText.value) {
  const cleaned = prompt.trim();
  if (!cleaned) {
    createError.value = '请输入视频创作需求';
    return;
  }
  isCreating.value = true;
  createError.value = '';
  try {
    const created = await createVideoGeneration(cleaned);
    const refreshed = await fetchVideoWorkbench();
    if (!refreshed.tasks.some((task) => task.id === created.id)) {
      refreshed.tasks = [created, ...refreshed.tasks];
    }
    workbench.value = refreshed;
    promptText.value = cleaned;
  } catch (error) {
    createError.value = error instanceof Error ? error.message : '创建任务失败';
  } finally {
    isCreating.value = false;
  }
}

function useAction(action: VideoAction) {
  promptText.value = action.prompt;
  createFromPrompt(action.prompt);
}

function useTemplate(template: VideoTemplate) {
  promptText.value = template.prompt;
  createFromPrompt(template.prompt);
}

function statusMeta(status: string) {
  return getVideoStatusMeta(status);
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return '刚刚';
  }
  return value.replace('T', ' ').slice(0, 16);
}

function compactPrompt(task: VideoTask) {
  return task.prompt.length > 15 ? `${task.prompt.slice(0, 15)}...` : task.prompt;
}
</script>

<template>
  <section class="video-page">
    <div class="video-layout">
      <div class="video-main">
        <header class="video-head">
          <div>
            <h1>AI视频创作中心</h1>
            <p>一站式AI视频创作，轻松生成高质量视频内容</p>
          </div>
          <button class="video-create-btn" :disabled="isCreating" @click="createFromPrompt()">
            <component :is="getIcon('Sparkles')" :size="18" />
            {{ isCreating ? '创建中' : '立即创作' }}
          </button>
        </header>

        <section class="video-creation-grid">
          <article class="video-primary-tool">
            <div class="video-tool-copy">
              <h2>文案生成视频</h2>
              <p>输入文案，自动匹配画面、配音与字幕。</p>
              <textarea v-model="promptText" rows="4" aria-label="视频创作需求"></textarea>
              <button :disabled="isCreating" @click="createFromPrompt()">
                去创作
                <component :is="getIcon('Sparkles')" :size="17" />
              </button>
              <span v-if="createError" class="video-error">{{ createError }}</span>
            </div>
            <div class="video-preview-card" aria-hidden="true">
              <div class="preview-window">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div class="preview-scene">
                <div class="preview-play"><component :is="getIcon('MonitorPlay')" :size="28" /></div>
              </div>
              <div class="preview-caption">这段风景真的太美了</div>
              <div class="preview-wave"></div>
            </div>
          </article>

          <button v-for="action in actions" :key="action.title" class="video-action-card" @click="useAction(action)">
            <span><component :is="getIcon(action.icon)" :size="30" /></span>
            <strong>{{ action.title }}</strong>
            <p>{{ action.subtitle }}</p>
          </button>
        </section>

        <section class="video-panel">
          <div class="video-section-title">
            <div>
              <h2>视频模板库</h2>
              <nav aria-label="视频模板分类">
                <span>全部</span>
                <span>营销推广</span>
                <span>产品介绍</span>
                <span>知识讲解</span>
                <span>企业宣传</span>
                <span>电商带货</span>
              </nav>
            </div>
            <button>更多模板 <component :is="getIcon('ChevronRight')" :size="18" /></button>
          </div>
          <div class="video-template-strip">
            <button v-for="template in templates" :key="template.title" class="video-template" @click="useTemplate(template)">
              <span v-if="template.badge" class="template-badge">{{ template.badge }}</span>
              <strong>{{ template.title }}</strong>
              <small>{{ template.category }}</small>
              <em>{{ template.duration }}</em>
            </button>
          </div>
        </section>

        <section class="video-panel">
          <div class="video-section-title compact">
            <h2>最近项目</h2>
            <button>查看全部项目 <component :is="getIcon('ChevronRight')" :size="18" /></button>
          </div>
          <div class="video-project-table">
            <div class="project-row project-head">
              <span>项目名称</span>
              <span>类型</span>
              <span>时长</span>
              <span>分辨率</span>
              <span>更新于</span>
              <span>状态</span>
              <span>操作</span>
            </div>
            <div v-for="project in recentProjects" :key="project.id" class="project-row">
              <strong>{{ project.name }}</strong>
              <span>{{ project.type }}</span>
              <span>{{ project.duration }}</span>
              <span>{{ project.resolution }}</span>
              <span>{{ project.updatedAt }}</span>
              <span :class="['project-status', statusMeta(project.status).tone]">
                {{ statusMeta(project.status).label }}
              </span>
              <span class="project-actions">查看 · 继续编辑</span>
            </div>
          </div>
        </section>
      </div>

      <aside class="video-side">
        <section class="video-side-box">
          <header>
            <strong>渲染队列</strong>
            <span>{{ walletLabel }} · {{ frozenLabel }}</span>
          </header>
          <div class="video-queue-list">
            <article v-for="task in queueTasks" :key="task.id" class="queue-item">
              <div class="queue-thumb"><component :is="getIcon('FileVideo')" :size="24" /></div>
              <div>
                <strong>{{ compactPrompt(task) }}</strong>
                <span>{{ statusMeta(task.status).label }} · {{ task.estimatedCost }} 积分</span>
                <div class="queue-progress">
                  <i :style="{ width: `${statusMeta(task.status).progress}%` }"></i>
                </div>
              </div>
              <em>{{ statusMeta(task.status).progress }}%</em>
            </article>
          </div>
          <p v-if="queueTasks.length === 0" class="queue-empty">暂无渲染任务</p>
        </section>

        <section class="video-vip-panel">
          <div>
            <strong>开通会员，解锁更多AI视频特权</strong>
            <span>高清无水印导出、批量渲染、字幕样式和模板优先使用</span>
          </div>
          <button>立即开通</button>
        </section>

        <section class="video-side-box">
          <header>
            <strong>创作小贴士</strong>
            <span>更多</span>
          </header>
          <button v-for="tip in tips" :key="tip.title" class="video-tip">
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

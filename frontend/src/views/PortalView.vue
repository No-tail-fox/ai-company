<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  Bell,
  CloudUpload,
  Download,
  Headphones,
  Sparkles
} from 'lucide-vue-next';
import AssistantPage from '../components/AssistantPage.vue';
import HomeDashboardPage from '../components/HomeDashboardPage.vue';
import DynamicPage from '../components/DynamicPage.vue';
import MarketingPage from '../components/MarketingPage.vue';
import TextWorkbenchPage from '../components/TextWorkbenchPage.vue';
import {
  fetchAssistantCenter,
  fetchHomeDashboard,
  fetchPortalConfig,
  fetchPortalPage,
  fetchPortalUserActions,
  runPortalAction
} from '../services/api';
import { getIcon } from '../services/icons';
import {
  buildHomeDashboardModel,
  createFallbackHomeDashboard,
  createFallbackAssistantCenter,
  createFallbackPageConfig,
  createFallbackPortalConfig,
  createHomeMenuPageConfig,
  getHomeMenuHint,
  shouldHideWorkspaceDock,
  shouldUseAssistantPage,
  shouldUseCodingPage,
  shouldUseHomeDashboardPage,
  shouldUseMarketingPage,
  shouldUseWritingPage,
  shouldShowHomeSidebar,
  type HomeDashboardModel,
  type AssistantCard,
  type AssistantCenter,
  type PromptTemplate,
  type PortalConfig,
  type PortalItem,
  type PortalPageConfig,
  type UserPortalAction
} from '../services/viewModel';

const route = useRoute();
const router = useRouter();
const portal = ref<PortalConfig>(createFallbackPortalConfig());
const pageConfig = ref<PortalPageConfig>(createFallbackPageConfig(String(route.params.pageKey || 'home')));
const homeDashboard = ref<HomeDashboardModel>(createFallbackHomeDashboard(pageConfig.value));
const assistantCenter = ref<AssistantCenter>(createFallbackAssistantCenter());
const activeHomeMenuKey = ref('basic');
const selectedTool = ref('');
const promptText = ref('');
const backupEnabled = ref(false);
const floatPanel = ref<'message' | 'download' | 'support' | ''>('');
const floatActions = ref<UserPortalAction[]>([]);
const floatLoading = ref(false);
const floatMessage = ref('');

const activePageKey = computed(() => String(route.params.pageKey || 'home'));
const showHomeSidebar = computed(() => shouldShowHomeSidebar(activePageKey.value));
const showHomeDashboard = computed(() => shouldUseHomeDashboardPage(activePageKey.value, activeHomeMenuKey.value));
const isAssistantPage = computed(() => shouldUseAssistantPage(activePageKey.value));
const isMarketingPage = computed(() => shouldUseMarketingPage(activePageKey.value));
const isCodingPage = computed(() => shouldUseCodingPage(activePageKey.value));
const isWritingPage = computed(() => shouldUseWritingPage(activePageKey.value));
const hideWorkspaceDock = computed(() => isMarketingPage.value || shouldHideWorkspaceDock(activePageKey.value));
const hideFloatTools = computed(() => isMarketingPage.value || isCodingPage.value || isWritingPage.value);
const workbenchRoute = computed(() => {
  const routes: Record<string, string> = {
    image: '/workbench/image',
    video: '/workbench/video',
    audio: '/workbench/audio'
  };
  return routes[activePageKey.value] ?? '/workbench';
});
const workbenchDockLabel = computed(() => {
  const labels: Record<string, string> = {
    image: '工作台',
    video: '工作台',
    audio: '工作台'
  };
  return labels[activePageKey.value] ?? '进入工作台';
});
const defaultDockCopy = computed(() => {
  const copies: Record<string, { title: string; prompt: string }> = {
    home: {
      title: 'AI 工作台',
      prompt: '真实对话、图像、视频和音频任务统一入口。'
    },
    image: {
      title: '图像生成工作台',
      prompt: '进入工作台处理提示词、预览、历史和队列。'
    },
    video: {
      title: '视频生成工作台',
      prompt: '进入工作台处理脚本、故事板、预览和导出。'
    },
    audio: {
      title: '音频生成工作台',
      prompt: '进入工作台处理音色、波形、转写和导出。'
    }
  };
  return copies[activePageKey.value] ?? {
    title: 'AI 工作台',
    prompt: '继续上次的工具、素材和内容生成任务。'
  };
});
const dockTitle = computed(() => selectedTool.value || defaultDockCopy.value.title);
const dockPrompt = computed(() => promptText.value || defaultDockCopy.value.prompt);
const displayPageConfig = computed(() =>
  showHomeSidebar.value ? createHomeMenuPageConfig(pageConfig.value, activeHomeMenuKey.value) : pageConfig.value
);
const homeDashboardModel = computed(() => buildHomeDashboardModel(pageConfig.value, homeDashboard.value));
const floatPanelTitle = computed(() => {
  const titles = {
    message: '站内消息',
    download: '下载记录',
    support: '客服支持',
    '': ''
  };
  return titles[floatPanel.value];
});

onMounted(async () => {
  portal.value = await fetchPortalConfig();
  await loadPage(activePageKey.value);
  await refreshPortalActions();
});

watch(activePageKey, async (pageKey) => {
  selectedTool.value = '';
  promptText.value = '';
  await loadPage(pageKey);
});

async function loadPage(pageKey: string) {
  pageConfig.value = await fetchPortalPage(pageKey);
  if (pageKey === 'home') {
    activeHomeMenuKey.value = 'basic';
  }
  homeDashboard.value = pageKey === 'home' ? await fetchHomeDashboard() : createFallbackHomeDashboard(pageConfig.value);
  if (shouldUseAssistantPage(pageKey)) {
    assistantCenter.value = await fetchAssistantCenter();
  }
}

function openItem(item: PortalItem) {
  selectedTool.value = item.title;
  promptText.value = `以「${item.title}」的身份，帮我完成一个可交付的项目方案。`;
  if (item.actionValue === '/workbench') {
    void router.push(workbenchRoute.value);
  }
}

function openAssistant(assistant: AssistantCard) {
  selectedTool.value = assistant.name;
  promptText.value = `以「${assistant.name}」的身份，帮我完成一个可交付的项目方案。`;
}

function openTemplate(template: PromptTemplate) {
  selectedTool.value = template.title;
  promptText.value = template.content;
}

function goWorkbench() {
  void router.push(workbenchRoute.value);
}

function selectHomeMenu(menuKey: string) {
  activeHomeMenuKey.value = menuKey;
}

async function refreshPortalActions() {
  try {
    const actions = await fetchPortalUserActions('demo-user', 'all');
    backupEnabled.value = actions.some((action) => action.actionKey === 'backup' && action.status === 'COMPLETED');
  } catch {
    backupEnabled.value = false;
  }
}

async function enableBackup() {
  const result = await runPortalAction({
    userId: 'demo-user',
    detailPath: '/backup/workspace',
    actionKey: 'backup'
  });
  backupEnabled.value = result.status === 'completed';
  floatMessage.value = result.message;
}

async function openFloatPanel(panel: 'message' | 'download' | 'support') {
  floatPanel.value = panel;
  floatMessage.value = '';
  if (panel === 'support') {
    floatActions.value = [];
    return;
  }
  floatLoading.value = true;
  try {
    floatActions.value = await fetchPortalUserActions('demo-user', panel === 'download' ? 'download' : 'all');
  } finally {
    floatLoading.value = false;
  }
}

function closeFloatPanel() {
  floatPanel.value = '';
}

function scrollToTop() {
  const chromeBody = document.querySelector('.portal-chrome-body') as HTMLElement | null;
  if (chromeBody) {
    chromeBody.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }
  const content = document.querySelector('.content') as HTMLElement | null;
  if (content) {
    content.scrollTo({ top: 0, behavior: 'smooth' });
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
</script>

<template>
  <div :class="['desktop-shell', { 'home-shell': showHomeSidebar }]">
    <div :class="['app-frame', { 'no-sidebar': !showHomeSidebar }]">
      <aside v-if="showHomeSidebar" class="sidebar">
        <button
          v-for="nav in portal.leftNav"
          :key="nav.key"
          :class="{ active: activeHomeMenuKey === nav.key }"
          @click="selectHomeMenu(nav.key)"
        >
          <component :is="getIcon(nav.icon)" :size="22" />
          <span class="nav-copy">
            <strong>{{ nav.label }}</strong>
            <small>{{ getHomeMenuHint(nav.key) }}</small>
          </span>
        </button>
        <div class="backup-card">
          <button class="backup-action" :class="{ active: backupEnabled }" @click="enableBackup">
            <CloudUpload :size="18" />{{ backupEnabled ? '已开启备份' : '开启备份' }}
          </button>
          <strong>工作与学习文件备份</strong>
        </div>
      </aside>

      <main
        :class="[
          'content',
          {
            'marketing-content': isMarketingPage,
            'craft-content': isCodingPage || isWritingPage
          }
        ]"
      >
        <AssistantPage
          v-if="isAssistantPage"
          :center="assistantCenter"
          @open-assistant="openAssistant"
          @open-template="openTemplate"
        />
        <HomeDashboardPage v-else-if="showHomeDashboard" :model="homeDashboardModel" @open-item="openItem" />
        <MarketingPage v-else-if="isMarketingPage" :page-config="displayPageConfig" @open-item="openItem" />
        <TextWorkbenchPage v-else-if="isCodingPage || isWritingPage" :page-config="displayPageConfig" />
        <DynamicPage v-else :page-config="displayPageConfig" @open-item="openItem" />
        <section v-if="!hideWorkspaceDock" class="workspace-dock">
          <div>
            <Sparkles :size="22" />
            <strong>{{ dockTitle }}</strong>
            <span>{{ dockPrompt }}</span>
          </div>
          <button @click="goWorkbench">{{ workbenchDockLabel }}</button>
        </section>
      </main>

      <aside v-if="!hideFloatTools" class="float-tools portal-float-actions">
        <button @click="openFloatPanel('message')"><Bell :size="20" /><span>消息</span></button>
        <button @click="openFloatPanel('download')"><Download :size="20" /><span>下载</span></button>
        <button @click="openFloatPanel('support')"><Headphones :size="20" /><span>客服</span></button>
        <button class="top-btn" @click="scrollToTop">TOP</button>
      </aside>

      <section v-if="floatPanel" class="float-panel">
        <header>
          <strong>{{ floatPanelTitle }}</strong>
          <button @click="closeFloatPanel">关闭</button>
        </header>
        <p v-if="floatMessage">{{ floatMessage }}</p>
        <p v-if="floatLoading">加载中...</p>
        <div v-else-if="floatPanel === 'support'" class="support-panel">
          <strong>新商机 客服</strong>
          <span>已为你打开站内客服入口，工作日 10:00-19:00 处理课程、模板、下载和会员问题。</span>
          <button @click="router.push('/community/starter')">进入入门交流群</button>
        </div>
        <div v-else class="float-action-list">
          <button v-for="action in floatActions" :key="action.id" @click="router.push(action.detailPath)">
            <strong>{{ action.message || action.actionKey }}</strong>
            <span>{{ action.detailPath }}</span>
          </button>
          <span v-if="floatActions.length === 0">暂无记录</span>
        </div>
      </section>
    </div>
  </div>
</template>

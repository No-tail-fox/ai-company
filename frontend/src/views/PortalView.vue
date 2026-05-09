<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  Bell,
  CircleUserRound,
  CloudUpload,
  Download,
  Gift,
  Headphones,
  Menu,
  Search,
  Sparkles
} from 'lucide-vue-next';
import AssistantPage from '../components/AssistantPage.vue';
import AudioPage from '../components/AudioPage.vue';
import DynamicPage from '../components/DynamicPage.vue';
import ImagePage from '../components/ImagePage.vue';
import MarketingPage from '../components/MarketingPage.vue';
import VideoPage from '../components/VideoPage.vue';
import { fetchAssistantCenter, fetchPortalConfig, fetchPortalPage } from '../services/api';
import { getIcon } from '../services/icons';
import {
  createFallbackAssistantCenter,
  createFallbackPageConfig,
  createFallbackPortalConfig,
  createHomeMenuPageConfig,
  getHomeMenuHint,
  shouldHideWorkspaceDock,
  shouldUseAudioPage,
  shouldUseAssistantPage,
  shouldUseImagePage,
  shouldUseMarketingPage,
  shouldUseVideoPage,
  shouldShowHomeSidebar,
  type AssistantCard,
  type AssistantCenter,
  type PromptTemplate,
  type PortalConfig,
  type PortalItem,
  type PortalPageConfig
} from '../services/viewModel';

const route = useRoute();
const router = useRouter();
const portal = ref<PortalConfig>(createFallbackPortalConfig());
const pageConfig = ref<PortalPageConfig>(createFallbackPageConfig(String(route.params.pageKey || 'home')));
const assistantCenter = ref<AssistantCenter>(createFallbackAssistantCenter());
const activeHomeMenuKey = ref('basic');
const selectedTool = ref('AI 接单陪跑工作台');
const promptText = ref('帮我生成一套适合新手学习 AI 接单的 7 天训练计划。');

const activePageKey = computed(() => String(route.params.pageKey || 'home'));
const showHomeSidebar = computed(() => shouldShowHomeSidebar(activePageKey.value));
const isAssistantPage = computed(() => shouldUseAssistantPage(activePageKey.value));
const isAudioPage = computed(() => shouldUseAudioPage(activePageKey.value));
const isImagePage = computed(() => shouldUseImagePage(activePageKey.value));
const isMarketingPage = computed(() => shouldUseMarketingPage(activePageKey.value));
const isVideoPage = computed(() => shouldUseVideoPage(activePageKey.value));
const hideWorkspaceDock = computed(() => isAudioPage.value || isMarketingPage.value || shouldHideWorkspaceDock(activePageKey.value));
const hideFloatTools = computed(() => isAudioPage.value || isImagePage.value || isMarketingPage.value || isVideoPage.value);
const displayPageConfig = computed(() =>
  showHomeSidebar.value ? createHomeMenuPageConfig(pageConfig.value, activeHomeMenuKey.value) : pageConfig.value
);

onMounted(async () => {
  portal.value = await fetchPortalConfig();
  await loadPage(activePageKey.value);
});

watch(activePageKey, async (pageKey) => {
  await loadPage(pageKey);
});

async function loadPage(pageKey: string) {
  pageConfig.value = await fetchPortalPage(pageKey);
  if (shouldUseAssistantPage(pageKey)) {
    assistantCenter.value = await fetchAssistantCenter();
  }
}

function openItem(item: PortalItem) {
  selectedTool.value = item.title;
  promptText.value = `请以「${item.title}」身份，帮我完成一个可交付的项目方案。`;
}

function openAssistant(assistant: AssistantCard) {
  selectedTool.value = assistant.name;
  promptText.value = `请以「${assistant.name}」身份，帮我完成一个可交付的项目方案。`;
}

function openTemplate(template: PromptTemplate) {
  selectedTool.value = template.title;
  promptText.value = template.content;
}

function goPage(pageKey: string) {
  router.push(`/${pageKey}`);
}

function selectHomeMenu(menuKey: string) {
  activeHomeMenuKey.value = menuKey;
}
</script>

<template>
  <div class="desktop-shell">
    <header class="window-bar">
      <div class="window-tab">
        <component :is="getIcon(displayPageConfig.page.icon)" :size="16" />
        <span>{{ displayPageConfig.page.label }}</span>
      </div>
      <div class="window-actions">
        <Gift class="gift" :size="24" />
        <button class="login-pill" @click="router.push('/admin')"><CircleUserRound :size="22" />管理端</button>
        <Menu :size="20" />
      </div>
    </header>

    <section class="brand-row">
      <button class="logo" @click="goPage('home')">
        <span class="logo-red">新商机</span>
        <span class="logo-gold">OPC社区</span>
      </button>
      <div class="search-box">
        <span>搜索你需要的 AI 助理、工具或模板</span>
        <button aria-label="搜索"><Search :size="24" /></button>
      </div>
      <div class="vip-strip">
        <span class="vip-mark">VIP</span>
        <span>开通会员，享100+办公权益</span>
        <button>立即开通</button>
      </div>
    </section>

    <nav class="top-tabs">
      <button
        v-for="channel in portal.channels"
        :key="channel.key"
        :class="{ active: activePageKey === channel.key }"
        @click="goPage(channel.key)"
      >
        {{ channel.label }}
      </button>
    </nav>

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
          <strong>工作&学习文件备份</strong>
          <button><CloudUpload :size="18" />开启备份</button>
        </div>
      </aside>

      <main :class="['content', { 'audio-content': isAudioPage, 'image-content': isImagePage, 'marketing-content': isMarketingPage, 'video-content': isVideoPage }]">
        <AssistantPage
          v-if="isAssistantPage"
          :center="assistantCenter"
          @open-assistant="openAssistant"
          @open-template="openTemplate"
        />
        <AudioPage v-else-if="isAudioPage" :page-config="displayPageConfig" @open-item="openItem" />
        <ImagePage v-else-if="isImagePage" />
        <MarketingPage v-else-if="isMarketingPage" :page-config="displayPageConfig" @open-item="openItem" />
        <VideoPage v-else-if="isVideoPage" />
        <DynamicPage v-else :page-config="displayPageConfig" @open-item="openItem" />
        <section v-if="!hideWorkspaceDock" class="workspace-dock">
          <div>
            <Sparkles :size="22" />
            <strong>{{ selectedTool }}</strong>
            <span>{{ promptText }}</span>
          </div>
          <button>进入工作台</button>
        </section>
      </main>

      <aside v-if="!hideFloatTools" class="float-tools">
        <button><Bell :size="20" /><span>消息</span></button>
        <button><Download :size="20" /><span>下载</span></button>
        <button><Headphones :size="20" /><span>客服</span></button>
        <button class="top-btn">TOP</button>
      </aside>
    </div>
  </div>
</template>

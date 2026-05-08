<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  Bell,
  ChevronDown,
  CircleUserRound,
  CloudUpload,
  Download,
  Gift,
  Headphones,
  Menu,
  Search,
  Sparkles
} from 'lucide-vue-next';
import DynamicPage from '../components/DynamicPage.vue';
import { fetchPortalConfig, fetchPortalPage } from '../services/api';
import { getIcon } from '../services/icons';
import { createFallbackPageConfig, createFallbackPortalConfig, type PortalConfig, type PortalItem, type PortalPageConfig } from '../services/viewModel';

const route = useRoute();
const router = useRouter();
const portal = ref<PortalConfig>(createFallbackPortalConfig());
const pageConfig = ref<PortalPageConfig>(createFallbackPageConfig('home'));
const selectedTool = ref('AI 接单陪跑工作台');
const promptText = ref('帮我生成一套适合新手学习 AI 接单的 7 天训练计划。');

const activePageKey = computed(() => String(route.params.pageKey || 'home'));

onMounted(async () => {
  portal.value = await fetchPortalConfig();
  await loadPage(activePageKey.value);
});

watch(activePageKey, async (pageKey) => {
  await loadPage(pageKey);
});

async function loadPage(pageKey: string) {
  pageConfig.value = await fetchPortalPage(pageKey);
}

function openItem(item: PortalItem) {
  selectedTool.value = item.title;
  promptText.value = `请以「${item.title}」身份，帮我完成一个可交付的项目方案。`;
}

function goPage(pageKey: string) {
  router.push(`/${pageKey}`);
}
</script>

<template>
  <div class="desktop-shell">
    <header class="window-bar">
      <div class="window-dots">
        <span class="dot red"></span>
        <span class="dot amber"></span>
        <span class="dot green"></span>
      </div>
      <div class="window-tab">
        <component :is="getIcon(pageConfig.page.icon)" :size="16" />
        <span>{{ pageConfig.page.label }}</span>
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

    <div class="app-frame">
      <aside class="sidebar">
        <button v-for="nav in portal.leftNav" :key="nav.key" :class="{ active: nav.key === 'basic' }">
          <component :is="getIcon(nav.icon)" :size="22" />
          <span>{{ nav.label }}</span>
          <ChevronDown v-if="nav.key === 'workspace' || nav.key === 'toolkit'" :size="16" />
        </button>
        <div class="backup-card">
          <strong>工作&学习文件备份</strong>
          <button><CloudUpload :size="18" />开启备份</button>
        </div>
      </aside>

      <main class="content">
        <DynamicPage :page-config="pageConfig" @open-item="openItem" />
        <section class="workspace-dock">
          <div>
            <Sparkles :size="22" />
            <strong>{{ selectedTool }}</strong>
            <span>{{ promptText }}</span>
          </div>
          <button>进入工作台</button>
        </section>
      </main>

      <aside class="float-tools">
        <button><Bell :size="20" /><span>消息</span></button>
        <button><Download :size="20" /><span>下载</span></button>
        <button><Headphones :size="20" /><span>客服</span></button>
        <button class="top-btn">TOP</button>
      </aside>
    </div>
  </div>
</template>

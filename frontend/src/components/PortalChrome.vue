<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Search } from 'lucide-vue-next';
import { fetchMembershipStatus, searchPortal } from '../services/api';
import type { PortalSearchResult } from '../services/viewModel';

interface ChromeChannel {
  key: string;
  label: string;
}

const defaultChannels: ChromeChannel[] = [
  { key: 'home', label: '首页' },
  { key: 'assistant', label: 'AI 助理' },
  { key: 'workbench', label: '工作台' },
  { key: 'marketing', label: 'AI 营销' },
  { key: 'image', label: 'AI 图片' },
  { key: 'video', label: 'AI 视频' },
  { key: 'audio', label: 'AI 音频' },
  { key: 'coding', label: 'AI 编程' },
  { key: 'writing', label: 'AI 写作' },
  { key: 'ecommerce', label: 'AI 电商' },
  { key: 'legal', label: 'AI 法务' },
  { key: 'office', label: 'AI 办公' }
];

const props = withDefaults(defineProps<{
  enabled?: boolean;
  activePageKey: string;
  channels: ChromeChannel[];
}>(), {
  enabled: true
});

const router = useRouter();
const visibleChannels = computed(() => (props.channels.length > 0 ? props.channels : defaultChannels));
const showChrome = computed(() => props.enabled && props.activePageKey.length > 0);
const searchQuery = ref('');
const searchResults = ref<PortalSearchResult[]>([]);
const searchOpen = ref(false);
const searching = ref(false);
const membershipOpen = ref(false);
const membershipStatus = ref<any | null>(null);
let searchTimer = 0;

watch(searchQuery, (value) => {
  window.clearTimeout(searchTimer);
  if (value.trim().length < 2) {
    searchResults.value = [];
    return;
  }
  searchTimer = window.setTimeout(() => {
    void runSearch();
  }, 260);
});

watch(() => props.activePageKey, () => {
  searchOpen.value = false;
  membershipOpen.value = false;
});

function goPage(pageKey: string) {
  void router.push(`/${pageKey}`);
}

async function runSearch() {
  const query = searchQuery.value.trim();
  searchOpen.value = true;
  if (!query) {
    searchResults.value = [];
    return;
  }
  searching.value = true;
  try {
    searchResults.value = await searchPortal(query, props.activePageKey, 8);
  } finally {
    searching.value = false;
  }
}

function openSearchResult(result: PortalSearchResult) {
  searchOpen.value = false;
  const target = result.path || `/${result.pageKey || 'home'}`;
  void router.push(target);
}

async function toggleMembershipPanel() {
  membershipOpen.value = !membershipOpen.value;
  if (membershipOpen.value && !membershipStatus.value) {
    try {
      membershipStatus.value = await fetchMembershipStatus('demo-user');
    } catch {
      membershipStatus.value = { active: false, plan: null, entitlements: [] };
    }
  }
}
</script>

<template>
  <div v-if="showChrome" class="portal-chrome-shell">
    <section class="brand-row">
      <button class="logo" @click="goPage('home')">
        <span class="logo-red">新商盟</span>
        <span class="logo-gold">OPC社区</span>
      </button>

      <form class="search-box" @submit.prevent="runSearch">
        <input
          v-model="searchQuery"
          aria-label="搜索"
          placeholder="搜索你需要的 AI 助理、工具或模板"
          @focus="searchOpen = true"
        />
        <button aria-label="搜索" type="submit"><Search :size="24" /></button>
      </form>

      <section v-if="searchOpen && (searchQuery || searchResults.length)" class="search-results-panel">
        <span v-if="searching">搜索中...</span>
        <button v-for="result in searchResults" :key="result.id + result.path" @click="openSearchResult(result)">
          <strong>{{ result.title }}</strong>
          <small>{{ result.subtitle || result.path }}</small>
        </button>
        <span v-if="!searching && searchQuery && searchResults.length === 0">没有找到匹配内容</span>
      </section>

      <div class="vip-strip">
        <span class="vip-mark">VIP</span>
        <span>{{ membershipStatus?.active ? membershipStatus?.plan?.name || '会员已生效' : '开通会员，享 100+ 办公权益' }}</span>
        <button type="button" @click="toggleMembershipPanel">{{ membershipStatus?.active ? '查看权益' : '会员状态' }}</button>
      </div>

      <section v-if="membershipOpen" class="membership-panel">
        <strong>{{ membershipStatus?.active ? '会员权益已开启' : '当前为普通用户' }}</strong>
        <p v-if="membershipStatus?.active">有效期至 {{ membershipStatus?.expires_at || '长期' }}</p>
        <p v-else>第一轮不接真实支付，这里只展示站内会员状态和可用权益。</p>
        <ul>
          <li v-for="entitlement in membershipStatus?.entitlements ?? ['模板下载', '社群入口', '高阶课程']" :key="entitlement">
            {{ entitlement }}
          </li>
        </ul>
      </section>
    </section>

    <nav class="top-tabs">
      <button
        v-for="channel in visibleChannels"
        :key="channel.key"
        :class="{ active: activePageKey === channel.key }"
        @click="goPage(channel.key)"
      >
        {{ channel.label }}
      </button>
    </nav>

    <div class="portal-chrome-body">
      <slot />
    </div>
  </div>
  <slot v-else />
</template>

<style scoped>
.portal-chrome-shell {
  --portal-chrome-height: 136px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
}

.portal-chrome-body {
  flex: 1;
  min-height: 0;
}
</style>

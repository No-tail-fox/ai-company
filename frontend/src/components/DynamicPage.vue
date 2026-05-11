<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ChevronRight, Download, ExternalLink, Lock, PlayCircle, Plus, Search } from 'lucide-vue-next';
import { getIcon } from '../services/icons';
import type { PortalItem, PortalPageConfig, PortalSection } from '../services/viewModel';

const props = defineProps<{
  pageConfig: PortalPageConfig;
}>();

const emit = defineEmits<{
  openItem: [item: PortalItem];
}>();

const router = useRouter();
const thirdPartySearch = ref('');
const thirdPartyCategory = ref('全部');
const primarySections = computed(() => props.pageConfig.sections.filter((section) => section.layout !== 'ranking-list'));
const rankingSection = computed(() => props.pageConfig.sections.find((section) => section.layout === 'ranking-list'));
const isHomePage = computed(() => props.pageConfig.page.pageKey === 'home');
const workbenchEntry = computed(() => {
  const entries: Record<string, { route: string; label: string; panelTitle: string; panelSubtitle: string; icon: string }> = {
    image: {
      route: '/workbench/image',
      label: '工作台',
      panelTitle: '图像生成工作台',
      panelSubtitle: '提示词、预览、历史和队列',
      icon: 'Image'
    },
    video: {
      route: '/workbench/video',
      label: '工作台',
      panelTitle: '视频生成工作台',
      panelSubtitle: '脚本、故事板、预览和导出',
      icon: 'FileVideo'
    },
    audio: {
      route: '/workbench/audio',
      label: '工作台',
      panelTitle: '音频生成工作台',
      panelSubtitle: '音色、波形、转写和导出',
      icon: 'Headphones'
    }
  };
  return entries[props.pageConfig.page.pageKey];
});

function cardClass(section: PortalSection) {
  return {
    'tool-grid': section.layout === 'tool-grid',
    'learning-grid': section.layout === 'learning-grid',
    'order-grid': section.layout === 'order-grid',
    'banner-grid': section.layout === 'banner-row' || section.layout === 'promo',
    'template-list': section.layout === 'template-list',
    'task-list': section.layout === 'task-list',
    'stat-strip': section.layout === 'stat-strip',
    'default-grid': ![
      'tool-grid',
      'learning-grid',
      'order-grid',
      'banner-row',
      'promo',
      'template-list',
      'task-list',
      'stat-strip',
      'third-party-tools'
    ].includes(section.layout)
  };
}

function handleItem(item: PortalItem) {
  if (isExternalUrl(item.actionValue)) {
    window.open(item.actionValue, '_blank', 'noreferrer');
    return;
  }
  if (item.actionValue === '/workbench') {
    void router.push('/workbench');
    return;
  }
  if (workbenchEntry.value && item.actionType === 'workspace') {
    void router.push(workbenchEntry.value.route);
    return;
  }
  if (item.actionType === 'route' && item.actionValue.startsWith('/')) {
    void router.push(item.actionValue);
    return;
  }
  emit('openItem', item);
}

function openWorkbench(route = '/workbench') {
  void router.push(route);
}

function openSidePromo() {
  void router.push('/templates');
}

function isThirdPartyToolsSection(section: PortalSection) {
  return section.layout === 'third-party-tools';
}

function thirdPartyCategories(section: PortalSection) {
  return [
    '全部',
    ...Array.from(new Set(section.items.map((item) => item.category).filter(Boolean)))
  ];
}

function filteredThirdPartyItems(section: PortalSection) {
  const query = thirdPartySearch.value.trim().toLowerCase();
  const availableCategories = thirdPartyCategories(section);
  const activeCategory = availableCategories.includes(thirdPartyCategory.value) ? thirdPartyCategory.value : '全部';
  return section.items.filter((item) => {
    const matchesCategory = activeCategory === '全部' || item.category === activeCategory;
    const searchable = [
      item.title,
      item.subtitle,
      item.category,
      item.actionValue,
      ...(item.tags ?? [])
    ].join(' ').toLowerCase();
    return matchesCategory && (!query || searchable.includes(query));
  });
}

function setThirdPartyCategory(category: string) {
  thirdPartyCategory.value = category;
}

function thirdPartyBrandMark(item: PortalItem) {
  const mark = item.metadata?.brandMark ?? item.metadata?.brand_mark ?? item.badge;
  if (typeof mark === 'string' && mark.trim()) {
    return mark.trim().slice(0, 3).toUpperCase();
  }
  return item.title.trim().slice(0, 2).toUpperCase() || 'AI';
}

function thirdPartyVisitUrl(item: PortalItem) {
  return item.actionValue || thirdPartyDownloadUrl(item) || '#';
}

function thirdPartyDisplayUrl(item: PortalItem) {
  const value = thirdPartyVisitUrl(item);
  return value.replace(/^https?:\/\//, '').replace(/\/$/, '');
}

function thirdPartyDownloadUrl(item: PortalItem) {
  const detail = item.metadata?.detail;
  const download = detail && typeof detail === 'object' ? detail.download : null;
  const url = download && typeof download === 'object' ? download.url : '';
  return String(url || item.metadata?.downloadUrl || item.metadata?.download_url || '').trim();
}

function isExternalUrl(value: string) {
  return /^https?:\/\//i.test(value);
}

function thirdPartyLinkTarget(url: string) {
  return isExternalUrl(url) ? '_blank' : '_self';
}

function openAddThirdPartyTool() {
  void router.push('/admin');
}
</script>

<template>
  <section class="dynamic-page">
    <header class="page-hero">
      <div>
        <span class="page-kicker">{{ pageConfig.page.label }}</span>
        <h1>{{ pageConfig.page.title }}</h1>
        <p>{{ pageConfig.page.subtitle }}</p>
        <button v-if="isHomePage" class="home-workbench-btn" @click="openWorkbench()">
          <component :is="getIcon('LayoutGrid')" :size="18" />
          进入工作台
        </button>
        <button v-else-if="workbenchEntry" class="home-workbench-btn" @click="openWorkbench(workbenchEntry.route)">
          <component :is="getIcon(workbenchEntry.icon)" :size="18" />
          {{ workbenchEntry.label }}
        </button>
      </div>
      <div class="hero-stat">
        <component :is="getIcon(workbenchEntry?.icon || pageConfig.page.icon)" :size="34" />
        <strong>{{ workbenchEntry?.panelTitle || '模块化运营' }}</strong>
        <span>{{ workbenchEntry?.panelSubtitle || '由管理端实时配置' }}</span>
      </div>
    </header>

    <div class="page-layout">
      <div class="page-main">
        <section v-for="section in primarySections" :key="section.id" class="module-section">
          <div class="section-title">
            <div>
              <h2>{{ section.title }}</h2>
              <p v-if="section.subtitle">{{ section.subtitle }}</p>
            </div>
            <button class="section-more" @click="openSidePromo">
              <span>更多</span>
              <ChevronRight :size="18" />
            </button>
          </div>

          <div v-if="isThirdPartyToolsSection(section)" class="third-party-tools-panel">
            <div class="third-party-tools-toolbar">
              <label class="third-party-search">
                <Search :size="18" />
                <input v-model="thirdPartySearch" placeholder="搜索工具名称、用途或下载链接" />
              </label>
              <div class="third-party-segments" aria-label="第三方工具分类">
                <button
                  v-for="category in thirdPartyCategories(section)"
                  :key="category"
                  :class="{ active: thirdPartyCategory === category }"
                  type="button"
                  @click="setThirdPartyCategory(category)"
                >
                  {{ category }}
                </button>
              </div>
              <button class="third-party-add" type="button" @click="openAddThirdPartyTool">
                <Plus :size="16" />
                添加工具
              </button>
            </div>

            <div class="third-party-tools-grid">
              <article v-for="item in filteredThirdPartyItems(section)" :key="item.id" class="third-party-tool-card">
                <header>
                  <span class="third-party-mark">{{ thirdPartyBrandMark(item) }}</span>
                  <span class="third-party-title">
                    <strong>{{ item.title }}</strong>
                    <small>{{ item.subtitle }}</small>
                  </span>
                  <span class="third-party-tag">{{ item.category || '工具' }}</span>
                </header>
                <p>{{ item.metadata?.summary || item.subtitle }}</p>
                <a
                  class="third-party-link"
                  :href="thirdPartyVisitUrl(item)"
                  :target="thirdPartyLinkTarget(thirdPartyVisitUrl(item))"
                  rel="noreferrer"
                >
                  官网链接 · {{ thirdPartyDisplayUrl(item) }}
                </a>
                <div class="third-party-actions">
                  <a
                    class="third-party-visit"
                    :href="thirdPartyVisitUrl(item)"
                    :target="thirdPartyLinkTarget(thirdPartyVisitUrl(item))"
                    rel="noreferrer"
                  >
                    <ExternalLink :size="15" />
                    访问官网
                  </a>
                  <a
                    v-if="thirdPartyDownloadUrl(item)"
                    class="third-party-download"
                    :href="thirdPartyDownloadUrl(item)"
                    :target="thirdPartyLinkTarget(thirdPartyDownloadUrl(item))"
                    rel="noreferrer"
                  >
                    <Download :size="15" />
                    下载客户端
                  </a>
                  <button v-else class="third-party-download" type="button" @click="handleItem(item)">查看详情</button>
                </div>
              </article>
            </div>
          </div>

          <div v-else :class="['module-items', cardClass(section)]">
            <button v-for="item in section.items" :key="item.id" class="module-card" @click="handleItem(item)">
              <span class="icon-tile"><component :is="getIcon(item.icon)" :size="28" /></span>
              <div class="card-copy">
                <span v-if="item.badge" class="badge">{{ item.badge }}</span>
                <strong>{{ item.title }}</strong>
                <p>{{ item.subtitle }}</p>
                <small>{{ item.category }}</small>
              </div>
              <Lock v-if="item.requiredMembership" class="lock" :size="16" />
              <PlayCircle v-if="section.layout === 'template-list'" class="play" :size="20" />
            </button>
          </div>
        </section>
      </div>

      <aside class="page-side">
        <section v-if="rankingSection" class="side-box">
          <header>
            <strong>{{ rankingSection.title }}</strong>
            <button class="side-more" @click="openSidePromo">更多</button>
          </header>
          <ol class="ranking-list">
            <li v-for="(item, index) in rankingSection.items" :key="item.id" @click="handleItem(item)">
              <span>{{ index + 1 }}</span>
              <component :is="getIcon(item.icon)" :size="22" />
              <strong>{{ item.title }}</strong>
              <em>{{ item.subtitle }}</em>
            </li>
          </ol>
        </section>
        <section class="promo-panel">
          <strong>热门模板上新！</strong>
          <span>一键轻松取用办公模板</span>
          <button class="promo-route-btn" @click="openSidePromo">立即查看</button>
          <div class="template-stack">
            <div class="doc-card word">W</div>
            <div class="doc-card ppt">P</div>
            <div class="doc-card sheet">X</div>
          </div>
        </section>
      </aside>
    </div>
  </section>
</template>

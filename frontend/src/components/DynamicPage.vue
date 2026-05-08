<script setup lang="ts">
import { computed } from 'vue';
import { ChevronRight, Lock, PlayCircle } from 'lucide-vue-next';
import { getIcon } from '../services/icons';
import type { PortalItem, PortalPageConfig, PortalSection } from '../services/viewModel';

const props = defineProps<{
  pageConfig: PortalPageConfig;
}>();

const emit = defineEmits<{
  openItem: [item: PortalItem];
}>();

const primarySections = computed(() => props.pageConfig.sections.filter((section) => section.layout !== 'ranking-list'));
const rankingSection = computed(() => props.pageConfig.sections.find((section) => section.layout === 'ranking-list'));

function cardClass(section: PortalSection) {
  return {
    'tool-grid': section.layout === 'tool-grid',
    'learning-grid': section.layout === 'learning-grid',
    'order-grid': section.layout === 'order-grid',
    'banner-grid': section.layout === 'banner-row' || section.layout === 'promo',
    'template-list': section.layout === 'template-list',
    'task-list': section.layout === 'task-list',
    'stat-strip': section.layout === 'stat-strip',
    'default-grid': !['tool-grid', 'learning-grid', 'order-grid', 'banner-row', 'promo', 'template-list', 'task-list', 'stat-strip'].includes(section.layout)
  };
}
</script>

<template>
  <section class="dynamic-page">
    <header class="page-hero">
      <div>
        <span class="page-kicker">{{ pageConfig.page.label }}</span>
        <h1>{{ pageConfig.page.title }}</h1>
        <p>{{ pageConfig.page.subtitle }}</p>
      </div>
      <div class="hero-stat">
        <component :is="getIcon(pageConfig.page.icon)" :size="34" />
        <strong>模块化运营</strong>
        <span>由管理端实时配置</span>
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
            <ChevronRight :size="22" />
          </div>

          <div :class="['module-items', cardClass(section)]">
            <button v-for="item in section.items" :key="item.id" class="module-card" @click="emit('openItem', item)">
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
            <span>更多</span>
          </header>
          <ol class="ranking-list">
            <li v-for="(item, index) in rankingSection.items" :key="item.id" @click="emit('openItem', item)">
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
          <button>立即查看</button>
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

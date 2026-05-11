<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ChevronRight, Sparkles } from 'lucide-vue-next';
import { getIcon } from '../services/icons';
import type { HomeDashboardModel, HomeDashboardSlide, PortalItem } from '../services/viewModel';

const props = defineProps<{
  model: HomeDashboardModel;
}>();

const emit = defineEmits<{
  (event: 'open-item', item: PortalItem): void;
}>();

const router = useRouter();
const activeSlideIndex = ref(0);
const activeCommunityIndex = ref(0);

const sectionMap = computed(() => {
  return new Map(props.model.sections.map((section) => [section.sectionKey, section]));
});

const learningSection = computed(() => sectionMap.value.get('learning_center'));
const orderSection = computed(() => sectionMap.value.get('order_center'));
const communitySection = computed(() => sectionMap.value.get('communities'));
const workbenchSection = computed(() => sectionMap.value.get('workbench_shortcuts') ?? sectionMap.value.get('workspace_tools'));
const toolSection = computed(() => sectionMap.value.get('home_tools') ?? sectionMap.value.get('toolkit'));

const heroSlides = computed(() => sortSlides(props.model.heroSlides));
const activeSlide = computed(() => heroSlides.value[activeSlideIndex.value % heroSlides.value.length] ?? heroSlides.value[0] ?? fallbackSlide());
const kpiCards = computed(() => props.model.kpiCards.slice(0, 4));
const orderCards = computed(() => sortItems(orderSection.value?.items ?? []));
const communityCards = computed(() => sortItems(communitySection.value?.items ?? []));
const workbenchCards = computed(() => sortItems(props.model.workbenchShortcuts));
const toolCards = computed(() => sortItems(props.model.toolCards));
const learningCards = computed(() => buildLearningCards(learningSection.value?.items ?? []));
const learningFeatured = computed(() => learningCards.value.slice(0, 3));
const learningMini = computed(() => learningCards.value.slice(3, 7));
const lowerSections = computed(() =>
  props.model.sections.filter(
    (section) =>
      ![
        'learning_center',
        'order_center',
        'communities',
        'membership_benefits',
        'banners',
        'workbench_shortcuts',
        'workspace_tools',
        'home_tools',
        'toolkit'
      ].includes(section.sectionKey)
  )
);
const communityTabs = computed(() => communityCards.value.map((card) => card.title));
const activeCommunityCard = computed(() => {
  if (communityCards.value.length === 0) {
    return null;
  }
  return communityCards.value[activeCommunityIndex.value % communityCards.value.length] ?? communityCards.value[0];
});
const hasSlideCount = computed(() => heroSlides.value.length > 0);

function sortSlides(slides: HomeDashboardSlide[]) {
  return [...slides].sort((left, right) => left.sortOrder - right.sortOrder);
}

function sortItems(items: PortalItem[]) {
  return [...items].sort((left, right) => left.sortOrder - right.sortOrder);
}

function fallbackSlide(): HomeDashboardSlide {
  return {
    id: 'fallback-home-slide',
    title: '会员活动限时特惠',
    subtitle: '开通会员解锁模板、社群和接单资料',
    badge: '会员专享',
    ctaLabel: '立即开通',
    ctaSubtitle: '查看权益，不走支付',
    imageUrl: '',
    actionType: 'route',
    actionValue: '/membership/benefits',
    sortOrder: 10,
    enabled: true,
    metadata: { accent: 'gold', theme: 'vip' }
  };
}

function buildLearningCards(items: PortalItem[]) {
  const cards = sortItems(items).slice(0, 7);
  const fallbackCards: PortalItem[] = [
    {
      id: 'home-learning-fallback-1',
      itemType: 'course',
      title: '《0基础AI通识课》',
      subtitle: '从认知到上手的一站式入门路径',
      category: '基础必备',
      icon: 'FileVideo',
      imageUrl: '',
      badge: '基础必备',
      tags: [],
      sortOrder: 10,
      enabled: true,
      actionType: 'route',
      actionValue: '/workspace/course',
      requiredMembership: false,
      pointCost: 0,
      metadata: {}
    },
    {
      id: 'home-learning-fallback-2',
      itemType: 'course',
      title: '《AI实战必修课》',
      subtitle: '办公、剪辑、写作全场景效率翻倍',
      category: '基础必备',
      icon: 'MonitorPlay',
      imageUrl: '',
      badge: '基础必备',
      tags: [],
      sortOrder: 20,
      enabled: true,
      actionType: 'route',
      actionValue: '/workspace/course',
      requiredMembership: false,
      pointCost: 0,
      metadata: {}
    },
    {
      id: 'home-learning-fallback-3',
      itemType: 'course',
      title: '《AI商业变现课》',
      subtitle: '内容创作与电商营销全链路落地',
      category: '接单变现',
      icon: 'ScanSearch',
      imageUrl: '',
      badge: '接单变现',
      tags: [],
      sortOrder: 30,
      enabled: true,
      actionType: 'route',
      actionValue: '/workspace/course',
      requiredMembership: false,
      pointCost: 0,
      metadata: {}
    },
    {
      id: 'home-learning-fallback-4',
      itemType: 'course',
      title: '《AI爆款内容创作》',
      subtitle: '短视频脚本、标题、封面和投放流程',
      category: 'AI营销',
      icon: 'Presentation',
      imageUrl: '',
      badge: 'AI营销',
      tags: [],
      sortOrder: 40,
      enabled: true,
      actionType: 'route',
      actionValue: '/workspace/course',
      requiredMembership: false,
      pointCost: 0,
      metadata: {}
    },
    {
      id: 'home-learning-fallback-5',
      itemType: 'course',
      title: '《AI进阶实战营》',
      subtitle: '从工具使用到项目交付的系统训练',
      category: '学习成长',
      icon: 'NotebookTabs',
      imageUrl: '',
      badge: '学习成长',
      tags: [],
      sortOrder: 50,
      enabled: true,
      actionType: 'route',
      actionValue: '/workspace/course/advanced',
      requiredMembership: false,
      pointCost: 0,
      metadata: {}
    },
    {
      id: 'home-learning-fallback-6',
      itemType: 'course',
      title: '《AI项目交付训练》',
      subtitle: '拆解真实客户需求并完成可复用方案',
      category: '项目共创',
      icon: 'BriefcaseBusiness',
      imageUrl: '',
      badge: '项目共创',
      tags: [],
      sortOrder: 60,
      enabled: true,
      actionType: 'route',
      actionValue: '/workspace/course/project',
      requiredMembership: false,
      pointCost: 0,
      metadata: {}
    },
    {
      id: 'home-learning-fallback-7',
      itemType: 'course',
      title: '查看更多课程',
      subtitle: '打开学习成长看完整课程路径',
      category: '课程目录',
      icon: 'ChevronRight',
      imageUrl: '',
      badge: '课程目录',
      tags: [],
      sortOrder: 999,
      enabled: true,
      actionType: 'route',
      actionValue: '/learning/daily',
      requiredMembership: false,
      pointCost: 0,
      metadata: {}
    }
  ];
  for (const fallback of fallbackCards) {
    if (cards.length >= 7) {
      break;
    }
    if (cards.some((card) => card.id === fallback.id || card.title === fallback.title)) {
      continue;
    }
    cards.push(fallback);
  }
  return cards.slice(0, 7);
}

function accentFromSlide(slide: HomeDashboardSlide) {
  const accent = String(slide.metadata?.accent ?? '').toLowerCase();
  if (accent === 'blue' || accent === 'green' || accent === 'violet' || accent === 'orange') {
    return accent;
  }
  return 'gold';
}

function accentFromItem(item: PortalItem, fallbackTone: 'gold' | 'blue' | 'violet' | 'green' | 'orange' = 'blue') {
  const source = `${item.category} ${item.title} ${item.subtitle}`.toLowerCase();
  if (source.includes('会员') || source.includes('权益') || source.includes('接单')) {
    return 'gold';
  }
  if (source.includes('社群') || source.includes('群')) {
    return 'green';
  }
  if (source.includes('工具') || source.includes('办公') || source.includes('工作台')) {
    return 'violet';
  }
  if (source.includes('模板') || source.includes('内容') || source.includes('学习')) {
    return 'blue';
  }
  return fallbackTone;
}

function setActiveSlide(index: number) {
  if (!hasSlideCount.value) {
    return;
  }
  activeSlideIndex.value = index;
}

function setActiveCommunity(index: number) {
  if (communityCards.value.length === 0) {
    return;
  }
  activeCommunityIndex.value = index;
}

function openDestination(actionType: string | undefined, actionValue: string) {
  if (!actionValue) {
    return;
  }
  if (actionType === 'external_link' || /^https?:\/\//i.test(actionValue)) {
    window.open(actionValue, '_blank', 'noreferrer');
    return;
  }
  void router.push(actionValue);
}

function openItem(item: PortalItem) {
  emit('open-item', item);
  openDestination(item.actionType, item.actionValue);
}

function openMembershipBenefits() {
  void router.push('/membership/benefits');
}

function openSlide(slide: HomeDashboardSlide) {
  if (slide.actionValue === '/membership/benefits') {
    openMembershipBenefits();
    return;
  }
  openDestination(slide.actionType, slide.actionValue);
}

function lowerGridClass(layout: string) {
  if (layout === 'learning-grid') {
    return 'grid-learning';
  }
  if (layout === 'order-grid') {
    return 'grid-order';
  }
  if (layout === 'banner-row') {
    return 'grid-banner';
  }
  if (layout === 'task-list') {
    return 'grid-task';
  }
  if (layout === 'tool-grid') {
    return 'grid-tool';
  }
  if (layout === 'template-list') {
    return 'grid-template';
  }
  if (layout === 'ranking-list') {
    return 'grid-ranking';
  }
  if (layout === 'third-party-tools') {
    return 'grid-third-party';
  }
  return 'grid-default';
}

function previewTone(item: PortalItem) {
  return `tone-${accentFromItem(item)}`;
}
</script>

<template>
  <main class="home-dashboard">
    <section class="home-first-screen home-hero-stage">
      <article class="home-promo-carousel home-promo-card">
        <div class="promo-topline">
          <span class="promo-mark">会员活动</span>
          <span class="promo-hint">限时领取 / 立即开通 / 模板上新</span>
        </div>

        <div class="promo-body">
          <div class="promo-copy">
            <p class="promo-kicker">{{ activeSlide.badge || '会员专享' }}</p>
            <h2>{{ activeSlide.title }}</h2>
            <p class="promo-subtitle">{{ activeSlide.subtitle }}</p>

            <div class="promo-actions">
              <button class="promo-primary" type="button" @click="openSlide(activeSlide)">
                {{ activeSlide.ctaLabel || '立即查看' }}
              </button>
              <button class="promo-secondary" type="button" @click="openMembershipBenefits">查看权益</button>
            </div>

          </div>

          <div class="promo-visual">
            <div v-if="activeSlide.imageUrl" class="promo-image-wrap">
              <img :src="activeSlide.imageUrl" :alt="activeSlide.title" />
            </div>
            <div v-else class="promo-sheet-stack">
              <div class="promo-sheet promo-sheet-back"></div>
              <div class="promo-sheet promo-sheet-mid">
                <span class="promo-sheet-tag">{{ activeSlide.badge || '会员专享' }}</span>
                <strong>{{ activeSlide.ctaLabel || '立即开通' }}</strong>
                <small>{{ activeSlide.ctaSubtitle || '查看权益，不走支付' }}</small>
              </div>
              <div class="promo-sheet promo-sheet-front">
                <div class="promo-sheet-head">
                  <Sparkles :size="16" />
                  <span>热门模板上新</span>
                </div>
                <div class="promo-sheet-grid">
                  <span>PPT</span>
                  <span>报价单</span>
                  <span>社媒文案</span>
                  <span>交付资料</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="promo-slide-dots">
          <button
            v-for="(slide, index) in heroSlides"
            :key="slide.id"
            :class="['promo-dot', `tone-${accentFromSlide(slide)}`, { active: index === activeSlideIndex }]"
            type="button"
            @click="setActiveSlide(index)"
          >
            <span class="sr-only">{{ slide.title }}</span>
          </button>
        </div>
      </article>

      <section class="home-workbench-panel">
        <header class="panel-header">
          <div>
            <span class="panel-kicker">{{ workbenchSection?.title ?? '我的工作台' }}</span>
            <p>{{ workbenchSection?.subtitle ?? 'AI 对话、图片生成、视频脚本、PPT 办公、接单交付、素材库' }}</p>
          </div>
          <button class="section-link" type="button" @click="openDestination('route', '/workbench')">
            <span>自定义</span>
            <ChevronRight :size="16" />
          </button>
        </header>

        <div class="workbench-grid">
          <button
            v-for="card in workbenchCards"
            :key="card.id"
            :class="['workbench-card', previewTone(card)]"
            type="button"
            @click="openItem(card)"
          >
            <span class="workbench-icon">
              <component :is="getIcon(card.icon)" :size="20" />
            </span>
            <strong>{{ card.title }}</strong>
          </button>
        </div>

        <div class="workbench-recent">
          <span>最近使用</span>
          <div class="workbench-recent-icons">
            <button v-for="card in workbenchCards.slice(0, 5)" :key="`${card.id}-recent`" type="button" @click="openItem(card)">
              <component :is="getIcon(card.icon)" :size="16" />
            </button>
          </div>
          <button class="workbench-more" type="button" @click="openDestination('route', '/workbench')">更多</button>
        </div>
      </section>
    </section>

    <section class="home-kpi-strip">
      <button
        v-for="card in kpiCards"
        :key="card.id"
        :class="['kpi-card', `tone-${card.tone || 'blue'}`]"
        type="button"
        @click="openDestination(card.actionType, card.actionValue)"
      >
        <span class="kpi-icon">
          <component :is="getIcon(card.icon)" :size="18" />
        </span>
        <span class="kpi-label">{{ card.label }}</span>
        <strong class="kpi-value">{{ card.value }}</strong>
        <small class="kpi-trend">{{ card.trend }}</small>
      </button>
    </section>

    <section class="home-learning-panel home-learning-stage">
      <header class="panel-header">
        <div>
          <span class="panel-kicker">{{ learningSection?.title ?? '常用AI学习中心' }}</span>
          <p>{{ learningSection?.subtitle ?? '课程、实战和变现路径' }}</p>
        </div>
        <button class="section-link" type="button" @click="openDestination('route', '/learning/daily')">
          <span>查看全部</span>
          <ChevronRight :size="16" />
        </button>
      </header>

      <div class="learning-stage-grid">
        <button
          v-for="card in learningFeatured"
          :key="card.id"
          :class="['learning-card', 'learning-feature', previewTone(card)]"
          type="button"
          @click="openItem(card)"
        >
          <span class="card-badge">{{ card.badge || card.category }}</span>
          <span class="card-icon">
            <component :is="getIcon(card.icon)" :size="18" />
          </span>
          <strong>{{ card.title }}</strong>
          <small>{{ card.subtitle }}</small>
        </button>
        <button
          v-for="card in learningMini"
          :key="card.id"
          :class="['learning-card', 'learning-mini', previewTone(card)]"
          type="button"
          @click="openItem(card)"
        >
          <span class="card-badge">{{ card.badge || card.category }}</span>
          <span class="card-icon">
            <component :is="getIcon(card.icon)" :size="16" />
          </span>
          <strong>{{ card.title }}</strong>
          <small>{{ card.subtitle }}</small>
        </button>
      </div>
    </section>

    <section class="home-dual-row">
      <section class="home-community-panel">
        <header class="panel-header">
          <div>
            <span class="panel-kicker">{{ communitySection?.title ?? '精选社群' }}</span>
            <p>{{ communitySection?.subtitle ?? '入门交流群、学习打卡群、接单变现群、资源对接群' }}</p>
          </div>
        </header>

        <div class="community-tabs">
          <button
            v-for="(tab, index) in communityTabs"
            :key="tab"
            :class="{ active: index === activeCommunityIndex }"
            type="button"
            @click="setActiveCommunity(index)"
          >
            {{ tab }}
          </button>
        </div>

        <div class="community-banner-row">
          <button
            v-for="(card, index) in communityCards"
            :key="card.id"
            :class="['community-card', previewTone(card), { active: index === activeCommunityIndex }]"
            type="button"
            @click="openItem(card)"
          >
            <div class="community-preview">
              <span class="community-preview-chip">{{ index === activeCommunityIndex ? '当前推荐' : card.category }}</span>
              <span class="community-preview-grid">
                <i></i>
                <i></i>
                <i></i>
              </span>
            </div>
            <strong>{{ card.title }}</strong>
            <small>{{ card.subtitle }}</small>
          </button>
        </div>

        <div class="community-footer-strip">
          <span class="community-footer-tag">群公告</span>
          <span>本周直播：AI办公效率提升实战技巧</span>
          <span class="community-footer-tag muted">最新动态</span>
          <span>用户小明获得接单变现奖励¥888</span>
        </div>
      </section>

      <section class="home-tool-panel">
        <header class="panel-header">
          <div>
            <span class="panel-kicker">{{ toolSection?.title ?? '热门工具' }}</span>
            <p>{{ toolSection?.subtitle ?? '常用工具、办公模板、接单报价、内容生成、电商优化' }}</p>
          </div>
          <button class="section-link" type="button" @click="openDestination('route', '/toolkit/office')">
            <span>更多工具</span>
            <ChevronRight :size="16" />
          </button>
        </header>

        <div class="template-grid home-tool-grid">
          <button
            v-for="card in toolCards"
            :key="card.id"
            :class="['template-card', previewTone(card)]"
            type="button"
            @click="openItem(card)"
          >
            <span class="template-icon">
              <component :is="getIcon(card.icon)" :size="18" />
            </span>
            <strong>{{ card.title }}</strong>
            <small>{{ card.subtitle }}</small>
          </button>
        </div>

        <div class="tool-footer-strip">
          <span class="tool-footer-tag">工具榜单</span>
          <span>本周热门工具 TOP10</span>
          <span class="tool-footer-tag new">NEW</span>
          <span>从入门到精通，快速上手</span>
        </div>
      </section>
    </section>

    <section class="home-lower-stack">
      <section class="home-order-panel">
        <header class="panel-header">
          <div>
            <span class="panel-kicker">{{ orderSection?.title ?? '接单中心' }}</span>
            <p>{{ orderSection?.subtitle ?? '适合新手和团队交付的接单入口' }}</p>
          </div>
          <button class="section-link" type="button" @click="openDestination('route', '/workspace/deliveries')">
            <span>进入接单</span>
            <ChevronRight :size="16" />
          </button>
        </header>

        <div class="order-grid">
          <button
            v-for="card in orderCards"
            :key="card.id"
            :class="['order-card', previewTone(card)]"
            type="button"
            @click="openItem(card)"
          >
            <span class="order-icon">
              <component :is="getIcon(card.icon)" :size="20" />
            </span>
            <strong>{{ card.title }}</strong>
            <small>{{ card.subtitle }}</small>
          </button>
        </div>
      </section>

      <section v-for="section in lowerSections" :key="section.id" class="lower-section">
        <header class="panel-header">
          <div>
            <span class="panel-kicker">{{ section.title }}</span>
            <p>{{ section.subtitle }}</p>
          </div>
          <span class="section-layout">{{ section.layout }}</span>
        </header>

        <div :class="['lower-grid', lowerGridClass(section.layout)]">
          <button
            v-for="card in sortItems(section.items)"
            :key="card.id"
            :class="['lower-card', previewTone(card)]"
            type="button"
            @click="openItem(card)"
          >
            <span class="lower-card-icon">
              <component :is="getIcon(card.icon)" :size="18" />
            </span>
            <strong>{{ card.title }}</strong>
            <small>{{ card.subtitle }}</small>
          </button>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.home-dashboard {
  display: grid;
  gap: 14px;
  padding-bottom: 48px;
  color: #1b2435;
}

.home-first-screen,
.home-hero-stage {
  display: grid;
  grid-template-columns: minmax(0, 1.22fr) minmax(0, 0.98fr);
  gap: 18px;
  align-items: stretch;
}

.home-learning-panel,
.home-learning-stage,
.home-promo-carousel,
.home-promo-card,
.home-kpi-strip,
.home-order-panel,
.home-community-panel,
.home-workbench-panel,
.home-tool-panel,
.lower-section {
  min-width: 0;
}

.home-learning-panel,
.home-learning-stage,
.home-promo-carousel,
.home-promo-card,
.home-order-panel,
.home-community-panel,
.home-workbench-panel,
.home-tool-panel,
.lower-section {
  border: 1px solid #e3e8f4;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(27, 39, 68, 0.05);
}

.home-learning-panel,
.home-learning-stage {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.home-learning-stage,
.home-order-panel,
.home-community-panel,
.home-workbench-panel,
.home-tool-panel,
.lower-section {
  display: grid;
  gap: 14px;
  padding: 16px;
  border: 1px solid #e3e8f4;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(27, 39, 68, 0.05);
}

.home-promo-card {
  border: 0;
  box-shadow: none;
}

.home-workbench-panel {
  gap: 12px;
}

.home-community-panel,
.home-tool-panel {
  gap: 12px;
}

.panel-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
}

.panel-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #172033;
  font-size: 18px;
  line-height: 1.2;
  font-weight: 900;
}

.panel-header p {
  margin: 6px 0 0;
  color: #667085;
  line-height: 1.55;
}

.section-link {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 999px;
  padding: 0 12px;
  color: #6354f6;
  background: #f0edff;
  font-weight: 800;
  white-space: nowrap;
}

.learning-stage-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  grid-auto-rows: 62px;
  gap: 12px;
}

.learning-card {
  min-width: 0;
  display: grid;
  gap: 7px;
  border: 1px solid #e3e8f4;
  border-radius: 8px;
  padding: 12px;
  background: linear-gradient(180deg, #fff 0%, #fbfcff 100%);
  text-align: left;
}

.learning-feature {
  grid-row: span 2;
  min-height: 134px;
}

.learning-mini {
  align-content: start;
  min-height: 62px;
  gap: 6px;
  padding: 12px 13px;
}

.learning-mini .card-badge,
.learning-mini small {
  display: none;
}

.learning-mini strong {
  font-size: 14px;
  line-height: 1.35;
}

.card-badge {
  justify-self: start;
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0 8px;
  background: #f2f5ff;
  color: #5d4ef4;
  font-size: 12px;
  font-weight: 900;
}

.card-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: #f6f7ff;
  color: #5d4ef4;
}

.learning-card strong,
.learning-card small,
.order-card strong,
.order-card small,
.tool-card strong,
.tool-card small,
.template-card strong,
.template-card small,
.community-card strong,
.community-card small,
.lower-card strong,
.lower-card small {
  min-width: 0;
  display: block;
  overflow-wrap: anywhere;
}

.learning-card strong {
  color: #1c2435;
  font-size: 14px;
  line-height: 1.3;
}

.learning-feature strong {
  font-size: 15px;
}

.learning-card small {
  color: #667085;
  font-size: 12px;
  line-height: 1.4;
}

.home-promo-carousel {
  display: grid;
  gap: 12px;
  padding: 14px;
  min-height: 100%;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 243, 239, 0.94)),
    linear-gradient(150deg, #ffb26b 0%, #ff704f 38%, #ff533d 100%);
}

.home-promo-card {
  background: linear-gradient(180deg, #ff7a3f 0%, #ff633f 52%, #ff8a58 100%);
}

.promo-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.promo-mark {
  min-height: 26px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border-radius: 999px;
  color: #8b5a00;
  background: #ffe8b6;
  font-size: 12px;
  font-weight: 900;
}

.promo-hint {
  color: rgba(84, 61, 38, 0.78);
  font-size: 11px;
  font-weight: 700;
}

.promo-body {
  display: grid;
  gap: 12px;
}

.promo-copy h2 {
  margin: 0;
  color: #fff;
  font-size: 22px;
  line-height: 1.12;
  letter-spacing: 0;
}

.promo-kicker {
  margin: 0 0 8px;
  color: #fff1d0;
  font-size: 12px;
  font-weight: 900;
}

.promo-subtitle {
  margin: 8px 0 0;
  color: rgba(255, 255, 255, 0.93);
  line-height: 1.45;
  font-size: 14px;
  max-height: 44px;
  overflow: hidden;
}

.promo-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.promo-primary,
.promo-secondary {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 8px;
  padding: 0 12px;
  font-weight: 900;
}

.promo-primary {
  color: #fff;
  background: #ff6c3f;
  box-shadow: 0 12px 24px rgba(255, 104, 55, 0.26);
}

.promo-secondary {
  color: #4c2c1b;
  background: #ffe5b2;
}

.promo-visual {
  min-height: 104px;
}

.promo-image-wrap {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 8px;
}

.promo-image-wrap img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.promo-sheet-stack {
  position: relative;
  min-height: 104px;
}

.promo-sheet {
  position: absolute;
  border-radius: 8px;
  box-shadow: 0 12px 28px rgba(111, 57, 41, 0.18);
}

.promo-sheet-back {
  inset: 16px 16px 6px 12px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.82), rgba(255, 226, 209, 0.82));
  transform: rotate(-4deg);
}

.promo-sheet-mid {
  inset: 10px 40px 10px 38px;
  display: grid;
  align-content: center;
  gap: 6px;
  padding: 12px;
  background: linear-gradient(135deg, #ffffff, #fff8ee);
  transform: rotate(2deg);
}

.promo-sheet-front {
  inset: 0 72px 28px 0;
  display: grid;
  gap: 8px;
  padding: 12px;
  color: #fff;
  background: linear-gradient(135deg, #ff7a42 0%, #ff5a3c 100%);
}

.promo-sheet-tag {
  justify-self: start;
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  padding: 0 8px;
  border-radius: 999px;
  color: #8b5a00;
  background: #ffe7ba;
  font-size: 12px;
  font-weight: 900;
}

.promo-sheet-mid strong {
  color: #1d2433;
  font-size: 16px;
}

.promo-sheet-mid small {
  color: #6e7584;
  line-height: 1.5;
}

.promo-sheet-head {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  font-size: 12px;
}

.promo-sheet-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.promo-sheet-grid span {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.16);
  font-size: 11px;
  font-weight: 800;
}

.promo-slide-dots {
  display: flex;
  align-items: center;
  gap: 8px;
}

.promo-dot {
  width: 10px;
  height: 10px;
  border: 0;
  border-radius: 999px;
  background: #e5e7ef;
}

.promo-dot.active {
  width: 26px;
}

.home-kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.kpi-card {
  min-width: 0;
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  grid-template-areas:
    "icon label value"
    "icon trend value";
  align-items: center;
  column-gap: 10px;
  row-gap: 4px;
  border: 1px solid #e3e8f4;
  border-radius: 8px;
  min-height: 74px;
  padding: 12px 14px;
  background: #fff;
  text-align: left;
}

.kpi-card strong {
  grid-area: value;
  justify-self: end;
  color: #182033;
  font-size: 24px;
  line-height: 1;
}

.kpi-label {
  grid-area: label;
  color: #667085;
  font-size: 13px;
  font-weight: 800;
}

.kpi-trend {
  grid-area: trend;
  color: #667085;
  line-height: 1.25;
  font-size: 11px;
}

.kpi-icon {
  grid-area: icon;
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  background: #eef1ff;
  color: #5d4ef4;
}

.kpi-card.tone-gold .kpi-icon,
.order-card.tone-gold .order-icon,
.tool-card.tone-gold .tool-icon,
.template-card.tone-gold .template-icon,
.community-card.tone-gold .community-preview-chip,
.lower-card.tone-gold .lower-card-icon,
.learning-card.tone-gold .card-icon {
  color: #8b5a00;
  background: #fff0cc;
}

.kpi-card.tone-blue .kpi-icon,
.order-card.tone-blue .order-icon,
.tool-card.tone-blue .tool-icon,
.template-card.tone-blue .template-icon,
.community-card.tone-blue .community-preview-chip,
.lower-card.tone-blue .lower-card-icon,
.learning-card.tone-blue .card-icon {
  color: #1d4ed8;
  background: #e8f0ff;
}

.kpi-card.tone-violet .kpi-icon,
.order-card.tone-violet .order-icon,
.tool-card.tone-violet .tool-icon,
.template-card.tone-violet .template-icon,
.community-card.tone-violet .community-preview-chip,
.lower-card.tone-violet .lower-card-icon,
.learning-card.tone-violet .card-icon {
  color: #6354f6;
  background: #efeaff;
}

.kpi-card.tone-green .kpi-icon,
.order-card.tone-green .order-icon,
.tool-card.tone-green .tool-icon,
.template-card.tone-green .template-icon,
.community-card.tone-green .community-preview-chip,
.lower-card.tone-green .lower-card-icon,
.learning-card.tone-green .card-icon {
  color: #0b8a56;
  background: #e7f9ef;
}

.kpi-card.tone-orange .kpi-icon,
.order-card.tone-orange .order-icon,
.tool-card.tone-orange .tool-icon,
.template-card.tone-orange .template-icon,
.community-card.tone-orange .community-preview-chip,
.lower-card.tone-orange .lower-card-icon,
.learning-card.tone-orange .card-icon {
  color: #c35b12;
  background: #fff1e2;
}

.home-order-panel,
.home-community-panel,
.home-workbench-panel,
.home-tool-panel,
.lower-section {
  padding: 0;
}

.order-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.order-card,
.tool-card,
.template-card,
.community-card,
.lower-card {
  min-width: 0;
  display: grid;
  gap: 8px;
  border: 1px solid #e3e8f4;
  border-radius: 8px;
  padding: 14px;
  background: #fff;
  text-align: left;
}

.order-card {
  min-height: 84px;
  padding: 12px;
  gap: 6px;
}

.order-icon,
.tool-icon,
.template-icon,
.lower-card-icon {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #5d4ef4;
  background: #eef1ff;
}

.order-card strong,
.tool-card strong,
.template-card strong,
.lower-card strong {
  color: #172033;
  font-size: 15px;
  line-height: 1.32;
}

.order-card small,
.tool-card small,
.template-card small,
.lower-card small {
  color: #667085;
  line-height: 1.38;
  font-size: 12px;
}

.home-community-panel {
  display: grid;
  gap: 14px;
}

.community-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.community-tabs button {
  min-height: 30px;
  border: 0;
  border-radius: 0;
  padding: 0;
  color: #3a4255;
  background: transparent;
  font-weight: 700;
}

.community-tabs button.active {
  color: #6354f6;
  box-shadow: inset 0 -3px 0 #6354f6;
}

.community-gallery,
.community-banner-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.community-card {
  min-height: 186px;
}

.community-card.active {
  border-color: #b6c5ff;
  box-shadow: 0 14px 28px rgba(95, 83, 244, 0.12);
}

.community-preview {
  position: relative;
  overflow: hidden;
  min-height: 110px;
  border-radius: 8px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.26)),
    linear-gradient(135deg, #eef1ff 0%, #dde6ff 100%);
}

.community-preview-chip {
  position: absolute;
  top: 12px;
  left: 12px;
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0 8px;
  color: #6354f6;
  background: #efeaff;
  font-size: 12px;
  font-weight: 900;
}

.community-preview-grid {
  position: absolute;
  inset: auto 12px 12px 12px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.community-preview-grid i {
  height: 34px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.65);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.4);
}

.community-highlight {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #f6f4ff 0%, #eef4ff 100%);
}

.community-highlight-label {
  color: #6354f6;
  font-size: 12px;
  font-weight: 900;
}

.community-highlight strong {
  font-size: 16px;
}

.community-highlight p {
  margin: 0;
  color: #667085;
  line-height: 1.6;
}

.home-dual-row {
  display: grid;
  grid-template-columns: minmax(0, 1.04fr) minmax(0, 0.96fr);
  gap: 18px;
}

.workbench-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px 10px;
}

.workbench-card {
  min-height: 84px;
  justify-items: center;
  align-content: center;
  gap: 8px;
  padding: 12px 8px;
}

.workbench-card strong {
  font-size: 13px;
  text-align: center;
}

.workbench-card .workbench-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
}

.workbench-recent,
.community-footer-strip,
.tool-footer-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid #e6e9f4;
  border-radius: 8px;
  background: #fbfcff;
  color: #667085;
  font-size: 12px;
}

.workbench-recent > span,
.community-footer-tag,
.tool-footer-tag {
  color: #6354f6;
  font-weight: 800;
  white-space: nowrap;
}

.community-footer-tag.muted,
.tool-footer-tag.new {
  color: #ef4444;
}

.workbench-recent-icons {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.workbench-recent-icons button {
  width: 26px;
  height: 26px;
  border: 0;
  border-radius: 8px;
  background: #eef1ff;
  color: #6354f6;
}

.workbench-more {
  margin-left: auto;
  border: 0;
  color: #6354f6;
  background: transparent;
  font-weight: 800;
}

.template-grid.home-tool-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.tool-card,
.template-card {
  min-height: 104px;
}

.home-lower-stack {
  display: grid;
  gap: 18px;
}

.lower-section {
  display: grid;
  gap: 14px;
}

.section-layout {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  border: 1px solid #e3e8f4;
  border-radius: 999px;
  padding: 0 10px;
  color: #667085;
  background: #fff;
  font-size: 12px;
  font-weight: 800;
}

.lower-grid {
  display: grid;
  gap: 12px;
}

.grid-learning,
.grid-order,
.grid-template,
.grid-task,
.grid-banner,
.grid-ranking {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.grid-tool {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.grid-third-party {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.grid-default {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.lower-card {
  min-height: 116px;
}

.tone-gold {
  border-color: #f0d9a6;
}

.tone-blue {
  border-color: #cfe0ff;
}

.tone-violet {
  border-color: #d8d2ff;
}

.tone-green {
  border-color: #cfead9;
}

.tone-orange {
  border-color: #f6d2ba;
}

.home-dashboard button:hover {
  border-color: #b8c7ff;
  box-shadow: 0 10px 24px rgba(90, 101, 180, 0.08);
}

.home-dashboard button:focus-visible {
  outline: 2px solid rgba(90, 101, 244, 0.34);
  outline-offset: 2px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 1080px) {
  .home-first-screen,
  .home-hero-stage,
  .home-dual-row {
    grid-template-columns: 1fr;
  }

  .community-gallery,
  .community-banner-row,
  .order-grid,
  .learning-stage-grid,
  .tool-grid.home-workbench-grid,
  .template-grid.home-tool-grid,
  .grid-learning,
  .grid-order,
  .grid-template,
  .grid-task,
  .grid-banner,
  .grid-ranking,
  .grid-tool,
  .grid-third-party {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .home-kpi-strip,
  .community-gallery,
  .community-banner-row,
  .learning-stage-grid,
  .tool-grid.home-workbench-grid,
  .template-grid.home-tool-grid,
  .grid-learning,
  .grid-order,
  .grid-template,
  .grid-task,
  .grid-banner,
  .grid-ranking,
  .grid-tool,
  .grid-third-party,
  .order-grid {
    grid-template-columns: 1fr;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

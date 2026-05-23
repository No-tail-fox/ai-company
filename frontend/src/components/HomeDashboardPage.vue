<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ChevronRight } from 'lucide-vue-next';
import { getIcon } from '../services/icons';
import type { HomeDashboardModel, HomeDashboardSlide, PortalItem } from '../services/viewModel';

const props = defineProps<{
  model: HomeDashboardModel;
}>();

const emit = defineEmits<{
  (event: 'open-item', item: PortalItem): void;
}>();

type Tone = 'gold' | 'blue' | 'cyan' | 'orange' | 'green' | 'violet' | 'red';

const router = useRouter();
const activeSlideIndex = ref(0);

const workbenchToneCycle: Tone[] = ['violet', 'cyan', 'orange', 'red', 'green', 'violet'];
const priorityToneCycle: Tone[] = ['blue', 'violet', 'green', 'orange', 'cyan'];

const sectionMap = computed(() => new Map(props.model.sections.map((section) => [section.sectionKey, section])));
const learningSection = computed(() => sectionMap.value.get('learning_center'));
const orderSection = computed(() => sectionMap.value.get('order_center'));
const communitySection = computed(() => sectionMap.value.get('communities'));
const workbenchSection = computed(() => sectionMap.value.get('workbench_shortcuts') ?? sectionMap.value.get('workspace_tools'));
const toolSection = computed(() => sectionMap.value.get('home_tools') ?? sectionMap.value.get('toolkit'));

const heroSlides = computed(() => sortSlides(props.model.heroSlides));
const activeSlide = computed(() => {
  const slides = heroSlides.value;
  if (slides.length === 0) {
    return fallbackSlide();
  }
  return slides[activeSlideIndex.value % slides.length] ?? slides[0];
});
const ctaSecondaryLabel = computed(() => String(activeSlide.value.metadata?.secondaryLabel ?? activeSlide.value.metadata?.secondary_label ?? '查看权益'));
const countdownChips = computed(() => {
  const raw = activeSlide.value.metadata?.countdown;
  if (Array.isArray(raw) && raw.length > 0) {
    return raw.slice(0, 4).map((item) => String(item));
  }
  return ['03', '23', '45', '18'];
});
const slideTeasers = computed(() => {
  const raw = activeSlide.value.metadata?.teasers;
  if (Array.isArray(raw) && raw.length > 0) {
    return raw.slice(0, 3).map((item) => String(item));
  }
  return ['电商详情页模板', '小红书爆款笔记', '年终总结汇报模板'];
});
const hasSlideCount = computed(() => heroSlides.value.length > 0);
const kpiCards = computed(() => props.model.kpiCards.slice(0, 4));
const orderCards = computed(() => sortItems(orderSection.value?.items ?? []));
const workbenchCards = computed(() => sortItems(props.model.workbenchShortcuts).slice(0, 6));
const communityCards = computed(() => {
  const sectionItems = communitySection.value?.items ?? [];
  return sortItems(sectionItems.length > 0 ? sectionItems : props.model.communityCards).slice(0, 4);
});
const toolCards = computed(() => {
  const sectionItems = toolSection.value?.items ?? [];
  return sortItems(sectionItems.length > 0 ? sectionItems : props.model.toolCards).slice(0, 5);
});
const communityPanelTitle = computed(() =>
  homePanelTitle(communitySection.value?.title, '精选社群', ['兴趣社群'])
);
const toolPanelTitle = computed(() =>
  homePanelTitle(toolSection.value?.title, '热门工具', ['专业工具包'])
);
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

function sortSlides(slides: HomeDashboardSlide[]) {
  return [...slides].sort((left, right) => left.sortOrder - right.sortOrder);
}

function sortItems(items: PortalItem[]) {
  return [...items].sort((left, right) => left.sortOrder - right.sortOrder);
}

function homePanelTitle(title: string | undefined, fallback: string, legacyTitles: string[]) {
  const trimmed = title?.trim();
  if (!trimmed || legacyTitles.includes(trimmed)) {
    return fallback;
  }
  return trimmed;
}

function fallbackSlide(): HomeDashboardSlide {
  return {
    id: 'fallback-home-slide',
    title: '会员活动限时特惠',
    subtitle: '开通会员解锁模板、社群和交付资料',
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
    fallbackLearningCard('home-learning-fallback-1', '《0基础AI通识课》', '12 大核心渠道从认知到上手一站式通关', '基础必备', 'FileVideo', '/workspace/course', 10),
    fallbackLearningCard('home-learning-fallback-2', '《AI 实战必修课》', '办公、剪辑、写作全场景效率翻倍', '基础必备', 'MonitorPlay', '/workspace/course', 20),
    fallbackLearningCard('home-learning-fallback-3', '《AI 商业变现课》', '内容创作 + 电商营销全链路落地盈利', '接单变现', 'ScanSearch', '/workspace/course', 30),
    fallbackLearningCard('home-learning-fallback-4', '《AI 爆款内容创作》', '短视频脚本、标题、封面和投放流程', 'AI 营销', 'Presentation', '/workspace/course', 40),
    fallbackLearningCard('home-learning-fallback-5', '《AI高阶实战》', '从工具使用到项目交付训练', '学习成长', 'NotebookTabs', '/workspace/course/advanced', 50),
    fallbackLearningCard('home-learning-fallback-6', '《AI项目交付训练》', '拆解真实客户需求并完成可复用方案', '项目共创', 'BriefcaseBusiness', '/workspace/course/project', 60),
    fallbackLearningCard('home-learning-fallback-7', '查看更多课程', '打开学习成长查看完整课程路径', '课程目录', 'ChevronRight', '/learning', 999)
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

function fallbackLearningCard(
  id: string,
  title: string,
  subtitle: string,
  category: string,
  icon: string,
  actionValue: string,
  sortOrder: number
): PortalItem {
  return {
    id,
    itemType: 'course',
    title,
    subtitle,
    category,
    icon,
    imageUrl: '',
    badge: category,
    tags: [],
    sortOrder,
    enabled: true,
    actionType: 'route',
    actionValue,
    requiredMembership: false,
    pointCost: 0,
    metadata: {}
  };
}

function accentFromSlide(slide: HomeDashboardSlide) {
  const accent = String(slide.metadata?.accent ?? '').toLowerCase();
  if (['blue', 'green', 'violet', 'orange', 'cyan', 'red'].includes(accent)) {
    return accent as Tone;
  }
  return 'gold';
}

function accentFromItem(item: PortalItem, fallbackTone: Tone = 'blue') {
  const metadataTone = String(item.metadata?.tone ?? '').toLowerCase();
  if (['gold', 'blue', 'green', 'violet', 'orange', 'cyan', 'red'].includes(metadataTone)) {
    return metadataTone as Tone;
  }
  const source = `${item.category} ${item.title} ${item.subtitle}`.toLowerCase();
  if (source.includes('会员') || source.includes('权益') || source.includes('接单')) {
    return 'gold';
  }
  if (source.includes('社群') || source.includes('群')) {
    return 'green';
  }
  if (source.includes('工作台') || source.includes('工具') || source.includes('办公')) {
    return 'violet';
  }
  if (source.includes('视频') || source.includes('脚本')) {
    return 'orange';
  }
  if (source.includes('图片') || source.includes('素材')) {
    return 'cyan';
  }
  return fallbackTone;
}

function toneClass(item: PortalItem, fallbackTone: Tone) {
  return `tone-${accentFromItem(item, fallbackTone)}`;
}

function setActiveSlide(index: number) {
  if (!hasSlideCount.value) {
    return;
  }
  activeSlideIndex.value = index;
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
</script>

<template>
  <main class="home-dashboard">
    <section class="home-first-screen home-hero-stage">
      <article class="home-promo-carousel home-promo-card">
        <div class="promo-copy">
          <div class="promo-topline">
            <span class="promo-pill">
              <component :is="getIcon('Crown')" :size="15" />
              {{ activeSlide.badge || '限时特惠' }}
            </span>
            <span class="promo-pill ghost">尊享会员特权</span>
          </div>
          <h2>{{ activeSlide.title }}</h2>
          <p class="promo-subtitle">{{ activeSlide.subtitle }}</p>

          <div class="vip-benefit-row">
            <span>
              <component :is="getIcon('FileText')" :size="17" />
              专属模板
            </span>
            <span>
              <component :is="getIcon('WandSparkles')" :size="17" />
              AI工具特权
            </span>
            <span>
              <component :is="getIcon('Download')" :size="17" />
              无限下载
            </span>
            <span>
              <component :is="getIcon('Headphones')" :size="17" />
              优先客服
            </span>
          </div>

          <div class="vip-countdown-row">
            <span>活动倒计时</span>
            <strong v-for="chip in countdownChips" :key="chip">{{ chip }}</strong>
          </div>

          <div class="promo-actions">
            <button class="promo-primary" type="button" @click="openSlide(activeSlide)">
              {{ activeSlide.ctaLabel || '立即开通会员' }}
            </button>
            <button class="promo-secondary" type="button" @click="openMembershipBenefits">
              {{ ctaSecondaryLabel }}
              <ChevronRight :size="15" />
            </button>
          </div>
        </div>

        <div class="vip-visual-card">
          <div v-if="activeSlide.imageUrl" class="promo-image-wrap">
            <img :src="activeSlide.imageUrl" :alt="activeSlide.title" />
          </div>
          <template v-else>
            <div class="vip-card-plate">
              <span>VIP</span>
              <strong>+200</strong>
            </div>
            <div class="vip-gift-box">
              <span></span>
              <i></i>
            </div>
            <div class="vip-template-list">
              <strong>模板上新</strong>
              <button v-for="teaser in slideTeasers" :key="teaser" type="button" @click="openSlide(activeSlide)">
                {{ teaser }}
                <ChevronRight :size="14" />
              </button>
            </div>
          </template>
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
            v-for="(card, index) in workbenchCards"
            :key="card.id"
            :class="['workbench-card', 'workbench-app-card', toneClass(card, workbenchToneCycle[index % workbenchToneCycle.length])]"
            type="button"
            @click="openItem(card)"
          >
            <span class="workbench-app-icon">
              <component :is="getIcon(card.icon)" :size="25" />
            </span>
            <strong>{{ card.title }}</strong>
          </button>
        </div>

        <div class="workbench-recent">
          <span>最近使用</span>
          <div class="workbench-recent-icons">
            <button
              v-for="(card, index) in workbenchCards.slice(0, 5)"
              :key="`${card.id}-recent`"
              :class="toneClass(card, workbenchToneCycle[index % workbenchToneCycle.length])"
              type="button"
              @click="openItem(card)"
            >
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
          <component :is="getIcon(card.icon)" :size="25" />
        </span>
        <span class="kpi-copy">
          <span class="kpi-label">{{ card.label }}</span>
          <small class="kpi-trend">{{ card.trend }}</small>
        </span>
        <strong class="kpi-value">{{ card.value }}</strong>
      </button>
    </section>

    <section class="home-priority-row">
      <section class="home-community-panel featured-community-panel">
        <header class="panel-header">
          <div>
            <span class="panel-kicker">{{ communityPanelTitle }}</span>
            <p>{{ communitySection?.subtitle ?? '按成长阶段和赛道加入社群' }}</p>
          </div>
          <button class="section-link flat" type="button" @click="openDestination('route', '/community/starter')">
            <span>全部社群</span>
            <ChevronRight :size="16" />
          </button>
        </header>

        <div class="community-banner-row">
          <button
            v-for="(card, index) in communityCards"
            :key="card.id"
            :class="['community-card', toneClass(card, priorityToneCycle[index % priorityToneCycle.length])]"
            type="button"
            @click="openItem(card)"
          >
            <span class="community-icon">
              <component :is="getIcon(card.icon)" :size="24" />
            </span>
            <strong>{{ card.title }}</strong>
            <small>{{ card.subtitle }}</small>
            <span class="community-cta">加入群聊</span>
          </button>
        </div>

        <div class="community-footer-strip">
          <span class="community-footer-tag">公告</span>
          <span>本周直播：AI办公效率提升实战技巧</span>
          <span class="community-footer-tag muted">最新动态</span>
          <span>用户小明获得接单变现奖励¥888</span>
        </div>
      </section>

      <section class="home-tool-panel hot-tools-panel">
        <header class="panel-header">
          <div>
            <span class="panel-kicker">{{ toolPanelTitle }}</span>
            <p>{{ toolSection?.subtitle ?? '常用工具、办公模板、接单报价、内容生成、电商优化' }}</p>
          </div>
          <button class="section-link flat" type="button" @click="openDestination('route', '/toolkit/office')">
            <span>更多工具</span>
            <ChevronRight :size="16" />
          </button>
        </header>

        <div class="template-grid home-tool-grid">
          <button
            v-for="(card, index) in toolCards"
            :key="card.id"
            :class="['template-card', toneClass(card, priorityToneCycle[index % priorityToneCycle.length])]"
            type="button"
            @click="openItem(card)"
          >
            <span class="template-icon">
              <component :is="getIcon(card.icon)" :size="24" />
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

    <section class="home-learning-panel home-learning-stage">
      <header class="panel-header">
        <div>
          <span class="panel-kicker">{{ learningSection?.title ?? '常用AI学习中心' }}</span>
          <p>{{ learningSection?.subtitle ?? '课程、实战和变现路径' }}</p>
        </div>
        <button class="section-link" type="button" @click="openDestination('route', '/learning')">
          <span>查看全部</span>
          <ChevronRight :size="16" />
        </button>
      </header>

      <div class="learning-stage-grid">
        <button
          v-for="card in learningFeatured"
          :key="card.id"
          :class="['learning-card', 'learning-feature', toneClass(card, 'blue')]"
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
          :class="['learning-card', 'learning-mini', toneClass(card, 'blue')]"
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
          v-for="(card, index) in orderCards"
          :key="card.id"
          :class="['order-card', toneClass(card, priorityToneCycle[index % priorityToneCycle.length])]"
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

    <section class="home-lower-stack">
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
            v-for="(card, index) in sortItems(section.items)"
            :key="card.id"
            :class="['lower-card', toneClass(card, priorityToneCycle[index % priorityToneCycle.length])]"
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
  gap: 16px;
  padding-bottom: 48px;
  color: #172033;
}

.home-first-screen,
.home-hero-stage {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(330px, 0.78fr);
  gap: 18px;
  align-items: stretch;
}

.home-promo-carousel,
.home-promo-card,
.home-workbench-panel,
.home-learning-panel,
.home-order-panel,
.home-community-panel,
.home-tool-panel,
.lower-section {
  min-width: 0;
  border: 1px solid #dfe7f4;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 12px 26px rgba(26, 38, 64, 0.06);
}

.home-promo-card {
  position: relative;
  min-height: 310px;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 18px;
  padding: 22px 24px;
  color: #fff;
  border: 0;
  background:
    linear-gradient(110deg, rgba(255, 221, 139, 0.16) 0 1px, transparent 1px 78px),
    linear-gradient(135deg, #10175d 0%, #192878 48%, #0d164c 100%);
}

.home-promo-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, transparent 0%, rgba(255, 223, 161, 0.12) 58%, transparent 100%),
    repeating-linear-gradient(145deg, transparent 0 18px, rgba(255, 255, 255, 0.035) 19px 20px);
  pointer-events: none;
}

.promo-copy,
.vip-visual-card,
.promo-slide-dots {
  position: relative;
  z-index: 1;
}

.promo-copy {
  min-width: 0;
  display: grid;
  align-content: center;
  gap: 14px;
}

.promo-topline,
.vip-benefit-row,
.vip-countdown-row,
.promo-actions,
.panel-header,
.workbench-recent,
.community-footer-strip,
.tool-footer-strip {
  display: flex;
  align-items: center;
}

.promo-topline {
  gap: 10px;
  flex-wrap: wrap;
}

.promo-pill {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  border: 1px solid rgba(255, 218, 145, 0.54);
  border-radius: 999px;
  padding: 0 12px;
  color: #ffe3a7;
  background: rgba(255, 213, 125, 0.12);
  font-weight: 900;
}

.promo-pill.ghost {
  color: #f9d791;
  background: rgba(14, 19, 66, 0.35);
}

.promo-copy h2 {
  margin: 0;
  color: #ffecc1;
  font-size: 34px;
  line-height: 1.12;
  letter-spacing: 0;
}

.promo-subtitle {
  max-width: 560px;
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 17px;
  line-height: 1.6;
}

.vip-benefit-row {
  gap: 24px;
  flex-wrap: wrap;
  color: #f4d496;
}

.vip-benefit-row span {
  min-height: 30px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 800;
}

.vip-countdown-row {
  gap: 8px;
  flex-wrap: wrap;
  color: rgba(255, 255, 255, 0.86);
  font-weight: 800;
}

.vip-countdown-row strong {
  min-width: 36px;
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #1f244f;
  background: linear-gradient(180deg, #fff4ce 0%, #f4c86c 100%);
  box-shadow: 0 8px 18px rgba(244, 184, 86, 0.22);
}

.promo-actions {
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 2px;
}

.promo-primary,
.promo-secondary {
  min-height: 46px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border-radius: 999px;
  padding: 0 24px;
  font-weight: 900;
  white-space: nowrap;
}

.promo-primary {
  border: 1px solid rgba(255, 218, 145, 0.72);
  color: #fff;
  background: linear-gradient(180deg, #ff6a4e 0%, #ef3e35 100%);
  box-shadow: 0 14px 26px rgba(240, 63, 54, 0.32);
}

.promo-secondary {
  border: 1px solid rgba(255, 214, 142, 0.62);
  color: #3f260b;
  background: linear-gradient(180deg, #ffe8ad 0%, #f8bf5f 100%);
}

.vip-visual-card {
  min-width: 0;
  position: relative;
  align-self: stretch;
  min-height: 252px;
}

.promo-image-wrap {
  width: 100%;
  height: 100%;
  min-height: 252px;
  overflow: hidden;
  border-radius: 8px;
}

.promo-image-wrap img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.vip-card-plate {
  position: absolute;
  top: 24px;
  left: 22px;
  width: 174px;
  height: 126px;
  display: grid;
  align-content: center;
  justify-items: center;
  gap: 4px;
  border-radius: 24px;
  color: #7a4308;
  background: linear-gradient(135deg, #ffe5a9 0%, #c58029 100%);
  box-shadow: 0 22px 40px rgba(2, 8, 43, 0.32);
  transform: rotate(5deg);
}

.vip-card-plate span {
  font-size: 36px;
  font-weight: 1000;
  letter-spacing: 0;
}

.vip-card-plate strong {
  color: #fff7d6;
  font-size: 28px;
  line-height: 1;
}

.vip-gift-box {
  position: absolute;
  right: 42px;
  bottom: 38px;
  width: 102px;
  height: 90px;
  border-radius: 14px;
  background: linear-gradient(135deg, #ff745b 0%, #d92e35 100%);
  box-shadow: 0 18px 34px rgba(4, 11, 46, 0.28);
}

.vip-gift-box span,
.vip-gift-box i {
  position: absolute;
  display: block;
  background: #ffd989;
}

.vip-gift-box span {
  left: 45px;
  top: 0;
  bottom: 0;
  width: 13px;
}

.vip-gift-box i {
  left: 0;
  right: 0;
  top: 30px;
  height: 12px;
}

.vip-template-list {
  position: absolute;
  right: 0;
  top: 28px;
  width: 190px;
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.09);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
}

.vip-template-list strong {
  color: #fff8d9;
  font-size: 15px;
}

.vip-template-list button {
  min-height: 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 8px;
  padding: 0 10px;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.1);
  text-align: left;
}

.promo-slide-dots {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.promo-dot {
  width: 10px;
  height: 10px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.56);
}

.promo-dot.active {
  width: 28px;
  background: #fff;
}

.home-workbench-panel,
.home-learning-panel,
.home-order-panel,
.home-community-panel,
.home-tool-panel,
.lower-section {
  display: grid;
  gap: 14px;
  padding: 18px;
}

.panel-header {
  justify-content: space-between;
  gap: 14px;
}

.panel-kicker {
  display: inline-flex;
  align-items: center;
  color: #101828;
  font-size: 20px;
  line-height: 1.15;
  font-weight: 900;
}

.panel-header p {
  margin: 6px 0 0;
  color: #667085;
  line-height: 1.45;
}

.section-link {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 999px;
  padding: 0 13px;
  color: #6354f6;
  background: #f0edff;
  font-weight: 900;
  white-space: nowrap;
}

.section-link.flat {
  background: transparent;
}

.workbench-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px 16px;
}

.workbench-card,
.kpi-card,
.learning-card,
.order-card,
.template-card,
.community-card,
.lower-card {
  min-width: 0;
  border: 1px solid #e3e9f3;
  border-radius: 8px;
  background: #fff;
  text-align: left;
}

.workbench-app-card {
  min-height: 112px;
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 10px;
  padding: 14px 10px;
}

.workbench-app-card strong {
  color: #172033;
  font-size: 15px;
  line-height: 1.3;
  text-align: center;
}

.workbench-app-icon,
.kpi-icon,
.card-icon,
.order-icon,
.template-icon,
.community-icon,
.lower-card-icon {
  display: grid;
  place-items: center;
  color: #5d4ef4;
  background: #eef1ff;
}

.workbench-app-icon {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(135deg, #8066ff 0%, #5a45df 100%);
  box-shadow: 0 10px 20px rgba(98, 77, 234, 0.18);
}

.workbench-recent,
.community-footer-strip,
.tool-footer-strip {
  gap: 10px;
  min-height: 36px;
  overflow: hidden;
  padding: 0 12px;
  border: 1px solid #e7ebf4;
  border-radius: 8px;
  background: #fbfcff;
  color: #667085;
  font-size: 12px;
}

.workbench-recent > span,
.community-footer-tag,
.tool-footer-tag {
  color: #6354f6;
  font-weight: 900;
  white-space: nowrap;
}

.workbench-recent-icons {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.workbench-recent-icons button {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 8px;
  color: #6354f6;
  background: #eef1ff;
}

.workbench-more {
  flex: 0 0 auto;
  margin-left: auto;
  border: 0;
  color: #6354f6;
  background: transparent;
  font-weight: 900;
}

.home-kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.kpi-card {
  min-height: 128px;
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 18px;
  box-shadow: 0 10px 24px rgba(26, 38, 64, 0.05);
}

.kpi-icon {
  width: 58px;
  height: 58px;
  border-radius: 50%;
}

.kpi-copy {
  min-width: 0;
  display: grid;
  gap: 7px;
}

.kpi-label {
  color: #1f2937;
  font-size: 16px;
  font-weight: 900;
}

.kpi-trend {
  min-width: 0;
  color: #667085;
  line-height: 1.4;
}

.kpi-value {
  justify-self: end;
  color: #0f172a;
  font-size: 32px;
  line-height: 1;
}

.home-priority-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(380px, 0.9fr);
  gap: 18px;
}

.community-banner-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.community-card {
  min-height: 122px;
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 14px 12px;
  text-align: center;
}

.community-icon,
.template-icon,
.order-icon,
.lower-card-icon,
.card-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
}

.community-card strong,
.community-card small,
.template-card strong,
.template-card small,
.learning-card strong,
.learning-card small,
.order-card strong,
.order-card small,
.lower-card strong,
.lower-card small {
  min-width: 0;
  display: block;
  overflow-wrap: anywhere;
}

.community-card strong {
  color: #172033;
  font-size: 15px;
  line-height: 1.25;
}

.community-card small {
  color: #667085;
  font-size: 12px;
  line-height: 1.35;
}

.community-cta {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #bcb4ff;
  border-radius: 999px;
  padding: 0 14px;
  color: #6354f6;
  font-size: 12px;
  font-weight: 900;
}

.community-footer-tag.muted,
.tool-footer-tag.new {
  color: #ef4444;
}

.template-grid.home-tool-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.template-card,
.order-card,
.lower-card {
  display: grid;
  gap: 8px;
  align-content: start;
  padding: 14px;
}

.template-card {
  min-height: 126px;
  justify-items: center;
  text-align: center;
}

.template-card strong,
.order-card strong,
.lower-card strong {
  color: #172033;
  font-size: 15px;
  line-height: 1.3;
}

.template-card small,
.order-card small,
.lower-card small {
  color: #667085;
  line-height: 1.38;
  font-size: 12px;
}

.learning-stage-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  grid-auto-rows: 62px;
  gap: 12px;
}

.learning-card {
  display: grid;
  gap: 7px;
  padding: 12px;
  background: linear-gradient(180deg, #fff 0%, #fbfcff 100%);
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

.order-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.order-card {
  min-height: 92px;
}

.home-lower-stack {
  display: grid;
  gap: 18px;
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
  border-color: #f1d79b;
}

.tone-blue {
  border-color: #cfe0ff;
}

.tone-cyan {
  border-color: #bfeafe;
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

.tone-red {
  border-color: #ffd1cf;
}

.tone-gold .workbench-app-icon,
.tone-gold .kpi-icon,
.tone-gold .order-icon,
.tone-gold .template-icon,
.tone-gold .community-icon,
.tone-gold .lower-card-icon,
.tone-gold .card-icon {
  color: #8b5a00;
  background: #fff0cc;
}

.tone-blue .workbench-app-icon,
.tone-blue .kpi-icon,
.tone-blue .order-icon,
.tone-blue .template-icon,
.tone-blue .community-icon,
.tone-blue .lower-card-icon,
.tone-blue .card-icon {
  color: #1d4ed8;
  background: #e8f0ff;
}

.tone-cyan .workbench-app-icon,
.tone-cyan .kpi-icon,
.tone-cyan .order-icon,
.tone-cyan .template-icon,
.tone-cyan .community-icon,
.tone-cyan .lower-card-icon,
.tone-cyan .card-icon {
  color: #027a9e;
  background: #e5f7ff;
}

.tone-violet .workbench-app-icon,
.tone-violet .kpi-icon,
.tone-violet .order-icon,
.tone-violet .template-icon,
.tone-violet .community-icon,
.tone-violet .lower-card-icon,
.tone-violet .card-icon {
  color: #6354f6;
  background: #efeaff;
}

.tone-green .workbench-app-icon,
.tone-green .kpi-icon,
.tone-green .order-icon,
.tone-green .template-icon,
.tone-green .community-icon,
.tone-green .lower-card-icon,
.tone-green .card-icon {
  color: #0b8a56;
  background: #e7f9ef;
}

.tone-orange .workbench-app-icon,
.tone-orange .kpi-icon,
.tone-orange .order-icon,
.tone-orange .template-icon,
.tone-orange .community-icon,
.tone-orange .lower-card-icon,
.tone-orange .card-icon {
  color: #c35b12;
  background: #fff1e2;
}

.tone-red .workbench-app-icon,
.tone-red .kpi-icon,
.tone-red .order-icon,
.tone-red .template-icon,
.tone-red .community-icon,
.tone-red .lower-card-icon,
.tone-red .card-icon {
  color: #d43d30;
  background: #fff0f0;
}

.workbench-app-card.tone-violet .workbench-app-icon {
  color: #fff;
  background: linear-gradient(135deg, #8066ff 0%, #5a45df 100%);
}

.workbench-app-card.tone-cyan .workbench-app-icon {
  color: #fff;
  background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
}

.workbench-app-card.tone-orange .workbench-app-icon {
  color: #fff;
  background: linear-gradient(135deg, #ffb25f 0%, #f97316 100%);
}

.workbench-app-card.tone-red .workbench-app-icon {
  color: #fff;
  background: linear-gradient(135deg, #ff7669 0%, #ef4444 100%);
}

.workbench-app-card.tone-green .workbench-app-icon {
  color: #fff;
  background: linear-gradient(135deg, #7bd86f 0%, #22a35a 100%);
}

.home-dashboard button:hover {
  border-color: #b8c7ff;
  box-shadow: 0 12px 24px rgba(90, 101, 180, 0.1);
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

@media (max-width: 1320px) {
  .home-promo-card {
    grid-template-columns: minmax(0, 1fr) 300px;
  }

  .home-priority-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1080px) {
  .home-first-screen,
  .home-hero-stage {
    grid-template-columns: 1fr;
  }

  .home-promo-card,
  .home-priority-row {
    grid-template-columns: 1fr;
  }

  .vip-visual-card {
    min-height: 240px;
  }

  .home-kpi-strip,
  .community-banner-row,
  .template-grid.home-tool-grid,
  .order-grid,
  .learning-stage-grid,
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
  .workbench-grid,
  .community-banner-row,
  .template-grid.home-tool-grid,
  .order-grid,
  .learning-stage-grid,
  .grid-learning,
  .grid-order,
  .grid-template,
  .grid-task,
  .grid-banner,
  .grid-ranking,
  .grid-tool,
  .grid-third-party {
    grid-template-columns: 1fr;
  }

  .home-promo-card {
    min-height: 0;
    padding: 20px;
  }

  .promo-copy h2 {
    font-size: 28px;
  }

  .vip-template-list {
    position: relative;
    top: auto;
    right: auto;
    width: 100%;
    margin-top: 168px;
  }

  .panel-header,
  .kpi-card {
    align-items: flex-start;
  }

  .panel-header {
    flex-direction: column;
  }

  .kpi-card {
    grid-template-columns: 58px minmax(0, 1fr);
  }

  .kpi-value {
    grid-column: 1 / -1;
    justify-self: start;
  }
}
</style>

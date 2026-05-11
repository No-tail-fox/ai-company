<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import {
  ArrowLeft,
  BadgeCheck,
  BriefcaseBusiness,
  ChevronRight,
  Crown,
  Gift,
  LayoutGrid,
  MessageCircle,
  MonitorPlay,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Users
} from 'lucide-vue-next';
import { fetchAccountSummary, fetchHomeDashboard } from '../services/api';
import type { AccountSummary, HomeDashboardModel, HomeDashboardSlide } from '../services/viewModel';

type Tone = 'gold' | 'blue' | 'violet' | 'green' | 'orange';

const router = useRouter();
const loading = ref(true);
const account = ref<AccountSummary | null>(null);
const dashboard = ref<HomeDashboardModel | null>(null);
const activeSlideIndex = ref(0);
const benefitsRef = ref<HTMLElement | null>(null);

const fallbackSlides: HomeDashboardSlide[] = [
  {
    id: 'fallback-slide-vip',
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
    metadata: { accent: 'gold' }
  },
  {
    id: 'fallback-slide-template',
    title: '模板上新不停',
    subtitle: 'PPT、报价单、社媒和交付模板持续更新',
    badge: '今日上新',
    ctaLabel: '立即查看',
    ctaSubtitle: '今天就能直接用',
    imageUrl: '',
    actionType: 'route',
    actionValue: '/templates',
    sortOrder: 20,
    enabled: true,
    metadata: { accent: 'blue' }
  },
  {
    id: 'fallback-slide-community',
    title: '社群和工作台一起用',
    subtitle: '入门群、打卡群、接单群和资源群都在这里',
    badge: '社群活跃',
    ctaLabel: '进入社群',
    ctaSubtitle: '打开首页就能直达',
    imageUrl: '',
    actionType: 'route',
    actionValue: '/community/starter',
    sortOrder: 30,
    enabled: true,
    metadata: { accent: 'green' }
  }
];

const benefitCards = [
  {
    title: '模板上新',
    subtitle: 'PPT、报价单、脚本和复盘模板持续更新',
    icon: Gift,
    tone: 'gold',
    actionValue: '/templates'
  },
  {
    title: '社群入口',
    subtitle: '入门群、打卡群、接单群和资源群',
    icon: Users,
    tone: 'blue',
    actionValue: '/community/starter'
  },
  {
    title: '接单资料',
    subtitle: '报价、验收和复购跟进素材一键可用',
    icon: BriefcaseBusiness,
    tone: 'orange',
    actionValue: '/workspace/deliveries'
  },
  {
    title: '工作台捷径',
    subtitle: 'AI 对话、图片、视频和素材库统一入口',
    icon: LayoutGrid,
    tone: 'violet',
    actionValue: '/workbench'
  },
  {
    title: '优先更新',
    subtitle: '新内容优先看见，后台可随时替换',
    icon: Sparkles,
    tone: 'green',
    actionValue: '/home'
  },
  {
    title: '会员权益',
    subtitle: '模板、社群和接单内容统一解锁',
    icon: ShieldCheck,
    tone: 'gold',
    actionValue: '/home'
  }
] as const;

const communityCards = [
  {
    title: '入门交流群',
    subtitle: '新人答疑、工具清单和上手路线',
    icon: MessageCircle,
    tone: 'red',
    actionValue: '/community/starter'
  },
  {
    title: '学习打卡群',
    subtitle: '每日任务、案例拆解和作业反馈',
    icon: BadgeCheck,
    tone: 'violet',
    actionValue: '/community/study'
  },
  {
    title: '接单变现群',
    subtitle: '接单案例、报价模板和交付流程',
    icon: BriefcaseBusiness,
    tone: 'blue',
    actionValue: '/community/orders'
  },
  {
    title: '资源对接群',
    subtitle: '工具资源、客户线索和行业资料交换',
    icon: Users,
    tone: 'gold',
    actionValue: '/community/resources'
  }
] as const;

const templateCards = computed(() => heroSlides.value.slice(0, 3));

const heroSlides = computed(() => dashboard.value?.heroSlides?.length ? dashboard.value.heroSlides : fallbackSlides);
const activeSlide = computed(() => heroSlides.value[activeSlideIndex.value % heroSlides.value.length] ?? heroSlides.value[0]);
const membership = computed(
  () => account.value?.membership ?? { active: false, plan: null, expiresAt: null, entitlements: [] as string[] }
);
const membershipTitle = computed(() => (membership.value.active ? membership.value.plan?.name || '会员已开通' : '当前未开通'));
const membershipSubtitle = computed(() =>
  membership.value.active
    ? `有效期至 ${membership.value.expiresAt || '长期'}`
    : '开通后即可解锁模板、社群和接单资料'
);
const entitlementChips = computed(() =>
  membership.value.entitlements.length > 0
    ? membership.value.entitlements
    : ['模板下载', '社群入口', '接单资料', '优先上新']
);
const kpiCards = computed(() => dashboard.value?.kpiCards?.length ? dashboard.value.kpiCards : []);

onMounted(async () => {
  loading.value = true;
  try {
    const [summary, homeDashboard] = await Promise.all([
      fetchAccountSummary('demo-user').catch(() => null),
      fetchHomeDashboard()
    ]);
    account.value = summary;
    dashboard.value = homeDashboard;
  } finally {
    loading.value = false;
  }
});

function accentFromSlide(slide: HomeDashboardSlide): Tone {
  const accent = String(slide.metadata?.accent ?? '').toLowerCase();
  if (accent === 'blue' || accent === 'green' || accent === 'violet' || accent === 'orange') {
    return accent;
  }
  return 'gold';
}

function setActiveSlide(index: number) {
  activeSlideIndex.value = index;
}

function scrollToBenefits() {
  benefitsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function openPath(path: string) {
  if (!path) {
    return;
  }
  if (/^https?:\/\//i.test(path)) {
    window.open(path, '_blank', 'noreferrer');
    return;
  }
  void router.push(path);
}

function handleSlideAction(slide: HomeDashboardSlide) {
  if (slide.actionValue === '/membership/benefits') {
    scrollToBenefits();
    return;
  }
  openPath(slide.actionValue);
}

function handlePrimaryAction() {
  if (activeSlide.value.actionValue === '/membership/benefits') {
    scrollToBenefits();
    return;
  }
  handleSlideAction(activeSlide.value);
}
</script>

<template>
  <main class="membership-benefits-page">
    <section class="membership-hero">
      <div class="membership-shell">
        <div class="membership-breadcrumb">
          <button class="breadcrumb-back" type="button" @click="router.push('/home')">
            <ArrowLeft :size="16" />
            <span>返回首页</span>
          </button>
          <span class="breadcrumb-chip">会员权益专页</span>
        </div>

        <div class="hero-grid">
          <div class="hero-copy">
            <div class="hero-kicker">
              <span class="hero-badge">{{ activeSlide.badge || '会员专享' }}</span>
              <span class="hero-label">活动宣传页</span>
            </div>
            <h1>{{ activeSlide.title || '会员活动限时特惠' }}</h1>
            <p>{{ activeSlide.subtitle || '开通会员，模板、社群和接单资料一次到位。' }}</p>
            <span v-if="loading" class="hero-loading">正在同步会员状态...</span>

            <div class="hero-actions">
              <button class="hero-primary" type="button" @click="handlePrimaryAction">
                {{ activeSlide.ctaLabel || '立即查看' }}
                <ChevronRight :size="16" />
              </button>
              <button class="hero-secondary" type="button" @click="scrollToBenefits">查看权益</button>
              <button class="hero-secondary ghost" type="button" @click="router.push('/workbench')">去工作台</button>
            </div>

            <div class="hero-metrics" v-if="kpiCards.length">
              <button
                v-for="card in kpiCards.slice(0, 4)"
                :key="card.id"
                type="button"
                class="metric-chip"
                @click="openPath(card.actionValue)"
              >
                <span>{{ card.label }}</span>
                <strong>{{ card.value }}</strong>
              </button>
            </div>
          </div>

          <aside class="status-panel">
            <div class="status-head">
              <div class="status-icon">
                <Crown :size="22" />
              </div>
              <div>
                <span class="status-title">{{ membershipTitle }}</span>
                <p>{{ membershipSubtitle }}</p>
              </div>
            </div>

            <div class="status-note">
              <span>当前权益</span>
              <strong>{{ loading ? '加载中' : membership.active ? '会员已生效' : '未开通' }}</strong>
            </div>

            <div class="status-entitlements">
              <button
                v-for="item in entitlementChips"
                :key="item"
                type="button"
                class="entitlement-chip"
                @click="scrollToBenefits"
              >
                <CheckCircle2 :size="14" />
                <span>{{ item }}</span>
              </button>
            </div>

            <button class="status-cta" type="button" @click="scrollToBenefits">
              查看全部权益
              <ChevronRight :size="16" />
            </button>
          </aside>
        </div>
      </div>
    </section>

    <section class="membership-band">
      <div class="membership-shell">
        <header class="section-head">
          <div>
            <span>轮播内容</span>
            <h2>会员活动、模板上新和社群入口</h2>
          </div>
          <p>这些卡片会直接读取首页后台轮播与会员状态，内容可随后台调整。</p>
        </header>

        <div class="slide-rail">
          <button
            v-for="(slide, index) in heroSlides"
            :key="slide.id"
            :class="['slide-card', `tone-${accentFromSlide(slide)}`, { active: index === activeSlideIndex }]"
            type="button"
            @click="setActiveSlide(index)"
          >
            <span class="slide-badge">{{ slide.badge }}</span>
            <strong>{{ slide.title }}</strong>
            <small>{{ slide.ctaSubtitle || slide.subtitle }}</small>
            <em>{{ slide.ctaLabel }}</em>
          </button>
        </div>
      </div>
    </section>

    <section ref="benefitsRef" class="membership-band benefits-band">
      <div class="membership-shell">
        <header class="section-head">
          <div>
            <span>会员权益</span>
            <h2>首页第一眼看到的核心福利</h2>
          </div>
          <p>直接连到模板、工作台、社群和接单资料，不接支付闭环。</p>
        </header>

        <div class="benefit-grid">
          <button
            v-for="card in benefitCards"
            :key="card.title"
            type="button"
            :class="['benefit-card', `tone-${card.tone}`]"
            @click="openPath(card.actionValue)"
          >
            <span class="benefit-icon">
              <component :is="card.icon" :size="20" />
            </span>
            <strong>{{ card.title }}</strong>
            <small>{{ card.subtitle }}</small>
          </button>
        </div>
      </div>
    </section>

    <section class="membership-band">
      <div class="membership-shell">
        <header class="section-head">
          <div>
            <span>模板上新</span>
            <h2>后台轮播与精选活动</h2>
          </div>
          <p>点击后会直接进入对应页面，继续浏览模板或社群内容。</p>
        </header>

        <div class="template-grid">
          <button
            v-for="slide in templateCards"
            :key="slide.id"
            type="button"
            :class="['template-card', `tone-${accentFromSlide(slide)}`]"
            @click="handleSlideAction(slide)"
          >
            <span class="template-mark">{{ slide.badge }}</span>
            <strong>{{ slide.title }}</strong>
            <small>{{ slide.subtitle }}</small>
            <em>{{ slide.ctaLabel }}</em>
          </button>
        </div>
      </div>
    </section>

    <section class="membership-band">
      <div class="membership-shell">
        <header class="section-head">
          <div>
            <span>社群入口</span>
            <h2>四个最常用的社群分区</h2>
          </div>
          <p>入门、打卡、接单和资源对接，都是独立可点的真实路由。</p>
        </header>

        <div class="community-grid">
          <button
            v-for="card in communityCards"
            :key="card.title"
            type="button"
            :class="['community-card', `tone-${card.tone}`]"
            @click="openPath(card.actionValue)"
          >
            <span class="community-icon">
              <component :is="card.icon" :size="22" />
            </span>
            <strong>{{ card.title }}</strong>
            <small>{{ card.subtitle }}</small>
          </button>
        </div>
      </div>
    </section>

    <section class="membership-footer">
      <div class="membership-shell">
        <div class="footer-cta">
          <div>
            <span>下一步</span>
            <strong>去工作台继续操作，或返回首页看基础必备首屏</strong>
            <p>会员页只是入口，后续操作仍然落在原有工作台、社群和模板页面里。</p>
          </div>
          <div class="footer-actions">
            <button type="button" class="footer-primary" @click="router.push('/workbench')">去工作台</button>
            <button type="button" class="footer-secondary" @click="router.push('/home')">返回首页</button>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.membership-benefits-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8f7ff 0%, #fbfcff 34%, #ffffff 100%);
  color: #1c2330;
}

.membership-shell {
  width: min(1180px, calc(100vw - 32px));
  margin: 0 auto;
}

.membership-hero {
  padding: 22px 0 14px;
}

.membership-breadcrumb {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.breadcrumb-back,
.breadcrumb-chip,
.hero-primary,
.hero-secondary,
.status-cta,
.entitlement-chip,
.slide-card,
.benefit-card,
.template-card,
.community-card,
.footer-primary,
.footer-secondary {
  border-radius: 8px;
}

.breadcrumb-back {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #dbe2ef;
  padding: 0 14px;
  color: #334155;
  background: #fff;
  font-weight: 800;
}

.breadcrumb-chip {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  border: 1px solid #f0d9a6;
  padding: 0 12px;
  color: #8a5a00;
  background: #fff8ea;
  font-size: 13px;
  font-weight: 800;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) 340px;
  gap: 18px;
  align-items: stretch;
}

.hero-copy {
  padding: 28px 26px 24px;
  border: 1px solid #e2e8f5;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(248, 246, 255, 0.96)),
    linear-gradient(135deg, #f6f3ff 0%, #fef9f0 100%);
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.hero-badge {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  padding: 0 10px;
  border-radius: 999px;
  color: #8b5a00;
  background: #ffe7b3;
  font-size: 12px;
  font-weight: 900;
}

.hero-label {
  color: #6b7280;
  font-size: 12px;
  font-weight: 800;
}

.hero-copy h1 {
  margin: 0;
  max-width: 14em;
  font-size: 44px;
  line-height: 1.08;
  letter-spacing: 0;
}

.hero-copy p {
  margin: 12px 0 0;
  max-width: 35em;
  color: #5d6678;
  line-height: 1.72;
}

.hero-loading {
  display: inline-flex;
  margin-top: 12px;
  color: #6354f6;
  font-size: 12px;
  font-weight: 800;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.hero-primary,
.hero-secondary,
.status-cta,
.footer-primary,
.footer-secondary {
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid transparent;
  padding: 0 16px;
  font-weight: 800;
}

.hero-primary {
  color: #fff;
  background: linear-gradient(135deg, #ff6b43 0%, #ff5538 100%);
}

.hero-secondary {
  border-color: #d7dfef;
  color: #344054;
  background: #fff;
}

.hero-secondary.ghost {
  background: #f7f9ff;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.metric-chip {
  display: grid;
  gap: 4px;
  border: 1px solid #e3e8f4;
  background: #fff;
  text-align: left;
}

.metric-chip span {
  color: #657084;
  font-size: 12px;
}

.metric-chip strong {
  color: #182033;
  font-size: 18px;
}

.status-panel {
  display: grid;
  gap: 14px;
  padding: 22px;
  border: 1px solid #e2e8f5;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%);
}

.status-head {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.status-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #8b5a00;
  background: #fff1c8;
}

.status-title {
  display: block;
  font-weight: 900;
}

.status-head p {
  margin: 4px 0 0;
  color: #667085;
  line-height: 1.55;
}

.status-note {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid #e6ebf6;
  border-radius: 8px;
  background: #fff;
}

.status-note span {
  color: #667085;
  font-size: 12px;
  font-weight: 800;
}

.status-note strong {
  color: #182033;
}

.status-entitlements {
  display: grid;
  gap: 10px;
}

.entitlement-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #e3e8f4;
  padding: 10px 12px;
  color: #334155;
  background: #fff;
  text-align: left;
}

.status-cta {
  color: #8b5a00;
  background: #fff1c8;
}

.membership-band {
  padding: 14px 0;
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.section-head span {
  color: #6354f6;
  font-size: 12px;
  font-weight: 900;
}

.section-head h2 {
  margin: 4px 0 0;
  font-size: 22px;
  line-height: 1.2;
  letter-spacing: 0;
}

.section-head p {
  margin: 0;
  max-width: 36em;
  color: #667085;
  line-height: 1.55;
}

.slide-rail,
.benefit-grid,
.template-grid,
.community-grid {
  display: grid;
  gap: 12px;
}

.slide-rail {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.slide-card,
.benefit-card,
.template-card,
.community-card {
  min-width: 0;
  border: 1px solid #e3e8f4;
  text-align: left;
  background: #fff;
}

.slide-card {
  display: grid;
  gap: 8px;
  padding: 16px;
  min-height: 150px;
}

.slide-card.active {
  box-shadow: 0 14px 30px rgba(102, 87, 245, 0.12);
}

.slide-badge,
.template-mark {
  justify-self: start;
  min-height: 24px;
  display: inline-flex;
  align-items: center;
  padding: 0 8px;
  border-radius: 999px;
  background: #eef1ff;
  color: #6354f6;
  font-size: 12px;
  font-weight: 900;
}

.slide-card strong,
.benefit-card strong,
.template-card strong,
.community-card strong {
  color: #172033;
  font-size: 16px;
  line-height: 1.25;
}

.slide-card small,
.benefit-card small,
.template-card small,
.community-card small {
  color: #667085;
  line-height: 1.55;
}

.slide-card em,
.template-card em {
  justify-self: start;
  font-style: normal;
  color: #1d4ed8;
  font-weight: 900;
}

.tone-gold {
  border-color: #f0d9a6;
}

.tone-gold .slide-badge,
.tone-gold .template-mark,
.tone-gold .benefit-icon {
  color: #8b5a00;
  background: #fff1c8;
}

.tone-blue {
  border-color: #cfe0ff;
}

.tone-blue .slide-badge,
.tone-blue .template-mark,
.tone-blue .benefit-icon {
  color: #1d4ed8;
  background: #e8f0ff;
}

.tone-violet {
  border-color: #d8d2ff;
}

.tone-violet .slide-badge,
.tone-violet .template-mark,
.tone-violet .benefit-icon {
  color: #6354f6;
  background: #efeaff;
}

.tone-green {
  border-color: #cfead9;
}

.tone-green .slide-badge,
.tone-green .template-mark,
.tone-green .benefit-icon {
  color: #0d8a58;
  background: #e7f9ef;
}

.tone-orange {
  border-color: #f6d2ba;
}

.tone-orange .slide-badge,
.tone-orange .template-mark,
.tone-orange .benefit-icon {
  color: #d97706;
  background: #fff1e3;
}

.tone-red {
  border-color: #f7c5c0;
}

.tone-red .community-icon {
  color: #dc2626;
  background: #ffebe9;
}

.benefits-band {
  background: linear-gradient(180deg, rgba(248, 246, 255, 0.7), rgba(255, 255, 255, 0.8));
}

.benefit-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.benefit-card {
  display: grid;
  gap: 8px;
  padding: 18px;
}

.benefit-card:hover,
.template-card:hover,
.community-card:hover,
.slide-card:hover,
.hero-secondary:hover,
.hero-primary:hover,
.status-cta:hover,
.footer-primary:hover,
.footer-secondary:hover,
.breadcrumb-back:hover {
  border-color: #b6c5ff;
}

.benefit-icon,
.community-icon {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
}

.benefit-icon {
  color: #6354f6;
  background: #efeaff;
}

.template-grid,
.community-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.template-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  min-height: 154px;
}

.community-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.community-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  min-height: 164px;
}

.community-icon {
  color: #6354f6;
  background: #efeaff;
}

.membership-footer {
  padding: 14px 0 28px;
}

.footer-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 18px 20px;
  border: 1px solid #e2e8f5;
  border-radius: 8px;
  background: #fff;
}

.footer-cta span {
  color: #6354f6;
  font-size: 12px;
  font-weight: 900;
}

.footer-cta strong {
  display: block;
  margin-top: 4px;
  font-size: 18px;
}

.footer-cta p {
  margin: 6px 0 0;
  color: #667085;
  line-height: 1.6;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.footer-primary {
  color: #fff;
  background: linear-gradient(135deg, #ff6b43 0%, #ff5538 100%);
}

.footer-secondary {
  border-color: #dbe2ef;
  color: #344054;
  background: #fff;
}

@media (max-width: 1120px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .community-grid,
  .template-grid,
  .benefit-grid,
  .slide-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .membership-shell {
    width: min(100vw - 24px, 1180px);
  }

  .community-grid,
  .template-grid,
  .benefit-grid,
  .slide-rail {
    grid-template-columns: 1fr;
  }

  .hero-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .footer-cta {
    display: grid;
  }

  .footer-actions {
    justify-content: stretch;
    flex-wrap: wrap;
  }
}
</style>

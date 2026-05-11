<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, CheckCircle2, Download, Loader2, Lock, Star } from 'lucide-vue-next';
import { fetchPortalDetail, runPortalAction } from '../services/api';
import { getIcon } from '../services/icons';
import type { PortalActionResult, PortalDetailAction, PortalDetailDownload, PortalDetailPayload } from '../services/viewModel';

const DEMO_USER_ID = 'demo-user';

const route = useRoute();
const router = useRouter();
const detail = ref<PortalDetailPayload | null>(null);
const loading = ref(false);
const actionLoading = ref('');
const errorMessage = ref('');
const actionMessage = ref('');
const actionDownload = ref<PortalDetailDownload | null>(null);

const detailPath = computed(() => route.path || '/');
const completedActions = computed(() => new Set(detail.value?.userState.completedActions ?? []));
const includedItems = computed(() => detail.value?.items ?? []);

onMounted(loadDetail);

watch(detailPath, () => {
  void loadDetail();
});

async function loadDetail() {
  loading.value = true;
  errorMessage.value = '';
  actionMessage.value = '';
  actionDownload.value = null;
  try {
    detail.value = await fetchPortalDetail(detailPath.value, DEMO_USER_ID);
  } catch (error) {
    detail.value = null;
    errorMessage.value = error instanceof Error ? error.message : '详情暂时无法加载';
  } finally {
    loading.value = false;
  }
}

async function executeAction(action: PortalDetailAction, itemId?: string) {
  if (!detail.value) {
    return;
  }
  if (detail.value.userState.locked) {
    actionMessage.value = '该内容需要会员权限，开通会员后即可使用。';
    return;
  }
  actionLoading.value = action.key;
  actionMessage.value = '';
  actionDownload.value = null;
  try {
    const result = await runPortalAction({
      userId: DEMO_USER_ID,
      detailPath: detail.value.path,
      itemId: itemId ?? detail.value.items[0]?.id,
      actionKey: action.key
    });
    applyActionResult(result, action.key);
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : '操作失败，请稍后重试。';
  } finally {
    actionLoading.value = '';
  }
}

function applyActionResult(result: PortalActionResult, actionKey: string) {
  actionMessage.value = result.message;
  actionDownload.value = result.download ?? null;
  if (detail.value && result.status !== 'locked') {
    detail.value = {
      ...detail.value,
      userState: {
        ...detail.value.userState,
        completedActions: Array.from(new Set([...detail.value.userState.completedActions, actionKey]))
      }
    };
  }
  if (result.route) {
    void router.push(result.route);
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  void router.push('/home');
}
</script>

<template>
  <main class="portal-detail-page">
    <header class="detail-topbar">
      <button class="detail-back" @click="goBack"><ArrowLeft :size="18" />返回</button>
      <button class="detail-home" @click="router.push('/home')">首页</button>
    </header>

    <section v-if="loading" class="detail-state">
      <Loader2 class="spin" :size="28" />
      <span>正在加载详情</span>
    </section>

    <section v-else-if="errorMessage" class="detail-state">
      <strong>未找到这个入口</strong>
      <span>{{ errorMessage }}</span>
      <button class="detail-primary" @click="router.push('/home')">回到首页</button>
    </section>

    <template v-else-if="detail">
      <section class="detail-hero">
        <div class="detail-icon"><component :is="getIcon(detail.icon)" :size="36" /></div>
        <div>
          <span class="detail-kicker">{{ detail.kind === 'directory' ? '目录专页' : '详情专页' }}</span>
          <h1>{{ detail.title }}</h1>
          <p>{{ detail.subtitle || detail.detail.summary }}</p>
          <div class="detail-meta">
            <span v-if="detail.requiredMembership"><Lock :size="15" />会员内容</span>
            <span v-if="detail.effectivePointCost > 0"><Star :size="15" />{{ detail.effectivePointCost }} 积分</span>
            <span><CheckCircle2 :size="15" />{{ includedItems.length }} 个入口</span>
          </div>
        </div>
        <div class="detail-actions">
          <button
            class="detail-primary"
            :disabled="Boolean(actionLoading)"
            @click="executeAction(detail.detail.primaryAction)"
          >
            <Loader2 v-if="actionLoading === detail.detail.primaryAction.key" class="spin" :size="17" />
            <CheckCircle2 v-else-if="completedActions.has(detail.detail.primaryAction.key)" :size="17" />
            <span>{{ completedActions.has(detail.detail.primaryAction.key) ? '已完成' : detail.detail.primaryAction.label }}</span>
          </button>
          <button
            v-for="action in detail.detail.secondaryActions"
            :key="action.key"
            class="detail-secondary"
            :disabled="Boolean(actionLoading)"
            @click="executeAction(action)"
          >
            {{ completedActions.has(action.key) ? '已' + action.label : action.label }}
          </button>
        </div>
      </section>

      <section v-if="detail.userState.locked" class="detail-lock">
        <Lock :size="18" />
        <span>当前账号未开通所需会员权益，可以先查看目录，站内动作会在开通后放行。</span>
      </section>

      <section v-if="actionMessage || actionDownload" class="detail-result">
        <span>{{ actionMessage }}</span>
        <a v-if="actionDownload" :href="actionDownload.url" target="_blank" rel="noreferrer">
          <Download :size="16" />{{ actionDownload.fileName || '下载文件' }}
        </a>
      </section>

      <div class="detail-layout">
        <section class="detail-main">
          <article class="detail-section">
            <h2>概览</h2>
            <p>{{ detail.detail.summary }}</p>
          </article>

          <article v-if="detail.detail.highlights.length" class="detail-section">
            <h2>亮点</h2>
            <ul class="detail-list">
              <li v-for="highlight in detail.detail.highlights" :key="highlight">
                <CheckCircle2 :size="16" />{{ highlight }}
              </li>
            </ul>
          </article>

          <article v-if="detail.detail.steps.length" class="detail-section">
            <h2>步骤/目录</h2>
            <ol class="detail-steps">
              <li v-for="(step, index) in detail.detail.steps" :key="step">
                <span>{{ index + 1 }}</span>{{ step }}
              </li>
            </ol>
          </article>

          <article v-if="detail.detail.deliverables.length" class="detail-section">
            <h2>交付物</h2>
            <ul class="detail-list">
              <li v-for="deliverable in detail.detail.deliverables" :key="deliverable">
                <Download :size="16" />{{ deliverable }}
              </li>
            </ul>
          </article>
        </section>

        <aside class="detail-side">
          <section class="detail-section">
            <h2>包含入口</h2>
            <button
              v-for="item in includedItems"
              :key="item.id"
              class="detail-item"
              :disabled="Boolean(actionLoading)"
              @click="executeAction(detail.detail.primaryAction, item.id)"
            >
              <component :is="getIcon(item.icon)" :size="22" />
              <span>
                <strong>{{ item.title }}</strong>
                <small>{{ item.subtitle }}</small>
              </span>
              <Lock v-if="item.requiredMembership" :size="15" />
            </button>
          </section>

          <section v-if="detail.detail.faqs.length" class="detail-section">
            <h2>FAQ</h2>
            <details v-for="faq in detail.detail.faqs" :key="faq.question" class="detail-faq">
              <summary>{{ faq.question }}</summary>
              <p>{{ faq.answer }}</p>
            </details>
          </section>
        </aside>
      </div>
    </template>
  </main>
</template>

<style scoped>
.portal-detail-page {
  min-height: calc(100vh - var(--portal-chrome-height, 0px));
  background: #f6f7fb;
  color: #1f2633;
}

.detail-topbar,
.detail-hero,
.detail-layout,
.detail-lock,
.detail-result {
  width: min(1180px, calc(100vw - 48px));
  margin: 0 auto;
}

.detail-topbar {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-back,
.detail-home,
.detail-secondary,
.detail-primary {
  min-height: 40px;
  border-radius: 8px;
  cursor: pointer;
}

.detail-back,
.detail-home,
.detail-secondary {
  border: 1px solid #dce1eb;
  background: #fff;
  color: #30384c;
}

.detail-back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
}

.detail-home,
.detail-secondary {
  padding: 0 16px;
}

.detail-hero {
  min-height: 230px;
  display: grid;
  grid-template-columns: 72px 1fr auto;
  gap: 22px;
  align-items: center;
  padding: 34px;
  border: 1px solid #e2e6ef;
  border-radius: 8px;
  background: #fff;
}

.detail-icon {
  width: 72px;
  height: 72px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  background: #6657f5;
}

.detail-kicker {
  color: #6657f5;
  font-weight: 800;
}

.detail-hero h1 {
  margin: 8px 0 10px;
  font-size: 34px;
  letter-spacing: 0;
}

.detail-hero p,
.detail-section p {
  margin: 0;
  color: #667085;
  line-height: 1.7;
}

.detail-meta,
.detail-actions,
.detail-result,
.detail-lock {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail-meta span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #596276;
}

.detail-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
}

.detail-primary {
  min-width: 132px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 0;
  padding: 0 18px;
  color: #fff;
  background: #6657f5;
  font-weight: 800;
}

.detail-primary:disabled,
.detail-secondary:disabled,
.detail-item:disabled {
  opacity: 0.62;
  cursor: wait;
}

.detail-lock,
.detail-result {
  margin-top: 16px;
  min-height: 48px;
  padding: 0 16px;
  border-radius: 8px;
}

.detail-lock {
  border: 1px solid #ffe0a7;
  background: #fff8e8;
  color: #7a4b00;
}

.detail-result {
  justify-content: space-between;
  border: 1px solid #ccebd6;
  background: #eefbf3;
  color: #1f6b3f;
}

.detail-result a {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #2352d8;
  font-weight: 800;
  text-decoration: none;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 18px;
  align-items: start;
  padding: 20px 0 48px;
}

.detail-main,
.detail-side {
  display: grid;
  gap: 18px;
}

.detail-section {
  padding: 22px;
  border: 1px solid #e2e6ef;
  border-radius: 8px;
  background: #fff;
}

.detail-section h2 {
  margin: 0 0 14px;
  font-size: 18px;
}

.detail-list,
.detail-steps {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.detail-list li,
.detail-steps li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #3d4658;
  line-height: 1.6;
}

.detail-steps li span {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  background: #1f2633;
  font-size: 13px;
  font-weight: 800;
}

.detail-item {
  width: 100%;
  min-height: 72px;
  display: grid;
  grid-template-columns: 28px 1fr 18px;
  gap: 10px;
  align-items: center;
  border: 1px solid #e5e9f1;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fff;
  text-align: left;
  cursor: pointer;
}

.detail-item + .detail-item {
  margin-top: 10px;
}

.detail-item span {
  min-width: 0;
}

.detail-item strong,
.detail-item small {
  display: block;
}

.detail-item small {
  margin-top: 4px;
  color: #667085;
}

.detail-faq {
  border-top: 1px solid #edf0f6;
  padding: 12px 0;
}

.detail-faq summary {
  cursor: pointer;
  font-weight: 800;
}

.detail-state {
  min-height: calc(100vh - var(--portal-chrome-height, 0px) - 80px);
  display: grid;
  place-items: center;
  align-content: center;
  gap: 12px;
  color: #667085;
}

.spin {
  animation: detail-spin 0.8s linear infinite;
}

@keyframes detail-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 860px) {
  .detail-topbar,
  .detail-hero,
  .detail-layout,
  .detail-lock,
  .detail-result {
    width: min(100vw - 28px, 1180px);
  }

  .detail-hero,
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .detail-actions {
    justify-content: flex-start;
  }
}
</style>

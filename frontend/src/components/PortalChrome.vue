<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  ChevronDown,
  CreditCard,
  KeyRound,
  LogIn,
  LogOut,
  Search,
  Settings,
  ShieldCheck,
  Ticket
} from 'lucide-vue-next';
import {
  changePassword,
  clearUserSession,
  createRechargeOrder,
  fetchAccountSummary,
  getCurrentUserId,
  getUserSession,
  redeemCode,
  searchPortal,
  updateAccountProfile
} from '../services/api';
import type { AccountSummary, PortalSearchResult, RechargeOrder } from '../services/viewModel';

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

const accountPackages = [
  { key: 'points_1000', points: 1000, amountCents: 990, label: '1000 积分', price: '￥9.90' },
  { key: 'points_5000', points: 5000, amountCents: 4900, label: '5000 积分', price: '￥49.00' },
  { key: 'points_10000', points: 10000, amountCents: 8900, label: '10000 积分', price: '￥89.00' }
] as const;

const demoUserId = 'demo-user';
const fallbackSummary = (): AccountSummary => ({
  user: {
    id: demoUserId,
    tenantId: 'demo',
    phone: '',
    displayName: '演示用户',
    role: 'USER',
    status: 'ACTIVE'
  },
  wallet: {
    balance: 0,
    frozenBalance: 0,
    currency: 'POINT'
  },
  membership: {
    active: false,
    plan: null,
    entitlements: []
  }
});

const props = withDefaults(defineProps<{
  enabled?: boolean;
  activePageKey: string;
  channels: ChromeChannel[];
}>(), {
  enabled: true
});

const router = useRouter();
const visibleChannels = computed(() =>
  (props.channels.length > 0 ? props.channels : defaultChannels).map((channel) =>
    channel.key === 'home' ? { ...channel, label: '常用' } : channel
  )
);
const showChrome = computed(() => props.enabled && props.activePageKey.length > 0);
const searchQuery = ref('');
const searchResults = ref<PortalSearchResult[]>([]);
const searchOpen = ref(false);
const searching = ref(false);
const membershipOpen = ref(false);
const accountOpen = ref(false);
const accountPanel = ref<'settings' | 'redeem' | 'password' | 'recharge' | ''>('');
const accountSummary = ref<AccountSummary>(fallbackSummary());
const userSession = ref(getUserSession());
const profileName = ref('');
const profileSaving = ref(false);
const redeemCodeInput = ref('');
const redeeming = ref(false);
const passwordForm = ref({ currentPassword: '', newPassword: '', confirmPassword: '' });
const passwordSaving = ref(false);
const rechargePackageKey = ref<(typeof accountPackages)[number]['key']>('points_1000');
const rechargeOrder = ref<RechargeOrder | null>(null);
const accountMessage = ref('');
const searchTimer = ref<number | undefined>(undefined);
const chromeBodyRef = ref<HTMLElement | null>(null);

const isLoggedIn = computed(() => Boolean(userSession.value?.accessToken));
const currentUserId = computed(() => userSession.value?.user.id || getCurrentUserId(demoUserId));
const accountName = computed(() => {
  if (!isLoggedIn.value) {
    return '登录 / 注册';
  }
  return accountSummary.value.user.displayName?.trim() || userSession.value?.user.displayName?.trim() || '用户';
});
const accountPhone = computed(() => {
  if (!isLoggedIn.value) {
    return '手机号登录后同步积分和会员';
  }
  return accountSummary.value.user.phone || userSession.value?.user.phone || '已登录';
});
const avatarLabel = computed(() => (accountName.value.charAt(0) || 'U').toUpperCase());
const pointsText = computed(() => formatPoints(accountSummary.value.wallet.balance));
const frozenPointsText = computed(() => formatPoints(accountSummary.value.wallet.frozenBalance));
const membership = computed(() => accountSummary.value.membership);
const currentRechargePackage = computed(
  () => accountPackages.find((pkg) => pkg.key === rechargePackageKey.value) ?? accountPackages[0]
);

watch(searchQuery, (value) => {
  window.clearTimeout(searchTimer.value);
  if (value.trim().length < 2) {
    searchResults.value = [];
    return;
  }
  searchTimer.value = window.setTimeout(() => {
    void runSearch();
  }, 260);
});

watch(() => props.activePageKey, () => {
  searchOpen.value = false;
  membershipOpen.value = false;
  accountOpen.value = false;
  accountPanel.value = '';
});

onMounted(() => {
  void refreshAccountSummary();
  window.addEventListener('keydown', handleScrollKeys, { passive: false });
});

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleScrollKeys);
});

function goPage(pageKey: string) {
  void router.push(`/${pageKey}`);
}

async function refreshAccountSummary() {
  try {
    userSession.value = getUserSession();
    if (!userSession.value?.accessToken) {
      accountSummary.value = fallbackSummary();
      profileName.value = accountSummary.value.user.displayName;
      return;
    }
    accountSummary.value = await fetchAccountSummary(currentUserId.value);
    profileName.value = accountSummary.value.user.displayName;
  } catch {
    accountSummary.value = fallbackSummary();
    profileName.value = accountSummary.value.user.displayName;
  }
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

function toggleMembershipPanel() {
  void router.push('/membership/benefits');
}

function openAccountMenu() {
  accountOpen.value = !accountOpen.value;
  if (accountOpen.value) {
    membershipOpen.value = false;
    accountMessage.value = '';
    if (accountPanel.value === 'settings') {
      profileName.value = accountSummary.value.user.displayName;
    }
  } else {
    accountPanel.value = '';
  }
}

function openSettingsPanel() {
  if (!isLoggedIn.value) {
    void router.push('/auth');
    return;
  }
  accountOpen.value = true;
  membershipOpen.value = false;
  accountPanel.value = 'settings';
  profileName.value = accountSummary.value.user.displayName;
}

function openRechargePanel() {
  accountOpen.value = true;
  membershipOpen.value = false;
  accountPanel.value = 'recharge';
  accountMessage.value = '';
}

function openRedeemPanel() {
  if (!isLoggedIn.value) {
    void router.push('/auth');
    return;
  }
  accountOpen.value = true;
  membershipOpen.value = false;
  accountPanel.value = 'redeem';
  accountMessage.value = '';
}

function openPasswordPanel() {
  if (!isLoggedIn.value) {
    void router.push('/auth');
    return;
  }
  accountOpen.value = true;
  membershipOpen.value = false;
  accountPanel.value = 'password';
  accountMessage.value = '';
  passwordForm.value = { currentPassword: '', newPassword: '', confirmPassword: '' };
}

function goAuth() {
  void router.push('/auth');
}

function logoutUser() {
  clearUserSession();
  userSession.value = null;
  accountSummary.value = fallbackSummary();
  closeAccountPanels();
}

async function saveProfile() {
  if (!isLoggedIn.value) {
    void router.push('/auth');
    return;
  }
  const nextName = profileName.value.trim();
  if (!nextName) {
    accountMessage.value = '昵称不能为空';
    return;
  }
  profileSaving.value = true;
  try {
    const user = await updateAccountProfile({ userId: currentUserId.value, displayName: nextName });
    accountSummary.value.user = {
      ...accountSummary.value.user,
      ...user
    };
    profileName.value = accountSummary.value.user.displayName;
    accountMessage.value = '昵称已保存';
  } finally {
    profileSaving.value = false;
  }
}

async function submitRecharge() {
  accountMessage.value = '';
  rechargeOrder.value = null;
  try {
    rechargeOrder.value = await createRechargeOrder({
      userId: demoUserId,
      packageKey: rechargePackageKey.value
    });
    accountMessage.value = rechargeOrder.value.message || '订单已创建';
  } catch (error) {
    accountMessage.value = error instanceof Error ? error.message : '创建订单失败';
  }
}

async function submitRedeemCode() {
  if (!isLoggedIn.value) {
    void router.push('/auth');
    return;
  }
  const code = redeemCodeInput.value.trim();
  if (!code) {
    accountMessage.value = '请输入兑换码';
    return;
  }
  redeeming.value = true;
  accountMessage.value = '';
  try {
    const result = await redeemCode(code);
    accountSummary.value = result.accountSummary;
    redeemCodeInput.value = '';
    accountMessage.value = `兑换成功，到账 ${formatPoints(result.pointsGranted)} 积分`;
  } catch (error) {
    accountMessage.value = error instanceof Error ? error.message : '兑换失败';
  } finally {
    redeeming.value = false;
  }
}

async function submitPasswordChange() {
  if (!isLoggedIn.value) {
    void router.push('/auth');
    return;
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    accountMessage.value = '两次输入的密码不一致';
    return;
  }
  passwordSaving.value = true;
  accountMessage.value = '';
  try {
    await changePassword({
      currentPassword: passwordForm.value.currentPassword,
      newPassword: passwordForm.value.newPassword
    });
    passwordForm.value = { currentPassword: '', newPassword: '', confirmPassword: '' };
    accountMessage.value = '密码已修改';
  } catch (error) {
    accountMessage.value = error instanceof Error ? error.message : '修改密码失败';
  } finally {
    passwordSaving.value = false;
  }
}

function closeAccountPanels() {
  accountOpen.value = false;
  accountPanel.value = '';
}

function formatPoints(value: number) {
  return new Intl.NumberFormat('zh-CN').format(value);
}

function handleScrollKeys(event: KeyboardEvent) {
  if (!showChrome.value) {
    return;
  }
  if (event.defaultPrevented) {
    return;
  }
  const active = document.activeElement as HTMLElement | null;
  if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT' || active.isContentEditable)) {
    return;
  }

  const body = chromeBodyRef.value;
  if (!body) {
    return;
  }

  const pageStep = Math.max(220, body.clientHeight - 88);
  if (event.key === 'PageDown' || (event.key === ' ' && !event.shiftKey)) {
    event.preventDefault();
    body.scrollBy({ top: pageStep, behavior: 'smooth' });
    return;
  }
  if (event.key === 'PageUp' || (event.key === ' ' && event.shiftKey)) {
    event.preventDefault();
    body.scrollBy({ top: -pageStep, behavior: 'smooth' });
    return;
  }
  if (event.key === 'Home') {
    event.preventDefault();
    body.scrollTo({ top: 0, behavior: 'smooth' });
    return;
  }
  if (event.key === 'End') {
    event.preventDefault();
    body.scrollTo({ top: body.scrollHeight, behavior: 'smooth' });
  }
}
</script>

<template>
  <div v-if="showChrome" class="portal-chrome-shell">
    <section class="brand-row">
      <button class="logo" type="button" @click="goPage('home')">
        <span class="logo-red">新商机</span>
        <span class="logo-gold">OPC社区</span>
      </button>

      <form class="search-box" @submit.prevent="runSearch">
        <input
          v-model="searchQuery"
          aria-label="搜索"
          placeholder="搜索你需要的 AI 助理、工具或模板"
          @focus="searchOpen = true"
        />
        <button aria-label="搜索" type="submit"><Search :size="22" /></button>
      </form>

      <section v-if="searchOpen && (searchQuery || searchResults.length)" class="search-results-panel">
        <span v-if="searching">搜索中...</span>
        <button v-for="result in searchResults" :key="result.id + result.path" type="button" @click="openSearchResult(result)">
          <strong>{{ result.title }}</strong>
          <small>{{ result.subtitle || result.path }}</small>
        </button>
        <span v-if="!searching && searchQuery && searchResults.length === 0">没有找到匹配内容</span>
      </section>

      <div class="vip-strip">
        <span class="vip-mark">VIP</span>
        <span>{{ membership.active ? membership.plan?.name || '会员已生效' : '开通会员，享 100+ 办公权益' }}</span>
        <button type="button" @click="toggleMembershipPanel">{{ membership.active ? '查看权益' : '会员状态' }}</button>
      </div>

      <div class="account-zone">
        <button class="account-chip" type="button" @click="openAccountMenu">
          <span class="account-avatar">{{ avatarLabel }}</span>
          <span class="account-copy">
            <strong>{{ accountName }}</strong>
            <small>{{ pointsText }} 积分</small>
          </span>
          <ChevronDown :size="16" />
        </button>

        <section v-if="accountOpen" class="account-menu" @click.stop>
          <header class="account-summary">
            <div class="account-summary-user">
              <span class="account-avatar account-avatar-large">{{ avatarLabel }}</span>
              <span>
                <strong>{{ accountName }}</strong>
                <small>{{ accountPhone }}</small>
              </span>
            </div>
            <div class="account-summary-points">
              <strong>{{ pointsText }}</strong>
              <span>可用积分</span>
            </div>
          </header>

          <div class="account-meta">
            <span>冻结 {{ frozenPointsText }}</span>
            <button type="button" @click="toggleMembershipPanel">
              <ShieldCheck :size="16" />
              <span>{{ membership.active ? '会员权益' : '会员状态' }}</span>
            </button>
          </div>

          <div class="account-menu-actions">
            <button v-if="!isLoggedIn" type="button" @click="goAuth">
              <LogIn :size="16" />
              <span>登录 / 注册</span>
            </button>
            <button :class="{ active: accountPanel === 'redeem' }" type="button" @click="openRedeemPanel">
              <Ticket :size="16" />
              <span>兑换码</span>
            </button>
            <button :class="{ active: accountPanel === 'password' }" type="button" @click="openPasswordPanel">
              <KeyRound :size="16" />
              <span>修改密码</span>
            </button>
            <button :class="{ active: accountPanel === 'settings' }" type="button" @click="openSettingsPanel">
              <Settings :size="16" />
              <span>账号设置</span>
            </button>
            <button type="button" @click="toggleMembershipPanel">
              <CreditCard :size="16" />
              <span>会员权益</span>
            </button>
            <button v-if="isLoggedIn" type="button" @click="logoutUser">
              <LogOut :size="16" />
              <span>退出登录</span>
            </button>
          </div>

          <section v-if="accountPanel === 'settings'" class="account-settings-panel">
            <strong>账号设置</strong>
            <label>
              <span>昵称</span>
              <input v-model="profileName" maxlength="64" placeholder="请输入昵称" />
            </label>
            <div class="panel-actions">
              <button type="button" @click="closeAccountPanels">关闭</button>
              <button :disabled="profileSaving" type="button" @click="saveProfile">
                {{ profileSaving ? '保存中...' : '保存昵称' }}
              </button>
            </div>
            <p v-if="accountMessage" class="panel-note">{{ accountMessage }}</p>
          </section>

          <section v-else-if="accountPanel === 'redeem'" class="redeem-panel">
            <strong>兑换码</strong>
            <label>
              <span>兑换码</span>
              <input v-model="redeemCodeInput" placeholder="请输入兑换码" />
            </label>
            <div class="panel-actions">
              <button type="button" @click="closeAccountPanels">关闭</button>
              <button :disabled="redeeming" type="button" @click="submitRedeemCode">
                {{ redeeming ? '兑换中...' : '立即兑换' }}
              </button>
            </div>
            <p class="panel-note">兑换成功后会自动刷新积分和会员状态。</p>
            <p v-if="accountMessage" class="panel-note">{{ accountMessage }}</p>
          </section>

          <section v-else-if="accountPanel === 'password'" class="password-panel">
            <strong>修改密码</strong>
            <label>
              <span>当前密码</span>
              <input v-model="passwordForm.currentPassword" type="password" />
            </label>
            <label>
              <span>新密码</span>
              <input v-model="passwordForm.newPassword" type="password" />
            </label>
            <label>
              <span>确认新密码</span>
              <input v-model="passwordForm.confirmPassword" type="password" />
            </label>
            <div class="panel-actions">
              <button type="button" @click="closeAccountPanels">关闭</button>
              <button :disabled="passwordSaving" type="button" @click="submitPasswordChange">
                {{ passwordSaving ? '保存中...' : '保存密码' }}
              </button>
            </div>
            <p v-if="accountMessage" class="panel-note">{{ accountMessage }}</p>
          </section>

          <section v-else-if="accountPanel === 'recharge'" class="recharge-panel">
            <strong>积分充值</strong>
            <div class="recharge-options">
              <button
                v-for="pkg in accountPackages"
                :key="pkg.key"
                :class="{ active: rechargePackageKey === pkg.key }"
                type="button"
                @click="rechargePackageKey = pkg.key"
              >
                <strong>{{ pkg.label }}</strong>
                <small>{{ pkg.price }}</small>
              </button>
            </div>
            <div class="recharge-summary">
              <span>当前选择</span>
              <strong>{{ currentRechargePackage.label }} · {{ currentRechargePackage.price }}</strong>
            </div>
            <div class="panel-actions">
              <button type="button" @click="closeAccountPanels">关闭</button>
              <button type="button" @click="submitRecharge">创建待支付订单</button>
            </div>
            <p class="panel-note">订单会保持 PENDING，实际到账仍由支付回调完成。</p>
            <article v-if="rechargeOrder" class="recharge-order">
              <strong>{{ rechargeOrder.status }}</strong>
              <span>订单号 {{ rechargeOrder.providerOrderNo }}</span>
              <span>{{ rechargeOrder.points }} 积分 · {{ rechargeOrder.amountCents / 100 }} 元</span>
              <small>{{ rechargeOrder.message }}</small>
            </article>
            <p v-if="accountMessage" class="panel-note">{{ accountMessage }}</p>
          </section>

          <p v-else class="account-empty">从上面的按钮进入登录、兑换或账号设置。</p>
        </section>
      </div>

      <section v-if="membershipOpen" class="membership-panel">
        <strong>{{ membership.active ? '会员权益已开启' : '当前为普通用户' }}</strong>
        <p v-if="membership.active">有效期至 {{ membership.expiresAt || '长期' }}</p>
        <p v-else>这里展示会员状态和可用权益，暂不接真实支付成功回调。</p>
        <ul>
          <li v-for="entitlement in membership.entitlements.length > 0 ? membership.entitlements : ['模板下载', '社群入口', '高阶课程']" :key="entitlement">
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
        type="button"
        @click="goPage(channel.key)"
      >
        {{ channel.label }}
      </button>
    </nav>

    <div ref="chromeBodyRef" class="portal-chrome-body" tabindex="0">
      <slot />
    </div>
  </div>
  <slot v-else />
</template>

<style scoped>
.portal-chrome-shell {
  --portal-chrome-height: 136px;
  height: 100vh;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
}

.portal-chrome-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  scrollbar-gutter: stable;
}
</style>

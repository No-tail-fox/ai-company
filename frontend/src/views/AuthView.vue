<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { KeyRound, LogIn, RotateCcw, UserPlus } from 'lucide-vue-next';
import {
  loginUser,
  registerUser,
  requestVerificationCode,
  resetPassword,
  type LoginUserRequest,
  type RegisterUserRequest
} from '../services/api';

type AuthMode = 'login' | 'register' | 'reset';

const router = useRouter();
const mode = ref<AuthMode>('login');
const loading = ref(false);
const message = ref('');
const form = reactive({
  phone: '',
  password: '',
  confirmPassword: '',
  displayName: '',
  verificationCode: ''
});

const modeTitle = computed(() => {
  if (mode.value === 'register') {
    return '注册账号';
  }
  if (mode.value === 'reset') {
    return '忘记密码';
  }
  return '登录账号';
});

const submitLabel = computed(() => {
  if (mode.value === 'register') {
    return '注册并登录';
  }
  if (mode.value === 'reset') {
    return '重置密码';
  }
  return '登录';
});

function switchMode(nextMode: AuthMode) {
  mode.value = nextMode;
  message.value = '';
}

async function sendVerificationCode() {
  message.value = '';
  loading.value = true;
  try {
    const purpose = mode.value === 'reset' ? 'RESET_PASSWORD' : mode.value === 'register' ? 'REGISTER' : 'LOGIN';
    const response = await requestVerificationCode({ phone: form.phone.trim(), purpose });
    message.value = response.devCode ? `验证码已生成：${response.devCode}` : '验证码已发送';
  } catch (error) {
    message.value = error instanceof Error ? error.message : '验证码发送失败';
  } finally {
    loading.value = false;
  }
}

async function submitAuth() {
  message.value = '';
  if ((mode.value === 'register' || mode.value === 'reset') && form.password !== form.confirmPassword) {
    message.value = '两次输入的密码不一致';
    return;
  }
  loading.value = true;
  try {
    if (mode.value === 'register') {
      const payload: RegisterUserRequest = {
        phone: form.phone.trim(),
        password: form.password,
        displayName: form.displayName.trim() || form.phone.trim(),
        verificationCode: form.verificationCode.trim()
      };
      await registerUser(payload);
      await router.push('/home');
      return;
    }
    if (mode.value === 'reset') {
      await resetPassword({
        phone: form.phone.trim(),
        verificationCode: form.verificationCode.trim(),
        newPassword: form.password
      });
      message.value = '密码已重置，请登录';
      mode.value = 'login';
      return;
    }
    const payload: LoginUserRequest = {
      phone: form.phone.trim(),
      password: form.password,
      verificationCode: form.verificationCode.trim()
    };
    await loginUser(payload);
    await router.push('/home');
  } catch (error) {
    message.value = error instanceof Error ? error.message : '账号操作失败';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-panel">
      <header>
        <span>账号中心</span>
        <h1>{{ modeTitle }}</h1>
      </header>

      <div class="auth-tabs">
        <button :class="{ active: mode === 'login' }" type="button" @click="switchMode('login')">
          <LogIn :size="16" />
          登录
        </button>
        <button :class="{ active: mode === 'register' }" type="button" @click="switchMode('register')">
          <UserPlus :size="16" />
          注册
        </button>
        <button :class="{ active: mode === 'reset' }" type="button" @click="switchMode('reset')">
          <RotateCcw :size="16" />
          忘记密码
        </button>
      </div>

      <form class="auth-form" @submit.prevent="submitAuth">
        <label>
          手机号
          <input v-model="form.phone" autocomplete="username" inputmode="tel" />
        </label>
        <label v-if="mode === 'register'">
          昵称
          <input v-model="form.displayName" maxlength="64" />
        </label>
        <label>
          密码
          <input v-model="form.password" :autocomplete="mode === 'login' ? 'current-password' : 'new-password'" type="password" />
        </label>
        <label v-if="mode !== 'login'">
          确认密码
          <input v-model="form.confirmPassword" autocomplete="new-password" type="password" />
        </label>
        <label class="code-field">
          验证码
          <span>
            <input v-model="form.verificationCode" inputmode="numeric" />
            <button :disabled="loading || !form.phone.trim()" type="button" @click="sendVerificationCode">
              <KeyRound :size="16" />
              获取验证码
            </button>
          </span>
        </label>
        <button class="auth-submit" :disabled="loading" type="submit">{{ loading ? '处理中...' : submitLabel }}</button>
      </form>

      <p v-if="message" class="auth-message">{{ message }}</p>
    </section>
  </main>
</template>

<style scoped>
.auth-page {
  min-height: calc(100vh - 136px);
  display: grid;
  place-items: center;
  background: #f6f8fb;
  color: #172033;
  padding: 32px 16px;
}

.auth-panel {
  width: min(420px, 100%);
  display: grid;
  gap: 18px;
  padding: 24px;
  border: 1px solid #dfe7f3;
  border-radius: 8px;
  background: #fff;
}

.auth-panel h1 {
  margin: 4px 0 0;
  font-size: 28px;
  letter-spacing: 0;
}

.auth-panel header span {
  color: #5b6b82;
  font-size: 13px;
  font-weight: 800;
}

.auth-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.auth-tabs button,
.code-field button,
.auth-submit {
  min-height: 38px;
  border: 1px solid #d9e3f0;
  border-radius: 8px;
  background: #fff;
  color: #243244;
  font-weight: 800;
}

.auth-tabs button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.auth-tabs button.active,
.auth-submit {
  border-color: #2448ff;
  color: #fff;
  background: #2448ff;
}

.auth-form {
  display: grid;
  gap: 12px;
}

.auth-form label {
  display: grid;
  gap: 6px;
  color: #4d5b6d;
  font-size: 13px;
  font-weight: 800;
}

.auth-form input {
  min-height: 40px;
  border: 1px solid #d9e3f0;
  border-radius: 8px;
  padding: 0 12px;
  color: #172033;
}

.code-field span {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 132px;
  gap: 8px;
}

.code-field button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.auth-message {
  margin: 0;
  color: #2448ff;
  font-weight: 800;
}
</style>

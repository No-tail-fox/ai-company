<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  History,
  Loader2,
  Lock,
  MessageCircle,
  Pencil,
  RotateCcw,
  Save,
  Send,
  Star,
  Tag,
  UserRound
} from 'lucide-vue-next';
import {
  createPortalDetailComment,
  fetchPortalDetail,
  getCurrentUserId,
  getUserSession,
  publishPortalDetail,
  rollbackPortalDetailVersion,
  runPortalAction,
  updatePortalDetail
} from '../services/api';
import { getIcon } from '../services/icons';
import type {
  PortalActionResult,
  PortalDetailAction,
  PortalDetailDownload,
  PortalDetailPayload,
  PortalDetailVersion
} from '../services/viewModel';

type DetailTab = 'preview' | 'edit' | 'history';

const route = useRoute();
const router = useRouter();
const detail = ref<PortalDetailPayload | null>(null);
const loading = ref(false);
const actionLoading = ref('');
const saveLoading = ref(false);
const publishLoading = ref(false);
const rollbackLoading = ref('');
const commentLoading = ref(false);
const errorMessage = ref('');
const actionMessage = ref('');
const editorMessage = ref('');
const commentMessage = ref('');
const actionDownload = ref<PortalDetailDownload | null>(null);
const activeDetailTab = ref<DetailTab>('preview');
const commentDraft = ref('');
const releaseNote = ref('');
const editor = reactive({
  title: '',
  summary: '',
  bodyMarkdown: '',
  tagsText: '',
  visibility: 'community'
});

const detailPath = computed(() => route.path || '/');
const currentUserId = computed(() => getCurrentUserId('demo-user'));
const completedActions = computed(() => new Set(detail.value?.userState.completedActions ?? []));
const includedItems = computed(() => detail.value?.items ?? []);
const detailTags = computed(() => detail.value?.detail.tags.length ? detail.value.detail.tags : ['Markdown']);
const markdownHtml = computed(() => renderMarkdown(detail.value?.detail.bodyMarkdown || editor.bodyMarkdown || ''));
const commentCount = computed(() => detail.value?.detail.comments.length ?? 0);

onMounted(loadDetail);

watch(detailPath, () => {
  void loadDetail();
});

watch(() => detail.value?.permissions.canEdit, (canEdit) => {
  if (!canEdit && activeDetailTab.value !== 'preview') {
    activeDetailTab.value = 'preview';
  }
});

async function loadDetail() {
  loading.value = true;
  errorMessage.value = '';
  actionMessage.value = '';
  editorMessage.value = '';
  commentMessage.value = '';
  actionDownload.value = null;
  try {
    detail.value = await fetchPortalDetail(detailPath.value, currentUserId.value);
    syncEditor();
  } catch (error) {
    detail.value = null;
    errorMessage.value = error instanceof Error ? error.message : '详情暂时无法加载';
  } finally {
    loading.value = false;
  }
}

function syncEditor() {
  if (!detail.value) {
    return;
  }
  editor.title = detail.value.detail.title || detail.value.title;
  editor.summary = detail.value.detail.summary || detail.value.subtitle;
  editor.bodyMarkdown = detail.value.detail.bodyMarkdown;
  editor.tagsText = detail.value.detail.tags.join('\n');
  editor.visibility = detail.value.detail.visibility || 'community';
  releaseNote.value = '';
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
      userId: currentUserId.value,
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

async function saveDetail() {
  if (!detail.value || !detail.value.permissions.canEdit) {
    return;
  }
  saveLoading.value = true;
  editorMessage.value = '';
  try {
    detail.value = await updatePortalDetail(detail.value.path, buildEditorPayload());
    syncEditor();
    activeDetailTab.value = 'preview';
    editorMessage.value = '已保存正文草稿。';
  } catch (error) {
    editorMessage.value = error instanceof Error ? error.message : '保存失败，请稍后重试。';
  } finally {
    saveLoading.value = false;
  }
}

async function publishDetail() {
  if (!detail.value || !detail.value.permissions.canEdit) {
    return;
  }
  publishLoading.value = true;
  editorMessage.value = '';
  try {
    detail.value = await updatePortalDetail(detail.value.path, buildEditorPayload());
    detail.value = await publishPortalDetail(detail.value.path, releaseNote.value || '发布更新');
    syncEditor();
    activeDetailTab.value = 'preview';
    editorMessage.value = '更新已发布。';
  } catch (error) {
    editorMessage.value = error instanceof Error ? error.message : '发布失败，请稍后重试。';
  } finally {
    publishLoading.value = false;
  }
}

async function rollbackVersion(version: PortalDetailVersion) {
  if (!detail.value || !detail.value.permissions.canEdit || !version.id) {
    return;
  }
  rollbackLoading.value = version.id;
  editorMessage.value = '';
  try {
    detail.value = await rollbackPortalDetailVersion(detail.value.path, version.id, `回滚到 v${version.version}`);
    syncEditor();
    activeDetailTab.value = 'preview';
    editorMessage.value = `已回滚到 v${version.version}。`;
  } catch (error) {
    editorMessage.value = error instanceof Error ? error.message : '回滚失败，请稍后重试。';
  } finally {
    rollbackLoading.value = '';
  }
}

async function submitComment() {
  if (!detail.value || !commentDraft.value.trim()) {
    return;
  }
  if (!getUserSession()?.accessToken) {
    commentMessage.value = '请先登录后再发布评论。';
    return;
  }
  commentLoading.value = true;
  commentMessage.value = '';
  try {
    const result = await createPortalDetailComment(detail.value.path, commentDraft.value.trim());
    detail.value = {
      ...detail.value,
      detail: {
        ...detail.value.detail,
        comments: result.detail.comments
      },
      permissions: {
        ...detail.value.permissions,
        canComment: true
      }
    };
    commentDraft.value = '';
  } catch (error) {
    commentMessage.value = error instanceof Error ? error.message : '评论发布失败，请稍后重试。';
  } finally {
    commentLoading.value = false;
  }
}

function buildEditorPayload() {
  return {
    title: editor.title.trim(),
    summary: editor.summary.trim(),
    bodyMarkdown: editor.bodyMarkdown,
    tags: editor.tagsText
      .split(/\r?\n|,/)
      .map((tag) => tag.trim())
      .filter(Boolean),
    visibility: editor.visibility
  };
}

function goBack() {
  if (window.history.length > 1) {
    router.back();
    return;
  }
  void router.push('/home');
}

function goHall() {
  void router.push('/communication');
}

function formatDate(value: string | null) {
  if (!value) {
    return '刚刚';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function renderMarkdown(markdown: string) {
  const lines = markdown.replace(/\r\n/g, '\n').split('\n');
  const html: string[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();
    if (!trimmed) {
      index += 1;
      continue;
    }
    if (trimmed.startsWith('```')) {
      const code: string[] = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith('```')) {
        code.push(lines[index]);
        index += 1;
      }
      html.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);
      index += 1;
      continue;
    }
    if (isTableStart(lines, index)) {
      const tableLines: string[] = [];
      while (index < lines.length && lines[index].trim().startsWith('|')) {
        tableLines.push(lines[index]);
        index += 1;
      }
      html.push(renderTable(tableLines));
      continue;
    }
    if (/^#{1,3}\s+/.test(trimmed)) {
      const level = Math.min(3, trimmed.match(/^#+/)?.[0].length ?? 2);
      html.push(`<h${level}>${renderInline(trimmed.replace(/^#{1,3}\s+/, ''))}</h${level}>`);
      index += 1;
      continue;
    }
    if (trimmed.startsWith('>')) {
      const quote: string[] = [];
      while (index < lines.length && lines[index].trim().startsWith('>')) {
        quote.push(lines[index].trim().replace(/^>\s?/, ''));
        index += 1;
      }
      html.push(`<blockquote>${quote.map(renderInline).join('<br>')}</blockquote>`);
      continue;
    }
    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^[-*]\s+/, ''));
        index += 1;
      }
      html.push(`<ul>${items.map((item) => `<li>${renderInline(item)}</li>`).join('')}</ul>`);
      continue;
    }
    if (/^\d+\.\s+/.test(trimmed)) {
      const items: string[] = [];
      while (index < lines.length && /^\d+\.\s+/.test(lines[index].trim())) {
        items.push(lines[index].trim().replace(/^\d+\.\s+/, ''));
        index += 1;
      }
      html.push(`<ol>${items.map((item) => `<li>${renderInline(item)}</li>`).join('')}</ol>`);
      continue;
    }
    const paragraph: string[] = [];
    while (index < lines.length && lines[index].trim() && !isBlockStart(lines, index)) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    html.push(`<p>${renderInline(paragraph.join(' '))}</p>`);
  }

  return html.join('');
}

function isBlockStart(lines: string[], index: number) {
  const trimmed = lines[index].trim();
  return /^#{1,3}\s+/.test(trimmed)
    || trimmed.startsWith('>')
    || trimmed.startsWith('```')
    || /^[-*]\s+/.test(trimmed)
    || /^\d+\.\s+/.test(trimmed)
    || isTableStart(lines, index);
}

function isTableStart(lines: string[], index: number) {
  return lines[index]?.trim().startsWith('|') && /\|\s*:?-{3,}:?\s*\|/.test(lines[index + 1] ?? '');
}

function renderTable(lines: string[]) {
  const rows = lines
    .filter((line, index) => index !== 1)
    .map((line) => line.trim().replace(/^\||\|$/g, '').split('|').map((cell) => cell.trim()));
  const [head = [], ...body] = rows;
  return `<table><thead><tr>${head.map((cell) => `<th>${renderInline(cell)}</th>`).join('')}</tr></thead><tbody>${body
    .map((row) => `<tr>${row.map((cell) => `<td>${renderInline(cell)}</td>`).join('')}</tr>`)
    .join('')}</tbody></table>`;
}

function renderInline(value: string) {
  const pieces: string[] = [];
  const pattern = /(!?\[([^\]]*)\]\(([^)]+)\))|(`([^`]+)`)|(\*\*([^*]+)\*\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(value)) !== null) {
    pieces.push(escapeHtml(value.slice(lastIndex, match.index)));
    if (match[1]?.startsWith('!')) {
      pieces.push(`<img src="${safeUrl(match[3])}" alt="${escapeAttr(match[2])}">`);
    } else if (match[1]) {
      pieces.push(`<a href="${safeUrl(match[3])}" target="_blank" rel="noreferrer">${escapeHtml(match[2])}</a>`);
    } else if (match[5]) {
      pieces.push(`<code>${escapeHtml(match[5])}</code>`);
    } else if (match[7]) {
      pieces.push(`<strong>${escapeHtml(match[7])}</strong>`);
    }
    lastIndex = pattern.lastIndex;
  }
  pieces.push(escapeHtml(value.slice(lastIndex)));
  return pieces.join('');
}

function safeUrl(value: string) {
  const url = value.trim();
  if (/^(https?:|mailto:|\/|#)/i.test(url)) {
    return escapeAttr(url);
  }
  return '#';
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeAttr(value: string) {
  return escapeHtml(value).replace(/`/g, '&#96;');
}
</script>

<template>
  <main class="portal-detail-page">
    <header class="detail-topbar">
      <div class="detail-topbar-left">
        <button class="detail-back" type="button" @click="goBack"><ArrowLeft :size="18" />返回</button>
        <strong>资源详情</strong>
      </div>
      <div class="detail-topbar-right">
        <button class="detail-home" type="button" @click="goHall">进入沟通大厅</button>
        <button class="detail-home" type="button" @click="router.push('/home')">首页</button>
      </div>
    </header>

    <section v-if="loading" class="detail-state">
      <Loader2 class="spin" :size="28" />
      <span>正在加载详情</span>
    </section>

    <section v-else-if="errorMessage" class="detail-state">
      <strong>未找到这个入口</strong>
      <span>{{ errorMessage }}</span>
      <button class="detail-primary" type="button" @click="router.push('/home')">回到首页</button>
    </section>

    <template v-else-if="detail">
      <section class="detail-hero">
        <div class="detail-icon">MD</div>
        <div class="detail-hero-copy">
          <span class="detail-kicker">详情专页 / Markdown 内容</span>
          <h1>{{ detail.detail.title || detail.title }}</h1>
          <p>{{ detail.detail.summary || detail.subtitle }}</p>
          <div class="detail-meta">
            <span>◉ {{ includedItems.length }} 个入口</span>
            <span>✎ {{ detail.permissions.canEdit ? '可编辑维护' : '由管理员维护' }}</span>
            <span>💬 {{ commentCount }} 条评论</span>
            <span>最近更新：{{ formatDate(detail.detail.version?.createdAt ?? detail.detail.version?.createdAt ?? null) }}</span>
          </div>
        </div>
        <div class="detail-actions">
          <button
            v-if="detail.permissions.canEdit"
            class="detail-primary"
            type="button"
            @click="activeDetailTab = 'edit'"
          >
            <Pencil :size="17" />编辑正文
          </button>
          <button
            v-if="detail.permissions.canEdit"
            class="detail-secondary strong"
            type="button"
            :disabled="publishLoading"
            @click="publishDetail"
          >
            <Loader2 v-if="publishLoading" class="spin" :size="16" />
            <Save v-else :size="16" />
            发布更新
          </button>
          <button
            v-for="action in detail.detail.secondaryActions"
            :key="action.key"
            class="detail-secondary"
            type="button"
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

      <section v-if="actionMessage || actionDownload || editorMessage" class="detail-result">
        <span>{{ editorMessage || actionMessage }}</span>
        <a v-if="actionDownload" :href="actionDownload.url" target="_blank" rel="noreferrer">
          <Download :size="16" />{{ actionDownload.fileName || '下载文件' }}
        </a>
      </section>

      <div class="detail-layout">
        <main class="detail-main">
          <article class="detail-card detail-markdown-card">
            <div class="detail-section-head">
              <div>
                <h2>正文区域（Markdown 渲染）</h2>
                <span>支持标题、列表、引用、表格、链接、代码块和图片；编辑后可重新发布。</span>
              </div>
              <div class="detail-tabs">
                <button :class="['detail-tab', { active: activeDetailTab === 'preview' }]" type="button" @click="activeDetailTab = 'preview'">预览</button>
                <button
                  v-if="detail.permissions.canEdit"
                  :class="['detail-tab', { active: activeDetailTab === 'edit' }]"
                  type="button"
                  @click="activeDetailTab = 'edit'"
                >
                  编辑
                </button>
                <button
                  v-if="detail.permissions.canEdit"
                  :class="['detail-tab', { active: activeDetailTab === 'history' }]"
                  type="button"
                  @click="activeDetailTab = 'history'"
                >
                  历史版本
                </button>
              </div>
            </div>

            <div v-if="activeDetailTab === 'preview'" class="markdown-body" v-html="markdownHtml"></div>

            <form v-else-if="activeDetailTab === 'edit'" class="detail-editor" @submit.prevent="saveDetail">
              <label>标题<input v-model="editor.title" /></label>
              <label>摘要<textarea v-model="editor.summary" rows="2" /></label>
              <label>
                可见范围
                <select v-model="editor.visibility">
                  <option value="community">社区成员</option>
                  <option value="public">公开可见</option>
                  <option value="members">会员可见</option>
                  <option value="private">仅作者可见</option>
                </select>
              </label>
              <label>标签<textarea v-model="editor.tagsText" rows="3" /></label>
              <label class="field-wide">正文（Markdown）<textarea v-model="editor.bodyMarkdown" rows="16" /></label>
              <label class="field-wide">发布说明<input v-model="releaseNote" placeholder="例如：补充权益有效期和商用授权说明" /></label>
              <div class="detail-editor-actions">
                <button class="detail-secondary" type="button" @click="activeDetailTab = 'preview'">取消</button>
                <button class="detail-secondary strong" type="submit" :disabled="saveLoading">
                  <Loader2 v-if="saveLoading" class="spin" :size="16" />
                  <Save v-else :size="16" />
                  保存
                </button>
                <button class="detail-primary" type="button" :disabled="publishLoading" @click="publishDetail">
                  <Loader2 v-if="publishLoading" class="spin" :size="16" />
                  发布更新
                </button>
              </div>
            </form>

            <div v-else class="history-list">
              <article v-for="version in detail.detail.versions" :key="version.id || version.version" class="history-row">
                <div>
                  <strong>v{{ version.version }} · {{ version.title || detail.title }}</strong>
                  <p>{{ version.releaseNote || '版本快照' }}</p>
                  <small>{{ formatDate(version.createdAt) }}</small>
                </div>
                <button class="detail-secondary" type="button" :disabled="Boolean(rollbackLoading)" @click="rollbackVersion(version)">
                  <Loader2 v-if="rollbackLoading === version.id" class="spin" :size="16" />
                  <RotateCcw v-else :size="16" />
                  回滚
                </button>
              </article>
            </div>
          </article>

          <section class="detail-card comment-card">
            <div class="detail-section-head">
              <h2>交流评论</h2>
              <span>用户可提问、补充渠道、反馈失效链接</span>
            </div>
            <form class="comment-composer" @submit.prevent="submitComment">
              <div class="comment-avatar">我</div>
              <input v-model="commentDraft" placeholder="写下你的补充，例如：某个工具权益是否仍可领取？" />
              <button class="detail-primary" type="submit" :disabled="commentLoading || !commentDraft.trim()">
                <Loader2 v-if="commentLoading" class="spin" :size="16" />
                <Send v-else :size="16" />
                发布评论
              </button>
            </form>
            <p v-if="commentMessage" class="comment-message">{{ commentMessage }}</p>
            <article v-for="comment in detail.detail.comments" :key="comment.id" class="comment-row">
              <div class="comment-avatar alt"><UserRound :size="18" /></div>
              <div>
                <strong>{{ comment.authorName || '社区成员' }}<span v-if="comment.isAuthor"> · 作者</span></strong>
                <p>{{ comment.content }}</p>
                <small>{{ formatDate(comment.createdAt) }}</small>
              </div>
            </article>
          </section>
        </main>

        <aside class="detail-side">
          <section class="detail-card side-card">
            <h2>发布信息</h2>
            <div class="info-row">
              <span class="small-icon">发</span>
              <span><strong>发布类型：{{ detail.detail.publishInfo.typeLabel }}</strong><small>{{ detail.detail.publishInfo.typeHint }}</small></span>
            </div>
            <div class="info-row">
              <span class="small-icon">版</span>
              <span><strong>当前版本：{{ detail.detail.publishInfo.versionLabel }}</strong><small>{{ detail.detail.publishInfo.versionHint }}</small></span>
            </div>
            <div class="info-row">
              <span class="small-icon">权</span>
              <span><strong>可见范围：{{ detail.detail.publishInfo.visibilityLabel }}</strong><small>{{ detail.detail.publishInfo.visibilityHint }}</small></span>
            </div>
          </section>

          <section class="detail-card side-card">
            <h2>包含入口</h2>
            <button
              v-for="item in includedItems"
              :key="item.id"
              class="detail-item"
              type="button"
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

          <section class="detail-card side-card">
            <h2>标签</h2>
            <div class="chip-row">
              <span v-for="(tag, index) in detailTags" :key="tag" :class="['chip', { primary: index === 0 }]">
                <Tag :size="13" />{{ tag }}
              </span>
            </div>
          </section>

          <section class="detail-card side-card">
            <button
              class="detail-primary full"
              type="button"
              :disabled="Boolean(actionLoading)"
              @click="executeAction(detail.detail.primaryAction)"
            >
              <Loader2 v-if="actionLoading === detail.detail.primaryAction.key" class="spin" :size="17" />
              <CheckCircle2 v-else-if="completedActions.has(detail.detail.primaryAction.key)" :size="17" />
              <span>{{ completedActions.has(detail.detail.primaryAction.key) ? '已完成' : detail.detail.primaryAction.label }}</span>
            </button>
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
  color: #111827;
}

.detail-topbar,
.detail-hero,
.detail-layout,
.detail-lock,
.detail-result {
  width: min(1500px, calc(100vw - 48px));
  margin: 0 auto;
}

.detail-topbar {
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-topbar-left,
.detail-topbar-right,
.detail-actions,
.detail-meta,
.detail-result,
.detail-lock,
.detail-editor-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-topbar strong {
  font-size: 24px;
  font-weight: 900;
}

button {
  font: inherit;
}

.detail-back,
.detail-home,
.detail-secondary,
.detail-primary,
.detail-tab {
  min-height: 40px;
  border-radius: 8px;
  cursor: pointer;
}

.detail-back,
.detail-home,
.detail-secondary {
  border: 1px solid #dce3ee;
  background: #fff;
  color: #172033;
}

.detail-back,
.detail-secondary,
.detail-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.detail-back,
.detail-home,
.detail-secondary {
  padding: 0 16px;
}

.detail-primary {
  min-width: 120px;
  border: 1px solid #6d4df2;
  padding: 0 20px;
  color: #fff;
  background: #6d4df2;
  font-weight: 800;
}

.detail-primary.full {
  width: 100%;
}

.detail-secondary.strong {
  font-weight: 800;
}

.detail-primary:disabled,
.detail-secondary:disabled,
.detail-item:disabled {
  opacity: 0.62;
  cursor: wait;
}

.detail-hero {
  min-height: 186px;
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  gap: 24px;
  align-items: center;
  padding: 34px 40px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
}

.detail-icon,
.small-icon,
.comment-avatar {
  display: grid;
  place-items: center;
}

.detail-icon {
  width: 72px;
  height: 72px;
  border-radius: 10px;
  background: linear-gradient(135deg, #7657ff, #6747ee);
  color: #fff;
  font-size: 32px;
  font-weight: 950;
}

.detail-kicker {
  color: #2147ff;
  font-weight: 800;
}

.detail-hero h1 {
  margin: 8px 0 10px;
  font-size: 34px;
  line-height: 1.16;
  letter-spacing: 0;
}

.detail-hero p,
.detail-section-head span,
.info-row small,
.detail-item small,
.history-row p,
.comment-row p {
  color: #627086;
}

.detail-hero p {
  margin: 0;
  line-height: 1.65;
}

.detail-meta {
  flex-wrap: wrap;
  margin-top: 8px;
  color: #526176;
  font-size: 14px;
}

.detail-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
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

.detail-card {
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
}

.detail-markdown-card,
.side-card {
  padding: 20px;
}

.detail-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #edf1f7;
}

.detail-section-head h2,
.side-card h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 900;
}

.detail-tabs {
  display: flex;
  gap: 8px;
}

.detail-tab {
  border: 0;
  padding: 0 14px;
  color: #4d5b72;
  background: transparent;
  font-weight: 800;
}

.detail-tab.active {
  color: #2147ff;
  background: #edf1ff;
}

.markdown-body {
  padding-top: 18px;
  color: #1b2435;
  font-size: 16px;
  line-height: 1.72;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(p) {
  margin: 0;
}

.markdown-body :deep(h1) {
  margin-bottom: 12px;
  font-size: 28px;
}

.markdown-body :deep(h2) {
  margin: 22px 0 10px;
  font-size: 24px;
}

.markdown-body :deep(h3) {
  margin: 18px 0 8px;
  font-size: 19px;
}

.markdown-body :deep(p) {
  margin: 10px 0;
}

.markdown-body :deep(blockquote) {
  margin: 18px 0;
  padding: 14px 16px;
  border-left: 4px solid #6d4df2;
  border-radius: 0 8px 8px 0;
  background: #f7f5ff;
  color: #25314a;
  font-weight: 700;
}

.markdown-body :deep(ul) {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 24px;
  margin: 14px 0;
  padding: 0;
  list-style: none;
}

.markdown-body :deep(li) {
  position: relative;
  padding-left: 22px;
}

.markdown-body :deep(li)::before {
  content: "";
  position: absolute;
  left: 0;
  top: 12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6d4df2;
}

.markdown-body :deep(ol) {
  display: grid;
  gap: 8px;
  padding-left: 22px;
}

.markdown-body :deep(table) {
  width: 100%;
  margin-top: 16px;
  border-collapse: collapse;
  overflow: hidden;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  font-size: 15px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 11px 13px;
  border-bottom: 1px solid #edf1f7;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f4f6fb;
  color: #111827;
  font-weight: 900;
}

.markdown-body :deep(code),
.markdown-body :deep(pre) {
  border-radius: 8px;
  background: #f4f6fb;
}

.markdown-body :deep(code) {
  padding: 2px 5px;
}

.markdown-body :deep(pre) {
  overflow-x: auto;
  padding: 14px;
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}

.detail-editor {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding-top: 18px;
}

.detail-editor label {
  display: grid;
  gap: 7px;
  color: #475569;
  font-size: 13px;
  font-weight: 800;
}

.field-wide {
  grid-column: 1 / -1;
}

.detail-editor input,
.detail-editor textarea,
.detail-editor select,
.comment-composer input {
  width: 100%;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fbfcff;
  color: #172033;
  font: inherit;
}

.detail-editor input,
.detail-editor select,
.comment-composer input {
  height: 42px;
  padding: 0 12px;
}

.detail-editor textarea {
  min-height: 78px;
  padding: 10px 12px;
  resize: vertical;
}

.detail-editor-actions {
  grid-column: 1 / -1;
  justify-content: flex-end;
}

.history-list {
  display: grid;
  gap: 12px;
  padding-top: 18px;
}

.history-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px;
  border: 1px solid #edf1f7;
  border-radius: 8px;
}

.history-row p,
.history-row small {
  margin: 4px 0 0;
}

.comment-card {
  padding: 18px 22px;
}

.comment-composer {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  margin-top: 16px;
}

.comment-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #101a33;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
}

.comment-avatar.alt {
  background: #6d4df2;
}

.comment-message {
  margin: 10px 0 0;
  color: #b45309;
}

.comment-row {
  display: grid;
  grid-template-columns: 38px 1fr;
  gap: 12px;
  margin-top: 16px;
}

.comment-row p {
  margin: 5px 0 0;
  line-height: 1.55;
}

.comment-row small {
  display: block;
  margin-top: 4px;
  color: #8b95a7;
}

.side-card {
  display: grid;
  gap: 12px;
}

.info-row,
.detail-item {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 13px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
  text-align: left;
}

.small-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: #f1edff;
  color: #6d4df2;
  font-weight: 950;
}

.info-row strong,
.info-row small,
.detail-item strong,
.detail-item small {
  display: block;
}

.detail-item {
  width: 100%;
  cursor: pointer;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #f2f5fa;
  color: #526176;
  font-size: 13px;
  font-weight: 800;
}

.chip.primary {
  color: #6d4df2;
  background: #f1edff;
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

@media (max-width: 980px) {
  .detail-topbar,
  .detail-hero,
  .detail-layout,
  .detail-lock,
  .detail-result {
    width: min(100vw - 28px, 1500px);
  }

  .detail-topbar,
  .detail-hero,
  .detail-layout,
  .detail-section-head,
  .comment-composer {
    grid-template-columns: 1fr;
  }

  .detail-topbar {
    height: auto;
    align-items: stretch;
    padding: 14px 0;
  }

  .detail-topbar,
  .detail-topbar-left,
  .detail-topbar-right {
    flex-wrap: wrap;
  }

  .detail-actions,
  .detail-editor-actions {
    justify-content: flex-start;
  }

  .detail-editor {
    grid-template-columns: 1fr;
  }

  .markdown-body :deep(ul) {
    grid-template-columns: 1fr;
  }
}
</style>

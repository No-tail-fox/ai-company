<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Heart, Search, Send, Settings, SlidersHorizontal } from 'lucide-vue-next';
import {
  buildCommunicationDetailPath,
  createCommunicationDraft,
  createFallbackCommunicationHallPayload,
  filterCommunicationPosts,
  validateCommunicationDraft,
  type CommunicationHallAction,
  type CommunicationHallCategory,
  type CommunicationHallDraft,
  type CommunicationHallPost,
  type CommunicationSortMode
} from '../services/communicationHall';
import {
  createCommunicationHallPost,
  fetchCommunicationHall,
  getCurrentUserId,
  getUserSession,
  runPortalAction
} from '../services/api';

const router = useRouter();
const fallbackPayload = createFallbackCommunicationHallPayload();
const posts = ref<CommunicationHallPost[]>([...fallbackPayload.posts]);
const categories = ref<CommunicationHallCategory[]>([...fallbackPayload.categories]);
const hotTags = ref<string[]>([...fallbackPayload.hotTags]);
const hotTopics = ref(fallbackPayload.hotTopics.map((topic) => ({ ...topic })));
const selectedCategory = ref('all');
const selectedTag = ref('');
const searchQuery = ref('');
const favoritesOnly = ref(false);
const favoriteIds = ref(new Set<string>());
const sortMode = ref<CommunicationSortMode>('latest');
const settingsOpen = ref(false);
const draft = ref(createCommunicationDraft());
const formErrors = ref<Partial<Record<keyof CommunicationHallDraft, string>>>({});
const statusMessage = ref('');
const hallLoading = ref(false);
const publishLoading = ref(false);
const publisherRef = ref<HTMLElement | null>(null);
const titleInputRef = ref<HTMLInputElement | null>(null);

onMounted(() => {
  void loadHall();
});

const visiblePosts = computed(() =>
  filterCommunicationPosts(posts.value, {
    query: searchQuery.value,
    categoryKey: selectedCategory.value,
    tag: selectedTag.value,
    favoritesOnly: favoritesOnly.value,
    favoriteIds: favoriteIds.value,
    sortMode: sortMode.value
  })
);
const activeCategoryLabel = computed(() =>
  categories.value.find((category) => category.key === selectedCategory.value)?.label ?? '全部'
);
const favoriteCount = computed(() => favoriteIds.value.size);
const sortLabel = computed(() => (sortMode.value === 'hot' ? '热度' : '最新'));

async function loadHall() {
  hallLoading.value = true;
  const payload = await fetchCommunicationHall(getCurrentUserId('demo-user'));
  categories.value = payload.categories;
  hotTags.value = payload.hotTags;
  hotTopics.value = payload.hotTopics;
  posts.value = payload.posts;
  favoriteIds.value = new Set(payload.posts.filter((post) => post.isFavorite).map((post) => post.id));
  hallLoading.value = false;
}

function selectCategory(categoryKey: string) {
  selectedCategory.value = categoryKey;
  selectedTag.value = '';
  statusMessage.value = categoryKey === 'all' ? '已显示全部帖子' : `已筛选：${activeCategoryLabel.value}`;
}

function selectTag(tag: string) {
  selectedTag.value = selectedTag.value === tag ? '' : tag;
  selectedCategory.value = 'all';
  statusMessage.value = selectedTag.value ? `已筛选标签：${tag}` : '已取消标签筛选';
}

function toggleFavoritesOnly() {
  favoritesOnly.value = !favoritesOnly.value;
  statusMessage.value = favoritesOnly.value ? `只看收藏：${favoriteCount.value} 条` : '已显示全部帖子';
}

async function toggleFavorite(post: CommunicationHallPost, actionKey: 'favorite' | 'follow' = 'favorite') {
  if (!getUserSession()?.accessToken) {
    statusMessage.value = '请先登录后再收藏或关注帖子';
    return;
  }
  const next = new Set(favoriteIds.value);
  if (next.has(post.id)) {
    next.delete(post.id);
  } else {
    next.add(post.id);
  }
  favoriteIds.value = next;
  try {
    const result = await runPortalAction({
      userId: getCurrentUserId('demo-user'),
      detailPath: buildCommunicationDetailPath(post),
      itemId: post.itemId ?? post.id,
      actionKey
    });
    const confirmed = new Set(favoriteIds.value);
    if (result.action?.status === 'COMPLETED') {
      confirmed.add(post.id);
      statusMessage.value = actionKey === 'follow' ? `已关注：${post.title}` : `已收藏：${post.title}`;
    } else {
      confirmed.delete(post.id);
      statusMessage.value = actionKey === 'follow' ? `已取消关注：${post.title}` : `已取消收藏：${post.title}`;
    }
    favoriteIds.value = confirmed;
  } catch {
    favoriteIds.value = favoriteIds.value.has(post.id)
      ? new Set([...favoriteIds.value].filter((id) => id !== post.id))
      : new Set([...favoriteIds.value, post.id]);
    statusMessage.value = '收藏状态同步失败，请稍后重试';
  }
}

async function focusPublisher() {
  publisherRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  await nextTick();
  titleInputRef.value?.focus();
}

async function publishPost() {
  const errors = validateCommunicationDraft(draft.value);
  formErrors.value = errors;
  if (Object.keys(errors).length > 0) {
    statusMessage.value = '请补全标题和正文后再发布';
    return;
  }
  if (!getUserSession()?.accessToken) {
    statusMessage.value = '请先登录后再发布，未登录不会写入后台';
    return;
  }
  publishLoading.value = true;
  try {
    const created = await createCommunicationHallPost({
      categoryKey: draft.value.categoryKey,
      title: draft.value.title.trim(),
      bodyMarkdown: draft.value.body.trim()
    });
    posts.value = [created.post, ...posts.value.filter((post) => post.id !== created.post.id)];
    draft.value = createCommunicationDraft();
    selectedCategory.value = 'all';
    selectedTag.value = '';
    sortMode.value = 'latest';
    statusMessage.value = '已发布到大厅并写入后台，刷新后仍可查看';
  } catch (error) {
    statusMessage.value = error instanceof Error ? error.message : '发布失败，请稍后重试';
  } finally {
    publishLoading.value = false;
  }
}

function openPost(post: CommunicationHallPost) {
  void router.push(buildCommunicationDetailPath(post));
}

async function handleAction(post: CommunicationHallPost, action: CommunicationHallAction) {
  if (action.kind === 'copy') {
    await copyTemplate(post);
    return;
  }
  if (action.kind === 'favorite' || action.kind === 'follow') {
    await toggleFavorite(post, action.kind);
    return;
  }
  openPost(post);
}

async function copyTemplate(post: CommunicationHallPost) {
  const text = post.templateText ?? `# ${post.title}\n\n${post.summary}`;
  try {
    await navigator.clipboard.writeText(text);
    statusMessage.value = `已复制：${post.title}`;
  } catch {
    statusMessage.value = '复制失败，请进入详情页后手动复制';
  }
}
</script>

<template>
  <main class="communication-hall-page">
    <header class="communication-head">
      <div>
        <h1>沟通大厅</h1>
        <p>公共沟通与发布平台：接单、模板、交流、资源对接都在这里沉淀。</p>
      </div>
      <label class="communication-search">
        <Search :size="18" />
        <input v-model="searchQuery" placeholder="搜索帖子、模板、接单需求或标签" />
      </label>
      <div class="communication-head-actions">
        <button type="button" aria-label="排序设置" @click="settingsOpen = !settingsOpen">
          <Settings :size="20" />
        </button>
        <button :class="{ active: favoritesOnly }" type="button" aria-label="只看收藏" @click="toggleFavoritesOnly">
          <Heart :size="21" />
        </button>
        <button class="communication-primary" type="button" @click="focusPublisher">发布信息</button>
      </div>
      <section v-if="settingsOpen" class="communication-settings">
        <strong>排序方式</strong>
        <button :class="{ active: sortMode === 'latest' }" type="button" @click="sortMode = 'latest'">最新优先</button>
        <button :class="{ active: sortMode === 'hot' }" type="button" @click="sortMode = 'hot'">热度优先</button>
      </section>
    </header>

    <nav class="communication-tabs" aria-label="沟通大厅分类">
      <button
        v-for="category in categories"
        :key="category.key"
        :class="{ active: selectedCategory === category.key && !selectedTag }"
        type="button"
        @click="selectCategory(category.key)"
      >
        {{ category.label }}
      </button>
    </nav>

    <p v-if="statusMessage || hallLoading" class="communication-status">
      {{ hallLoading ? '正在同步大厅数据...' : statusMessage }}
    </p>

    <div class="communication-layout">
      <section class="communication-post-grid">
        <article
          v-for="post in visiblePosts"
          :key="post.id"
          class="communication-post-card"
          role="button"
          tabindex="0"
          @click="openPost(post)"
          @keydown.enter="openPost(post)"
        >
          <div class="communication-post-top">
            <span :class="['communication-mark', `tone-${post.tone}`]">{{ post.mark }}</span>
            <div>
              <h2>{{ post.title }}</h2>
              <p>{{ post.summary }}</p>
            </div>
            <span :class="['communication-badge', `tone-${post.tone}`]">{{ post.badgeLabel }}</span>
          </div>

          <div v-if="post.actions.length" class="communication-post-actions">
            <button
              v-for="action in post.actions"
              :key="action.key"
              :class="['communication-soft-action', action.tone]"
              type="button"
              @click.stop="handleAction(post, action)"
            >
              {{ favoriteIds.has(post.id) && (action.kind === 'favorite' || action.kind === 'follow') ? (action.kind === 'follow' ? '已关注' : '已收藏') : action.label }}
            </button>
          </div>
          <p v-if="post.replyStrip" class="communication-reply">{{ post.replyStrip }}</p>
          <footer>
            <span>{{ post.comments }} 条交流 · {{ post.viewLabel }} 浏览</span>
            <span>{{ post.timeLabel }}</span>
          </footer>
        </article>

        <section v-if="visiblePosts.length === 0" class="communication-empty">
          <SlidersHorizontal :size="28" />
          <strong>没有匹配的帖子</strong>
          <span>试试切换分类、清空搜索或取消只看收藏。</span>
        </section>
      </section>

      <aside class="communication-side">
        <section ref="publisherRef" class="communication-side-card">
          <h2>快速发布</h2>
          <label>
            <span>发布区域</span>
            <select v-model="draft.categoryKey">
              <option v-for="category in categories.filter((category) => category.key !== 'all')" :key="category.key" :value="category.key">
                {{ category.label }}
              </option>
            </select>
          </label>
          <label>
            <span>标题</span>
            <input ref="titleInputRef" v-model="draft.title" placeholder="一句话说明你要发布什么" />
            <small v-if="formErrors.title">{{ formErrors.title }}</small>
          </label>
          <label>
            <span>正文（Markdown）</span>
            <textarea v-model="draft.body" placeholder="支持 **重点**、清单、链接、报价表。发布后会进入详情页，可继续评论交流。" />
            <small v-if="formErrors.body">{{ formErrors.body }}</small>
          </label>
          <button class="communication-publish" type="button" :disabled="publishLoading" @click="publishPost">
            <Send :size="17" />
            {{ publishLoading ? '发布中...' : '发布到大厅' }}
          </button>
        </section>

        <section class="communication-side-card">
          <h2>热门标签</h2>
          <div class="communication-chip-row">
            <button
              v-for="tag in hotTags"
              :key="tag"
              :class="{ active: selectedTag === tag }"
              type="button"
              @click="selectTag(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </section>

        <section class="communication-side-card">
          <h2>本周热议</h2>
          <div class="communication-hot-list">
            <button
              v-for="(topic, index) in hotTopics"
              :key="topic.title"
              type="button"
              @click="searchQuery = topic.title"
            >
              <span>{{ index + 1 }}</span>
              <strong>{{ topic.title }}</strong>
              <em>{{ topic.count }}</em>
            </button>
          </div>
        </section>
      </aside>
    </div>

    <span class="communication-sort-note">当前：{{ activeCategoryLabel }} · {{ sortLabel }}</span>
  </main>
</template>
<style scoped>
.communication-hall-page {
  min-height: calc(100vh - var(--portal-chrome-height, 136px));
  padding: 24px 58px 58px;
  background: #f6f7fb;
  color: #111827;
}

.communication-head {
  position: relative;
  display: grid;
  grid-template-columns: minmax(360px, 1fr) 520px auto;
  align-items: center;
  gap: 18px;
}

.communication-head h1 {
  margin: 0;
  font-size: 30px;
  letter-spacing: 0;
}

.communication-head p {
  margin: 4px 0 0;
  color: #627086;
}

.communication-search,
.communication-head-actions,
.communication-head-actions button,
.communication-tabs,
.communication-post-actions,
.communication-post-card footer,
.communication-soft-action,
.communication-publish,
.communication-hot-list button {
  display: flex;
  align-items: center;
}

.communication-search {
  height: 44px;
  gap: 10px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  padding: 0 14px;
  background: #fff;
  color: #8b95a7;
}

.communication-search input {
  width: 100%;
  border: 0;
  color: #172033;
  background: transparent;
}

.communication-head-actions {
  gap: 12px;
}

.communication-head-actions button {
  height: 42px;
  justify-content: center;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
  color: #172033;
}

.communication-head-actions button:not(.communication-primary) {
  width: 42px;
}

.communication-head-actions button.active {
  color: #6d4df2;
  background: #f1edff;
}

.communication-head-actions .communication-primary,
.communication-publish {
  border-color: #6d4df2;
  color: #fff;
  background: #6d4df2;
  font-weight: 900;
}

.communication-primary {
  min-width: 120px;
  padding: 0 18px;
}

.communication-settings {
  position: absolute;
  right: 144px;
  top: 52px;
  z-index: 4;
  width: 170px;
  display: grid;
  gap: 8px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  padding: 12px;
  background: #fff;
  box-shadow: 0 14px 28px rgba(18, 27, 45, 0.12);
}

.communication-settings strong {
  font-size: 13px;
}

.communication-settings button {
  height: 34px;
  border: 0;
  border-radius: 7px;
  color: #526176;
  background: #f6f8fc;
  font-weight: 800;
}

.communication-settings button.active {
  color: #2147ff;
  background: #edf1ff;
}

.communication-tabs {
  height: 58px;
  gap: 14px;
  margin-top: 16px;
  border-bottom: 1px solid #edf1f7;
}

.communication-tabs button {
  height: 36px;
  border: 0;
  border-radius: 8px;
  padding: 0 13px;
  color: #58647a;
  background: transparent;
  font-weight: 800;
}

.communication-tabs button.active {
  color: #2147ff;
  background: #e9eeff;
}

.communication-status,
.communication-sort-note {
  display: inline-flex;
  margin-top: 10px;
  color: #526176;
  font-size: 13px;
  font-weight: 700;
}

.communication-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 390px;
  gap: 20px;
  margin-top: 18px;
}

.communication-post-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  align-content: start;
}

.communication-post-card {
  min-height: 236px;
  display: flex;
  flex-direction: column;
  padding: 18px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 2px rgba(18, 27, 45, 0.03);
  cursor: pointer;
}

.communication-post-top {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
}

.communication-mark {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #fff;
  font-weight: 950;
}

.communication-mark.tone-order,
.communication-mark.tone-pitch {
  background: #0ea5e9;
}

.communication-mark.tone-template {
  background: #6d4df2;
}

.communication-mark.tone-talk {
  background: #10b981;
}

.communication-mark.tone-resource {
  background: #f59e0b;
}

.communication-post-card h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.36;
  letter-spacing: 0;
}

.communication-post-card p {
  margin: 10px 0 0;
  color: #42506a;
  line-height: 1.58;
}

.communication-badge {
  height: 28px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0 10px;
  font-size: 13px;
  font-weight: 900;
}

.communication-badge.tone-order,
.communication-badge.tone-pitch {
  color: #0369a1;
  background: #e0f2fe;
}

.communication-badge.tone-template {
  color: #5b3ee9;
  background: #f0edff;
}

.communication-badge.tone-talk {
  color: #047857;
  background: #dcfce7;
}

.communication-badge.tone-resource {
  color: #a16207;
  background: #fef3c7;
}

.communication-post-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 16px;
}

.communication-soft-action {
  min-height: 42px;
  justify-content: center;
  border: 0;
  border-radius: 8px;
  font-weight: 900;
}

.communication-soft-action.blue {
  color: #0369a1;
  background: #eef7ff;
}

.communication-soft-action.pink {
  color: #d11d48;
  background: #fff0f0;
}

.communication-reply {
  padding: 10px 12px;
  border-radius: 8px;
  background: #f7f9fc;
  font-size: 13px;
}

.communication-post-card footer {
  justify-content: space-between;
  gap: 12px;
  margin-top: auto;
  padding-top: 14px;
  color: #748096;
  font-size: 13px;
}

.communication-side {
  display: grid;
  gap: 16px;
  align-content: start;
}

.communication-side-card,
.communication-empty {
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
}

.communication-side-card {
  display: grid;
  gap: 12px;
  padding: 20px;
}

.communication-side-card h2 {
  margin: 0;
  font-size: 18px;
}

.communication-side-card label {
  display: grid;
  gap: 7px;
}

.communication-side-card label span {
  color: #475569;
  font-size: 13px;
  font-weight: 900;
}

.communication-side-card input,
.communication-side-card select,
.communication-side-card textarea {
  width: 100%;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  color: #172033;
  background: #fbfcff;
}

.communication-side-card input,
.communication-side-card select {
  height: 42px;
  padding: 0 12px;
}

.communication-side-card textarea {
  min-height: 124px;
  resize: vertical;
  padding: 12px;
  line-height: 1.55;
}

.communication-side-card small {
  color: #d11d48;
  font-weight: 800;
}

.communication-publish {
  min-height: 44px;
  justify-content: center;
  gap: 8px;
  border: 0;
  border-radius: 8px;
}

.communication-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.communication-chip-row button {
  height: 30px;
  border: 0;
  border-radius: 999px;
  padding: 0 11px;
  color: #526176;
  background: #f2f5fa;
  font-size: 13px;
  font-weight: 800;
}

.communication-chip-row button.active {
  color: #6d4df2;
  background: #f1edff;
}

.communication-hot-list {
  display: grid;
  gap: 10px;
}

.communication-hot-list button {
  display: grid;
  grid-template-columns: 26px 1fr auto;
  gap: 10px;
  min-height: 30px;
  border: 0;
  background: transparent;
  color: #344054;
  text-align: left;
}

.communication-hot-list span {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 7px;
  color: #fff;
  background: #111827;
  font-size: 12px;
  font-weight: 900;
}

.communication-hot-list strong {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
}

.communication-hot-list em {
  font-style: normal;
  font-weight: 900;
}

.communication-empty {
  min-height: 220px;
  grid-column: 1 / -1;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 8px;
  color: #627086;
}

.communication-empty strong {
  color: #111827;
}

@media (max-width: 1440px) and (min-width: 1121px) {
  .communication-post-card {
    padding: 16px;
  }

  .communication-post-top {
    grid-template-columns: 42px minmax(0, 1fr);
    gap: 10px;
  }

  .communication-mark {
    width: 42px;
    height: 42px;
  }

  .communication-badge {
    grid-column: 1 / -1;
    justify-self: start;
  }

  .communication-post-card h2 {
    font-size: 17px;
  }
}

@media (max-width: 1120px) {
  .communication-head,
  .communication-layout,
  .communication-post-grid {
    grid-template-columns: 1fr;
  }

  .communication-head-actions {
    justify-content: flex-start;
  }
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { BookOpen, ChevronLeft, ChevronRight, Loader2, Lock, Search } from 'lucide-vue-next';
import { fetchCourses } from '../services/api';
import type { CourseCatalogItem, CourseCatalogPayload } from '../services/viewModel';

const router = useRouter();
const loading = ref(false);
const errorMessage = ref('');
const query = ref('');
const category = ref('');
const page = ref(1);
const pageSize = 20;
const catalog = ref<CourseCatalogPayload>({
  tenantId: 'demo',
  total: 0,
  page: 1,
  pageSize,
  categories: [],
  items: []
});

const totalPages = computed(() => Math.max(1, Math.ceil(catalog.value.total / catalog.value.pageSize)));
const hasCourses = computed(() => catalog.value.items.length > 0);

onMounted(loadCourses);

watch(category, () => {
  page.value = 1;
  void loadCourses();
});

async function loadCourses() {
  loading.value = true;
  errorMessage.value = '';
  try {
    catalog.value = await fetchCourses({
      query: query.value.trim(),
      category: category.value,
      page: page.value,
      pageSize
    });
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '课程库暂时无法加载';
  } finally {
    loading.value = false;
  }
}

function submitSearch() {
  page.value = 1;
  void loadCourses();
}

function changePage(offset: number) {
  const nextPage = Math.min(totalPages.value, Math.max(1, page.value + offset));
  if (nextPage === page.value) {
    return;
  }
  page.value = nextPage;
  void loadCourses();
}

function openCourse(course: CourseCatalogItem) {
  if (course.detailPath) {
    void router.push(course.detailPath);
  }
}

function formatDate(value: string | null) {
  if (!value) {
    return '刚刚同步';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
}
</script>

<template>
  <main class="course-library-page">
    <section class="course-library-header">
      <div>
        <span class="course-kicker">学习成长</span>
        <h1>副业课程库</h1>
        <p>汇总飞书知识库同步的课程、实操复盘和案例拆解，按分类检索并进入 Markdown 详情页学习。</p>
      </div>
      <div class="course-stat">
        <strong>{{ catalog.total }}</strong>
        <span>已入库课程</span>
      </div>
    </section>

    <section class="course-toolbar">
      <form class="course-search" @submit.prevent="submitSearch">
        <Search :size="18" />
        <input v-model="query" placeholder="搜索课程标题、摘要或分类" />
        <button type="submit">搜索</button>
      </form>
      <select v-model="category" class="category-filter" aria-label="课程分类">
        <option value="">全部分类</option>
        <option v-for="item in catalog.categories" :key="item" :value="item">{{ item }}</option>
      </select>
    </section>

    <section v-if="loading" class="course-state">
      <Loader2 class="spin" :size="26" />
      <span>正在加载课程</span>
    </section>

    <section v-else-if="errorMessage" class="course-state">
      <strong>课程库加载失败</strong>
      <span>{{ errorMessage }}</span>
      <button type="button" @click="loadCourses">重试</button>
    </section>

    <section v-else-if="!hasCourses" class="course-state">
      <BookOpen :size="28" />
      <strong>还没有同步课程</strong>
      <span>管理员完成飞书知识库同步后，课程会显示在这里。</span>
    </section>

    <section v-else class="course-grid">
      <button v-for="course in catalog.items" :key="course.id" class="course-card" type="button" @click="openCourse(course)">
        <span class="course-card-top">
          <span class="course-category">{{ course.category || '飞书课程' }}</span>
          <span v-if="course.requiredMembership" class="member-chip"><Lock :size="13" />会员</span>
        </span>
        <strong>{{ course.title }}</strong>
        <small>{{ course.subtitle }}</small>
        <span class="source-path">{{ course.sourcePath.join(' / ') || '飞书知识库' }}</span>
        <span class="course-card-foot">
          <span>{{ formatDate(course.updatedAt) }}</span>
          <ChevronRight :size="16" />
        </span>
      </button>
    </section>

    <section class="page-actions">
      <button type="button" :disabled="page <= 1 || loading" @click="changePage(-1)">
        <ChevronLeft :size="16" />上一页
      </button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button type="button" :disabled="page >= totalPages || loading" @click="changePage(1)">
        下一页<ChevronRight :size="16" />
      </button>
    </section>
  </main>
</template>

<style scoped>
.course-library-page {
  min-height: calc(100vh - var(--portal-chrome-height, 0px));
  display: grid;
  gap: 18px;
  padding: 24px min(36px, 4vw) 48px;
  background: #f6f7fb;
  color: #111827;
}

.course-library-header,
.course-toolbar,
.course-grid,
.page-actions {
  width: min(1380px, 100%);
  margin: 0 auto;
}

.course-library-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 18px;
  align-items: center;
  padding: 24px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
}

.course-kicker,
.course-category,
.member-chip {
  display: inline-flex;
  align-items: center;
  font-weight: 900;
}

.course-kicker {
  color: #3b63f6;
}

.course-library-header h1 {
  margin: 6px 0 8px;
  font-size: 32px;
  line-height: 1.16;
}

.course-library-header p,
.course-card small,
.source-path {
  color: #667085;
  line-height: 1.55;
}

.course-stat {
  min-height: 120px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 6px;
  border-radius: 8px;
  background: #eef3ff;
  color: #234bdc;
}

.course-stat strong {
  font-size: 34px;
}

.course-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 12px;
}

.course-search,
.category-filter,
.page-actions button {
  min-height: 44px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
}

.course-search {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 0 10px 0 14px;
}

.course-search input,
.category-filter {
  width: 100%;
  border: 0;
  color: #111827;
  font: inherit;
}

.course-search input:focus,
.category-filter:focus {
  outline: none;
}

.course-search button,
.page-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 0;
  border-radius: 8px;
  padding: 0 16px;
  color: #fff;
  background: #5f50f5;
  font-weight: 900;
}

.category-filter {
  padding: 0 12px;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.course-card {
  min-height: 212px;
  display: grid;
  align-content: start;
  gap: 10px;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  text-align: left;
}

.course-card-top,
.course-card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.course-category,
.member-chip {
  min-height: 26px;
  border-radius: 999px;
  padding: 0 9px;
  font-size: 12px;
}

.course-category {
  color: #3b63f6;
  background: #eef3ff;
}

.member-chip {
  gap: 4px;
  color: #9a5a00;
  background: #fff4d6;
}

.course-card strong {
  color: #172033;
  font-size: 17px;
  line-height: 1.35;
}

.source-path {
  overflow-wrap: anywhere;
  font-size: 12px;
}

.course-card-foot {
  align-self: end;
  color: #5f50f5;
  font-weight: 900;
}

.course-state {
  width: min(1380px, 100%);
  min-height: 280px;
  display: grid;
  place-items: center;
  align-content: center;
  gap: 10px;
  margin: 0 auto;
  border: 1px solid #dce3ee;
  border-radius: 8px;
  background: #fff;
  color: #667085;
}

.course-state button {
  min-height: 38px;
  border: 0;
  border-radius: 8px;
  padding: 0 16px;
  color: #fff;
  background: #5f50f5;
  font-weight: 900;
}

.page-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
}

.page-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin {
  animation: course-spin 0.8s linear infinite;
}

@keyframes course-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1180px) {
  .course-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .course-library-header,
  .course-toolbar,
  .course-grid {
    grid-template-columns: 1fr;
  }

  .course-library-header h1 {
    font-size: 28px;
  }
}
</style>

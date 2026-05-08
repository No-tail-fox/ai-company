<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowLeft, Eye, EyeOff, ImagePlus, Lock, Maximize2, Minus, Plus, RefreshCw, X } from 'lucide-vue-next';
import {
  adminFetchPageContent,
  adminCreateItem,
  adminCreatePage,
  adminCreateSection,
  adminListPages,
  adminReorderItems,
  adminReorderPages,
  adminReorderSections,
  adminUpdateItem,
  adminUpdatePage,
  adminUpdateSection,
  adminUploadImage,
  clearAdminToken,
  getAdminToken,
  loginAdmin
} from '../services/api';
import DynamicPage from '../components/DynamicPage.vue';
import { clampPreviewScale, moveRecord, reorderByDrop } from '../services/adminInteractions';
import { buildItemPayload, buildPagePayload, buildReorderPayload, buildSectionPayload } from '../services/adminForms';
import type { PageConfigSummary, PortalItem, PortalPageConfig, PortalSection } from '../services/viewModel';

type AdminPanel = 'page' | 'section' | 'item' | '';

const router = useRouter();
const token = ref(getAdminToken());
const errorMessage = ref('');
const notice = ref('');
const loginForm = reactive({ phone: '13900000000', password: 'admin123456' });
const pages = ref<PageConfigSummary[]>([]);
const selectedPageKey = ref('home');
const pageConfig = ref<PortalPageConfig | null>(null);
const draggedPageId = ref('');
const draggedSectionId = ref('');
const draggedItemId = ref('');
const activeDropPageId = ref('');
const activeDropSectionId = ref('');
const activeDropItemId = ref('');
const activePanel = ref<AdminPanel>('');
const previewScale = ref(0.55);
const previewWidth = ref(560);

let resizeStartX = 0;
let resizeStartWidth = 0;

const pageForm = reactive({
  pageKey: 'new-page',
  label: '新页面',
  title: '新页面中心',
  subtitle: '由管理端新增的模块化页面',
  icon: 'Sparkles',
  sortOrder: 120,
  enabled: true
});

const sectionForm = reactive({
  pageKey: 'home',
  sectionKey: 'new_section',
  title: '新增模块',
  subtitle: '模块说明',
  layout: 'tool-grid',
  sortOrder: 100,
  enabled: true
});

const itemForm = reactive({
  sectionId: '',
  itemType: 'tool',
  title: '新增工具卡片',
  subtitle: '卡片说明',
  category: '工具',
  icon: 'Sparkles',
  imageUrl: '',
  badge: '',
  tagsText: 'AI,模板',
  sortOrder: 100,
  enabled: true,
  actionType: 'workspace',
  actionValue: 'new-tool',
  requiredMembership: false,
  pointCost: 0
});

const allItems = computed<PortalItem[]>(() => pageConfig.value?.sections.flatMap((section) => section.items) ?? []);
const selectedSections = computed<PortalSection[]>(() => pageConfig.value?.sections ?? []);
const sortablePages = computed<Array<PageConfigSummary & { id: string }>>(
  () => pages.value.filter((page): page is PageConfigSummary & { id: string } => Boolean(page.id))
);
const previewPageConfig = computed<PortalPageConfig | null>(() => {
  if (!pageConfig.value) {
    return null;
  }
  return {
    ...pageConfig.value,
    sections: pageConfig.value.sections
      .filter((section) => section.enabled)
      .map((section) => ({
        ...section,
        items: section.items.filter((item) => item.enabled)
      }))
  };
});
const activePanelTitle = computed(() => {
  if (activePanel.value === 'page') {
    return '新增页面';
  }
  if (activePanel.value === 'section') {
    return '新增模块';
  }
  if (activePanel.value === 'item') {
    return '新增卡片';
  }
  return '';
});
const previewPercent = computed(() => `${Math.round(previewScale.value * 100)}%`);
const previewPanelStyle = computed(() => ({ width: `${previewWidth.value}px` }));
const previewStageStyle = computed(() => ({
  width: '1120px',
  transform: `scale(${previewScale.value})`
}));

onMounted(async () => {
  if (token.value) {
    await refreshAdmin();
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', resizePreview);
  window.removeEventListener('pointerup', stopPreviewResize);
});

async function submitLogin() {
  await run(async () => {
    const result = await loginAdmin(loginForm.phone, loginForm.password);
    token.value = result.accessToken;
    notice.value = `已登录：${result.user.displayName || result.user.phone}`;
    await refreshAdmin();
  });
}

async function refreshAdmin() {
  const rawPages = await adminListPages();
  pages.value = rawPages.map((page: any) => ({
    id: page.id,
    tenantId: page.tenant_id ?? page.tenantId,
    pageKey: page.page_key ?? page.pageKey,
    label: page.label,
    title: page.title,
    subtitle: page.subtitle ?? '',
    icon: page.icon ?? 'Sparkles',
    sortOrder: Number(page.sort_order ?? page.sortOrder ?? 100),
    enabled: Boolean(page.enabled ?? true)
  }));
  if (!pages.value.some((page) => page.pageKey === selectedPageKey.value)) {
    selectedPageKey.value = pages.value[0]?.pageKey ?? 'home';
  }
  await loadSelectedPage();
}

async function loadSelectedPage() {
  sectionForm.pageKey = selectedPageKey.value;
  const nextPageConfig = await adminFetchPageContent(selectedPageKey.value);
  pageConfig.value = nextPageConfig;
  itemForm.sectionId = nextPageConfig.sections[0]?.id ?? '';
}

async function createPage() {
  await run(async () => {
    await adminCreatePage(buildPagePayload(pageForm));
    selectedPageKey.value = pageForm.pageKey;
    notice.value = '页面已创建';
    activePanel.value = '';
    await refreshAdmin();
  });
}

async function togglePageVisibility(page: PageConfigSummary) {
  if (!page.id) {
    return;
  }
  await run(async () => {
    await adminUpdatePage(page.id!, { enabled: !page.enabled });
    notice.value = page.enabled ? '页面已设为不可视' : '页面已恢复可视';
    await refreshAdmin();
  });
}

async function movePage(pageId: string, direction: -1 | 1) {
  const nextPages = moveRecord(sortablePages.value, pageId, direction);
  if (!nextPages) {
    return;
  }
  await savePageOrder(nextPages as PageConfigSummary[]);
}

async function dropPage(targetPageId?: string) {
  if (!targetPageId) {
    return;
  }
  const nextPages = reorderByDrop(sortablePages.value, draggedPageId.value, targetPageId);
  draggedPageId.value = '';
  activeDropPageId.value = '';
  if (!nextPages) {
    return;
  }
  await savePageOrder(nextPages as PageConfigSummary[]);
}

async function savePageOrder(nextPages: PageConfigSummary[]) {
  await run(async () => {
    await adminReorderPages(buildReorderPayload(nextPages.map((page) => ({ id: page.id! }))));
    notice.value = '页面顺序已保存';
    await refreshAdmin();
  });
}

async function createSection() {
  await run(async () => {
    sectionForm.pageKey = selectedPageKey.value;
    await adminCreateSection(buildSectionPayload(sectionForm));
    notice.value = '模块已创建';
    activePanel.value = '';
    await refreshAdmin();
  });
}

async function toggleSectionVisibility(section: PortalSection) {
  await run(async () => {
    await adminUpdateSection(section.id, { enabled: !section.enabled });
    notice.value = section.enabled ? '模块已设为不可视' : '模块已恢复可视';
    await refreshAdmin();
  });
}

async function moveSection(sectionId: string, direction: -1 | 1) {
  const nextSections = moveRecord(selectedSections.value, sectionId, direction);
  if (!nextSections) {
    return;
  }
  await saveSectionOrder(nextSections);
}

async function dropSection(targetSectionId: string) {
  const nextSections = reorderByDrop(selectedSections.value, draggedSectionId.value, targetSectionId);
  draggedSectionId.value = '';
  activeDropSectionId.value = '';
  if (!nextSections) {
    return;
  }
  await saveSectionOrder(nextSections);
}

async function saveSectionOrder(nextSections: PortalSection[]) {
  await run(async () => {
    await adminReorderSections(buildReorderPayload(nextSections));
    notice.value = '模块顺序已保存';
    await refreshAdmin();
  });
}

async function createItem() {
  await run(async () => {
    await adminCreateItem(
      buildItemPayload({
        ...itemForm,
        tags: itemForm.tagsText.split(',').map((tag) => tag.trim()).filter(Boolean)
      })
    );
    notice.value = '卡片已创建';
    activePanel.value = '';
    await refreshAdmin();
  });
}

async function moveItem(itemId: string, direction: -1 | 1) {
  const section = selectedSections.value.find((candidate) => candidate.items.some((item) => item.id === itemId));
  if (!section) {
    return;
  }
  const nextItems = moveRecord(section.items, itemId, direction);
  if (!nextItems) {
    return;
  }
  await saveItemOrder(section.id, nextItems);
}

async function dropItem(section: PortalSection, targetItemId: string) {
  const nextItems = reorderByDrop(section.items, draggedItemId.value, targetItemId);
  draggedItemId.value = '';
  activeDropItemId.value = '';
  if (!nextItems) {
    return;
  }
  await saveItemOrder(section.id, nextItems);
}

async function saveItemOrder(sectionId: string, nextItems: PortalItem[]) {
  await run(async () => {
    await adminReorderItems(buildReorderPayload(nextItems, sectionId));
    notice.value = '卡片顺序已保存';
    await refreshAdmin();
  });
}

async function toggleItemVisibility(item: PortalItem) {
  await run(async () => {
    await adminUpdateItem(item.id, { enabled: !item.enabled });
    notice.value = item.enabled ? '卡片已设为不可视' : '卡片已恢复可视';
    await refreshAdmin();
  });
}

async function uploadImage(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    return;
  }
  await run(async () => {
    const result = await adminUploadImage(file);
    itemForm.imageUrl = result.url;
    notice.value = '图片已上传并填入卡片图片地址';
  });
}

function logout() {
  clearAdminToken();
  token.value = '';
  pages.value = [];
  pageConfig.value = null;
}

function openPanel(panel: AdminPanel) {
  activePanel.value = panel;
  sectionForm.pageKey = selectedPageKey.value;
  itemForm.sectionId = pageConfig.value?.sections[0]?.id ?? '';
}

function closePanel() {
  activePanel.value = '';
}

function setPreviewScale(value: number) {
  previewScale.value = clampPreviewScale(value);
}

function nudgePreviewScale(delta: number) {
  setPreviewScale(previewScale.value + delta);
}

function startPreviewResize(event: PointerEvent) {
  event.preventDefault();
  resizeStartX = event.clientX;
  resizeStartWidth = previewWidth.value;
  window.addEventListener('pointermove', resizePreview);
  window.addEventListener('pointerup', stopPreviewResize);
}

function resizePreview(event: PointerEvent) {
  const delta = event.clientX - resizeStartX;
  previewWidth.value = Math.min(960, Math.max(380, resizeStartWidth - delta));
}

function stopPreviewResize() {
  window.removeEventListener('pointermove', resizePreview);
  window.removeEventListener('pointerup', stopPreviewResize);
}

async function run(task: () => Promise<void>) {
  errorMessage.value = '';
  try {
    await task();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '操作失败';
  }
}
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <button class="back-link" @click="router.push('/home')"><ArrowLeft :size="18" />返回前台</button>
      <h1>OPC 管理端</h1>
      <p>页面、模块、卡片和素材统一配置。</p>
      <button v-if="token" class="ghost-btn" @click="logout"><Lock :size="18" />退出登录</button>
    </aside>

    <main class="admin-main">
      <section v-if="!token" class="admin-login">
        <h2>管理员登录</h2>
        <label>手机号<input v-model="loginForm.phone" /></label>
        <label>密码<input v-model="loginForm.password" type="password" /></label>
        <button class="primary-btn" @click="submitLogin">登录管理端</button>
      </section>

      <template v-else>
        <header class="admin-header">
          <div>
            <span>内容中台</span>
            <h2>模块化页面管理</h2>
          </div>
          <button class="ghost-btn" @click="refreshAdmin"><RefreshCw :size="18" />刷新</button>
        </header>

        <p v-if="notice" class="notice">{{ notice }}</p>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <section class="admin-workbench">
          <div class="admin-edit-column">
            <section class="admin-grid">
              <div class="admin-card page-list">
                <header>
                  <strong>页面列表</strong>
                  <button class="small-action" @click="openPanel('page')"><Plus :size="16" />新增页面</button>
                </header>
                <div
                  v-for="page in pages"
                  :key="page.pageKey"
                  :class="['page-row', 'draggable-row', { active: selectedPageKey === page.pageKey, 'drop-target': activeDropPageId === page.id, 'is-hidden': !page.enabled }]"
                  draggable="true"
                  @dragstart="draggedPageId = page.id || ''"
                  @dragend="draggedPageId = ''; activeDropPageId = ''"
                  @dragenter.prevent="activeDropPageId = page.id || ''"
                  @dragover.prevent
                  @drop="dropPage(page.id)"
                  @click="selectedPageKey = page.pageKey; loadSelectedPage()"
                >
                  <span class="drag-handle">⋮⋮</span>
                  <span>{{ page.label }}</span>
                  <small>{{ page.pageKey }}</small>
                  <span class="row-actions">
                    <button class="mini-btn" @click.stop="movePage(page.id || '', -1)">↑</button>
                    <button class="mini-btn" @click.stop="movePage(page.id || '', 1)">↓</button>
                    <button class="icon-btn visibility-btn" @click.stop="togglePageVisibility(page)">
                      <Eye v-if="page.enabled" :size="16" />
                      <EyeOff v-else :size="16" />
                    </button>
                  </span>
                </div>
              </div>
            </section>

            <section class="admin-grid two">
              <div class="admin-card">
                <header>
                  <strong>模块列表</strong>
                  <button class="small-action" @click="openPanel('section')"><Plus :size="16" />新增模块</button>
                </header>
                <div
                  v-for="section in selectedSections"
                  :key="section.id"
                  :class="['admin-row', 'draggable-row', { 'drop-target': activeDropSectionId === section.id, 'is-hidden': !section.enabled }]"
                  draggable="true"
                  @dragstart="draggedSectionId = section.id"
                  @dragend="draggedSectionId = ''; activeDropSectionId = ''"
                  @dragenter.prevent="activeDropSectionId = section.id"
                  @dragover.prevent
                  @drop="dropSection(section.id)"
                >
                  <span class="drag-handle">⋮⋮</span>
                  <div>
                    <strong>{{ section.title }}</strong>
                    <span>{{ section.layout }} · {{ section.sectionKey }}</span>
                  </div>
                  <div class="row-actions">
                    <button class="mini-btn" @click="moveSection(section.id, -1)">↑</button>
                    <button class="mini-btn" @click="moveSection(section.id, 1)">↓</button>
                    <button class="icon-btn visibility-btn" @click="toggleSectionVisibility(section)">
                      <Eye v-if="section.enabled" :size="16" />
                      <EyeOff v-else :size="16" />
                    </button>
                  </div>
                </div>
              </div>
            </section>

            <section class="admin-grid">
              <div class="admin-card">
                <header>
                  <strong>卡片列表</strong>
                  <button class="small-action" @click="openPanel('item')"><Plus :size="16" />新增卡片</button>
                </header>
                <div v-for="section in selectedSections" :key="section.id" class="item-group">
                  <strong>{{ section.title }}</strong>
                  <div
                    v-for="item in section.items"
                    :key="item.id"
                    :class="['admin-row', 'draggable-row', 'compact', { 'drop-target': activeDropItemId === item.id, 'is-hidden': !item.enabled }]"
                    draggable="true"
                    @dragstart="draggedItemId = item.id"
                    @dragend="draggedItemId = ''; activeDropItemId = ''"
                    @dragenter.prevent="activeDropItemId = item.id"
                    @dragover.prevent
                    @drop="dropItem(section, item.id)"
                  >
                    <span class="drag-handle">⋮⋮</span>
                    <div>
                      <strong>{{ item.title }}</strong>
                      <span>{{ item.category }} · {{ item.itemType }}</span>
                    </div>
                    <div class="row-actions">
                      <button class="mini-btn" @click="moveItem(item.id, -1)">↑</button>
                      <button class="mini-btn" @click="moveItem(item.id, 1)">↓</button>
                      <button class="icon-btn visibility-btn" @click="toggleItemVisibility(item)">
                        <Eye v-if="item.enabled" :size="16" />
                        <EyeOff v-else :size="16" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </div>

          <aside class="admin-preview-panel" :style="previewPanelStyle">
            <span class="preview-resize-handle" @pointerdown="startPreviewResize"></span>
            <header>
              <div>
                <span>实时预览</span>
                <strong>{{ pageConfig?.page.title }}</strong>
              </div>
              <div class="preview-actions">
                <button class="ghost-btn" @click="setPreviewScale(0.55)">适配</button>
                <button class="ghost-btn" @click="router.push(`/${selectedPageKey}`)">打开页面</button>
              </div>
            </header>
            <header class="preview-toolbar">
              <button class="mini-btn" @click="nudgePreviewScale(-0.05)"><Minus :size="14" /></button>
              <input
                :value="previewScale"
                type="range"
                min="0.3"
                max="1.2"
                step="0.05"
                @input="setPreviewScale(Number(($event.target as HTMLInputElement).value))"
              />
              <button class="mini-btn" @click="nudgePreviewScale(0.05)"><Plus :size="14" /></button>
              <button class="ghost-btn" @click="setPreviewScale(1)"><Maximize2 :size="16" />{{ previewPercent }}</button>
            </header>
            <div class="preview-canvas">
              <div class="preview-stage" :style="previewStageStyle">
                <DynamicPage v-if="previewPageConfig" :page-config="previewPageConfig" @open-item="() => undefined" />
              </div>
            </div>
          </aside>
        </section>

        <div v-if="activePanel" class="modal-backdrop" @click.self="closePanel">
          <section class="modal-panel">
            <header>
              <strong>{{ activePanelTitle }}</strong>
              <button class="icon-btn" @click="closePanel"><X :size="16" /></button>
            </header>

            <form v-if="activePanel === 'page'" class="form-card" @submit.prevent="createPage">
              <label>页面Key<input v-model="pageForm.pageKey" /></label>
              <label>导航名称<input v-model="pageForm.label" /></label>
              <label>页面标题<input v-model="pageForm.title" /></label>
              <label>副标题<input v-model="pageForm.subtitle" /></label>
              <label>图标<input v-model="pageForm.icon" /></label>
              <label>排序<input v-model.number="pageForm.sortOrder" type="number" /></label>
              <button class="primary-btn">创建页面</button>
            </form>

            <form v-else-if="activePanel === 'section'" class="form-card" @submit.prevent="createSection">
              <label>模块Key<input v-model="sectionForm.sectionKey" /></label>
              <label>模块标题<input v-model="sectionForm.title" /></label>
              <label>副标题<input v-model="sectionForm.subtitle" /></label>
              <label>
                模板类型
                <select v-model="sectionForm.layout">
                  <option value="stat-strip">stat-strip</option>
                  <option value="tool-grid">tool-grid</option>
                  <option value="learning-grid">learning-grid</option>
                  <option value="order-grid">order-grid</option>
                  <option value="banner-row">banner-row</option>
                  <option value="template-list">template-list</option>
                  <option value="ranking-list">ranking-list</option>
                </select>
              </label>
              <label>排序<input v-model.number="sectionForm.sortOrder" type="number" /></label>
              <button class="primary-btn">创建模块</button>
            </form>

            <form v-else class="form-card" @submit.prevent="createItem">
              <label>
                所属模块
                <select v-model="itemForm.sectionId">
                  <option v-for="section in selectedSections" :key="section.id" :value="section.id">{{ section.title }}</option>
                </select>
              </label>
              <label>卡片标题<input v-model="itemForm.title" /></label>
              <label>说明<input v-model="itemForm.subtitle" /></label>
              <label>类型<input v-model="itemForm.itemType" /></label>
              <label>分类<input v-model="itemForm.category" /></label>
              <label>图标<input v-model="itemForm.icon" /></label>
              <label>图片URL<input v-model="itemForm.imageUrl" /></label>
              <label>标签<input v-model="itemForm.tagsText" /></label>
              <label>跳转值<input v-model="itemForm.actionValue" /></label>
              <label>积分<input v-model.number="itemForm.pointCost" type="number" /></label>
              <label class="check-label"><input v-model="itemForm.requiredMembership" type="checkbox" />会员可用</label>
              <label class="upload-line"><ImagePlus :size="18" />上传图片<input type="file" accept="image/*" @change="uploadImage" /></label>
              <button class="primary-btn">创建卡片</button>
            </form>
          </section>
        </div>
      </template>
    </main>
  </div>
</template>

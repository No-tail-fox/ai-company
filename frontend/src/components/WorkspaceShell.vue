<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { CircleUserRound } from 'lucide-vue-next';
import { getIcon } from '../services/icons';

interface WorkspaceModule {
  key: string;
  label: string;
  route: string;
  icon: string;
}

const props = withDefaults(
  defineProps<{
    activeModuleKey: string;
    pageTitle: string;
    pageSubtitle?: string;
    pageIcon?: string;
    variant?: string;
    modules?: WorkspaceModule[];
  }>(),
  {
    pageSubtitle: '',
    pageIcon: 'Sparkles',
    variant: 'chat',
    modules: () => [
      { key: 'chat', label: '对话', route: '/workbench', icon: 'MessageCircle' },
      { key: 'image', label: '图像生成', route: '/workbench/image', icon: 'Image' },
      { key: 'video', label: '视频生成', route: '/workbench/video', icon: 'FileVideo' },
      { key: 'audio', label: '音频生成', route: '/workbench/audio', icon: 'Headphones' }
    ]
  }
);

const router = useRouter();
const pageIcon = computed(() => getIcon(props.pageIcon));

function navigateModule(item: WorkspaceModule) {
  if (item.route) {
    void router.push(item.route);
  }
}

function openAdmin() {
  void router.push('/admin');
}
</script>

<template>
  <section :class="['workspace-shell', 'workspace-shared-shell', `workspace-${variant}`]">
    <aside class="workspace-rail">
      <nav class="workspace-rail-nav" aria-label="工作台模块">
        <button
          v-for="item in modules"
          :key="item.key"
          :class="['workspace-rail-button', { active: item.key === activeModuleKey }]"
          @click="navigateModule(item)"
        >
          <component :is="getIcon(item.icon)" :size="26" />
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div v-if="$slots.leftFooter" class="workspace-rail-footer">
        <slot name="leftFooter" />
      </div>
    </aside>

    <div class="workspace-content">
      <header class="workspace-head">
        <div class="workspace-title">
          <span class="workspace-title-icon">
            <component :is="pageIcon" :size="24" />
          </span>
          <div>
            <h1>{{ pageTitle }}</h1>
            <p v-if="pageSubtitle">{{ pageSubtitle }}</p>
          </div>
        </div>

        <div class="workspace-head-actions">
          <slot name="headerActions" />
          <button class="workspace-icon-button" aria-label="管理端" title="管理端" @click="openAdmin">
            <CircleUserRound :size="21" />
          </button>
        </div>
      </header>

      <div class="workspace-inner">
        <main class="workspace-main">
          <slot name="main" />
        </main>
        <aside class="workspace-side">
          <slot name="side" />
        </aside>
      </div>
    </div>
  </section>
</template>

<style scoped>
.workspace-shell {
  --workspace-accent: #5f62f5;
  --workspace-accent-soft: #f0f2ff;
  height: calc(100vh - var(--portal-chrome-height, 0px));
  min-height: calc(720px - var(--portal-chrome-height, 0px));
  display: grid;
  grid-template-columns: 236px minmax(0, 1fr);
  overflow: hidden;
  color: #111827;
  background:
    radial-gradient(circle at 28% 6%, rgba(96, 112, 255, 0.07), transparent 30%),
    linear-gradient(180deg, #fbfdff 0%, #f7f9fd 100%);
}

.workspace-image {
  --workspace-accent: #5264ff;
  --workspace-accent-soft: #f1f3ff;
}

.workspace-video {
  --workspace-accent: #5f63f1;
  --workspace-accent-soft: #f0f1ff;
}

.workspace-audio {
  --workspace-accent: #4f6df6;
  --workspace-accent-soft: #eef3ff;
}

.workspace-rail {
  min-width: 0;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 20px;
  padding: 30px 18px 24px;
  border-right: 1px solid #e4e9f1;
  background: rgba(255, 255, 255, 0.84);
}

.workspace-rail-nav {
  display: grid;
  align-content: start;
  gap: 14px;
}

.workspace-rail-button {
  min-height: 58px;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 0;
  border-radius: 8px;
  padding: 0 16px;
  color: #202636;
  background: transparent;
  font-size: 16px;
  font-weight: 800;
  text-align: left;
}

.workspace-rail-button svg {
  flex: 0 0 auto;
}

.workspace-rail-button.active {
  color: var(--workspace-accent);
  background: var(--workspace-accent-soft);
  box-shadow: 0 12px 30px rgba(79, 91, 229, 0.1);
}

.workspace-rail-footer {
  display: grid;
  gap: 12px;
}

.workspace-content {
  min-width: 0;
  min-height: 0;
  display: grid;
  grid-template-rows: 88px minmax(0, 1fr);
}

.workspace-head {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding: 0 28px;
  border-bottom: 1px solid #e4e9f1;
  background: rgba(255, 255, 255, 0.82);
}

.workspace-title {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 14px;
}

.workspace-title-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: var(--workspace-accent);
  background: var(--workspace-accent-soft);
}

.workspace-title h1 {
  margin: 0;
  font-size: 26px;
  line-height: 1.2;
  letter-spacing: 0;
}

.workspace-title p {
  margin: 5px 0 0;
  color: #6b7280;
  font-size: 14px;
}

.workspace-head-actions {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.workspace-icon-button,
.workspace-head-actions :deep(.workspace-icon-action) {
  width: 40px;
  height: 40px;
  display: inline-grid;
  place-items: center;
  border: 1px solid #dfe5ef;
  border-radius: 8px;
  color: #4b5563;
  background: #fff;
}

.workspace-icon-button:hover,
.workspace-head-actions :deep(.workspace-icon-action:hover) {
  border-color: #c9d0ff;
  color: var(--workspace-accent);
}

.workspace-inner {
  min-width: 0;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 344px;
  gap: 20px;
  padding: 20px 20px 20px 18px;
  overflow: hidden;
}

.workspace-main,
.workspace-side {
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.workspace-side {
  display: grid;
  align-content: start;
  gap: 16px;
  padding-right: 4px;
}

@media (max-width: 1320px) {
  .workspace-shell {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .workspace-inner {
    grid-template-columns: minmax(0, 1fr) 320px;
    gap: 16px;
    padding-inline: 16px;
  }
}
</style>

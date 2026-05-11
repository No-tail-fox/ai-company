<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { RouterView, useRoute } from 'vue-router';
import PortalChrome from './components/PortalChrome.vue';
import { fetchPortalConfig } from './services/api';
import { createFallbackPortalConfig, type PortalConfig } from './services/viewModel';

const route = useRoute();
const portal = ref<PortalConfig>(createFallbackPortalConfig());
const frontendChromeEnabled = computed(() => !route.path.startsWith('/admin'));
const chromePageKeys = computed(() => new Set(portal.value.channels.map((channel) => channel.key)));
const activeChromePageKey = computed(() => {
  if (!frontendChromeEnabled.value) {
    return '';
  }
  if (route.path.startsWith('/workbench') || route.path.startsWith('/workspace')) {
    return 'workbench';
  }
  const pageKey = route.params.pageKey;
  if (typeof pageKey === 'string' && pageKey) {
    return pageKey;
  }
  const firstSegment = route.path.split('/').filter(Boolean)[0] || 'home';
  return firstSegment;
});

onMounted(async () => {
  portal.value = await fetchPortalConfig();
});
</script>

<template>
  <RouterView v-if="!frontendChromeEnabled" />
  <PortalChrome v-else :channels="portal.channels" :active-page-key="activeChromePageKey">
    <RouterView />
  </PortalChrome>
</template>

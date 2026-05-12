/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import app from '../src/App.vue?raw';
import portalView from '../src/views/PortalView.vue?raw';
import routerSource from '../src/router.ts?raw';
import audioPage from '../src/components/AudioPage.vue?raw';
import dynamicPage from '../src/components/DynamicPage.vue?raw';
import imagePage from '../src/components/ImagePage.vue?raw';
import videoPage from '../src/components/VideoPage.vue?raw';
import workbenchPage from '../src/components/WorkbenchPage.vue?raw';
import workspaceShell from '../src/components/WorkspaceShell.vue?raw';
import portalDetailPage from '../src/components/PortalDetailPage.vue?raw';

test('router isolates workbench pages from portal catalog routes', () => {
  expect(routerSource).toContain("path: '/workbench'");
  expect(routerSource).toContain("path: '/workbench/image'");
  expect(routerSource).toContain("path: '/workbench/video'");
  expect(routerSource).toContain("path: '/workbench/audio'");
  expect(routerSource).toContain('PortalDetailPage');
  expect(routerSource).toContain("path: '/:detailPath(.*)*'");
  expect(routerSource).toContain("path: '/:pageKey'");
  expect(app).toContain('PortalChrome');
  expect(app).toContain("route.path.startsWith('/workbench')");
  expect(app).toContain("route.path.startsWith('/workspace')");
  expect(portalView).not.toContain('PortalChrome');
  expect(portalView).toContain('DynamicPage');
  expect(portalView).toContain('workbenchRoute');
  expect(portalView).toContain('workbenchDockLabel');
  expect(portalView).not.toContain("import WorkbenchPage");
  expect(portalView).not.toContain("import ImagePage");
  expect(portalView).not.toContain("import VideoPage");
  expect(portalView).not.toContain("import AudioPage");
});

test('portal details and homepage routes use real routed actions', () => {
  expect(portalDetailPage).toContain('fetchPortalDetail');
  expect(portalDetailPage).toContain('runPortalAction');
  expect(portalDetailPage).toContain('completedActions');
  expect(portalDetailPage).toContain('renderMarkdown');
  expect(portalDetailPage).toContain('activeDetailTab');
  expect(portalDetailPage).toContain('updatePortalDetail');
  expect(portalDetailPage).toContain('publishPortalDetail');
  expect(portalDetailPage).toContain('createPortalDetailComment');
  expect(portalDetailPage).toContain('detail.permissions.canEdit');
  expect(portalDetailPage).toContain("router.push('/communication')");
  expect(dynamicPage).toContain('router.push(item.actionValue)');
  expect(dynamicPage).toContain('openSidePromo');
});

test('workbench page uses the shared shell and real chat behaviors', () => {
  expect(workbenchPage).toContain('<WorkspaceShell');
  expect(workbenchPage).not.toContain('PortalChrome');
  expect(workbenchPage).not.toContain(':enabled="(props.channels?.length ?? 0) > 0');
  expect(workspaceShell).toContain('workspace-rail');
  expect(workspaceShell).toContain("route: '/workbench/image'");
  expect(workspaceShell).toContain("route: '/workbench/video'");
  expect(workspaceShell).toContain("route: '/workbench/audio'");
  expect(workbenchPage).toContain('fetchChatWorkbench');
  expect(workbenchPage).toContain('sendChatMessage');
  expect(workbenchPage).toContain('exportChatSession');
  expect(workbenchPage).toContain('groupChatSessionsByRecency');
  expect(workbenchPage).toContain('workbench-file-card');
});

test('chat workbench does not render local demo fallback controls', () => {
  expect(workbenchPage).not.toContain('createFallbackChatWorkbench');
  expect(workbenchPage).not.toContain('fallbackWorkbench');
  expect(workbenchPage).not.toContain("id: 'image-link'");
  expect(workbenchPage).not.toContain('openFilePicker');
});

test('shared workbench shell supports a collapsed rail and single content scroll', () => {
  expect(workspaceShell).toContain('WORKSPACE_RAIL_COLLAPSED_KEY');
  expect(workspaceShell).toContain('railCollapsed');
  expect(workspaceShell).toContain('workspace-rail-toggle');
  expect(workspaceShell).toContain('.workspace-shell.collapsed');
  expect(workspaceShell).toContain('grid-template-columns: 64px minmax(0, 1fr)');
  expect(workspaceShell).toContain('overflow-y: auto');
  expect(workspaceShell).not.toContain('.workspace-main,\n.workspace-side {\n  min-width: 0;\n  min-height: 0;\n  overflow-y: auto;');
  expect(workbenchPage).not.toContain('workbench-side-panel');
  expect(workbenchPage).not.toContain('workbench-thread {\n  min-height: 0;\n  padding: 24px 28px;\n  overflow-y: auto;');
});

test('creative workbench child pages use workbench surface and local drafts', () => {
  for (const source of [imagePage, videoPage, audioPage]) {
    expect(source).toContain('<WorkspaceShell');
    expect(source).not.toContain('PortalChrome');
    expect(source).toContain("const SURFACE = 'workbench'");
    expect(source).toContain('loadWorkbenchDraft');
    expect(source).toContain('saveWorkbenchDraft');
  }
  expect(imagePage).toContain('fetchImageWorkbench(SURFACE)');
  expect(imagePage).toContain('fetchWorkbenchCapabilities(SURFACE)');
  expect(imagePage).toContain('selectedCapability');
  expect(imagePage).toContain('options: imageGenerationOptions()');
  expect(imagePage).toContain('surface: SURFACE');
  expect(videoPage).toContain('fetchVideoWorkbench(SURFACE)');
  expect(videoPage).toContain('fetchWorkbenchCapabilities(SURFACE)');
  expect(videoPage).toContain('selectedCapability');
  expect(videoPage).toContain('options: videoGenerationOptions()');
  expect(videoPage).toContain('surface: SURFACE');
  expect(audioPage).toContain('fetchAudioTasks(SURFACE)');
  expect(audioPage).toContain('fetchWorkbenchCapabilities(SURFACE)');
  expect(audioPage).toContain('managedAudioTools');
  expect(audioPage).toContain('buildAudioTaskPayload');
});

test('creative workbench pages poll real generation tasks and render provider media', () => {
  for (const source of [imagePage, videoPage, audioPage]) {
    expect(source).toContain('startTaskPolling');
    expect(source).toContain('hasActiveTasks');
    expect(source).toContain('onBeforeUnmount');
    expect(source).not.toContain('queueRows.length > 0\n    ? queueRows\n    : [');
  }
  expect(imagePage).toContain("<img :src=\"card.url || ''\"");
  expect(videoPage).toContain('class="video-result-player"');
  expect(audioPage).toContain('<audio v-if="latestAudioResult"');
  expect(audioPage).toContain('task.errorMessage');
});

test('creative workbench pages do not expose local fallback demos or fake editors', () => {
  expect(imagePage).not.toContain('createFallbackImageWorkbench');
  expect(videoPage).not.toContain('createFallbackVideoWorkbench');
  expect(imagePage).not.toContain('image-demo-');
  expect(videoPage).not.toContain('video-demo-');
  expect(imagePage).not.toContain('wb-reference-panel');
  expect(videoPage).not.toContain('const scenes: SceneItem[]');
  expect(videoPage).not.toContain('video-preview-scene walk');
  expect(videoPage).not.toContain('video-timeline-panel');
  expect(audioPage).not.toContain('const transcriptRows');
  expect(audioPage).not.toContain('audio-wave-editor');
});

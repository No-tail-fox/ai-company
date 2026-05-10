/// <reference types="vite/client" />

import { expect, test } from 'vitest';
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
  expect(portalView).toContain('PortalChrome');
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

test('creative workbench child pages use workbench surface and local drafts', () => {
  for (const source of [imagePage, videoPage, audioPage]) {
    expect(source).toContain('<WorkspaceShell');
    expect(source).not.toContain('PortalChrome');
    expect(source).toContain("const SURFACE = 'workbench'");
    expect(source).toContain('loadWorkbenchDraft');
    expect(source).toContain('saveWorkbenchDraft');
  }
  expect(imagePage).toContain('fetchImageWorkbench(SURFACE)');
  expect(imagePage).toContain('surface: SURFACE');
  expect(videoPage).toContain('fetchVideoWorkbench(SURFACE)');
  expect(videoPage).toContain('surface: SURFACE');
  expect(audioPage).toContain('fetchAudioTasks(SURFACE)');
  expect(audioPage).toContain('buildAudioTaskPayload');
});

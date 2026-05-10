/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import audioPage from '../src/components/AudioPage.vue?raw';
import imagePage from '../src/components/ImagePage.vue?raw';
import dynamicPage from '../src/components/DynamicPage.vue?raw';
import portalChrome from '../src/components/PortalChrome.vue?raw';
import portalView from '../src/views/PortalView.vue?raw';
import videoPage from '../src/components/VideoPage.vue?raw';
import workspaceShell from '../src/components/WorkspaceShell.vue?raw';

test('portal chrome keeps the brand header and top tabs while removing browser chrome', () => {
  expect(portalChrome).toContain('brand-row');
  expect(portalChrome).toContain('top-tabs');
  expect(portalChrome).toContain('vip-strip');
  expect(portalChrome).toContain('defaultChannels');
  expect(portalChrome).toContain('visibleChannels');
  expect(portalChrome).toContain('searchPortal');
  expect(portalChrome).toContain('membership-panel');
  expect(portalChrome).toContain('search-results-panel');
  expect(portalChrome).not.toContain('window-bar');
  expect(portalView).toContain('PortalChrome');
  expect(portalView).toContain('DynamicPage');
  expect(portalView).not.toContain('ImagePage');
  expect(portalView).not.toContain('VideoPage');
  expect(portalView).not.toContain('AudioPage');
  expect(imagePage).toContain('WorkspaceShell');
  expect(videoPage).toContain('WorkspaceShell');
  expect(audioPage).toContain('WorkspaceShell');
});

test('home chrome exposes backup and floating tool actions', () => {
  expect(portalView).toContain('runPortalAction');
  expect(portalView).toContain('fetchPortalUserActions');
  expect(portalView).toContain('openFloatPanel');
  expect(portalView).toContain('scrollToTop');
  expect(portalView).toContain('backupEnabled');
});

test('home page exposes a direct workbench entry and the shared shell exists', () => {
  expect(dynamicPage).toContain('home-workbench-btn');
  expect(dynamicPage).toContain('/workbench');
  expect(dynamicPage).toContain('/workbench/image');
  expect(dynamicPage).toContain('/workbench/video');
  expect(dynamicPage).toContain('/workbench/audio');
  expect(dynamicPage).toContain("label: '工作台'");
  expect(portalView).toContain("image: '工作台'");
  expect(portalView).toContain("video: '工作台'");
  expect(portalView).toContain("audio: '工作台'");
  expect(portalView).toContain("title: '图像生成工作台'");
  expect(portalView).toContain("title: '视频生成工作台'");
  expect(portalView).toContain("title: '音频生成工作台'");
  expect(workspaceShell).toContain('workspace-shared-shell');
});

/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import audioPage from '../src/components/AudioPage.vue?raw';
import adminView from '../src/views/AdminView.vue?raw';
import app from '../src/App.vue?raw';
import imagePage from '../src/components/ImagePage.vue?raw';
import dynamicPage from '../src/components/DynamicPage.vue?raw';
import indexHtml from '../index.html?raw';
import portalChrome from '../src/components/PortalChrome.vue?raw';
import portalView from '../src/views/PortalView.vue?raw';
import videoPage from '../src/components/VideoPage.vue?raw';
import viewModel from '../src/services/viewModel.ts?raw';
import workspaceShell from '../src/components/WorkspaceShell.vue?raw';

test('portal chrome keeps the brand header and top tabs while removing browser chrome', () => {
  expect(portalChrome).toContain('brand-row');
  expect(portalChrome).toContain('top-tabs');
  expect(portalChrome).toContain('vip-strip');
  expect(portalChrome).toContain('defaultChannels');
  expect(portalChrome).toContain('visibleChannels');
  expect(portalChrome).toContain("label: '常用'");
  expect(portalChrome).toContain('searchPortal');
  expect(portalChrome).toContain('membership-panel');
  expect(portalChrome).toContain('search-results-panel');
  expect(portalChrome).toContain('account-chip');
  expect(portalChrome).toContain('account-menu');
  expect(portalChrome).toContain('account-settings-panel');
  expect(portalChrome).toContain('recharge-panel');
  expect(portalChrome).toContain('account-summary');
  expect(portalChrome).toContain('handleScrollKeys');
  expect(portalChrome).toContain('chromeBodyRef');
  expect(portalChrome).toContain('tabindex="0"');
  expect(portalChrome).not.toContain('window-bar');
  expect(app).toContain('PortalChrome');
  expect(app).toContain('fetchPortalConfig');
  expect(app).toContain('activeChromePageKey');
  expect(app).toContain("route.path.startsWith('/workbench')");
  expect(portalView).not.toContain('PortalChrome');
  expect(portalView).toContain('HomeDashboardPage');
  expect(portalView).toContain('DynamicPage');
  expect(portalView).toContain('fetchHomeDashboard');
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
  expect(portalView).toContain('hideWorkspaceDock');
});

test('brand copy is synchronized to 新商机', () => {
  const brandSources = [portalChrome, portalView, adminView, viewModel, indexHtml].join('\n');

  expect(portalChrome).toContain('<span class="logo-red">新商机</span>');
  expect(portalChrome).toContain('<span class="logo-gold">OPC社区</span>');
  expect(indexHtml).toContain('<title>新商机</title>');
  expect(portalView).toContain('<strong>新商机 客服</strong>');
  expect(adminView).toContain('<h1>新商机管理后台</h1>');
  expect(viewModel).toContain("'新商机 接单中心'");
  expect(brandSources).not.toMatch(/新商盟|新商机 AI 社区/);
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

test('professional toolkit page has a dedicated third-party tools display area', () => {
  expect(dynamicPage).toContain("section.layout === 'third-party-tools'");
  expect(dynamicPage).toContain('third-party-tools-panel');
  expect(dynamicPage).toContain('thirdPartySearch');
  expect(dynamicPage).toContain('thirdPartyCategories');
  expect(dynamicPage).toContain('thirdPartyDownloadUrl');
  expect(dynamicPage).toContain('添加工具');
  expect(dynamicPage).toContain('下载客户端');
});

test('admin item form exposes external link cards for third-party tools', () => {
  expect(adminView).toContain('third-party-tools');
  expect(adminView).toContain('external_link');
  expect(adminView).toContain('动作类型');
  expect(adminView).toContain('下载URL');
});

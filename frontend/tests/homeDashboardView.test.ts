/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import apiSource from '../src/services/api.ts?raw';
import homeDashboardPage from '../src/components/HomeDashboardPage.vue?raw';
import adminView from '../src/views/AdminView.vue?raw';
import portalView from '../src/views/PortalView.vue?raw';

test('home dashboard component renders the reference-style first screen and prioritized follow-up blocks', () => {
  const heroStart = homeDashboardPage.indexOf('<section class="home-first-screen home-hero-stage">');
  const promoCard = homeDashboardPage.indexOf('<article class="home-promo-carousel home-promo-card">');
  const workbenchPanel = homeDashboardPage.indexOf('<section class="home-workbench-panel">');
  const kpiStrip = homeDashboardPage.indexOf('<section class="home-kpi-strip">');
  const priorityRow = homeDashboardPage.indexOf('<section class="home-priority-row">');
  const communityPanel = homeDashboardPage.indexOf('<section class="home-community-panel featured-community-panel">');
  const toolPanel = homeDashboardPage.indexOf('<section class="home-tool-panel hot-tools-panel">');
  const learningPanel = homeDashboardPage.indexOf('<section class="home-learning-panel home-learning-stage">');
  const orderPanel = homeDashboardPage.indexOf('<section class="home-order-panel">');

  expect(heroStart).toBeGreaterThan(-1);
  expect(promoCard).toBeGreaterThan(heroStart);
  expect(workbenchPanel).toBeGreaterThan(promoCard);
  expect(kpiStrip).toBeGreaterThan(workbenchPanel);
  expect(priorityRow).toBeGreaterThan(kpiStrip);
  expect(communityPanel).toBeGreaterThan(priorityRow);
  expect(toolPanel).toBeGreaterThan(communityPanel);
  expect(learningPanel).toBeGreaterThan(toolPanel);
  expect(orderPanel).toBeGreaterThan(learningPanel);

  expect(homeDashboardPage).toContain('learning-stage-grid');
  expect(homeDashboardPage).toContain('vip-visual-card');
  expect(homeDashboardPage).toContain('vip-benefit-row');
  expect(homeDashboardPage).toContain('vip-countdown-row');
  expect(homeDashboardPage).toContain('workbench-app-icon');
  expect(homeDashboardPage).toContain('community-banner-row');
  expect(homeDashboardPage).toContain('hot-tools-panel');
  expect(homeDashboardPage).toContain("homePanelTitle(communitySection.value?.title, '精选社群', ['兴趣社群'])");
  expect(homeDashboardPage).toContain("homePanelTitle(toolSection.value?.title, '热门工具', ['专业工具包'])");
  expect(homeDashboardPage).toContain('home-lower-stack');
  expect(homeDashboardPage).toContain('router.push');
  expect(homeDashboardPage).toContain('常用AI学习中心');
  expect(homeDashboardPage).toContain('/membership/benefits');
  expect(homeDashboardPage).toContain('会员活动');
  expect(homeDashboardPage).not.toContain('window-tab');
});

test('portal view switches home to the dedicated dashboard and hides the legacy dock', () => {
  expect(portalView).toContain('HomeDashboardPage');
  expect(portalView).toContain('fetchHomeDashboard');
  expect(portalView).toContain('homeDashboard');
  expect(portalView).toContain('buildHomeDashboardModel(pageConfig.value, homeDashboard.value)');
  expect(portalView).toContain('shouldUseHomeDashboardPage(activePageKey.value, activeHomeMenuKey.value)');
  expect(portalView).toContain("activeHomeMenuKey.value = 'basic'");
  expect(portalView).toContain("hideWorkspaceDock = computed(() =>");
  expect(portalView).toContain('showHomeDashboard');
});

test('admin content preview reuses the home dashboard component for home pages', () => {
  expect(adminView).toContain('HomeDashboardPage');
  expect(adminView).toContain('previewUsesHomeDashboardPage');
  expect(adminView).toContain('previewHomeDashboardModel');
  expect(adminView).toContain('buildHomeDashboardModel(previewPageConfig.value');
  expect(adminView).toContain('v-if="previewPageConfig && previewUsesHomeDashboardPage"');
  expect(adminView).toContain(':model="previewHomeDashboardModel"');
});

test('admin page content is normalized before the preview renders it', () => {
  expect(apiSource).toContain('return normalizePageConfig(await request(`/api/v1/admin/page-content/${encodeURIComponent(pageKey)}`');
});

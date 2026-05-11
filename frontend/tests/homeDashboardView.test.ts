/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import homeDashboardPage from '../src/components/HomeDashboardPage.vue?raw';
import portalView from '../src/views/PortalView.vue?raw';

test('home dashboard component renders the reference-style first screen and follow-up blocks', () => {
  const heroStart = homeDashboardPage.indexOf('<section class="home-first-screen home-hero-stage">');
  const promoCard = homeDashboardPage.indexOf('<article class="home-promo-carousel home-promo-card">');
  const workbenchPanel = homeDashboardPage.indexOf('<section class="home-workbench-panel">');
  const kpiStrip = homeDashboardPage.indexOf('<section class="home-kpi-strip">');
  const learningPanel = homeDashboardPage.indexOf('<section class="home-learning-panel home-learning-stage">');
  const orderPanel = homeDashboardPage.indexOf('<section class="home-order-panel">');

  expect(heroStart).toBeGreaterThan(-1);
  expect(promoCard).toBeGreaterThan(heroStart);
  expect(workbenchPanel).toBeGreaterThan(promoCard);
  expect(kpiStrip).toBeGreaterThan(workbenchPanel);
  expect(learningPanel).toBeGreaterThan(kpiStrip);
  expect(orderPanel).toBeGreaterThan(learningPanel);

  expect(homeDashboardPage).toContain('learning-stage-grid');
  expect(homeDashboardPage).toContain('promo-sheet-stack');
  expect(homeDashboardPage).toContain('community-banner-row');
  expect(homeDashboardPage).toContain('home-dual-row');
  expect(homeDashboardPage).toContain('home-tool-panel');
  expect(homeDashboardPage).toContain('home-lower-stack');
  expect(homeDashboardPage).toContain('router.push');
  expect(homeDashboardPage).toContain('常用AI学习中心');
  expect(homeDashboardPage).toContain('/membership/benefits');
  expect(homeDashboardPage).toContain('会员活动');
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

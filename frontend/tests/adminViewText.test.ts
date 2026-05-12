/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import adminView from '../src/views/AdminView.vue?raw';

test('admin view exposes a standard SaaS management shell', () => {
  expect(adminView).toContain('新商机管理后台');
  expect(adminView).toContain('模型中心');
  expect(adminView).toContain('内容管理');
  expect(adminView).toContain('审计日志');
});

test('admin model center exposes the new supplier configuration surface', () => {
  expect(adminView).toContain('adminListWorkbenchCapabilities');
  expect(adminView).toContain('adminUpdateWorkbenchCapability');
  expect(adminView).toContain('工作台能力筛选');
  expect(adminView).toContain('workbench-capability');
  expect(adminView).toContain('provider-preset-row');
  expect(adminView).toContain('provider-preset-chip');
  expect(adminView).toContain('OpenAI Official');
  expect(adminView).toContain('auth.json');
  expect(adminView).toContain('config.toml');
  expect(adminView).toContain('providerChannelForm.testConfigText');
  expect(adminView).toContain('providerChannelForm.billingConfigText');
  expect(adminView).toContain('modelConfigForm.testConfigText');
  expect(adminView).toContain('modelConfigForm.billingConfigText');
  expect(adminView).toContain('modelConfigForm.useMillionContextWindow');
  expect(adminView).toContain('modelConfigForm.compressionThreshold');
});

test('admin view exposes configurable home carousel management', () => {
  expect(adminView).toContain('adminListHomeSlides');
  expect(adminView).toContain('adminCreateHomeSlide');
  expect(adminView).toContain('home-slide');
  expect(adminView).toContain('promo-carousel');
});

test('admin item editor exposes the current drawer form and detail fields', () => {
  expect(adminView).toContain('modal-backdrop');
  expect(adminView).toContain('form-card');
  expect(adminView).toContain('卡片类型');
  expect(adminView).toContain('动作类型');
  expect(adminView).toContain('详情摘要');
  expect(adminView).toContain('详情配置');
});

test('admin add dialogs share a centered modal shell', () => {
  expect(adminView).toContain('modal-backdrop-center');
  expect(adminView).toContain('admin-modal-shell');
  expect(adminView).toContain('admin-card-modal');
  expect(adminView).not.toContain('admin-drawer');
});

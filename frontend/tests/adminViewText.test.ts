/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import adminView from '../src/views/AdminView.vue?raw';

test('admin view exposes a standard SaaS management shell', () => {
  expect(adminView).toContain('管理后台');
  expect(adminView).toContain('总览');
  expect(adminView).toContain('人员管理');
  expect(adminView).toContain('会员管理');
  expect(adminView).toContain('积分管理');
  expect(adminView).toContain('内容管理');
  expect(adminView).toContain('模型中心');
  expect(adminView).toContain('审计日志');
  expect(adminView).toContain('内容预览');
  expect(adminView).toContain('新增人员');
  expect(adminView).toContain('新增会员');
  expect(adminView).toContain('积分调整');
  expect(adminView).toContain('新增页面');
  expect(adminView).toContain('新增模型');
});

test('admin model center exposes managed workbench capability controls', () => {
  expect(adminView).toContain('adminListWorkbenchCapabilities');
  expect(adminView).toContain('adminUpdateWorkbenchCapability');
  expect(adminView).toContain('工作台能力筛选');
  expect(adminView).toContain('workbench-capability');
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
});

test('admin add dialogs share a centered modal shell', () => {
  expect(adminView).toContain('modal-backdrop-center');
  expect(adminView).toContain('admin-modal-shell');
  expect(adminView).toContain('admin-card-modal');
  expect(adminView).not.toContain('admin-drawer');
});

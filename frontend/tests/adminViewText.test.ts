/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import adminView from '../src/views/AdminView.vue?raw';

const mojibakeFragments = [
  '\u6e1a\u6d98\u7c32',
  '\u93c2\u677f',
  '\u93c8\ue047',
  '\u93c6\u509b',
  '\u59af\u2033',
  '\u7ec9\ue21a'
];

test('admin model center uses readable Chinese labels', () => {
  expect(adminView).toContain('供应商渠道');
  expect(adminView).toContain('新增渠道');
  expect(adminView).toContain('未设置密钥');
  expect(adminView).toContain('暂无模型配置');
  expect(adminView).toContain('工具绑定列表');
  for (const fragment of mojibakeFragments) {
    expect(adminView).not.toContain(fragment);
  }
});

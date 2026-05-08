import { expect, test } from 'vitest';
import {
  buildAssistantRanking,
  createHomeMenuPageConfig,
  createFallbackPortalConfig,
  createFallbackPageConfig,
  formatUsageCount,
  normalizePageConfig,
  normalizePortalConfig,
  shouldShowHomeSidebar
} from '../src/services/viewModel';

test('formats usage count with Chinese ten-thousand units', () => {
  expect(formatUsageCount(234500)).toBe('23.4万次使用');
  expect(formatUsageCount(9300)).toBe('9300次使用');
});

test('fallback portal config contains learning, orders and community sections', () => {
  const config = createFallbackPortalConfig();

  expect(config.pages.map((page) => page.pageKey)).toEqual([
    'home',
    'assistant',
    'marketing',
    'video',
    'audio',
    'coding',
    'writing',
    'ecommerce',
    'legal',
    'office'
  ]);
  expect(config.homeSections.map((section) => section.sectionKey)).toEqual(
    expect.arrayContaining(['learning_center', 'order_center', 'communities', 'banners', 'quick_start', 'toolkit'])
  );
  expect(config.leftNav[0].label).toBe('基础必备');
  expect(config.homeSections[0].items.length).toBeGreaterThan(2);
});

test('normalizes portal config pages and page sections from snake case API payloads', () => {
  const config = normalizePortalConfig({
    tenant_id: 'demo',
    pages: [
      {
        id: 'page-marketing',
        page_key: 'marketing',
        label: 'AI 营销',
        title: '营销增长中心',
        subtitle: '增长工具',
        icon: 'Megaphone',
        sort_order: 30,
        enabled: true
      }
    ],
    channels: [{ key: 'marketing', label: 'AI 营销' }],
    left_nav: [{ key: 'basic', label: '基础必备', icon: 'Flame' }],
    home_sections: []
  });

  expect(config.pages[0]).toMatchObject({
    pageKey: 'marketing',
    label: 'AI 营销',
    title: '营销增长中心',
    enabled: true
  });
  expect(config.channels[0].key).toBe('marketing');
});

test('shows the left sidebar only on the home page', () => {
  expect(shouldShowHomeSidebar('home')).toBe(true);
  expect(shouldShowHomeSidebar('assistant')).toBe(false);
  expect(shouldShowHomeSidebar('marketing')).toBe(false);
});

test('builds distinct home content for different left menu items', () => {
  const homePage = createFallbackPageConfig('home');

  const basic = createHomeMenuPageConfig(homePage, 'basic');
  const orders = createHomeMenuPageConfig(homePage, 'orders');
  const toolkit = createHomeMenuPageConfig(homePage, 'toolkit');

  expect(basic.sections.length).toBeGreaterThanOrEqual(2);
  expect(orders.sections.length).toBeGreaterThanOrEqual(2);
  expect(toolkit.sections.length).toBeGreaterThanOrEqual(2);
  expect(basic.sections.map((section) => section.sectionKey)).not.toEqual(
    orders.sections.map((section) => section.sectionKey)
  );
  expect(orders.sections.flatMap((section) => section.items).some((item) => item.category === '接单变现')).toBe(true);
  expect(toolkit.sections.flatMap((section) => section.items).some((item) => item.category === '专业工具包')).toBe(true);
});

test('home menu filtering does not affect non-home pages', () => {
  const marketing = createFallbackPageConfig('marketing');

  expect(createHomeMenuPageConfig(marketing, 'orders')).toBe(marketing);
});

test('normalizes a single page config with modular section layouts', () => {
  const page = normalizePageConfig({
    tenant_id: 'demo',
    page: {
      id: 'page-video',
      page_key: 'video',
      label: 'AI 视频',
      title: 'AI视频创作中心',
      subtitle: '脚本、数字人和剪辑',
      icon: 'FileVideo',
      sort_order: 40,
      enabled: true
    },
    sections: [
      {
        id: 'section-video-tools',
        page_key: 'video',
        section_key: 'tools',
        title: '视频工具矩阵',
        subtitle: '创作工具',
        layout: 'tool-grid',
        sort_order: 20,
        enabled: true,
        items: [
          {
            id: 'video-tool-1',
            section_id: 'section-video-tools',
            item_type: 'tool',
            title: '文案生成视频',
            subtitle: '输入脚本生成分镜',
            category: '工具',
            icon: 'MonitorPlay',
            image_url: '/storage/uploads/demo/video.png',
            badge: '新',
            tags: ['视频'],
            sort_order: 10,
            enabled: true,
            action_type: 'workspace',
            action_value: 'video-tool-1',
            required_membership: true,
            point_cost: 20
          }
        ]
      }
    ]
  });

  expect(page.page.pageKey).toBe('video');
  expect(page.sections[0].layout).toBe('tool-grid');
  expect(page.sections[0].items[0]).toMatchObject({
    itemType: 'tool',
    imageUrl: '/storage/uploads/demo/video.png',
    requiredMembership: true,
    pointCost: 20
  });
});

test('assistant ranking is sorted by usage count and capped at ten items', () => {
  const ranking = buildAssistantRanking([
    { id: 'a', name: 'A', category: '办公助理', description: '', icon: 'Bot', usageCount: 5, pointCost: 0, requiredMembership: false, actionValue: 'a' },
    { id: 'b', name: 'B', category: '办公助理', description: '', icon: 'Bot', usageCount: 20000, pointCost: 0, requiredMembership: false, actionValue: 'b' },
    { id: 'c', name: 'C', category: '办公助理', description: '', icon: 'Bot', usageCount: 10000, pointCost: 0, requiredMembership: false, actionValue: 'c' }
  ]);

  expect(ranking.map((item) => item.name)).toEqual(['B', 'C', 'A']);
  expect(ranking[0].usageCountLabel).toBe('2.0万次使用');
});

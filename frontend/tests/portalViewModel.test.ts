import { expect, test } from 'vitest';
import {
  buildMarketingDashboardModel,
  buildAssistantRanking,
  createFallbackImageWorkbench,
  createFallbackVideoWorkbench,
  createFallbackAssistantCenter,
  createHomeMenuPageConfig,
  createFallbackPortalConfig,
  createFallbackPageConfig,
  filterAssistantCardsByCategory,
  formatUsageCount,
  getVideoStatusMeta,
  getImageStatusMeta,
  normalizeImageWorkbench,
  normalizeVideoWorkbench,
  normalizePageConfig,
  normalizePortalConfig,
  shouldUseAssistantPage,
  shouldUseImagePage,
  shouldUseCodingPage,
  shouldUseMarketingPage,
  shouldUseWritingPage,
  shouldUseVideoPage,
  shouldHideWorkspaceDock,
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
    'image',
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

test('assistant center fallback has enough cards and templates for the square layout', () => {
  const center = createFallbackAssistantCenter();

  expect(center.assistants.length).toBeGreaterThanOrEqual(12);
  expect(center.featured).toHaveLength(4);
  expect(center.promptTemplates.length).toBeGreaterThanOrEqual(5);
  expect(center.categories).toEqual(
    expect.arrayContaining(['全部', '办公助理', '营销助理', '学习助理', '法务助理', '客服助理', '设计助理', '开发助理'])
  );
});

test('filters assistant cards by category while all keeps the full list', () => {
  const center = createFallbackAssistantCenter();

  expect(filterAssistantCardsByCategory(center.assistants, '全部')).toHaveLength(center.assistants.length);
  expect(filterAssistantCardsByCategory(center.assistants, '办公助理').every((item) => item.category === '办公助理')).toBe(true);
});

test('uses the dedicated assistant page only for the assistant route', () => {
  expect(shouldUseAssistantPage('assistant')).toBe(true);
  expect(shouldUseAssistantPage('home')).toBe(false);
  expect(shouldShowHomeSidebar('assistant')).toBe(false);
});

test('uses the dedicated marketing page only for the marketing route', () => {
  expect(shouldUseMarketingPage('marketing')).toBe(true);
  expect(shouldUseMarketingPage('home')).toBe(false);
  expect(shouldUseMarketingPage('assistant')).toBe(false);
  expect(shouldShowHomeSidebar('marketing')).toBe(false);
});

test('fallback marketing page provides dashboard-sized tool, template and ranking content', () => {
  const marketing = createFallbackPageConfig('marketing');
  const dashboard = buildMarketingDashboardModel(marketing);

  expect(marketing.sections.map((section) => section.sectionKey)).toEqual(
    expect.arrayContaining(['overview', 'tools', 'templates', 'ranking'])
  );
  expect(dashboard.tools).toHaveLength(9);
  expect(dashboard.templates).toHaveLength(5);
  expect(dashboard.ranking.length).toBeGreaterThanOrEqual(5);
  expect(dashboard.metrics).toHaveLength(5);
  expect(dashboard.channelRanking).toHaveLength(5);
  expect(dashboard.recentRecords).toHaveLength(5);
});

test('marketing dashboard model prefers configured sections before defaults', () => {
  const marketing = normalizePageConfig({
    tenant_id: 'demo',
    page: {
      id: 'page-marketing',
      page_key: 'marketing',
      label: 'AI 营销',
      title: '营销增长中心',
      subtitle: '增长工具',
      icon: 'Megaphone',
      sort_order: 30,
      enabled: true
    },
    sections: [
      {
        id: 'section-marketing-tools',
        page_key: 'marketing',
        section_key: 'tools',
        title: '营销工具矩阵',
        layout: 'tool-grid',
        items: [
          {
            id: 'custom-tool',
            item_type: 'tool',
            title: '自定义营销工具',
            subtitle: '来自管理端配置',
            category: '营销工具',
            icon: 'Megaphone',
            action_value: 'custom-tool',
            required_membership: false
          }
        ]
      },
      {
        id: 'section-marketing-templates',
        page_key: 'marketing',
        section_key: 'templates',
        title: '爆款模板推荐',
        layout: 'template-list',
        items: [
          {
            id: 'custom-template',
            item_type: 'template',
            title: '自定义模板',
            subtitle: '管理端模板',
            category: '模板',
            icon: 'FileText',
            action_value: 'custom-template',
            required_membership: true
          }
        ]
      }
    ]
  });

  const dashboard = buildMarketingDashboardModel(marketing);

  expect(dashboard.tools[0].title).toBe('自定义营销工具');
  expect(dashboard.templates[0].title).toBe('自定义模板');
  expect(dashboard.tools).toHaveLength(9);
  expect(dashboard.templates).toHaveLength(5);
});

test('normalizes video workbench payloads from snake case API responses', () => {
  const workbench = normalizeVideoWorkbench({
    tenant_id: 'demo',
    user_id: 'demo-user',
    wallet: { balance: 118000, frozen_balance: 400 },
    route: { route_key: 'video_text_to_video', unit_cost: 200 },
    tasks: [
      {
        id: 'task-1',
        tenant_id: 'demo',
        user_id: 'demo-user',
        task_type: 'VIDEO',
        route_key: 'video_text_to_video',
        prompt: '新品上市推广视频',
        status: 'PROCESSING',
        estimated_cost: 200,
        actual_cost: null,
        provider_task_id: 'provider-1',
        result_url: null,
        error_message: null,
        created_at: '2026-05-09T09:30:00'
      }
    ]
  });

  expect(workbench).toMatchObject({
    tenantId: 'demo',
    userId: 'demo-user',
    wallet: { balance: 118000, frozenBalance: 400 },
    route: { routeKey: 'video_text_to_video', unitCost: 200 }
  });
  expect(workbench.tasks[0]).toMatchObject({
    taskType: 'VIDEO',
    routeKey: 'video_text_to_video',
    providerTaskId: 'provider-1',
    createdAt: '2026-05-09T09:30:00'
  });
});

test('video status metadata maps generation states to labels and progress', () => {
  expect(getVideoStatusMeta('PENDING')).toMatchObject({ label: '排队中', progress: 8 });
  expect(getVideoStatusMeta('PROCESSING')).toMatchObject({ label: '渲染中', progress: 65 });
  expect(getVideoStatusMeta('SUCCESS')).toMatchObject({ label: '已完成', progress: 100 });
  expect(getVideoStatusMeta('FAILED')).toMatchObject({ label: '失败', progress: 100 });
});

test('fallback video workbench has queue and project data for offline rendering', () => {
  const workbench = createFallbackVideoWorkbench();

  expect(workbench.route.routeKey).toBe('video_text_to_video');
  expect(workbench.route.unitCost).toBe(200);
  expect(workbench.tasks.length).toBeGreaterThanOrEqual(4);
  expect(workbench.tasks.some((task) => task.status === 'PENDING')).toBe(true);
  expect(workbench.tasks.some((task) => task.status === 'SUCCESS')).toBe(true);
});

test('uses the dedicated video page and hides the workspace dock only for video', () => {
  expect(shouldUseVideoPage('video')).toBe(true);
  expect(shouldUseVideoPage('home')).toBe(false);
  expect(shouldShowHomeSidebar('video')).toBe(false);
  expect(shouldHideWorkspaceDock('video')).toBe(true);
  expect(shouldHideWorkspaceDock('assistant')).toBe(false);
});

test('uses the dedicated image page and hides the workspace dock only for creative workbenches', () => {
  expect(shouldUseImagePage('image')).toBe(true);
  expect(shouldUseImagePage('video')).toBe(false);
  expect(shouldUseImagePage('home')).toBe(false);
  expect(shouldShowHomeSidebar('image')).toBe(false);
  expect(shouldHideWorkspaceDock('image')).toBe(true);
});

test('uses dedicated coding and writing workbench pages', () => {
  expect(shouldUseCodingPage('coding')).toBe(true);
  expect(shouldUseCodingPage('writing')).toBe(false);
  expect(shouldUseWritingPage('writing')).toBe(true);
  expect(shouldUseWritingPage('coding')).toBe(false);
  expect(shouldShowHomeSidebar('coding')).toBe(false);
  expect(shouldShowHomeSidebar('writing')).toBe(false);
  expect(shouldHideWorkspaceDock('coding')).toBe(true);
  expect(shouldHideWorkspaceDock('writing')).toBe(true);
});

test('fallback navigation places AI image between marketing and video', () => {
  const channels = createFallbackPortalConfig().channels.map((channel) => channel.key);

  expect(channels.slice(channels.indexOf('marketing'), channels.indexOf('video') + 1)).toEqual(['marketing', 'image', 'video']);
});

test('normalizes image workbench payloads from snake case API responses', () => {
  const workbench = normalizeImageWorkbench({
    tenant_id: 'demo',
    user_id: 'demo-user',
    wallet: { balance: 118000, frozen_balance: 80 },
    route: { route_key: 'image_text_to_image', unit_cost: 80 },
    tasks: [
      {
        id: 'image-task-1',
        tenant_id: 'demo',
        user_id: 'demo-user',
        task_type: 'IMAGE',
        route_key: 'image_text_to_image',
        prompt: '生成一张新品推广海报',
        status: 'PROCESSING',
        estimated_cost: 80,
        actual_cost: null,
        provider_task_id: 'provider-image-1',
        result_url: null,
        error_message: null,
        created_at: '2026-05-09T09:30:00'
      }
    ]
  });

  expect(workbench).toMatchObject({
    tenantId: 'demo',
    userId: 'demo-user',
    wallet: { balance: 118000, frozenBalance: 80 },
    route: { routeKey: 'image_text_to_image', unitCost: 80 }
  });
  expect(workbench.tasks[0]).toMatchObject({
    taskType: 'IMAGE',
    routeKey: 'image_text_to_image',
    providerTaskId: 'provider-image-1',
    createdAt: '2026-05-09T09:30:00'
  });
});

test('image status metadata maps generation states to labels and progress', () => {
  expect(getImageStatusMeta('PENDING')).toMatchObject({ label: '排队中', progress: 10 });
  expect(getImageStatusMeta('PROCESSING')).toMatchObject({ label: '生成中', progress: 65 });
  expect(getImageStatusMeta('SUCCESS')).toMatchObject({ label: '已完成', progress: 100 });
  expect(getImageStatusMeta('FAILED')).toMatchObject({ label: '失败', progress: 100 });
});

test('fallback image workbench has queue and project data for offline rendering', () => {
  const workbench = createFallbackImageWorkbench();

  expect(workbench.route.routeKey).toBe('image_text_to_image');
  expect(workbench.route.unitCost).toBe(80);
  expect(workbench.tasks.length).toBeGreaterThanOrEqual(4);
  expect(workbench.tasks.some((task) => task.status === 'PENDING')).toBe(true);
  expect(workbench.tasks.some((task) => task.status === 'PROCESSING')).toBe(true);
  expect(workbench.tasks.some((task) => task.status === 'SUCCESS')).toBe(true);
});

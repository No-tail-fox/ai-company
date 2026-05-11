import { expect, test } from 'vitest';
import {
  HOME_PROMO_CAROUSEL_LAYOUT,
  buildHomeDashboardModel,
  createFallbackHomeDashboard,
  createFallbackPageConfig,
  normalizeHomeDashboard,
  shouldHideWorkspaceDock,
  shouldUseHomeDashboardPage
} from '../src/services/viewModel';

test('normalizes Chinese home dashboard payload from the backend', () => {
  const dashboard = normalizeHomeDashboard({
    tenant_id: 'demo',
    page: {
      page_key: 'home',
      label: '首页',
      title: '中文首页',
      subtitle: '会员活动、工作台、社群和工具统一入口',
      icon: 'Home',
      sort_order: 10,
      enabled: true
    },
    hero_slides: [
      {
        id: 'slide-vip',
        title: '会员活动限时特惠',
        subtitle: '开通会员领取模板、社群和接单资料',
        badge: '会员专享',
        cta_label: '立即开通',
        cta_subtitle: '查看权益，不走支付',
        image_url: '/storage/home/vip.png',
        action_type: 'route',
        action_value: '/membership/benefits',
        metadata_json: { accent: 'gold' }
      }
    ],
    kpi_cards: [{ id: 'today-new', label: '今日上新', value: '12', trend: '模板持续更新', icon: 'Sparkles', tone: 'blue' }],
    workbench_shortcuts: [
      {
        id: 'workbench-chat',
        item_type: 'tool',
        title: 'AI 对话',
        subtitle: '写作、问答和方案梳理',
        category: '应用工作台',
        icon: 'Bot',
        action_value: '/workbench',
        sort_order: 10,
        enabled: true,
        menu_keys: ['workspace']
      }
    ],
    community_cards: [
      {
        id: 'community-starter',
        item_type: 'community',
        title: '入门交流群',
        subtitle: '新人答疑和工具清单',
        category: '社群',
        icon: 'MessageCircle',
        action_value: '/community/starter',
        sort_order: 10,
        enabled: true,
        menu_keys: ['basic', 'growth']
      }
    ],
    tool_cards: [
      {
        id: 'tool-quote',
        item_type: 'template',
        title: '接单报价',
        subtitle: '快速生成报价单',
        category: '接单变现',
        icon: 'ReceiptText',
        action_value: '/toolkit/quote',
        sort_order: 10,
        enabled: true,
        metadata_json: { menuKeys: ['orders'] }
      }
    ]
  });

  expect(dashboard.heroSlides[0]).toMatchObject({
    title: '会员活动限时特惠',
    ctaLabel: '立即开通',
    actionValue: '/membership/benefits',
    metadata: { accent: 'gold' }
  });
  expect(dashboard.workbenchShortcuts[0].menuKeys).toEqual(['workspace']);
  expect(dashboard.communityCards[0].menuKeys).toEqual(['basic', 'growth']);
  expect(dashboard.toolCards[0].menuKeys).toEqual(['orders']);
  expect(dashboard.kpiCards[0].label).toBe('今日上新');
});

test('builds a home dashboard model with persistent core blocks and filtered sections', () => {
  const pageConfig = createFallbackPageConfig('home');
  const fallback = createFallbackHomeDashboard(pageConfig);
  const model = buildHomeDashboardModel(pageConfig, fallback);

  expect(HOME_PROMO_CAROUSEL_LAYOUT).toBe('promo-carousel');
  expect(shouldUseHomeDashboardPage('home')).toBe(true);
  expect(shouldUseHomeDashboardPage('home', 'basic')).toBe(true);
  expect(shouldUseHomeDashboardPage('home', 'growth')).toBe(false);
  expect(shouldUseHomeDashboardPage('home', 'orders')).toBe(false);
  expect(shouldUseHomeDashboardPage('assistant')).toBe(false);
  expect(shouldHideWorkspaceDock('home')).toBe(true);
  expect(model.heroSlides.length).toBeGreaterThanOrEqual(3);
  expect(model.workbenchShortcuts.map((item) => item.title)).toEqual(
    expect.arrayContaining(['AI 对话', '图片生成', '视频脚本', 'PPT 办公'])
  );
  expect(model.communityCards.map((item) => item.title)).toEqual(expect.arrayContaining(['入门交流群', '接单变现群']));
  expect(model.toolCards.map((item) => item.title)).toEqual(expect.arrayContaining(['常用工具', '电商优化']));
  expect(model.sections.map((section) => section.sectionKey)).toEqual(
    expect.arrayContaining(['learning_center', 'order_center', 'communities'])
  );
});

test('derives preview dashboard cards from home sections when dashboard arrays are empty', () => {
  const basePageConfig = createFallbackPageConfig('home');
  const configuredPageConfig = {
    ...basePageConfig,
    sections: [
      {
        id: 'preview-workbench-section',
        tenantId: 'demo',
        pageKey: 'home',
        sectionKey: 'workbench_shortcuts',
        title: 'Preview Workbench',
        subtitle: 'Configured in admin',
        layout: 'tool-grid',
        sortOrder: 10,
        enabled: true,
        items: [
          {
            id: 'preview-chat',
            itemType: 'tool',
            title: 'Admin Preview Chat',
            subtitle: 'Uses admin content',
            category: '应用工作台',
            icon: 'Bot',
            actionValue: '/workbench',
            requiredMembership: false,
            pointCost: 0,
            sortOrder: 10,
            enabled: true,
            tags: [],
            metadata: {}
          }
        ]
      },
      {
        id: 'preview-community-section',
        tenantId: 'demo',
        pageKey: 'home',
        sectionKey: 'communities',
        title: 'Preview Communities',
        subtitle: 'Configured in admin',
        layout: 'banner-row',
        sortOrder: 20,
        enabled: true,
        items: [
          {
            id: 'preview-community',
            itemType: 'community',
            title: 'Admin Preview Group',
            subtitle: 'Uses admin community',
            category: '社群',
            icon: 'Users',
            actionValue: '/community/admin-preview',
            requiredMembership: false,
            pointCost: 0,
            sortOrder: 10,
            enabled: true,
            tags: [],
            metadata: {}
          }
        ]
      },
      {
        id: 'preview-tool-section',
        tenantId: 'demo',
        pageKey: 'home',
        sectionKey: 'home_tools',
        title: 'Preview Tools',
        subtitle: 'Configured in admin',
        layout: 'tool-grid',
        sortOrder: 30,
        enabled: true,
        items: [
          {
            id: 'preview-tool',
            itemType: 'template',
            title: 'Admin Preview Tool',
            subtitle: 'Uses admin tool',
            category: '工具框',
            icon: 'LayoutGrid',
            actionValue: '/toolkit/admin-preview',
            requiredMembership: false,
            pointCost: 0,
            sortOrder: 10,
            enabled: true,
            tags: [],
            metadata: {}
          }
        ]
      }
    ]
  };
  const emptyDashboard = {
    ...createFallbackHomeDashboard(configuredPageConfig),
    heroSlides: [],
    kpiCards: [],
    workbenchShortcuts: [],
    communityCards: [],
    toolCards: []
  };

  const model = buildHomeDashboardModel(configuredPageConfig, emptyDashboard);

  expect(model.workbenchShortcuts.map((item) => item.title)).toEqual(['Admin Preview Chat']);
  expect(model.communityCards.map((item) => item.title)).toEqual(['Admin Preview Group']);
  expect(model.toolCards.map((item) => item.title)).toEqual(['Admin Preview Tool']);
});

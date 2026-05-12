import { expect, test } from 'vitest';
import {
  buildMarketingDashboardModel,
  buildAssistantRanking,
  createFallbackChatWorkbench,
  createFallbackImageWorkbench,
  createFallbackVideoWorkbench,
  createFallbackAssistantCenter,
  createHomeMenuPageConfig,
  createFallbackPortalConfig,
  createFallbackPageConfig,
  filterAssistantCardsByCategory,
  formatUsageCount,
  groupChatSessionsByRecency,
  getVideoStatusMeta,
  getImageStatusMeta,
  normalizeAssistantCenter,
  normalizePortalActionResult,
  normalizePortalDetail,
  normalizePortalUserActions,
  normalizeChatWorkbench,
  normalizeImageWorkbench,
  normalizeVideoWorkbench,
  normalizePageConfig,
  normalizePortalConfig,
  shouldUseAssistantPage,
  shouldUseImagePage,
  shouldUseCodingPage,
  shouldUseMarketingPage,
  shouldUseWorkbenchPage,
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
    'workbench',
    'communication',
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
  expect(
    config.homeSections
      .find((section) => section.sectionKey === 'workspace_tools')
      ?.items.some((item) => item.title === 'AI 工作台' && item.actionValue === '/workbench')
  ).toBe(true);
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

test('normalizes older portal configs by inserting the communication hall after workbench', () => {
  const config = normalizePortalConfig({
    tenant_id: 'demo',
    pages: [
      { id: 'page-home', page_key: 'home', label: '首页', title: '首页', icon: 'Home', sort_order: 10, enabled: true },
      { id: 'page-assistant', page_key: 'assistant', label: 'AI 助理', title: '智能助理广场', icon: 'Bot', sort_order: 20, enabled: true },
      { id: 'page-workbench', page_key: 'workbench', label: '工作台', title: 'AI 工作台', icon: 'LayoutDashboard', sort_order: 25, enabled: true },
      { id: 'page-marketing', page_key: 'marketing', label: 'AI 营销', title: '营销增长中心', icon: 'Megaphone', sort_order: 30, enabled: true }
    ],
    channels: [
      { key: 'home', label: '首页' },
      { key: 'assistant', label: 'AI 助理' },
      { key: 'workbench', label: '工作台' },
      { key: 'marketing', label: 'AI 营销' }
    ],
    left_nav: [],
    home_sections: []
  });

  expect(config.pages.map((page) => page.pageKey)).toEqual(['home', 'assistant', 'workbench', 'communication', 'marketing']);
  expect(config.channels.map((channel) => channel.key)).toEqual(['home', 'assistant', 'workbench', 'communication', 'marketing']);
});

test('normalizes model binding metadata on portal items, assistants and prompt templates', () => {
  const portal = normalizePortalConfig({
    tenant_id: 'demo',
    pages: [],
    channels: [],
    left_nav: [],
    home_sections: [
      {
        id: 'section-tools',
        area: 'home',
        section_key: 'tools',
        title: '工具',
        layout: 'tool-grid',
        enabled: true,
        items: [
          {
            id: 'item-image',
            item_type: 'tool',
            title: '图片生成',
            subtitle: '生成高质量图片',
            category: '工具',
            icon: 'Image',
            action_value: 'image_text_to_image',
            point_cost: 80,
            effective_point_cost: 45,
            model_config: {
              id: 'model-image',
              model_key: 'image_text_to_image',
              display_name: 'GPT Image 2',
              provider_model: 'gpt-image-2'
            }
          }
        ]
      }
    ]
  });

  expect((portal.homeSections[0].items[0] as any).effectivePointCost).toBe(45);
  expect((portal.homeSections[0].items[0] as any).modelConfig.modelKey).toBe('image_text_to_image');

  const center = normalizeAssistantCenter({
    categories: ['全部'],
    assistants: [
      {
        id: 'assistant-1',
        name: '写作助理',
        category: '写作',
        description: '智能写作',
        icon: 'Feather',
        usage_count: 12,
        point_cost: 30,
        effective_point_cost: 18,
        model_config: {
          id: 'model-writing',
          model_key: 'writing_text_default',
          display_name: 'Writing Model',
          provider_model: 'writing-1'
        }
      }
    ],
    prompt_templates: [
      {
        id: 'template-1',
        title: '标题模板',
        category: '写作',
        content: '生成标题',
        required_membership: false,
        effective_point_cost: 9,
        model_config: {
          id: 'model-template',
          model_key: 'writing_text_default',
          display_name: 'Template Model',
          provider_model: 'writing-1'
        }
      }
    ]
  });

  expect((center.assistants[0] as any).effectivePointCost).toBe(18);
  expect((center.assistants[0] as any).modelConfig.modelKey).toBe('writing_text_default');
  expect((center.promptTemplates[0] as any).effectivePointCost).toBe(9);
  expect((center.promptTemplates[0] as any).modelConfig.modelKey).toBe('writing_text_default');
});

test('normalizes portal detail payloads, action results and user action records', () => {
  const detail = normalizePortalDetail({
    path: '/workspace/course',
    kind: 'directory',
    title: '常用AI学习中心',
    subtitle: '课程、实战和变现路径',
    icon: 'FileVideo',
    requiredMembership: true,
    effectivePointCost: 20,
    items: [
      {
        id: 'learn-a',
        item_type: 'course',
        title: '0基础AI通识课',
        subtitle: '入门',
        category: '基础必备',
        icon: 'FileVideo',
        action_value: '/workspace/course',
        point_cost: 0,
        required_membership: false,
        metadata_json: {
          detail: {
            summary: '系统学习 AI 基础能力。'
          }
        }
      }
    ],
    detail: {
      summary: '系统学习 AI 基础能力。',
      highlights: ['12 个核心模块'],
      steps: ['完成入门测评'],
      deliverables: ['学习路线图'],
      faqs: [{ question: '适合谁？', answer: '零基础用户。' }],
      primaryAction: { key: 'enroll', label: '报名学习' },
      secondaryActions: [{ key: 'favorite', label: '收藏' }],
      download: { fileName: 'starter-kit.md', url: '/storage/resources/starter-kit.md' }
    },
    userState: {
      membershipActive: false,
      locked: true,
      completedActions: ['favorite']
    }
  });

  expect(detail.path).toBe('/workspace/course');
  expect(detail.items[0].metadata.detail.summary).toBe('系统学习 AI 基础能力。');
  expect(detail.detail.primaryAction.key).toBe('enroll');
  expect(detail.userState.completedActions).toEqual(['favorite']);

  const action = normalizePortalActionResult({
    status: 'completed',
    message: '资料已领取',
    action: {
      id: 'act-1',
      detail_path: '/resources/starter-kit',
      action_key: 'download',
      item_id: 'quick-03',
      status: 'COMPLETED',
      result: { download: { fileName: 'starter-kit.md' } }
    },
    download: { fileName: 'starter-kit.md', url: '/storage/resources/starter-kit.md' }
  });
  expect(action.action?.detailPath).toBe('/resources/starter-kit');
  expect(action.download?.fileName).toBe('starter-kit.md');

  const actions = normalizePortalUserActions({
    actions: [
      {
        id: 'act-1',
        detail_path: '/resources/starter-kit',
        action_key: 'download',
        item_id: 'quick-03',
        status: 'COMPLETED',
        message: '资料已领取'
      }
    ]
  });
  expect(actions[0].actionKey).toBe('download');
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

test('toolkit home menu includes third-party tools with external download metadata', () => {
  const toolkit = createHomeMenuPageConfig(createFallbackPageConfig('home'), 'toolkit');
  const thirdPartySection = toolkit.sections.find((section) => section.sectionKey === 'third_party_tools');

  expect(thirdPartySection).toBeDefined();
  expect(thirdPartySection?.layout).toBe('third-party-tools');
  expect(thirdPartySection?.items[0]).toMatchObject({
    itemType: 'third_party_tool',
    title: '剪映专业版',
    actionType: 'external_link',
    actionValue: expect.stringMatching(/^https:\/\//),
    metadata: {
      brandMark: 'JY',
      detail: {
        download: {
          url: expect.stringMatching(/^https:\/\//)
        }
      }
    }
  });
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

test('uses the dedicated workbench page only for the workbench route', () => {
  expect(shouldUseWorkbenchPage('workbench')).toBe(true);
  expect(shouldUseWorkbenchPage('assistant')).toBe(false);
  expect(shouldShowHomeSidebar('workbench')).toBe(false);
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

test('uses the dedicated video page without hiding the workspace dock', () => {
  expect(shouldUseVideoPage('video')).toBe(true);
  expect(shouldUseVideoPage('home')).toBe(false);
  expect(shouldShowHomeSidebar('video')).toBe(false);
  expect(shouldHideWorkspaceDock('video')).toBe(false);
  expect(shouldHideWorkspaceDock('assistant')).toBe(false);
});

test('uses the dedicated image page without hiding the workspace dock', () => {
  expect(shouldUseImagePage('image')).toBe(true);
  expect(shouldUseImagePage('video')).toBe(false);
  expect(shouldUseImagePage('home')).toBe(false);
  expect(shouldShowHomeSidebar('image')).toBe(false);
  expect(shouldHideWorkspaceDock('image')).toBe(false);
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

test('normalizes chat workbench payloads and groups sessions by recency', () => {
  const workbench = normalizeChatWorkbench({
    tenant_id: 'demo',
    user_id: 'demo-user',
    sessions: [
      {
        id: 'chat-today',
        title: '今日会话',
        preview: '刚刚发送',
        model_key: 'general_text_default',
        preset_role: 'assistant',
        status: 'ACTIVE',
        message_count: 2,
        updated_at: '2026-05-10T09:00:00'
      }
    ],
    active_session: {
      id: 'chat-today',
      title: '今日会话',
      model_key: 'general_text_default',
      preset_role: 'assistant',
      status: 'ACTIVE',
      messages: [
        { id: 'msg-1', role: 'user', content: '整理周报', sequence: 1, created_at: '2026-05-10T08:55:00' },
        { id: 'msg-2', role: 'assistant', content: '已整理完成', sequence: 2, created_at: '2026-05-10T08:56:00' }
      ]
    },
    models: [
      { id: 'model-1', model_key: 'general_text_default', display_name: 'GPT-4.1', provider_model: 'gpt-4.1' }
    ]
  });

  expect(workbench.activeSession?.messages[1].role).toBe('assistant');
  expect(workbench.models[0].displayName).toBe('GPT-4.1');

  const groups = groupChatSessionsByRecency(
    [
      { id: 'chat-today', title: '今日会话', preview: '刚刚发送', modelKey: 'general_text_default', presetRole: 'assistant', status: 'ACTIVE', messageCount: 2, updatedAt: '2026-05-10T09:00:00' },
      { id: 'chat-yesterday', title: '昨天会话', preview: '昨天内容', modelKey: 'general_text_default', presetRole: 'assistant', status: 'ACTIVE', messageCount: 2, updatedAt: '2026-05-09T09:00:00' },
      { id: 'chat-week', title: '本周会话', preview: '本周内容', modelKey: 'general_text_default', presetRole: 'assistant', status: 'ACTIVE', messageCount: 2, updatedAt: '2026-05-07T09:00:00' },
      { id: 'chat-older', title: '更早会话', preview: '更早内容', modelKey: 'general_text_default', presetRole: 'assistant', status: 'ACTIVE', messageCount: 2, updatedAt: '2026-04-30T09:00:00' }
    ],
    '2026-05-10T12:00:00'
  );

  expect(groups.map((group) => group.key)).toEqual(['today', 'yesterday', 'thisWeek', 'older']);
  expect(groups[0].sessions[0].id).toBe('chat-today');
});

test('fallback chat workbench has sessions, models and active messages for offline rendering', () => {
  const workbench = createFallbackChatWorkbench();

  expect(workbench.sessions.length).toBeGreaterThan(0);
  expect(workbench.models.length).toBeGreaterThan(0);
  expect(workbench.activeSession?.messages.length).toBeGreaterThan(0);
});

test('fallback navigation places AI image between marketing and video', () => {
  const channels = createFallbackPortalConfig().channels.map((channel) => channel.key);

  expect(channels.slice(channels.indexOf('marketing'), channels.indexOf('video') + 1)).toEqual(['marketing', 'image', 'video']);
});

test('fallback navigation places communication hall after workbench', () => {
  const channels = createFallbackPortalConfig().channels.map((channel) => channel.key);

  expect(channels.slice(channels.indexOf('workbench'), channels.indexOf('marketing') + 1)).toEqual([
    'workbench',
    'communication',
    'marketing'
  ]);
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

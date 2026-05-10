import { expect, test } from 'vitest';
import * as adminForms from '../src/services/adminForms';
import { buildItemPayload, buildPagePayload, buildReorderPayload, buildSectionPayload } from '../src/services/adminForms';

test('builds page payload expected by admin page API', () => {
  expect(
    buildPagePayload({
      pageKey: 'marketing',
      label: 'AI 营销',
      title: '营销增长中心',
      subtitle: '增长工具',
      icon: 'Megaphone',
      sortOrder: 30,
      enabled: true
    })
  ).toEqual({
    page_key: 'marketing',
    label: 'AI 营销',
    title: '营销增长中心',
    subtitle: '增长工具',
    icon: 'Megaphone',
    sort_order: 30,
    enabled: true
  });
});

test('builds section payload expected by admin section API', () => {
  expect(
    buildSectionPayload({
      pageKey: 'video',
      sectionKey: 'tools',
      title: '视频工具矩阵',
      subtitle: '创作工具',
      layout: 'tool-grid',
      sortOrder: 20,
      enabled: true
    })
  ).toEqual({
    page_key: 'video',
    section_key: 'tools',
    title: '视频工具矩阵',
    subtitle: '创作工具',
    layout: 'tool-grid',
    sort_order: 20,
    enabled: true
  });
});

test('builds item payload expected by admin item API', () => {
  expect(
    buildItemPayload({
      sectionId: 'section-video-tools',
      itemType: 'tool',
      title: '文案生成视频',
      subtitle: '输入脚本生成分镜',
      category: '工具',
      icon: 'MonitorPlay',
      imageUrl: '/storage/uploads/demo/video.png',
      badge: '新',
      tags: ['视频', '模板'],
      sortOrder: 10,
      enabled: true,
      actionType: 'workspace',
      actionValue: 'video-tool-1',
      requiredMembership: true,
      pointCost: 20
    })
  ).toEqual({
    section_id: 'section-video-tools',
    item_type: 'tool',
    title: '文案生成视频',
    subtitle: '输入脚本生成分镜',
    category: '工具',
    icon: 'MonitorPlay',
    image_url: '/storage/uploads/demo/video.png',
    badge: '新',
    tags: ['视频', '模板'],
    sort_order: 10,
    enabled: true,
    action_type: 'workspace',
    action_value: 'video-tool-1',
    required_membership: true,
    point_cost: 20
  });
});

test('builds reorder payload from ordered records', () => {
  expect(buildReorderPayload([{ id: 'section-b' }, { id: 'section-a' }])).toEqual({
    ordered_ids: ['section-b', 'section-a']
  });
  expect(buildReorderPayload([{ id: 'item-b' }, { id: 'item-a' }], 'section-a')).toEqual({
    section_id: 'section-a',
    ordered_ids: ['item-b', 'item-a']
  });
});

test('builds provider channel payload for model center forms', () => {
  expect(
    (adminForms as any).buildProviderChannelPayload({
      channelKey: 'openai-image',
      displayName: 'OpenAI 图片渠道',
      baseUrl: 'https://api.openai.example/v1/images',
      apiKey: 'sk-secret',
      channelType: 'IMAGE',
      priority: 5,
      enabled: true,
      timeoutSeconds: 90
    })
  ).toEqual({
    channel_key: 'openai-image',
    display_name: 'OpenAI 图片渠道',
    base_url: 'https://api.openai.example/v1/images',
    api_key: 'sk-secret',
    channel_type: 'IMAGE',
    priority: 5,
    enabled: true,
    timeout_seconds: 90
  });
});

test('builds model config and binding payloads for model center forms', () => {
  expect(
    (adminForms as any).buildModelConfigPayload({
      modelKey: 'image_text_to_image',
      displayName: 'GPT Image 2',
      capability: 'IMAGE',
      channelId: 'channel-image',
      providerModel: 'gpt-image-2',
      defaultPointCost: 120,
      enabled: true
    })
  ).toEqual({
    model_key: 'image_text_to_image',
    display_name: 'GPT Image 2',
    capability: 'IMAGE',
    channel_id: 'channel-image',
    provider_model: 'gpt-image-2',
    default_point_cost: 120,
    enabled: true
  });

  expect(
    (adminForms as any).buildToolModelBindingPayload({
      targetType: 'builtin',
      targetKey: 'image_text_to_image',
      modelConfigId: 'model-image',
      pointCostOverride: 45,
      enabled: true
    })
  ).toEqual({
    target_type: 'builtin',
    target_key: 'image_text_to_image',
    model_config_id: 'model-image',
    point_cost_override: 45,
    enabled: true
  });
});

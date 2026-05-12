import { expect, test } from 'vitest';
import {
  buildChatModelProfilePayload,
  buildCodexAuthJsonPreview,
  buildCodexConfigTomlPreview,
  buildItemPayload,
  buildModelConfigPayload,
  buildPagePayload,
  buildProviderChannelPayload,
  buildReorderPayload,
  buildSectionPayload,
  buildToolModelBindingPayload
} from '../src/services/adminForms';

test('builds page payload expected by admin page API', () => {
  expect(
    buildPagePayload({
      pageKey: 'marketing',
      label: 'AI 钀ラ攢',
      title: '钀ラ攢澧為暱涓績',
      subtitle: '澧為暱宸ュ叿',
      icon: 'Megaphone',
      sortOrder: 30,
      enabled: true
    })
  ).toEqual({
    page_key: 'marketing',
    label: 'AI 钀ラ攢',
    title: '钀ラ攢澧為暱涓績',
    subtitle: '澧為暱宸ュ叿',
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
      title: '瑙嗛宸ュ叿鐭╅樀',
      subtitle: '鍒涗綔宸ュ叿',
      layout: 'tool-grid',
      sortOrder: 20,
      enabled: true
    })
  ).toEqual({
    page_key: 'video',
    section_key: 'tools',
    title: '瑙嗛宸ュ叿鐭╅樀',
    subtitle: '鍒涗綔宸ュ叿',
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
      title: '鏂囨鐢熸垚瑙嗛',
      subtitle: '杈撳叆鑴氭湰鐢熸垚鍒嗛暅',
      category: '宸ュ叿',
      icon: 'MonitorPlay',
      imageUrl: '/storage/uploads/demo/video.png',
      badge: '鏂�',
      tags: ['瑙嗛', '妯℃澘'],
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
    title: '鏂囨鐢熸垚瑙嗛',
    subtitle: '杈撳叆鑴氭湰鐢熸垚鍒嗛暅',
    category: '宸ュ叿',
    icon: 'MonitorPlay',
    image_url: '/storage/uploads/demo/video.png',
    badge: '鏂�',
    tags: ['瑙嗛', '妯℃澘'],
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
    buildProviderChannelPayload({
      channelKey: 'openai-image',
      displayName: 'OpenAI Official',
      baseUrl: 'https://api.openai.example/v1/images',
      apiKey: 'sk-secret',
      channelType: 'IMAGE',
      adapterType: 'openai_compatible',
      priority: 5,
      enabled: true,
      timeoutSeconds: 90,
      presetKey: 'openai_official',
      remark: '公司专用账号',
      website: 'https://openai.com',
      useFullUrl: true,
      authJsonText: '{"OPENAI_API_KEY":""}',
      configTomlText: 'model_provider = "custom"',
      writeCommonConfig: true,
      testConfigText: '{"temperature":0.2}',
      billingConfigText: '{"mode":"flat","unit_cost":120}'
    })
  ).toEqual({
    channel_key: 'openai-image',
    display_name: 'OpenAI Official',
    base_url: 'https://api.openai.example/v1/images',
    api_key: 'sk-secret',
    channel_type: 'IMAGE',
    adapter_type: 'openai_compatible',
    priority: 5,
    enabled: true,
    timeout_seconds: 90,
    metadata_json: {
      preset_key: 'openai_official',
      remark: '公司专用账号',
      website: 'https://openai.com',
      use_full_url: true,
      auth_json: '{"OPENAI_API_KEY":""}',
      config_toml: 'model_provider = "custom"',
      write_common_config: true,
      test_config: '{"temperature":0.2}',
      billing_config: '{"mode":"flat","unit_cost":120}'
    }
  });
});

test('builds model config and binding payloads for model center forms', () => {
  expect(
    buildModelConfigPayload({
      modelKey: 'image_text_to_image',
      displayName: 'GPT Image 2',
      capability: 'IMAGE',
      channelId: 'channel-image',
      providerModel: 'gpt-image-2',
      defaultPointCost: 120,
      enabled: true,
      useMillionContextWindow: true,
      compressionThreshold: 900000,
      testConfigText: '{"temperature":0.2}',
      billingConfigText: '{"mode":"tiered","unit_cost":120}'
    })
  ).toEqual({
    model_key: 'image_text_to_image',
    display_name: 'GPT Image 2',
    capability: 'IMAGE',
    channel_id: 'channel-image',
    provider_model: 'gpt-image-2',
    default_point_cost: 120,
    enabled: true,
    metadata_json: {
      use_million_context_window: true,
      compression_threshold: 900000,
      test_config: '{"temperature":0.2}',
      billing_config: '{"mode":"tiered","unit_cost":120}'
    }
  });

  expect(
    buildToolModelBindingPayload({
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

test('builds chat model profile payload and generated Codex previews', () => {
  const profile = {
    providerName: '中转',
    note: '公司专用账号',
    officialUrl: 'https://ai.input.im',
    baseUrl: 'https://ai.input.im',
    apiKey: 'sk-secret-1234',
    modelName: 'gpt-5.5',
    modelKey: 'general_text_default',
    displayName: 'GPT-5.5',
    modelReasoningEffort: 'high',
    providerReasoningEffort: 'medium',
    serviceTier: 'fast',
    contextWindow: 1000000,
    autoCompactTokenLimit: 900000,
    disableResponseStorage: true,
    defaultPointCost: 0,
    timeoutSeconds: 60,
    enabled: true
  };

  expect(buildChatModelProfilePayload(profile)).toEqual({
    channel_key: 'openai-chat-compatible',
    provider_name: '中转',
    note: '公司专用账号',
    official_url: 'https://ai.input.im',
    base_url: 'https://ai.input.im',
    api_key: 'sk-secret-1234',
    model_name: 'gpt-5.5',
    model_key: 'general_text_default',
    display_name: 'GPT-5.5',
    model_reasoning_effort: 'high',
    provider_reasoning_effort: 'medium',
    service_tier: 'fast',
    context_window: 1000000,
    auto_compact_token_limit: 900000,
    disable_response_storage: true,
    default_point_cost: 0,
    timeout_seconds: 60,
    enabled: true
  });
  expect(
    buildChatModelProfilePayload({
      ...profile,
      modelKey: 'custom_chat_key'
    }).model_key
  ).toBe('general_text_default');

  expect(buildCodexAuthJsonPreview(profile.apiKey)).toContain('"OPENAI_API_KEY": "sk-secret-1234"');
  const toml = buildCodexConfigTomlPreview(profile);
  expect(toml).toContain('model_provider = "custom"');
  expect(toml).toContain('model = "gpt-5.5"');
  expect(toml).toContain('wire_api = "responses"');
  expect(toml).toContain('base_url = "https://ai.input.im"');
});

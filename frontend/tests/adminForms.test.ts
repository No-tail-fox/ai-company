import { expect, test } from 'vitest';
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

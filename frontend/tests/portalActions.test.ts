import { afterEach, expect, test, vi } from 'vitest';
import {
  fetchPortalDetail,
  fetchPortalUserActions,
  runPortalAction,
  searchPortal
} from '../src/services/api';
import { buildItemPayload } from '../src/services/adminForms';

function mockFetchResponse(payload: any) {
  return {
    ok: true,
    json: async () => payload
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test('portal detail request preserves slash paths and user id', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      path: '/workspace/course',
      kind: 'directory',
      title: '常用AI学习中心',
      items: [],
      detail: {},
      userState: {}
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await fetchPortalDetail('/workspace/course', 'demo-user');

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/portal/details/workspace/course?user_id=demo-user');
});

test('portal search and user action APIs normalize query payloads', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(mockFetchResponse({ results: [{ id: 'quick-03', title: '领取新手资料包', path: '/resources/starter-kit' }] }))
    .mockResolvedValueOnce(mockFetchResponse({ actions: [{ id: 'act-1', action_key: 'download', detail_path: '/resources/starter-kit' }] }));
  vi.stubGlobal('fetch', fetchMock);

  const results = await searchPortal('新手', 'home', 5);
  const actions = await fetchPortalUserActions('demo-user', 'download');

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/portal/search?q=%E6%96%B0%E6%89%8B&page_key=home&limit=5');
  expect(results[0].path).toBe('/resources/starter-kit');
  expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/portal/user-actions?user_id=demo-user&kind=download');
  expect(actions[0].actionKey).toBe('download');
});

test('portal action request posts snake case body', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      status: 'completed',
      message: '资料已领取',
      action: { id: 'act-1', action_key: 'download', detail_path: '/resources/starter-kit' },
      download: { fileName: 'starter-kit.md', url: '/storage/resources/starter-kit.md' }
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  await runPortalAction({
    userId: 'demo-user',
    detailPath: '/resources/starter-kit',
    itemId: 'quick-03',
    actionKey: 'download'
  });

  expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({
    user_id: 'demo-user',
    detail_path: '/resources/starter-kit',
    item_id: 'quick-03',
    action_key: 'download'
  });
});

test('admin item payload includes configurable detail metadata', () => {
  expect(
    buildItemPayload({
      sectionId: 'section-a',
      itemType: 'course',
      title: '0基础AI通识课',
      actionValue: '/workspace/course',
      detailSummary: '系统学习 AI 基础能力。',
      detailHighlightsText: '12 个核心模块\n站内记录进度',
      detailStepsText: '完成入门测评\n按章节学习',
      detailDeliverablesText: '学习路线图',
      detailFaqsText: '适合谁？|零基础用户。',
      detailPrimaryActionKey: 'enroll',
      detailPrimaryActionLabel: '报名学习',
      detailDownloadFileName: 'starter-kit.md',
      detailDownloadUrl: '/storage/resources/starter-kit.md'
    } as any).metadata_json
  ).toMatchObject({
    detail: {
      summary: '系统学习 AI 基础能力。',
      highlights: ['12 个核心模块', '站内记录进度'],
      steps: ['完成入门测评', '按章节学习'],
      deliverables: ['学习路线图'],
      faqs: [{ question: '适合谁？', answer: '零基础用户。' }],
      primaryAction: { key: 'enroll', label: '报名学习' },
      download: { fileName: 'starter-kit.md', url: '/storage/resources/starter-kit.md' }
    }
  });
});

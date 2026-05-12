import { afterEach, expect, test, vi } from 'vitest';
import {
  createCommunicationHallPost,
  createRechargeOrder,
  fetchAccountSummary,
  fetchCommunicationHall,
  updateAccountProfile,
  fetchPortalDetail,
  fetchPortalUserActions,
  runPortalAction,
  searchPortal
} from '../src/services/api';
import * as api from '../src/services/api';
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

test('communication hall APIs fetch posts and create persistent detail-backed posts', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(
      mockFetchResponse({
        categories: [{ key: 'all', label: '全部' }, { key: 'talk', label: '交流' }],
        hot_tags: ['RAG'],
        hot_topics: [{ title: '企业知识库', count: 3 }],
        posts: [
          {
            id: 'rag-project-notes',
            item_id: 'rag-project-notes',
            detail_path: '/communication/detail/rag-project-notes',
            category_key: 'talk',
            category_label: '交流',
            badge_label: '交流',
            title: 'RAG project notes',
            summary: 'First version',
            tags: ['RAG']
          }
        ]
      })
    )
    .mockResolvedValueOnce(
      mockFetchResponse({
        detail_path: '/communication/detail/new-note',
        post: {
          id: 'new-note',
          item_id: 'new-note',
          detail_path: '/communication/detail/new-note',
          category_key: 'talk',
          category_label: '交流',
          badge_label: '交流',
          title: 'New note',
          summary: 'Body',
          tags: ['交流']
        }
      })
    );
  vi.stubGlobal('fetch', fetchMock);

  const hall = await fetchCommunicationHall('author-a');
  const created = await createCommunicationHallPost({
    categoryKey: 'talk',
    title: 'New note',
    bodyMarkdown: 'Body'
  });

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/communication/posts?user_id=author-a');
  expect(hall.posts[0].detailPath).toBe('/communication/detail/rag-project-notes');
  expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/communication/posts');
  expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string)).toEqual({
    category_key: 'talk',
    title: 'New note',
    body_markdown: 'Body'
  });
  expect(created.post.detailPath).toBe('/communication/detail/new-note');
  expect(created.detailPath).toBe('/communication/detail/new-note');
});

test('portal detail API normalizes markdown documents, versions, comments, and permissions', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      path: '/resources/tools',
      title: '工具优惠合集',
      detail: {
        summary: '模型、剪辑、设计和办公工具权益',
        body_markdown: '# 工具优惠合集\n\n正文',
        tags: ['工具权益', 'Markdown'],
        version: { id: 'ver-2', version: 2, release_note: '补充权益' },
        versions: [
          { id: 'ver-2', version: 2, release_note: '补充权益' },
          { id: 'ver-1', version: 1, release_note: '初始版本' }
        ],
        comments: [{ id: 'comment-1', content: '建议增加商用授权列。', author_name: '浏览者' }],
        publish_info: { type_label: '资源合集', version_label: 'v2', visibility_label: '社区成员' }
      },
      permissions: { can_edit: true, can_comment: true },
      userState: {}
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  const detail = await fetchPortalDetail('/resources/tools', 'viewer-user');

  expect(detail.detail.bodyMarkdown).toBe('# 工具优惠合集\n\n正文');
  expect(detail.detail.tags).toEqual(['工具权益', 'Markdown']);
  expect(detail.detail.version?.version).toBe(2);
  expect(detail.detail.versions).toHaveLength(2);
  expect(detail.detail.comments[0].authorName).toBe('浏览者');
  expect(detail.detail.publishInfo.typeLabel).toBe('资源合集');
  expect(detail.permissions.canEdit).toBe(true);
});

test('portal detail mutation APIs post snake case bodies with auth', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(mockFetchResponse({ detail: {} }))
    .mockResolvedValueOnce(mockFetchResponse({ detail: {} }))
    .mockResolvedValueOnce(mockFetchResponse({ detail: {}, comment: { id: 'comment-1' } }));
  vi.stubGlobal('fetch', fetchMock);

  await (api as any).updatePortalDetail('/resources/tools', {
    title: '工具优惠合集 v1.5',
    bodyMarkdown: '# 新正文',
    tags: ['工具权益'],
    visibility: 'community'
  });
  await (api as any).publishPortalDetail('/resources/tools', '补充权益');
  await (api as any).createPortalDetailComment('/resources/tools', '建议增加商用授权列。');

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/portal/details/resources/tools');
  expect(fetchMock.mock.calls[0][1]?.method).toBe('PATCH');
  expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({
    title: '工具优惠合集 v1.5',
    body_markdown: '# 新正文',
    tags: ['工具权益'],
    visibility: 'community'
  });
  expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/portal/details/resources/tools/versions');
  expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string)).toEqual({ release_note: '补充权益' });
  expect(fetchMock.mock.calls[2][0]).toBe('/api/v1/portal/details/resources/tools/comments');
  expect(JSON.parse(fetchMock.mock.calls[2][1]?.body as string)).toEqual({ content: '建议增加商用授权列。' });
});

test('account summary and profile APIs normalize and post snake case payloads', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(
      mockFetchResponse({
        user: {
          id: 'demo-user',
          tenant_id: 'demo',
          phone: '13800000000',
          display_name: '演示用户',
          role: 'USER',
          status: 'ACTIVE'
        },
        wallet: {
          balance: 120000,
          frozen_balance: 80,
          currency: 'POINT'
        },
        membership: {
          active: true,
          plan: { id: 'plan-vip-monthly', plan_key: 'vip_monthly', name: 'VIP 月卡' },
          expires_at: '2026-06-10T00:00:00',
          entitlements: ['assistant.vip']
        }
      })
    )
    .mockResolvedValueOnce(mockFetchResponse({ user: { display_name: '新昵称' } }));
  vi.stubGlobal('fetch', fetchMock);

  const summary = await fetchAccountSummary('demo-user');
  const updated = await updateAccountProfile({ userId: 'demo-user', displayName: '新昵称' });

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/account/summary?user_id=demo-user');
  expect(summary.user.displayName).toBe('演示用户');
  expect(summary.wallet.balance).toBe(120000);
  expect(summary.membership?.plan?.name).toBe('VIP 月卡');
  expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/account/profile');
  expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string)).toEqual({
    user_id: 'demo-user',
    display_name: '新昵称'
  });
  expect(updated.displayName).toBe('新昵称');
});

test('recharge order API posts package key and normalizes pending order payloads', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      id: 'pay-1',
      status: 'PENDING',
      provider: 'manual',
      provider_order_no: 'RECHARGE-001',
      request_key: 'recharge-001',
      user_id: 'demo-user',
      package_key: 'points_5000',
      amount_cents: 4900,
      points: 5000,
      message: '等待支付渠道接入'
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  const order = await createRechargeOrder({ userId: 'demo-user', packageKey: 'points_5000' });

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/payments/recharge-orders');
  expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({
    user_id: 'demo-user',
    package_key: 'points_5000'
  });
  expect(order.status).toBe('PENDING');
  expect(order.points).toBe(5000);
  expect(order.amountCents).toBe(4900);
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

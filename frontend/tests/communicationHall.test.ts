import { expect, test } from 'vitest';
import {
  buildCommunicationDetailPath,
  communicationCategories,
  communicationHotTags,
  communicationPosts,
  createCommunicationDraft,
  createCommunicationPost,
  filterCommunicationPosts,
  normalizeCommunicationHallPayload,
  validateCommunicationDraft
} from '../src/services/communicationHall';

test('communication hall ships design categories and posts', () => {
  expect(communicationCategories.map((category) => category.key)).toEqual([
    'all',
    'order',
    'template',
    'talk',
    'benefit',
    'resource',
    'pitch',
    'local-order',
    'short-drama',
    'ecommerce'
  ]);
  expect(communicationHotTags).toEqual(expect.arrayContaining(['AI短剧', '接单报价', '工具权益']));
  expect(communicationPosts).toHaveLength(9);
  expect(communicationPosts[0]).toMatchObject({
    id: 'short-drama-editing-team',
    categoryKey: 'order',
    title: expect.stringContaining('AI 短剧剪辑团队')
  });
});

test('communication hall filters by search, category, hot tag and favorites', () => {
  expect(filterCommunicationPosts(communicationPosts, { query: 'RAG' }).map((post) => post.id)).toEqual([
    'rag-or-finetune'
  ]);
  expect(filterCommunicationPosts(communicationPosts, { categoryKey: 'template' }).map((post) => post.id)).toEqual([
    'ecommerce-detail-template',
    'poster-copy-template'
  ]);
  expect(filterCommunicationPosts(communicationPosts, { tag: '合同经验' }).map((post) => post.id)).toEqual([
    'opc-contract-subject'
  ]);
  expect(
    filterCommunicationPosts(communicationPosts, {
      favoritesOnly: true,
      favoriteIds: new Set(['poster-copy-template', 'tool-benefits-v14'])
    }).map((post) => post.id)
  ).toEqual(['tool-benefits-v14', 'poster-copy-template']);
});

test('communication hall sorts by latest and hot score', () => {
  expect(filterCommunicationPosts(communicationPosts, { sortMode: 'latest' })[0].id).toBe('short-drama-editing-team');
  expect(filterCommunicationPosts(communicationPosts, { sortMode: 'hot' })[0].id).toBe('rag-or-finetune');
});

test('communication hall validates and creates local draft posts', () => {
  expect(validateCommunicationDraft(createCommunicationDraft())).toEqual({
    title: '请输入标题',
    body: '请输入正文'
  });

  const post = createCommunicationPost(
    { categoryKey: 'resource', title: '新算力券资料', body: '整理申请清单和预算表。' },
    new Date('2026-05-12T08:00:00Z')
  );

  expect(post).toMatchObject({
    id: 'local-1778572800000',
    categoryKey: 'resource',
    title: '新算力券资料',
    summary: '整理申请清单和预算表。',
    timeLabel: '刚刚'
  });
  expect(post.tags).toContain('资源对接');
});

test('communication hall detail links use the shared detail contract', () => {
  expect(buildCommunicationDetailPath('tool-benefits-v14')).toBe('/communication/detail/tool-benefits-v14');
  expect(buildCommunicationDetailPath(communicationPosts[0])).toBe('/communication/detail/short-drama-editing-team');
});

test('communication hall normalizes backend payloads and preserves detail paths', () => {
  const payload = normalizeCommunicationHallPayload({
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
        mark: '聊',
        tone: 'talk',
        title: 'RAG project notes',
        summary: 'First version',
        comments: 1,
        views: 2,
        view_label: '2',
        time_label: '刚刚',
        timestamp: 1778572800000,
        tags: ['RAG'],
        actions: [{ key: 'read', label: '查看正文', tone: 'blue', kind: 'detail' }],
        is_favorite: true
      }
    ]
  });

  expect(payload.hotTags).toEqual(['RAG']);
  expect(payload.posts[0]).toMatchObject({
    id: 'rag-project-notes',
    itemId: 'rag-project-notes',
    detailPath: '/communication/detail/rag-project-notes',
    categoryKey: 'talk',
    isFavorite: true
  });
  expect(buildCommunicationDetailPath(payload.posts[0])).toBe('/communication/detail/rag-project-notes');
});

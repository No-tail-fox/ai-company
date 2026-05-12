export type CommunicationSortMode = 'latest' | 'hot';
export type CommunicationPostTone = 'order' | 'template' | 'talk' | 'resource' | 'pitch';
export type CommunicationActionKind = 'detail' | 'copy' | 'favorite' | 'follow';

export interface CommunicationHallCategory {
  key: string;
  label: string;
}

export interface CommunicationHallAction {
  key: string;
  label: string;
  tone: 'blue' | 'pink';
  kind: CommunicationActionKind;
}

export interface CommunicationHallPost {
  id: string;
  itemId?: string;
  detailPath?: string;
  categoryKey: string;
  categoryLabel: string;
  badgeLabel: string;
  mark: string;
  tone: CommunicationPostTone;
  title: string;
  summary: string;
  replyStrip?: string;
  comments: number;
  views: number;
  viewLabel: string;
  timeLabel: string;
  timestamp: number;
  pinned?: boolean;
  tags: string[];
  actions: CommunicationHallAction[];
  templateText?: string;
  isFavorite?: boolean;
}

export interface CommunicationHallDraft {
  categoryKey: string;
  title: string;
  body: string;
}

export interface CommunicationHallPayload {
  categories: CommunicationHallCategory[];
  hotTags: string[];
  hotTopics: Array<{ title: string; count: number }>;
  posts: CommunicationHallPost[];
}

export interface CommunicationHallPostCreateRequest {
  categoryKey: string;
  title: string;
  bodyMarkdown: string;
}

export interface CommunicationHallPostResponse {
  post: CommunicationHallPost;
  detailPath: string;
}

export interface CommunicationFilterOptions {
  query?: string;
  categoryKey?: string;
  tag?: string;
  favoritesOnly?: boolean;
  favoriteIds?: Set<string>;
  sortMode?: CommunicationSortMode;
}

export const communicationCategories: CommunicationHallCategory[] = [
  { key: 'all', label: '全部' },
  { key: 'order', label: '接单' },
  { key: 'template', label: '模板' },
  { key: 'talk', label: '交流' },
  { key: 'benefit', label: '工具权益' },
  { key: 'resource', label: '资源对接' },
  { key: 'pitch', label: '项目路演' },
  { key: 'local-order', label: '本地订单' },
  { key: 'short-drama', label: 'AI 短剧' },
  { key: 'ecommerce', label: '电商运营' }
];

export const communicationHotTags = ['AI短剧', '接单报价', '模板包', '工具权益', '算力券', '本地订单', '合同经验'];

export const communicationHotTopics = [
  { title: 'AI 客服 Demo 怎么报价', count: 52 },
  { title: '工具权益失效反馈', count: 34 },
  { title: '短剧剪辑交付规范', count: 28 },
  { title: 'OPC 合同主体经验', count: 21 }
];

const baseTime = Date.UTC(2026, 4, 12, 3, 20, 0);

export const communicationPosts: CommunicationHallPost[] = [
  post({
    id: 'short-drama-editing-team',
    categoryKey: 'order',
    badgeLabel: '接单',
    mark: '接',
    tone: 'order',
    title: '寻找 AI 短剧剪辑团队，20 条口播混剪，3 天交付',
    summary: '预算 3000-5000，需提供过往案例；可在帖子下方报价并补充交付周期。',
    comments: 18,
    views: 246,
    viewLabel: '246',
    timeLabel: '2 分钟前',
    timestamp: baseTime,
    tags: ['AI短剧', '接单报价', '短剧剪辑'],
    actions: [
      { key: 'quote', label: '我要报价', tone: 'blue', kind: 'detail' },
      { key: 'requirement', label: '查看需求', tone: 'pink', kind: 'detail' }
    ]
  }),
  post({
    id: 'ecommerce-detail-template',
    categoryKey: 'template',
    badgeLabel: '模板',
    mark: '模',
    tone: 'template',
    title: '上新：AI 电商详情页提示词模板包',
    summary: '包含主图卖点、详情页结构、短视频脚本三类 Markdown 模板，可复制后改写。',
    comments: 34,
    views: 1200,
    viewLabel: '1.2k',
    timeLabel: '置顶',
    timestamp: baseTime - 10 * 60 * 1000,
    pinned: true,
    tags: ['模板包', '电商运营', 'Markdown'],
    actions: [
      { key: 'copy-template', label: '获取模板', tone: 'blue', kind: 'copy' },
      { key: 'favorite', label: '收藏', tone: 'pink', kind: 'favorite' }
    ],
    templateText: '# AI 电商详情页提示词模板包\n\n请按主图卖点、详情页结构、短视频脚本输出可直接改写的 Markdown。'
  }),
  post({
    id: 'rag-or-finetune',
    categoryKey: 'talk',
    badgeLabel: '交流',
    mark: '聊',
    tone: 'talk',
    title: '大家现在做企业知识库，选 RAG 还是微调？',
    summary: '想听听本地企业项目的实际经验：成本、交付周期、后期维护分别怎么控。',
    replyStrip: '最新回复：先做 RAG，合同里把数据清洗和验收标准写清楚。',
    comments: 52,
    views: 908,
    viewLabel: '908',
    timeLabel: '12 分钟前',
    timestamp: baseTime - 12 * 60 * 1000,
    tags: ['RAG', '企业知识库', '项目交付'],
    actions: []
  }),
  post({
    id: 'tool-benefits-v14',
    categoryKey: 'benefit',
    badgeLabel: '资源',
    mark: '资',
    tone: 'resource',
    title: '工具优惠合集 v1.4：模型、剪辑、设计权益更新',
    summary: '正文使用 Markdown 渲染，失效链接可在评论区反馈，管理员每周统一更新。',
    comments: 23,
    views: 768,
    viewLabel: '768',
    timeLabel: '今天',
    timestamp: baseTime - 42 * 60 * 1000,
    tags: ['工具权益', '资源对接', 'Markdown'],
    actions: [
      { key: 'read', label: '查看正文', tone: 'blue', kind: 'detail' },
      { key: 'invalid', label: '反馈失效', tone: 'pink', kind: 'detail' }
    ]
  }),
  post({
    id: 'local-customer-service-demo',
    categoryKey: 'local-order',
    badgeLabel: '本地订单',
    mark: '单',
    tone: 'order',
    title: '本地商贸企业需要 AI 客服知识库 Demo',
    summary: '希望一周内出可演示版本，包含 FAQ 导入、问答记录、转人工规则。',
    replyStrip: '报价区开放：请附技术方案、交付物和后续维护费用。',
    comments: 9,
    views: 312,
    viewLabel: '312',
    timeLabel: '36 分钟前',
    timestamp: baseTime - 36 * 60 * 1000,
    tags: ['本地订单', '接单报价', '企业知识库'],
    actions: []
  }),
  post({
    id: 'poster-copy-template',
    categoryKey: 'template',
    badgeLabel: '模板',
    mark: '稿',
    tone: 'template',
    title: '招商海报文案模板：适合园区、联盟、路演',
    summary: '支持按「主标题 / 六大权益 / 入驻条件 / 联系方式」快速生成。',
    comments: 16,
    views: 650,
    viewLabel: '650',
    timeLabel: '昨天',
    timestamp: baseTime - 24 * 60 * 60 * 1000,
    tags: ['模板包', '项目路演', '电商运营'],
    actions: [
      { key: 'copy-template', label: '复制模板', tone: 'blue', kind: 'copy' },
      { key: 'edit', label: '二次编辑', tone: 'pink', kind: 'detail' }
    ],
    templateText: '# 招商海报文案模板\n\n主标题：\n六大权益：\n入驻条件：\n联系方式：'
  }),
  post({
    id: 'opc-contract-subject',
    categoryKey: 'talk',
    badgeLabel: '交流',
    mark: '问',
    tone: 'talk',
    title: 'OPC 公司做 AI 接单，合同主体怎么写更稳？',
    summary: '欢迎法务、财税和有实际接单经验的伙伴补充注意事项。',
    replyStrip: '管理员提醒：不要在公开评论区发布客户隐私和未脱敏合同。',
    comments: 41,
    views: 1000,
    viewLabel: '1.0k',
    timeLabel: '2 天前',
    timestamp: baseTime - 2 * 24 * 60 * 60 * 1000,
    tags: ['合同经验', '接单报价', '法务'],
    actions: []
  }),
  post({
    id: 'compute-voucher-materials',
    categoryKey: 'resource',
    badgeLabel: '资源对接',
    mark: '算',
    tone: 'resource',
    title: '算力券申请材料清单，有没有可复用版本？',
    summary: '征集申请材料、项目说明、预算表模板，沉淀成社区共享资料。',
    comments: 27,
    views: 540,
    viewLabel: '540',
    timeLabel: '3 天前',
    timestamp: baseTime - 3 * 24 * 60 * 60 * 1000,
    tags: ['算力券', '资源对接', '模板包'],
    actions: [
      { key: 'contribute', label: '贡献资料', tone: 'blue', kind: 'detail' },
      { key: 'follow', label: '关注更新', tone: 'pink', kind: 'follow' }
    ]
  }),
  post({
    id: 'roadshow-next-week',
    categoryKey: 'pitch',
    badgeLabel: '路演',
    mark: '演',
    tone: 'order',
    title: '下周项目路演征集：AI 短剧、电商、工具类优先',
    summary: '报名后在评论区提交一句话介绍、Demo 链接和需要对接的资源。',
    comments: 12,
    views: 388,
    viewLabel: '388',
    timeLabel: '本周',
    timestamp: baseTime - 4 * 24 * 60 * 60 * 1000,
    tags: ['AI短剧', '项目路演', '电商运营'],
    actions: [
      { key: 'signup', label: '我要报名', tone: 'blue', kind: 'detail' },
      { key: 'rules', label: '查看规则', tone: 'pink', kind: 'detail' }
    ]
  })
];

export function createCommunicationDraft(): CommunicationHallDraft {
  return {
    categoryKey: 'order',
    title: '',
    body: ''
  };
}

export function validateCommunicationDraft(draft: CommunicationHallDraft): Partial<Record<keyof CommunicationHallDraft, string>> {
  const errors: Partial<Record<keyof CommunicationHallDraft, string>> = {};
  if (!draft.title.trim()) {
    errors.title = '请输入标题';
  }
  if (!draft.body.trim()) {
    errors.body = '请输入正文';
  }
  return errors;
}

export function createCommunicationPost(draft: CommunicationHallDraft, now = new Date()): CommunicationHallPost {
  const category = communicationCategories.find((item) => item.key === draft.categoryKey) ?? communicationCategories[1];
  const timestamp = now.getTime();
  return post({
    id: `local-${timestamp}`,
    categoryKey: category.key === 'all' ? 'order' : category.key,
    badgeLabel: category.key === 'all' ? '接单' : category.label,
    mark: category.label.slice(0, 1) || '发',
    tone: toneForCategory(category.key),
    title: draft.title.trim(),
    summary: draft.body.trim(),
    comments: 0,
    views: 1,
    viewLabel: '1',
    timeLabel: '刚刚',
    timestamp,
    tags: [category.label, '用户发布'].filter((item) => item !== '全部'),
    actions: [
      { key: 'read', label: '查看正文', tone: 'blue', kind: 'detail' },
      { key: 'favorite', label: '收藏', tone: 'pink', kind: 'favorite' }
    ]
  });
}

export function filterCommunicationPosts(posts: CommunicationHallPost[], options: CommunicationFilterOptions = {}): CommunicationHallPost[] {
  const query = options.query?.trim().toLowerCase() ?? '';
  const categoryKey = options.categoryKey && options.categoryKey !== 'all' ? options.categoryKey : '';
  const tag = options.tag?.trim() ?? '';
  const favoriteIds = options.favoriteIds ?? new Set<string>();
  const filtered = posts.filter((postItem) => {
    const matchesQuery =
      !query ||
      [postItem.title, postItem.summary, postItem.categoryLabel, postItem.badgeLabel, ...postItem.tags]
        .join(' ')
        .toLowerCase()
        .includes(query);
    const matchesCategory = !categoryKey || postItem.categoryKey === categoryKey;
    const matchesTag = !tag || postItem.tags.includes(tag);
    const matchesFavorite = !options.favoritesOnly || favoriteIds.has(postItem.id);
    return matchesQuery && matchesCategory && matchesTag && matchesFavorite;
  });

  return filtered.sort((left, right) => {
    if (options.sortMode === 'hot') {
      return hotScore(right) - hotScore(left);
    }
    return right.timestamp - left.timestamp;
  });
}

export function buildCommunicationDetailPath(postOrId: CommunicationHallPost | string): string {
  if (typeof postOrId !== 'string' && postOrId.detailPath) {
    return postOrId.detailPath;
  }
  const id = typeof postOrId === 'string' ? postOrId : postOrId.id;
  return `/communication/detail/${encodeURIComponent(id)}`;
}

export function createFallbackCommunicationHallPayload(): CommunicationHallPayload {
  return {
    categories: [...communicationCategories],
    hotTags: [...communicationHotTags],
    hotTopics: communicationHotTopics.map((topic) => ({ ...topic })),
    posts: communicationPosts.map((postItem) => ({ ...postItem, actions: [...postItem.actions], tags: [...postItem.tags] }))
  };
}

export function normalizeCommunicationHallPayload(payload: any): CommunicationHallPayload {
  return {
    categories: normalizeCategories(payload?.categories),
    hotTags: normalizeStringList(payload?.hot_tags ?? payload?.hotTags, communicationHotTags),
    hotTopics: normalizeHotTopics(payload?.hot_topics ?? payload?.hotTopics),
    posts: Array.isArray(payload?.posts) ? payload.posts.map(normalizeCommunicationHallPost) : [...communicationPosts]
  };
}

export function normalizeCommunicationHallPost(payload: any): CommunicationHallPost {
  const categoryKey = String(payload?.category_key ?? payload?.categoryKey ?? 'talk');
  const categoryLabel = String(payload?.category_label ?? payload?.categoryLabel ?? categoryLabelFor(categoryKey));
  const badgeLabel = String(payload?.badge_label ?? payload?.badgeLabel ?? categoryLabel);
  const timestampValue = Number(payload?.timestamp ?? Date.now());
  return post({
    id: String(payload?.id ?? payload?.item_id ?? payload?.itemId ?? `post-${timestampValue}`),
    itemId: String(payload?.item_id ?? payload?.itemId ?? payload?.id ?? ''),
    detailPath: String(payload?.detail_path ?? payload?.detailPath ?? ''),
    categoryKey,
    categoryLabel,
    badgeLabel,
    mark: String(payload?.mark ?? categoryLabel.slice(0, 1) ?? '帖'),
    tone: normalizeTone(payload?.tone),
    title: String(payload?.title ?? ''),
    summary: String(payload?.summary ?? ''),
    replyStrip: String(payload?.reply_strip ?? payload?.replyStrip ?? ''),
    comments: Number(payload?.comments ?? 0),
    views: Number(payload?.views ?? 0),
    viewLabel: String(payload?.view_label ?? payload?.viewLabel ?? payload?.views ?? '0'),
    timeLabel: String(payload?.time_label ?? payload?.timeLabel ?? '刚刚'),
    timestamp: Number.isFinite(timestampValue) ? timestampValue : Date.now(),
    pinned: Boolean(payload?.pinned),
    tags: normalizeStringList(payload?.tags, []),
    actions: normalizeActions(payload?.actions),
    templateText: String(payload?.template_text ?? payload?.templateText ?? ''),
    isFavorite: Boolean(payload?.is_favorite ?? payload?.isFavorite)
  });
}

function post(payload: Omit<CommunicationHallPost, 'categoryLabel'> & { categoryLabel?: string }): CommunicationHallPost {
  const category = communicationCategories.find((item) => item.key === payload.categoryKey);
  return {
    ...payload,
    categoryLabel: payload.categoryLabel ?? category?.label ?? payload.badgeLabel
  };
}

function hotScore(postItem: CommunicationHallPost): number {
  return postItem.comments * 20 + postItem.views;
}

function toneForCategory(categoryKey: string): CommunicationPostTone {
  if (categoryKey === 'template') {
    return 'template';
  }
  if (categoryKey === 'talk') {
    return 'talk';
  }
  if (categoryKey === 'benefit' || categoryKey === 'resource') {
    return 'resource';
  }
  if (categoryKey === 'pitch') {
    return 'pitch';
  }
  return 'order';
}

function categoryLabelFor(categoryKey: string): string {
  return communicationCategories.find((category) => category.key === categoryKey)?.label ?? '交流';
}

function normalizeCategories(value: any): CommunicationHallCategory[] {
  if (!Array.isArray(value) || value.length === 0) {
    return [...communicationCategories];
  }
  return value.map((category) => ({
    key: String(category?.key ?? ''),
    label: String(category?.label ?? category?.key ?? '')
  })).filter((category) => category.key && category.label);
}

function normalizeHotTopics(value: any): Array<{ title: string; count: number }> {
  if (!Array.isArray(value) || value.length === 0) {
    return communicationHotTopics.map((topic) => ({ ...topic }));
  }
  return value.map((topic) => ({
    title: String(topic?.title ?? ''),
    count: Number(topic?.count ?? 0)
  })).filter((topic) => topic.title);
}

function normalizeStringList(value: any, fallback: string[]): string[] {
  if (!Array.isArray(value)) {
    return [...fallback];
  }
  return value.map((item) => String(item)).filter(Boolean);
}

function normalizeActions(value: any): CommunicationHallAction[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((action): CommunicationHallAction => ({
    key: String(action?.key ?? ''),
    label: String(action?.label ?? ''),
    tone: action?.tone === 'pink' ? 'pink' : 'blue',
    kind: normalizeActionKind(action?.kind)
  })).filter((action) => action.key && action.label);
}

function normalizeActionKind(value: any): CommunicationActionKind {
  return value === 'copy' || value === 'favorite' || value === 'follow' ? value : 'detail';
}

function normalizeTone(value: any): CommunicationPostTone {
  return value === 'template' || value === 'talk' || value === 'resource' || value === 'pitch' ? value : 'order';
}

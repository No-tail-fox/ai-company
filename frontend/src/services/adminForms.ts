import type {
  PageConfigSummary,
  PortalItem,
  PortalSection
} from './viewModel';

export interface EditableProviderChannel {
  channelKey: string;
  displayName: string;
  baseUrl: string;
  apiKey: string;
  channelType: string;
  adapterType?: string;
  priority: number;
  enabled: boolean;
  timeoutSeconds: number;
  presetKey?: string;
  remark?: string;
  website?: string;
  useFullUrl?: boolean;
  authJsonText?: string;
  configTomlText?: string;
  writeCommonConfig?: boolean;
  testConfigText?: string;
  billingConfigText?: string;
  metadataJson?: Record<string, unknown>;
}

export interface EditableModelConfig {
  modelKey: string;
  displayName: string;
  capability: string;
  channelId: string;
  providerModel: string;
  defaultPointCost: number;
  enabled: boolean;
  useMillionContextWindow?: boolean;
  compressionThreshold?: number;
  testConfigText?: string;
  billingConfigText?: string;
  metadataJson?: Record<string, unknown>;
}

export interface EditableToolModelBinding {
  targetType: string;
  targetKey: string;
  modelConfigId: string;
  pointCostOverride?: number | string | null;
  enabled: boolean;
}

export interface EditablePage extends Partial<PageConfigSummary> {
  pageKey: string;
  label: string;
  title: string;
}

export interface EditableSection extends Partial<PortalSection> {
  pageKey: string;
  sectionKey: string;
  title: string;
  layout: string;
}

export interface EditableItem extends Partial<PortalItem> {
  sectionId: string;
  itemType: string;
  title: string;
  actionValue: string;
  detailSummary?: string;
  detailHighlightsText?: string;
  detailStepsText?: string;
  detailDeliverablesText?: string;
  detailFaqsText?: string;
  detailPrimaryActionKey?: string;
  detailPrimaryActionLabel?: string;
  detailSecondaryActionsText?: string;
  detailDownloadFileName?: string;
  detailDownloadUrl?: string;
}

export interface EditableHomeSlide {
  title: string;
  subtitle: string;
  badge: string;
  ctaLabel: string;
  ctaSubtitle?: string;
  imageUrl?: string;
  actionType?: string;
  actionValue: string;
  sortOrder?: number;
  enabled?: boolean;
  metadataJson?: Record<string, unknown>;
}

export function buildPagePayload(page: EditablePage) {
  return {
    page_key: page.pageKey,
    label: page.label,
    title: page.title,
    subtitle: page.subtitle ?? '',
    icon: page.icon ?? 'Sparkles',
    sort_order: page.sortOrder ?? 100,
    enabled: page.enabled ?? true
  };
}

export function buildSectionPayload(section: EditableSection) {
  return {
    page_key: section.pageKey,
    section_key: section.sectionKey,
    title: section.title,
    subtitle: section.subtitle ?? '',
    layout: section.layout,
    sort_order: section.sortOrder ?? 100,
    enabled: section.enabled ?? true
  };
}

export function buildItemPayload(item: EditableItem) {
  const metadata = buildDetailMetadata(item);
  return {
    section_id: item.sectionId,
    item_type: item.itemType,
    title: item.title,
    subtitle: item.subtitle ?? '',
    category: item.category ?? '',
    icon: item.icon ?? 'Sparkles',
    image_url: item.imageUrl ?? '',
    badge: item.badge ?? '',
    tags: item.tags ?? [],
    sort_order: item.sortOrder ?? 100,
    enabled: item.enabled ?? true,
    action_type: item.actionType ?? 'route',
    action_value: item.actionValue,
    required_membership: item.requiredMembership ?? false,
    point_cost: item.pointCost ?? 0,
    ...(metadata ? { metadata_json: metadata } : {})
  };
}

export function buildHomeSlidePayload(slide: EditableHomeSlide) {
  return {
    title: slide.title,
    subtitle: slide.subtitle ?? '',
    badge: slide.badge ?? '',
    cta_label: slide.ctaLabel,
    cta_subtitle: slide.ctaSubtitle ?? '',
    image_url: slide.imageUrl ?? '',
    action_type: slide.actionType ?? 'route',
    action_value: slide.actionValue,
    sort_order: slide.sortOrder ?? 100,
    enabled: slide.enabled ?? true,
    metadata_json: slide.metadataJson ?? {}
  };
}

function buildProviderChannelMetadata(channel: EditableProviderChannel) {
  const metadata = { ...(channel.metadataJson ?? {}) };
  setMetadataText(metadata, 'preset_key', channel.presetKey);
  setMetadataText(metadata, 'remark', channel.remark);
  setMetadataText(metadata, 'website', channel.website);
  setMetadataBoolean(metadata, 'use_full_url', channel.useFullUrl);
  setMetadataText(metadata, 'auth_json', channel.authJsonText);
  setMetadataText(metadata, 'config_toml', channel.configTomlText);
  setMetadataBoolean(metadata, 'write_common_config', channel.writeCommonConfig);
  setMetadataText(metadata, 'test_config', channel.testConfigText);
  setMetadataText(metadata, 'billing_config', channel.billingConfigText);
  return Object.keys(metadata).length > 0 ? metadata : null;
}

function buildModelConfigMetadata(model: EditableModelConfig) {
  const metadata = { ...(model.metadataJson ?? {}) };
  setMetadataBoolean(metadata, 'use_million_context_window', model.useMillionContextWindow);
  setMetadataNumber(metadata, 'compression_threshold', model.compressionThreshold);
  setMetadataText(metadata, 'test_config', model.testConfigText);
  setMetadataText(metadata, 'billing_config', model.billingConfigText);
  return Object.keys(metadata).length > 0 ? metadata : null;
}

function buildDetailMetadata(item: EditableItem) {
  const existing = item.metadata && typeof item.metadata === 'object' ? item.metadata : {};
  const hasExistingMetadata = Object.keys(existing).length > 0;
  const hasDetailFields = [
    item.detailSummary,
    item.detailHighlightsText,
    item.detailStepsText,
    item.detailDeliverablesText,
    item.detailFaqsText,
    item.detailPrimaryActionKey,
    item.detailPrimaryActionLabel,
    item.detailSecondaryActionsText,
    item.detailDownloadFileName,
    item.detailDownloadUrl
  ].some((value) => cleanText(value).length > 0);
  if (!hasExistingMetadata && !hasDetailFields) {
    return null;
  }
  const primaryKey = cleanText(item.detailPrimaryActionKey) || defaultPrimaryActionKey(item);
  const primaryLabel = cleanText(item.detailPrimaryActionLabel) || defaultPrimaryActionLabel(primaryKey);
  const downloadFileName = cleanText(item.detailDownloadFileName);
  const downloadUrl = cleanText(item.detailDownloadUrl);
  return {
    ...existing,
    detail: {
      ...((existing as any).detail ?? {}),
      summary: cleanText(item.detailSummary),
      highlights: splitLines(item.detailHighlightsText),
      steps: splitLines(item.detailStepsText),
      deliverables: splitLines(item.detailDeliverablesText),
      faqs: parseFaqs(item.detailFaqsText),
      primaryAction: { key: primaryKey, label: primaryLabel },
      secondaryActions: parseSecondaryActions(item.detailSecondaryActionsText),
      download: downloadFileName || downloadUrl ? { fileName: downloadFileName, url: downloadUrl } : null
    }
  };
}

function cleanText(value?: string) {
  return String(value ?? '').trim();
}

function setMetadataText(metadata: Record<string, unknown>, key: string, value?: string) {
  const text = cleanText(value);
  if (text) {
    metadata[key] = text;
  } else {
    delete metadata[key];
  }
}

function setMetadataBoolean(metadata: Record<string, unknown>, key: string, value: boolean | undefined) {
  if (value === undefined) {
    delete metadata[key];
    return;
  }
  metadata[key] = Boolean(value);
}

function setMetadataNumber(metadata: Record<string, unknown>, key: string, value: number | string | null | undefined) {
  if (value === undefined || value === null || value === '') {
    delete metadata[key];
    return;
  }
  const next = Number(value);
  if (Number.isFinite(next)) {
    metadata[key] = next;
  } else {
    delete metadata[key];
  }
}

function splitLines(value?: string) {
  return cleanText(value)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function parseFaqs(value?: string) {
  return splitLines(value).map((line) => {
    const [question, ...answerParts] = line.split('|');
    return {
      question: question.trim(),
      answer: answerParts.join('|').trim()
    };
  }).filter((faq) => faq.question || faq.answer);
}

function parseSecondaryActions(value?: string) {
  return splitLines(value).map((line) => {
    const [key, ...labelParts] = line.split('|');
    return {
      key: (key || 'favorite').trim(),
      label: (labelParts.join('|') || key || '收藏').trim()
    };
  });
}

function defaultPrimaryActionKey(item: EditableItem) {
  if (String(item.actionValue ?? '').includes('/resources')) {
    return 'download';
  }
  if (String(item.actionValue ?? '').includes('/community')) {
    return 'join';
  }
  return 'enroll';
}

function defaultPrimaryActionLabel(actionKey: string) {
  const labels: Record<string, string> = {
    download: '领取资料',
    join: '加入',
    enroll: '报名',
    backup: '开启备份'
  };
  return labels[actionKey] ?? '立即查看';
}

export function buildProviderChannelPayload(channel: EditableProviderChannel) {
  const metadata = buildProviderChannelMetadata(channel);
  return {
    channel_key: channel.channelKey,
    display_name: channel.displayName,
    base_url: channel.baseUrl,
    api_key: channel.apiKey,
    channel_type: channel.channelType,
    adapter_type: channel.adapterType ?? 'custom_http',
    priority: channel.priority,
    enabled: channel.enabled,
    timeout_seconds: channel.timeoutSeconds,
    ...(metadata ? { metadata_json: metadata } : {})
  };
}

export function buildModelConfigPayload(model: EditableModelConfig) {
  const metadata = buildModelConfigMetadata(model);
  return {
    model_key: model.modelKey,
    display_name: model.displayName,
    capability: model.capability,
    channel_id: model.channelId,
    provider_model: model.providerModel,
    default_point_cost: model.defaultPointCost,
    enabled: model.enabled,
    ...(metadata ? { metadata_json: metadata } : {})
  };
}

export function buildToolModelBindingPayload(binding: EditableToolModelBinding) {
  const pointCostOverride =
    binding.pointCostOverride === undefined ||
    binding.pointCostOverride === null ||
    binding.pointCostOverride === ''
      ? null
      : Number(binding.pointCostOverride);
  return {
    target_type: binding.targetType,
    target_key: binding.targetKey,
    model_config_id: binding.modelConfigId,
    point_cost_override: pointCostOverride,
    enabled: binding.enabled
  };
}

export function buildReorderPayload(records: Array<{ id: string }>, sectionId?: string) {
  return {
    ...(sectionId ? { section_id: sectionId } : {}),
    ordered_ids: records.map((record) => record.id)
  };
}

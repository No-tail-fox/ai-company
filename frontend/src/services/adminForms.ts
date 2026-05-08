import type { PageConfigSummary, PortalItem, PortalSection } from './viewModel';

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
    point_cost: item.pointCost ?? 0
  };
}

export function buildReorderPayload(records: Array<{ id: string }>, sectionId?: string) {
  return {
    ...(sectionId ? { section_id: sectionId } : {}),
    ordered_ids: records.map((record) => record.id)
  };
}

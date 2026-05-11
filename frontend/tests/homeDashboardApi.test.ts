import { afterEach, expect, test, vi } from 'vitest';
import {
  adminCreateHomeSlide,
  adminDeleteHomeSlide,
  adminListHomeSlides,
  adminReorderHomeSlides,
  fetchHomeDashboard
} from '../src/services/api';
import { buildHomeSlidePayload } from '../src/services/adminForms';

afterEach(() => {
  vi.unstubAllGlobals();
});

function mockFetchResponse(payload: unknown, ok = true) {
  return {
    ok,
    status: ok ? 200 : 500,
    json: async () => payload
  } as Response;
}

function mockWindowToken() {
  vi.stubGlobal('window', {
    localStorage: {
      getItem: () => 'admin-token',
      setItem: vi.fn(),
      removeItem: vi.fn()
    }
  });
}

test('home dashboard API fetches the dedicated endpoint and normalizes Chinese blocks', async () => {
  mockWindowToken();
  const fetchMock = vi.fn().mockResolvedValueOnce(
    mockFetchResponse({
      tenant_id: 'demo',
      page: { page_key: 'home', label: '首页', title: '中文首页', icon: 'Home' },
      hero_slides: [{ id: 'slide-vip', title: '会员活动限时特惠', cta_label: '立即开通', action_value: '/membership/benefits' }],
      kpi_cards: [{ id: 'today-new', label: '今日上新', value: '3', trend: '持续更新', icon: 'Sparkles' }],
      workbench_shortcuts: [],
      community_cards: [],
      tool_cards: []
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  const dashboard = await fetchHomeDashboard();

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/home/dashboard');
  expect(dashboard.heroSlides[0].ctaLabel).toBe('立即开通');
  expect(dashboard.heroSlides[0].actionValue).toBe('/membership/benefits');
});

test('admin home slide APIs use the dedicated carousel endpoints', async () => {
  mockWindowToken();
  const payload = buildHomeSlidePayload({
    title: '会员活动限时特惠',
    subtitle: '开通会员领取模板、社群和接单资料',
    badge: '会员专享',
    ctaLabel: '立即开通',
    ctaSubtitle: '查看权益',
    imageUrl: '/storage/home/vip.png',
    actionValue: '/membership/benefits',
    sortOrder: 10,
    enabled: true,
    metadataJson: { accent: 'gold' }
  });
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(mockFetchResponse({ slides: [{ id: 'slide-a', title: '模板上新', cta_label: '立即查看' }] }))
    .mockResolvedValueOnce(mockFetchResponse({ id: 'slide-b', title: '会员活动限时特惠', cta_label: '立即开通' }))
    .mockResolvedValueOnce(mockFetchResponse({ slides: [{ id: 'slide-b', sort_order: 10 }] }))
    .mockResolvedValueOnce(mockFetchResponse({ id: 'slide-b', enabled: false }));
  vi.stubGlobal('fetch', fetchMock);

  const slides = await adminListHomeSlides();
  const created = await adminCreateHomeSlide(payload);
  await adminReorderHomeSlides([{ id: 'slide-b' }]);
  const disabled = await adminDeleteHomeSlide('slide-b');

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/admin/home-slides');
  expect(slides[0].ctaLabel).toBe('立即查看');
  expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/admin/home-slides');
  expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string)).toMatchObject({
    cta_label: '立即开通',
    image_url: '/storage/home/vip.png',
    action_value: '/membership/benefits',
    metadata_json: { accent: 'gold' }
  });
  expect(created.title).toBe('会员活动限时特惠');
  expect(fetchMock.mock.calls[2][0]).toBe('/api/v1/admin/home-slides/reorder');
  expect(JSON.parse(fetchMock.mock.calls[2][1]?.body as string)).toEqual({ ordered_ids: ['slide-b'] });
  expect(fetchMock.mock.calls[3][0]).toBe('/api/v1/admin/home-slides/slide-b');
  expect(disabled.enabled).toBe(false);
});

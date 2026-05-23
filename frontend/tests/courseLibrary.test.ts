import { expect, test, vi, afterEach } from 'vitest';
import { adminCleanupCourses, adminListCourses, fetchCourses } from '../src/services/api';
import routerSource from '../src/router.ts?raw';
import homeDashboardSource from '../src/components/HomeDashboardPage.vue?raw';
import courseLibrarySource from '../src/components/CourseLibraryPage.vue?raw';
import adminViewSource from '../src/views/AdminView.vue?raw';

function mockFetchResponse(payload: any) {
  return {
    ok: true,
    json: async () => payload
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubLocalStorage(values: Record<string, string> = {}) {
  const store = new Map(Object.entries(values));
  vi.stubGlobal('window', {
    localStorage: {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      }
    }
  });
}

test('courses API sends search filters and normalizes payload', async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    mockFetchResponse({
      total: 1,
      page: 1,
      page_size: 20,
      categories: ['实操复盘'],
      items: [
        {
          id: 'course-1',
          title: '小红书选品',
          subtitle: '选品摘要',
          category: '实操复盘',
          tags: ['2026年合集'],
          detail_path: '/learning/courses/node-1',
          required_membership: true,
          updated_at: '2026-05-20T00:00:00',
          source_path: ['2026年合集', '1月', '小红书选品']
        }
      ]
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  const payload = await fetchCourses({ query: '小红书', category: '实操复盘', page: 1, pageSize: 20 });

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/courses?q=%E5%B0%8F%E7%BA%A2%E4%B9%A6&category=%E5%AE%9E%E6%93%8D%E5%A4%8D%E7%9B%98&page=1&page_size=20');
  expect(payload.items[0].detailPath).toBe('/learning/courses/node-1');
  expect(payload.items[0].requiredMembership).toBe(true);
  expect(payload.items[0].sourcePath).toEqual(['2026年合集', '1月', '小红书选品']);
});

test('courses API uses the demo tenant header so imported courses are visible locally', async () => {
  const fetchMock = vi.fn().mockResolvedValue(mockFetchResponse({ total: 0, page: 1, page_size: 20, categories: [], items: [] }));
  vi.stubGlobal('fetch', fetchMock);

  await fetchCourses();

  const requestOptions = fetchMock.mock.calls[0][1] as RequestInit;
  expect((requestOptions.headers as Headers).get('X-Tenant-ID')).toBe('demo');
});

test('admin course APIs list and trigger cleanup with auth', async () => {
  stubLocalStorage({ opc_admin_token: 'admin-token' });
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(mockFetchResponse({ total: 1, page: 1, page_size: 50, categories: [], items: [{ id: 'course-1', dirty: true }] }))
    .mockResolvedValueOnce(mockFetchResponse({ scanned: 1, changed: 1, dirty_remaining: 0 }));
  vi.stubGlobal('fetch', fetchMock);

  await adminListCourses({ query: 'DeepSeek', page: 1, pageSize: 50 });
  await adminCleanupCourses();

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/admin/courses?q=DeepSeek&page=1&page_size=50');
  expect((fetchMock.mock.calls[0][1].headers as Headers).get('Authorization')).toBe('Bearer admin-token');
  expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/admin/courses/cleanup');
  expect(fetchMock.mock.calls[1][1].method).toBe('POST');
});

test('learning route renders the course library before detail catch-all', () => {
  const learningRouteIndex = routerSource.indexOf("path: '/learning'");
  const detailRouteIndex = routerSource.indexOf("path: '/learning/:detailPath");

  expect(learningRouteIndex).toBeGreaterThan(-1);
  expect(detailRouteIndex).toBeGreaterThan(-1);
  expect(learningRouteIndex).toBeLessThan(detailRouteIndex);
  expect(routerSource).toContain("CourseLibraryPage");
});

test('course library view contains search, category and pagination controls', () => {
  expect(courseLibrarySource).toContain('fetchCourses');
  expect(courseLibrarySource).toContain('course-search');
  expect(courseLibrarySource).toContain('category-filter');
  expect(courseLibrarySource).toContain('page-actions');
});

test('home dashboard all-learning link goes to the course library', () => {
  expect(homeDashboardSource).toContain("openDestination('route', '/learning')");
});

test('home dashboard fallback course directory card opens the course library', () => {
  expect(homeDashboardSource).toContain("'查看更多课程'");
  expect(homeDashboardSource).toContain("'ChevronRight', '/learning', 999");
  expect(homeDashboardSource).not.toContain("'/learning/daily'");
});

test('admin view exposes course management module and cleanup action', () => {
  expect(adminViewSource).toContain("key: 'courses'");
  expect(adminViewSource).toContain('adminCleanupCourses');
  expect(adminViewSource).toContain("activeModule === 'courses'");
});

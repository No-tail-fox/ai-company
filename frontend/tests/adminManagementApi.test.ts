import { afterEach, expect, test, vi } from 'vitest';
import {
  adminAdjustWallet,
  adminCreateMembershipPlan,
  adminCreateUser,
  adminGrantMembership,
  adminListAuditLogs,
  adminListMembershipPlans,
  adminListOverview,
  adminListUsers
} from '../src/services/api';

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

test('admin management APIs call SaaS back-office endpoints and normalize payloads', async () => {
  mockWindowToken();
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(
      mockFetchResponse({
        users: { total: 2, active: 2, admins: 1 },
        membership_plans: { total: 1, enabled: 1 },
        wallets: { total_balance: 1200, frozen_balance: 50 },
        recent_logs: [{ id: 'log-a', summary: '创建用户', actor_display_name: '管理员' }]
      })
    )
    .mockResolvedValueOnce(
      mockFetchResponse({
        users: [
          {
            id: 'user-a',
            phone: '13800000000',
            display_name: '演示用户',
            role: 'USER',
            status: 'ACTIVE',
            balance: 1200,
            frozen_balance: 50,
            membership_plan_name: 'VIP 月卡'
          }
        ]
      })
    )
    .mockResolvedValueOnce(mockFetchResponse({ id: 'user-b', display_name: '新成员', phone: '13700000000' }))
    .mockResolvedValueOnce(mockFetchResponse({ balance: 1500, frozen_balance: 50, transaction: { amount: 300 } }))
    .mockResolvedValueOnce(
      mockFetchResponse({
        plans: [{ id: 'plan-a', plan_key: 'vip_monthly', name: 'VIP 月卡', entitlements: ['assistant.vip'] }]
      })
    )
    .mockResolvedValueOnce(mockFetchResponse({ id: 'plan-b', plan_key: 'vip_quarterly', name: 'VIP 季卡' }))
    .mockResolvedValueOnce(mockFetchResponse({ id: 'membership-a', plan: { name: 'VIP 季卡' }, status: 'ACTIVE' }))
    .mockResolvedValueOnce(mockFetchResponse({ logs: [{ id: 'log-b', summary: '积分调整' }] }));
  vi.stubGlobal('fetch', fetchMock);

  const overview = await adminListOverview();
  const users = await adminListUsers();
  const createdUser = await adminCreateUser({ phone: '13700000000', displayName: '新成员', role: 'OPERATOR', status: 'ACTIVE' });
  const wallet = await adminAdjustWallet('user-a', { amount: 300, reason: '手工充值' });
  const plans = await adminListMembershipPlans();
  const createdPlan = await adminCreateMembershipPlan({ planKey: 'vip_quarterly', name: 'VIP 季卡', durationDays: 90 });
  const grant = await adminGrantMembership({ userId: 'user-b', planId: 'plan-b', durationDays: 60 });
  const logs = await adminListAuditLogs();

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/admin/overview');
  expect(overview.wallets.totalBalance).toBe(1200);
  expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/admin/users');
  expect(users[0].displayName).toBe('演示用户');
  expect(users[0].membershipPlanName).toBe('VIP 月卡');
  expect(JSON.parse(fetchMock.mock.calls[2][1]?.body as string)).toMatchObject({
    phone: '13700000000',
    display_name: '新成员',
    role: 'OPERATOR'
  });
  expect(createdUser.displayName).toBe('新成员');
  expect(fetchMock.mock.calls[3][0]).toBe('/api/v1/admin/wallets/user-a/adjust');
  expect(wallet.balance).toBe(1500);
  expect(fetchMock.mock.calls[4][0]).toBe('/api/v1/admin/membership-plans');
  expect(plans[0].planKey).toBe('vip_monthly');
  expect(JSON.parse(fetchMock.mock.calls[5][1]?.body as string)).toMatchObject({
    plan_key: 'vip_quarterly',
    duration_days: 90
  });
  expect(createdPlan.planKey).toBe('vip_quarterly');
  expect(JSON.parse(fetchMock.mock.calls[6][1]?.body as string)).toEqual({
    user_id: 'user-b',
    plan_id: 'plan-b',
    duration_days: 60
  });
  expect(grant.plan.name).toBe('VIP 季卡');
  expect(logs[0].summary).toBe('积分调整');
});

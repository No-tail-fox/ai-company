import { afterEach, expect, test, vi } from 'vitest';
import {
  adminCreateRedemptionBatch,
  adminDisableRedemptionCode,
  adminListRedemptionBatches,
  adminListRedemptionCodes,
  changePassword,
  clearUserSession,
  getUserSession,
  loginUser,
  redeemCode,
  registerUser,
  requestVerificationCode,
  resetPassword
} from '../src/services/api';

function mockFetchResponse(payload: unknown, ok = true) {
  return {
    ok,
    status: ok ? 200 : 500,
    json: async () => payload
  } as Response;
}

function mockWindowStorage(initial: Record<string, string> = {}) {
  const store = { ...initial };
  const dispatchEvent = vi.fn();
  vi.stubGlobal('window', {
    dispatchEvent,
    localStorage: {
      getItem: (key: string) => store[key] ?? '',
      setItem: (key: string, value: string) => {
        store[key] = value;
      },
      removeItem: (key: string) => {
        delete store[key];
      }
    }
  });
  return { store, dispatchEvent };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

test('user auth APIs post verification, register, login, reset, and change password payloads', async () => {
  const { store, dispatchEvent } = mockWindowStorage();
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(mockFetchResponse({ phone: '13800000001', purpose: 'REGISTER', dev_code: '123456' }))
    .mockResolvedValueOnce(
      mockFetchResponse({
        access_token: 'register-token',
        token_type: 'bearer',
        user: { id: 'user-a', tenant_id: 'demo', phone: '13800000001', display_name: 'New User', role: 'USER', status: 'ACTIVE' }
      })
    )
    .mockResolvedValueOnce(
      mockFetchResponse({
        access_token: 'login-token',
        token_type: 'bearer',
        user: { id: 'user-a', tenant_id: 'demo', phone: '13800000001', display_name: 'New User', role: 'USER', status: 'ACTIVE' }
      })
    )
    .mockResolvedValueOnce(
      mockFetchResponse({
        access_token: 'code-login-token',
        token_type: 'bearer',
        user: { id: 'user-a', tenant_id: 'demo', phone: '13800000001', display_name: 'New User', role: 'USER', status: 'ACTIVE' }
      })
    )
    .mockResolvedValueOnce(mockFetchResponse({ status: 'UPDATED' }))
    .mockResolvedValueOnce(mockFetchResponse({ status: 'UPDATED' }));
  vi.stubGlobal('fetch', fetchMock);

  await requestVerificationCode({ phone: '13800000001', purpose: 'REGISTER' });
  const registered = await registerUser({
    phone: '13800000001',
    password: 'user123456',
    displayName: 'New User',
    verificationCode: '123456'
  });
  const loggedIn = await loginUser({ phone: '13800000001', password: 'user123456', loginMethod: 'PASSWORD' });
  const codeLoggedIn = await loginUser({ phone: '13800000001', verificationCode: '123456', loginMethod: 'CODE' });
  await resetPassword({ phone: '13800000001', verificationCode: '123456', newPassword: 'reset123456' });
  await changePassword({ currentPassword: 'reset123456', newPassword: 'changed123456' });

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/auth/verification-codes');
  expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({ phone: '13800000001', purpose: 'REGISTER' });
  expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string)).toEqual({
    phone: '13800000001',
    password: 'user123456',
    display_name: 'New User',
    verification_code: '123456'
  });
  expect(JSON.parse(fetchMock.mock.calls[2][1]?.body as string)).toEqual({
    phone: '13800000001',
    password: 'user123456',
    login_method: 'PASSWORD'
  });
  expect(JSON.parse(fetchMock.mock.calls[3][1]?.body as string)).toEqual({
    phone: '13800000001',
    verification_code: '123456',
    login_method: 'CODE'
  });
  expect(JSON.parse(fetchMock.mock.calls[4][1]?.body as string)).toEqual({
    phone: '13800000001',
    verification_code: '123456',
    new_password: 'reset123456'
  });
  expect((fetchMock.mock.calls[5][1]?.headers as Headers).get('Authorization')).toBe('Bearer code-login-token');
  expect(JSON.parse(fetchMock.mock.calls[5][1]?.body as string)).toEqual({
    current_password: 'reset123456',
    new_password: 'changed123456'
  });
  expect(registered.user.displayName).toBe('New User');
  expect(loggedIn.accessToken).toBe('login-token');
  expect(codeLoggedIn.accessToken).toBe('code-login-token');
  expect(getUserSession()?.user.id).toBe('user-a');
  expect(store.opc_user_session).toContain('code-login-token');
  expect(dispatchEvent).toHaveBeenCalledWith(expect.objectContaining({ type: 'opc:user-session-changed' }));
  clearUserSession();
  expect(getUserSession()).toBeNull();
  expect(dispatchEvent).toHaveBeenCalledTimes(4);
});

test('redemption APIs use user token and admin code management endpoints', async () => {
  mockWindowStorage({
    opc_admin_token: 'admin-token',
    opc_user_session: JSON.stringify({
      accessToken: 'user-token',
      tokenType: 'bearer',
      user: { id: 'user-a', tenantId: 'demo', phone: '13800000001', displayName: 'New User', role: 'USER', status: 'ACTIVE' }
    })
  });
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(
      mockFetchResponse({
        status: 'REDEEMED',
        points_granted: 500,
        wallet: { balance: 600, frozen_balance: 0, currency: 'POINT' },
        membership: { active: true, plan: { id: 'plan-a', name: 'VIP' }, entitlements: ['assistant.vip'] },
        account_summary: {
          user: { id: 'user-a', tenant_id: 'demo', phone: '13800000001', display_name: 'New User', role: 'USER', status: 'ACTIVE' },
          wallet: { balance: 600, frozen_balance: 0, currency: 'POINT' },
          membership: { active: true, plan: { id: 'plan-a', name: 'VIP' }, entitlements: ['assistant.vip'] }
        }
      })
    )
    .mockResolvedValueOnce(mockFetchResponse({ batches: [{ id: 'batch-a', name: 'VIP bundle', generated_count: 2, redeemed_count: 1 }] }))
    .mockResolvedValueOnce(mockFetchResponse({ codes: [{ id: 'code-a', masked_code: '****ABC123', status: 'ACTIVE' }] }))
    .mockResolvedValueOnce(mockFetchResponse({ batch: { id: 'batch-b', name: 'New batch' }, codes: [{ id: 'code-b', code: 'RDM-ABCD' }] }))
    .mockResolvedValueOnce(mockFetchResponse({ id: 'code-a', status: 'DISABLED' }));
  vi.stubGlobal('fetch', fetchMock);

  const redemption = await redeemCode('rdm-abcd');
  const batches = await adminListRedemptionBatches();
  const codes = await adminListRedemptionCodes('batch-a');
  const generated = await adminCreateRedemptionBatch({
    name: 'New batch',
    quantity: 2,
    points: 500,
    membershipPlanId: 'plan-a',
    membershipDays: 30,
    expiresAt: '2026-06-01T00:00:00'
  });
  const disabled = await adminDisableRedemptionCode('code-a');

  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/redemptions/redeem');
  expect((fetchMock.mock.calls[0][1]?.headers as Headers).get('Authorization')).toBe('Bearer user-token');
  expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({ code: 'rdm-abcd' });
  expect(redemption.pointsGranted).toBe(500);
  expect(redemption.accountSummary.wallet.balance).toBe(600);
  expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/admin/redemption-batches?limit=100');
  expect(fetchMock.mock.calls[2][0]).toBe('/api/v1/admin/redemption-codes?batch_id=batch-a&limit=200');
  expect((fetchMock.mock.calls[3][1]?.headers as Headers).get('Authorization')).toBe('Bearer admin-token');
  expect(JSON.parse(fetchMock.mock.calls[3][1]?.body as string)).toEqual({
    name: 'New batch',
    quantity: 2,
    points: 500,
    membership_plan_id: 'plan-a',
    membership_days: 30,
    expires_at: '2026-06-01T00:00:00'
  });
  expect(fetchMock.mock.calls[4][0]).toBe('/api/v1/admin/redemption-codes/code-a');
  expect(batches[0].generatedCount).toBe(2);
  expect(codes[0].maskedCode).toBe('****ABC123');
  expect(generated.codes[0].code).toBe('RDM-ABCD');
  expect(disabled.status).toBe('DISABLED');
});

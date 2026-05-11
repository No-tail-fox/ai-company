/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import adminView from '../src/views/AdminView.vue?raw';
import authView from '../src/views/AuthView.vue?raw';
import portalChrome from '../src/components/PortalChrome.vue?raw';
import router from '../src/router.ts?raw';

test('auth view exposes register login reset and password flows', () => {
  expect(router).toContain("path: '/auth'");
  expect(authView).toContain('requestVerificationCode');
  expect(authView).toContain('registerUser');
  expect(authView).toContain('loginUser');
  expect(authView).toContain('resetPassword');
  expect(authView).toContain('loginMethod');
  expect(authView).toContain("'PASSWORD'");
  expect(authView).toContain("'CODE'");
  expect(authView).toContain("phone: '13800000000'");
  expect(authView).toContain("password: 'user123456'");
  expect(authView).toContain('verificationCode');
  expect(authView).toContain('confirmPassword');
});

test('portal account menu uses user session and redemption code actions', () => {
  expect(portalChrome).toContain('getUserSession');
  expect(portalChrome).toContain('clearUserSession');
  expect(portalChrome).toContain('userSessionChangedEvent');
  expect(portalChrome).toContain("window.addEventListener(userSessionChangedEvent");
  expect(portalChrome).toContain("window.removeEventListener(userSessionChangedEvent");
  expect(portalChrome).toContain('redeemCode');
  expect(portalChrome).toContain("accountPanel.value = 'redeem'");
  expect(portalChrome).toContain("accountPanel.value = 'password'");
  expect(portalChrome).toContain("router.push('/auth')");
  expect(portalChrome).toContain('兑换码');
});

test('admin view exposes redemption code management', () => {
  expect(adminView).toContain("'redemptions'");
  expect(adminView).toContain('adminCreateRedemptionBatch');
  expect(adminView).toContain('adminListRedemptionBatches');
  expect(adminView).toContain('adminDisableRedemptionCode');
  expect(adminView).toContain('兑换码管理');
  expect(adminView).toContain('批量生成');
});

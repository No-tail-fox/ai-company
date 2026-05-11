/// <reference types="vite/client" />

import { expect, test } from 'vitest';
import membershipBenefitsPage from '../src/components/MembershipBenefitsPage.vue?raw';
import routerSource from '../src/router.ts?raw';

test('membership benefits route uses a dedicated promotional page', () => {
  expect(routerSource).toContain('MembershipBenefitsPage');
  expect(routerSource).toContain("path: '/membership/benefits'");
  expect(routerSource).toContain('component: MembershipBenefitsPage');
  expect(routerSource.indexOf("path: '/membership/benefits'")).toBeLessThan(routerSource.indexOf("path: '/:detailPath(.*)*'"));
  expect(membershipBenefitsPage).toContain('membership-benefits-page');
  expect(membershipBenefitsPage).toContain('会员活动限时特惠');
  expect(membershipBenefitsPage).toContain('会员权益');
  expect(membershipBenefitsPage).toContain('模板上新');
  expect(membershipBenefitsPage).toContain('社群入口');
  expect(membershipBenefitsPage).toContain('fetchAccountSummary');
  expect(membershipBenefitsPage).toContain('fetchHomeDashboard');
});

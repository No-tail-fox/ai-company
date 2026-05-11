# Account And Redemption Findings

- Existing backend has `User`, `Wallet`, `MembershipPlan`, `UserMembership`, `PaymentOrder`, and wallet services, but no public register/reset/change-password or redemption-code models.
- Existing `/api/v1/auth/login` supports admin and normal users by password only; admin routes rely on bearer JWT and should stay compatible.
- Existing account endpoints use `user_id=demo-user` query/body defaults and do not authenticate ordinary users.
- Existing frontend stores only `opc_admin_token`; portal chrome always reads `demo-user`.
- Existing backend and frontend test baselines passed before implementation: backend 62 tests, frontend 84 tests.

# Account And Redemption Closure Plan

## Goal
Implement real user auth, profile/password flows, and redemption-code based membership/points fulfillment across the existing FastAPI + Vue app.

## Phases
- [ ] Phase 1: Add failing backend tests for auth, password, and redemption behavior.
- [ ] Phase 2: Implement backend schemas, models, services, and API routes.
- [ ] Phase 3: Add failing frontend API/component tests for auth and redemption flows.
- [ ] Phase 4: Implement frontend user session, account menu flows, auth page, and admin redemption management.
- [ ] Phase 5: Run full backend and frontend verification.

## Decisions
- Use phone + password + verification code for ordinary users.
- Keep admin login password-only compatible with existing admin routes.
- Verification sending is a placeholder using configured `OTP_DEFAULT_CODE`.
- Use external-platform redemption codes instead of direct payment integration.
- Redemption codes are single-use, case-insensitive, generated in admin, and can grant points, membership, or both.

## Errors Encountered
| Error | Attempt | Resolution |
|---|---:|---|

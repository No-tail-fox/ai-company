# Account And Redemption Progress

## 2026-05-11
- Started implementation from the user-approved plan.
- Confirmed repo is already on `codex/home-sidebar-menu` with unrelated dirty frontend changes; backend auth/account files are currently clean.
- Created task-specific planning files instead of overwriting older root planning files from a previous task.
- Added backend red tests for auth and redemption flows.
- Red verification: `.\.venv\Scripts\python.exe -m pytest tests\test_user_auth_flow.py tests\test_redemptions_api.py -q` failed with missing `/auth/verification-codes` and `/admin/redemption-batches` endpoints, as expected.
- Implemented backend auth and redemption services/routes.
- Backend verification: `.\.venv\Scripts\python.exe -m pytest -q` passed with 66 tests.

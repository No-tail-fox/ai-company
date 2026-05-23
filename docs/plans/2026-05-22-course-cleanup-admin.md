# Course Cleanup And Admin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore the course library entry, clean imported Feishu Markdown, and add a minimal admin course management surface.

**Architecture:** Keep courses inside the existing `ContentItem` and `PortalDetailDocument` model. Add a reusable Markdown sanitizer used by Feishu imports and a batch cleanup admin endpoint. Expose admin course list/cleanup APIs and wire a simple management panel into the existing admin view.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite, Vue 3, Vitest, pytest.

---

### Task 1: Restore Course Library Entry

**Files:**
- Modify: `frontend/src/components/HomeDashboardPage.vue`
- Test: `frontend/tests/courseLibrary.test.ts`

**Steps:**
1. Add a failing test that the home fallback "查看更多课程" card points to `/learning`.
2. Run `npm test -- courseLibrary.test.ts` in `frontend` and confirm the test fails.
3. Change the fallback route from `/learning/daily` to `/learning`.
4. Re-run the frontend course tests.

### Task 2: Markdown Sanitizer

**Files:**
- Create: `backend/app/services/content_sanitizer.py`
- Modify: `backend/app/services/feishu_import.py`
- Test: `backend/tests/test_feishu_import.py`

**Steps:**
1. Add tests for entity decoding, span/font/br cleanup, script/style/svg removal, image conversion, table conversion, zero-width removal, and batch cleanup.
2. Run the targeted pytest tests and confirm they fail because the sanitizer and admin cleanup API do not exist.
3. Implement the sanitizer and use it in both Feishu API sync and browser snapshot imports.
4. Add a cleanup service method to sanitize existing course documents and update metadata.
5. Re-run targeted backend tests.

### Task 3: Admin Course APIs

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/services/feishu_import.py`
- Test: `backend/tests/test_feishu_import.py`

**Steps:**
1. Add tests for `GET /api/v1/admin/courses` and `POST /api/v1/admin/courses/cleanup`.
2. Implement admin list and cleanup endpoints guarded by `CONTENT_EDITOR`.
3. Return cleanup statistics and dirty flags.
4. Re-run targeted backend tests.

### Task 4: Admin Course Panel

**Files:**
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/services/viewModel.ts`
- Modify: `frontend/src/views/AdminView.vue`
- Test: `frontend/tests/courseLibrary.test.ts`

**Steps:**
1. Add frontend tests checking admin API helpers and course module source.
2. Implement `adminListCourses` and `adminCleanupCourses`.
3. Add a `courses` admin module with search, refresh, cleanup, and course rows.
4. Re-run frontend tests and build if practical.

### Task 5: Verification

**Steps:**
1. Run `python -m pytest backend/tests/test_feishu_import.py -q`.
2. Run `npm test -- courseLibrary.test.ts` in `frontend`.
3. Run a local DB cleanup call or script, then re-check dirty pattern counts.
4. Use the in-app browser to verify `/learning`, `/home` entry, and `/admin` course management.

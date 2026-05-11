# 专有模型配置中心实现计划

## Goal
补齐前端对“模型库 + 工具绑定”的完整支持，包括 normalizer、管理端 payload、生成请求目标绑定，以及模型配置工作区 UI。

## Phases
- [x] Phase 1: 对齐后端返回形状与当前失败测试
- [x] Phase 2: 补齐 `viewModel.ts` 的模型/绑定 normalizer 与音视频任务 payload
- [x] Phase 3: 补齐 `adminForms.ts` 与 `api.ts` 的模型中心 payload/API
- [x] Phase 4: 改造 `ImagePage.vue`、`VideoPage.vue`、`AudioPage.vue` 的目标入口提交
- [x] Phase 5: 扩展 `AdminView.vue` 的模型配置工作区
- [x] Phase 6: 运行前端测试与 build 验证

## Decisions
- 工具级积分优先，模型默认积分兜底。
- 生成请求以 `target_type` + `target_id` 为准，`route_key` 只做兼容 fallback。
- 管理端 API Key 仅脱敏展示，空值更新不得覆盖旧密钥。

## Errors Encountered
| Error | Attempt | Resolution |
|---|---:|---|
| `session-catchup.py` 路径不存在 | 1 | 改为直接读取现有 diff 并继续 |

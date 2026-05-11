# Findings

- 后端已经提供 `provider-channels`、`model-configs`、`tool-model-bindings` 的管理接口。
- 后端 `model_context_for_target` 会给 portal/assistant/template 返回 `model_config` 与 `effective_point_cost`。
- 后端生成接口接受 `target_type` / `target_id`，并按绑定解析模型和积分。
- 前端当前缺口集中在：
  - `viewModel.ts` 未 normalize `effective_point_cost` / `model_config`
  - `buildAudioTaskPayload` 未写入 `target_type` / `target_id`
  - `api.ts` 仍使用旧的 image/video 生成签名
  - `adminForms.ts` 还没有模型中心 payload builders
  - `AdminView.vue` 还没有模型配置工作区
- 前端已补齐这些缺口，并通过 `npm test` 与 `npm run build` 验证。

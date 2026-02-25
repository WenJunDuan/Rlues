# Session Close

## 关闭目标
把本次执行中可复用信息沉淀为可检索上下文，避免原始冗长日志污染后续任务。

## 输入
- `task_id`
- `tenant_id`
- `operator_id`
- `result`（decision/summary/issues/evidence）
- `events`（可选）

## 回写流程
1. 提取最小摘要：
   - 决策结论
   - 关键 issue（最多 5 条）
   - 关键 evidence 引用（最多 5 条）
2. 压缩保存：
   - 原始大文本仅保留引用，不整体入库
   - 摘要限制在 500 字以内
3. 调用 `context_store.save_session` 写入会话与记忆。

## 失败策略
1. 上下文写入失败不应阻断主流程结果返回。
2. 写入失败需发出 `error` 和 `context_saved`（`ok=false`）事件。

## 事件
- 正常回写后发出 `context_saved`，包含 `session_id` 与 `memory_items`。

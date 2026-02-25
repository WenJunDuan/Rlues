# Session Init

## 初始化目标
在不突破上下文预算的前提下，为当前任务加载最相关信息。

## 输入
- `tenant_id`
- `operator_id`
- `task_id`
- `command`
- `payload`

## 加载流程
1. 先加载 L0（必需）：
   - 当前 `TaskEnvelope.payload`
   - 同 `task_id` 的执行中间状态（如存在）
2. 再尝试 L1（近期）：
   - 最近 3 条同 `tenant_id + operator_id` 会话摘要
   - 最近 1 条同 `command` 的审核结果摘要
3. 最后按需加载 L2（扩展）：
   - 规则版本摘要
   - 历史判例摘要（同业务域）

## 限流策略
1. L0 必载，不可裁剪。
2. L1 超预算时按时间逆序裁剪，保留最新。
3. L2 仅在命中关键词或显式需要时加载。

## 事件
- 成功加载后发出 `context_loaded`，包含 `level_hits` 和 `token_estimate`。

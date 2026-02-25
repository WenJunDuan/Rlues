# Context Strategy

统一上下文加载、检索与压缩策略入口。

## 目标
1. 保证同租户、同操作人会话可续审。
2. 控制上下文体积，避免无效 token 消耗。
3. 保证跨租户隔离，禁止上下文污染。

## 分层
- L0: 当前任务硬依赖上下文（task payload、最近结果摘要）。
- L1: 近期会话上下文（同 tenant/operator 最近 N 条）。
- L2: 低频知识与历史记忆（规则版本、历史判例摘要）。

## 文件分工
- `session-init.md`: 会话初始化与加载策略。
- `knowledge-access.md`: 知识访问优先级与租户边界。
- `memory-retrieval.md`: 记忆检索流程（keyword + semantic）。
- `session-close.md`: 会话结束时的压缩与回写策略。

## 边界
- 本目录定义策略，不直接访问外部系统。
- 具体读写由 `.claude/plugins/context_store.py` 承接。

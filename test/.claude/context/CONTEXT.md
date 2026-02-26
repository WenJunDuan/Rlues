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
- `session/init.md`: 会话初始化与加载策略。
- `knowledge/access.md`: 知识访问优先级与租户边界。
- `memory/retrieval.md`: 记忆检索流程（keyword + semantic）。
- `session/close.md`: 会话结束时的压缩与回写策略。

## 存储布局
- `MEMORY.md`: 索引层，只存核心信息和指向各层文件的索引。
- `memory/projects.md`: 项目层，记录项目当前状态与待办线索。
- `memory/infra.md`: 基础设施层，记录配置/地址等速查信息。
- `memory/lessons.md`: 教训层，按严重级别沉淀可复用经验。
- `memory/YYYY-MM-DD.md`: 日志层，记录每日变更与关键事件。

## 边界
- 本目录定义策略，不直接访问外部系统。
- 具体读写由 `.claude/plugins/context_store/main.py` 承接。

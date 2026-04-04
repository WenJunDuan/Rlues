# 工具调度规则

<important if="choosing tools, plugins, or delegating work">
按下表选择工具。不要猜测，按表执行。当首选工具不可用时，使用降级方案。

## 需求与设计阶段 (R₀ + R + D)

| 任务 | 首选工具 | 用法 | 降级方案 |
|------|---------|------|---------|
| 需求发散 | superpowers brainstorming | 自动激活: 开始分析需求时 superpowers 会接管 | 手动四步法 (定义→发散→追问→收敛) |
| 查库文档 | context7 | `npx ctx7 resolve {{库名}}` (bash) | 网络搜索 + 本地 node_modules |
| 搜索项目代码 | CC 内置 | Grep / Read 工具 | 无需降级 |
| 方案审查 | @evaluator | 委托 evaluator agent | `/review` (CC 内置) |
| 用户确认 | cunzhi MCP | DESIGN_READY 检查点 | 直接问用户 |

注意:
- superpowers 的 skills 会根据上下文自动激活, 不需要手动调用 slash 命令
- `/codex:adversarial-review` 只能审查已有代码变更, 设计阶段无代码时不要使用
- brainstorming 结果必须整理到 .ai_state/design.md (superpowers 可能写到别的位置)

## 执行阶段 (E) — 三级委托

| 级别 | 工具 | 用法 | 使用场景 | 降级触发 |
|------|------|------|---------|---------|
| **Level 1** | codex-plugin-cc | `/codex:rescue <task描述>` | 完整 Task 委托给 Codex | Codex 不可用或超时 |
| **Level 2** | @generator | `@generator 实现 Task X` | CC subagent 独立 worktree | @generator 失败 |
| **Level 3** | 主 Agent | 手动 TDD (先测试后实现) | 兜底方案 | 无降级 |

Level 1 详细用法:
- 委托: `/codex:rescue 实现用户登录功能，参照 design.md 验收标准`
- 查进度: `/codex:status`
- 取结果: `/codex:result`
- 取消: `/codex:cancel`
- 指定模型: `/codex:rescue --model gpt-5.4-mini --effort medium <task>`
- 后台执行: `/codex:rescue --background <task>` (推荐长任务使用)

## 审查阶段 (T)

| 任务 | 工具 | 命令 | 适用场景 |
|------|------|------|---------|
| 标准代码审查 | codex-plugin-cc | `/codex:review` | 所有 Path |
| 对抗审查 | codex-plugin-cc | `/codex:adversarial-review` | Path C+ 或风险区域 |
| 本地快速审查 | CC 内置 | `/review` | Path A 或快速检查 |
| 安全扫描 | ECC AgentShield | `npx ecc-agentshield scan` (bash) | Path C+ |
| 深度安全扫描 | ECC AgentShield | `npx ecc-agentshield scan --opus --stream` (bash) | 安全敏感项目 |
| 前端 E2E | playwright-skill | 按 skill 指引 | 有前端的项目 |
| 综合评分 | @evaluator | 委托 evaluator agent | Path B+ |

对抗审查聚焦方向 (可选参数):
- `/codex:adversarial-review challenge whether this was the right auth design`
- `/codex:adversarial-review look for race conditions`
- `/codex:adversarial-review --base main question the caching strategy`

## 归档阶段 (V)

| 任务 | 工具 |
|------|------|
| 更新项目规范 | 直接编辑 .ai_state/conventions.md |
| 记录教训 | 直接编辑 .ai_state/lessons.md |
| 重置状态 | 更新 .ai_state/state.json (stage → "", sprint +1) |
</important>

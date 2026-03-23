# VibeCoding Kernel v9.1.8

## 铁律 (违反即阻断交付)

1. **先搜后写** — augment-context-engine 搜项目代码 + context7/mcp-deepwiki 查库文档。不搜 = 不写
2. **先测后码** — 源码必须有对应测试。delivery-gate 用 git diff 检查。无测试 = 不交付
3. **寸止确认** — 设计/计划/交付前用 cunzhi MCP 人工确认。跳过 = 不交付

## 工作流入口

收到任务 → 读 .claude/workflows/pace.md 路由复杂度(A/B/C/D) → 按 riper-7.md 执行阶段

- Bug/error/crash/报错类需求 → 先激活 systematic-debugging skill
- .ai_state/ 存在且有未完成任务 → 先恢复断点 (读 status.md + plan.md)

## 框架地图

| 类别     | 位置                           | 说明                                                                                                                                                                                                     |
| -------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 工作流   | workflows/pace.md + riper-7.md | 路由 + 阶段编排(含 Sisyphus 循环、Micro-review、Plan Review)                                                                                                                                             |
| Skills   | skills/12个                    | brainstorm(需求) tdd(测试) plan-first(计划) verification(验证) code-review(审查+通用标准) systematic-debugging(调试) kaizen(复盘) context7(文档) agent-teams(并行) e2e-testing codex-delegate quickstart |
| 子代理   | agents/3个                     | builder(实现, effort:high) validator(审查+计划审查) explorer(调研, background) — Path C+ 启用, 遵守上下文隔离原则                                                                                        |
| 命令     | commands/4个                   | /vibe-dev(开发入口) /vibe-init(初始化) /vibe-resume(恢复) /vibe-status(进度)                                                                                                                             |
| 状态文件 | .ai_state/7个                  | status.md(当前进度) design.md(R₀→D) plan.md(P→V) quality.md(T) conventions.md(项目规范) knowledge.md lessons.md(经验)                                                                                    |
| MCP工具  | .mcp.json                      | augment-context-engine(搜代码) cunzhi(人工确认) mcp-deepwiki(查文档)                                                                                                                                     |
| Hooks    | settings.json/6个              | SessionStart(恢复) Stop(门控+LLM审查) StopFailure(崩溃保存) PostToolUse(格式化) PreToolUse(安全) PostCompact(状态+Sisyphus恢复)                                                                          |

## 行为校准

- 不确定时说出来, 不要猜
- compact 前存 .ai_state/status.md; 两次 compact = 任务太大, 拆分或用子代理
- 最简方案优先, 避免过度工程
- E 阶段 Sisyphus 循环: 读 plan.md → 执行 [ ] → micro-review → [x] → 重复直到全部完成

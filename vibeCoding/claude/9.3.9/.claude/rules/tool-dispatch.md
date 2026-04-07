# 工具调度

<important if="choosing tools, plugins, or delegating work">
PACE 决定调什么工具。按表执行, 不要猜测。

## 需求与设计 (R₀ + R + D)
| 任务 | 工具 | 用法 | 降级 |
|------|------|------|------|
| 需求发散 | superpowers brainstorming | 自动激活 | 手动四步法 (定义→发散→追问→收敛) |
| 查库文档 | context7 | `npx ctx7 resolve {{库名}}` | 搜索 + node_modules |
| 语义搜索 | augment-context-engine | MCP 工具自动调用 | Grep + Read |
| 方案审查 | @evaluator | 委托 | `/review` |
| 用户确认 | cunzhi MCP | DESIGN_READY / SPRINT_CONTRACT 检查点 | 直接问用户 |

注意: `/codex:adversarial-review` 只能审查代码变更, 设计阶段无代码时不要使用。

## 计划 (P)
| 任务 | 工具 | 用法 | 降级 |
|------|------|------|------|
| Task 分解 | 主 Agent | 分析 design.md 分解 Task | — |
| 依赖分析 | augment-context-engine | 跨文件依赖关联 | Grep 手动分析 |

## 执行 (E)
| 级别 | 工具 | 用法 | 降级 |
|------|------|------|------|
| Level 1 | codex:rescue | `/codex:rescue --background <task>` | Level 2 |
| Level 2 | @generator | `@generator 实现 Task` | Level 3 |
| Level 3 | 主 Agent | 手动 TDD (先测试后实现) | — |
| 并行 | CC /batch | `/batch 按 tasks.md 并行` (Path C/D) | 逐个执行 |
| 清理 | CC /simplify | 所有 Task 完成后运行 | 手动重构 |
| 调试 | CC /debug | 测试失败时分析 | 手动 debug |

Level 1 详细:
- `/codex:rescue --background <task 描述, 参照 .ai_state/handoff.md>`
- `/codex:status` → `/codex:result` → 审查 → 应用 → 测试

## 审查 (T)
| 任务 | 工具 | 用法 | Path |
|------|------|------|------|
| 标准审查 | codex | `/codex:review --background` → `/codex:result` | 所有 |
| 对抗审查 | codex | `/codex:adversarial-review` | C+ |
| 安全扫描 | ECC | `npx ecc-agentshield scan` | C+ |
| 深度扫描 | ECC | `npx ecc-agentshield scan --opus --stream` | 安全敏感 |
| E2E 测试 | playwright | 按 skill 指引 | D (有前端) |
| 综合评分 | @evaluator | 委托 (附带全部审查结果+测试结果) | B+ |
| 快速审查 | CC 内置 | `/review` | A 或降级 |

审查结果全部写入 .ai_state/reviews/sprint-N.md

## 归档 (V)
| 任务 | 工具 |
|------|------|
| 更新 conventions/gotchas | 编辑 .ai_state/project.json |
| 记录教训 | 编辑 .ai_state/lessons.md |
| 重置状态 | 更新 project.json: stage="", sprint+1 |
| 交付确认 | cunzhi MCP DELIVERY 检查点 (如可用) |

## 降级策略
| 工具 | 不可用信号 | 降级到 |
|------|-----------|--------|
| codex-plugin-cc | /codex:setup 报错 | @generator + /review |
| superpowers | 插件未安装 | 主 Agent 手动执行 |
| context7 | npx ctx7 报错 | 搜索 + node_modules |
| ECC AgentShield | npx ecc 报错 | 手动安全检查清单 |
| cunzhi MCP | 连接失败 | 直接问用户确认 |
| augment-context-engine | MCP 不可用 | Grep + Read 手动搜索 |
| playwright-skill | 插件未安装 | 手动浏览器测试 |
</important>

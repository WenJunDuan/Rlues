# VibeCoding Kernel v9.1.8 — Codex CLI

## 铁律 (违反即阻断交付)
1. **先搜后写** — 写代码前搜索项目现有实现 + web search 查库文档。不搜 = 不写
2. **先测后码** — 源码必须有对应测试。delivery-gate 用 git diff 检查。无测试 = 不交付
3. **寸止确认** — 设计/计划/交付前暂停等用户确认。跳过 = 不交付

## 工作流入口
收到任务 → 读 .codex/workflows/pace.md 路由复杂度(A/B/C/D) → 按 riper-7.md 执行
- Bug/error/crash/报错类 → 先激活 systematic-debugging skill
- .ai_state/ 有未完成任务 → 先恢复 (读 status.md + plan.md)

## 框架地图
| 类别 | 位置 | 说明 |
|------|------|------|
| 工作流 | workflows/pace.md + riper-7.md | 路由 + 阶段编排(Sisyphus循环、Micro-review、Plan Review) |
| Skills | skills/12个 | brainstorm(需求) tdd(测试) plan-first(计划) verification(验证) code-review(审查+通用标准) systematic-debugging(调试) kaizen(复盘) context7(文档) agent-teams(并行) e2e-testing claude-delegate quickstart |
| 子代理 | agents/3个 | builder(实现) validator(审查+计划审查) explorer(调研) — Path C+ 用 spawn_agent/wait_agent, 遵守上下文隔离 |
| 状态文件 | .ai_state/7个 | status.md(进度) design.md(R₀→D) plan.md(P→V) quality.md(T) conventions.md(规范) knowledge.md lessons.md(经验) |
| Hooks | plugin SDK | SessionStart/Stop 通过插件实现 (非 config.toml); 自带 delivery-gate.cjs 脚本可手动集成 |
| 原生命令 | Codex内置 | /plan(规划) /review(审查) /model(切换) spawn_agent/wait_agent(子代理) |

## 行为校准
- 不确定时说出来, 不要猜
- 最简方案优先, 避免过度工程
- 对话过长 = 任务太大, 拆分或用子代理
- E 阶段 Sisyphus: plan.md [ ] → 执行 → micro-review → [x] → 重复直到完成

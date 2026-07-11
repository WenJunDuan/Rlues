---
roadmap_slug: "claude-code-9-9-1-optimization"
created: "2026-07-10"
path: "System"
status: "design_review"
---

# Roadmap — Claude Code Athena 9.9.1 Optimization

## 目标

以 committed `vibeCoding/claude/9.9.0/.claude` 为唯一基线，重新定义 CC 9.9.1。共享 PACE、`.ai_state`、review、evidence 与 gate 语义对齐已发布 CX 9.9.1；模型、hooks、subagents、worktree、settings 与安全策略使用 Claude Code 原生能力，不追求逐文件机械对称。

## 发布边界

- 9.9.0 保持只读，Git object 必须不变。
- 现有 `vibeCoding/claude/9.9.1/.claude` 仅为候选实现参考，不作为设计基线。
- Fable5 review 和用户确认前，不修改任何 CC 版本包。
- 9.9.1 保持 patch：必修兼容层进入默认发布；实验能力只做可选增强或延后。

## 推进顺序

1. 冻结官方契约、共享状态和 Fable5 审查结论。
2. Hook/state/gate 与 subagent/worktree/model 两条互斥写集并行实现。
3. Prompt/skill/review 与 settings/security 可并行实现。
4. 最后执行定点迁移、stable/latest 双版本矩阵、runtime-verify、review、polish、architecture 和 ship。

## 版本策略

| 档位 | 版本 | 规则 |
|---|---:|---|
| Compatibility floor | 2.1.197 | 核心功能可运行；低于安全能力时显式降级 |
| Safe worktree floor | 2.1.203 | 红区自动 isolation 的最低推荐版本 |
| Release target | 2.1.206 | 全功能验证目标 |

## Fable5 审查门

- 当前只允许完成 `cc991-contract-design`。
- Fable5 返回 PASS/APPROVE 且用户确认后，才将第一项标记 completed 并进入实现。
- 若 Fable5 判断范围超出 patch，优先保留 P0/P1 兼容修复；Agent Teams、PostToolBatch 智能提醒等移至后续版本。

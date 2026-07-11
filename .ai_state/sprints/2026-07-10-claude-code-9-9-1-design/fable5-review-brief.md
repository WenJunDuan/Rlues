# Fable5 Review Brief — Claude Code Athena 9.9.1

## 任务

只做独立设计审查，不修改任何代码或配置。读取：

1. `.ai_state/sprints/2026-07-10-claude-code-9-9-1-design/design.md`
2. `.ai_state/roadmap/claude-code-9-9-1-optimization/{roadmap.md,items.yaml}`
3. `vibeCoding/claude/9.9.0/.claude`（唯一实现基线）
4. `vibeCoding/codex/9.9.1/.codex`（共享语义基线）
5. `vibeCoding/claude/9.9.1/.claude`（仅候选参考，不得反推设计正确）

官方依据：

- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/worktrees
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/agent-teams

## Review lenses

1. **版本纪律**：9.9.1 是否仍是 patch；哪些能力应延期。
2. **官方契约**：hooks、settings、models、subagents、worktrees 是否有错误理解。
3. **状态一致性**：CC/CX 是否真正能共用 `.ai_state` 并跨端 ship。
4. **证据真实性**：是否还有 unknown→pass、Start→complete、文本猜状态等假过路径。
5. **并发时序**：Start/Stop、background、sprint 切换、review 2+1 是否存在竞态。
6. **安全**：权限、sandbox、plugins、migrate、hook payload/path 是否越权或破坏用户配置。
7. **模型策略**：opusplan/best/fable、effort、fallback 与角色路由是否合理。
8. **Worktree**：2.1.197/2.1.203/2.1.206 的降级与 baseRef=head 是否安全。
9. **Agent Teams**：是否应进入 9.9.1；若保留，边界是否足够硬。
10. **可验证性**：每个 AC 是否有可复跑测试；是否存在无法机械证明的要求。

## 必答问题

请逐项回答 design.md `## 18. Open decisions for Fable5` 的 9 个问题，并指出任何遗漏的 P0/P1。

## Output format

```markdown
# Fable5 Review — CC Athena 9.9.1

VERDICT: PASS | NEEDS_REVISION | REJECT_SPLIT_VERSION

## P0
- ...

## P1
- ...

## P2
- ...

## Open Decision Answers
1. ...

## Required Design Changes
- ...

## Scope Decision
- 9.9.1 core: ...
- defer: ...
```

只有 `VERDICT: PASS` 且 Required Design Changes 已被主线程合并后，才允许进入实现。

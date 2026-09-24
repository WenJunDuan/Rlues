---
doc_type: learning
slug: "hook-order-and-worktree-counts"
created: "2026-07-08"
sprint_slug: "2026-07-07-f1-orchestrator-framework-design"
severity: "P1"
status: executed
---

# Learning: hook-order-and-worktree-counts

## 现象

Review and ship-gate testing found three false assumptions: Codex same-event command hooks were treated as ordered, System ship architecture counting only saw `main...HEAD` or `evidence.yaml`, and CX frontmatter parsing did not ignore inline comments after quoted values.

## 根因

The implementation trusted convenient local structure instead of the official hook execution contract, the actual delivery shape on `main`, and the existing inline-comment style in `_index.md`.

## 教训

Hook correctness must not depend on same-event command order; ship gates must count committed, staged, unstaged, and untracked files; frontmatter readers must parse the real `_index.md` style with inline comments.

## 通用化

Applies to all Athena hooks and delivery gates that infer state from git or hook sequencing. It does not require every hook to block; collectors can remain best-effort if their output is not a prerequisite for the gate.

## 相关引用

- Codex hooks: https://developers.openai.com/codex/hooks
- Sprint review: `.ai_state/sprints/2026-07-07-f1-orchestrator-framework-design/reviews/pass1.md`

---
sprint_slug: "2026-09-20-index-overflow-root-transaction"
path: "System"
created: "2026-09-20"
last_updated: "2026-09-20"
implementation_authorized: true
---

# Design — 根级 index overflow 事务

## 背景 (context)

当前 CC/CX bounds 根据 `current_sprint_slug` 把溢出写进 sprint 目录，但生成的 pointer 只有裸文件名。生产中该文件会与外部写者提交冲突，且 pointer 不能指向真实位置。根 `.ai_state/index-overflow.md` 已存在并被 Git 跟踪。

## 目标 (goals)

- 所有 index 溢出统一写入根 `.ai_state/index-overflow.md`。
- 新 pointer 使用明确的项目相对路径，并保持现有原子写、跨端锁和 no-op 行为。
- CC、CX 和仅含模板的 Pi 各按真实能力同步合同。

## 非目标 (non-goals)

- 不迁移或删除历史 sprint 内的 `index-overflow.md`。
- 不修改安装态 `~/.claude` / `~/.codex`；安装同步留给 roadmap 最终发行切片。
- 不处理 Q12 其他证据、review、ship 或 shell guard 问题。

## 关键决策 (key decisions)

- 删除 `readSlug/read_slug` 与 slug 参数；spiller 始终使用 `<aiState>/index-overflow.md`，不保留无消费者 plumbing。
- 新指针固定为 `.ai_state/index-overflow.md#<id>`，以仓库根为解析基准；heading ID 与文件内 `## <id>` 一致。
- 保留“先持久化 overflow，再提交 `_index.md`”的事务顺序；根文件继续受 `_index.md` 锁串行化。
- 不向 `.gitignore` 增加 root overflow；该文件是 Tier2 权威历史的一部分。

## Done Contract

- [ ] AC1: CC 与 CX 在存在 `current_sprint_slug` 时均只写 `.ai_state/index-overflow.md`，不会创建 sprint 级 overflow。
- [ ] AC2: route、当前状态、历史和整文件溢出的新 pointer 均为 `.ai_state/index-overflow.md#<id>`，目标文件含对应 `## <id>`。
- [ ] AC3: 同一 `_index` 锁内并发执行的 CC/CX bounds 把两份不同原文都保留在根 overflow、生成唯一 heading 且 pointer 可从仓库根解析；既有 overflow-before-index 崩溃恢复、原文保留及第二次 no-op 不写行为保持通过。
- [ ] AC4: CC/CX/Pi 的 `_index` 模板与长期 architecture 不再声明 sprint 级 overflow，且 root overflow 未被 Git ignore。

## 实现要点 (implementation notes)

先修改行为测试，使其断言根路径、项目相对 pointer、历史分支和“不产生 sprint 文件”；确认 RED 后再修改双端实现。新增真实 CC+CX 并发 bounds 用例：两个进程都通过同一 `_index` 的 `io.update` 锁注入不同 oversized payload，最终断言两份原文、唯一 heading、可解析 pointer 与无 sprint 文件。模板只改路径说明，Pi 不新增不存在的 bounds 实现。历史 sprint overflow 保留，不做启动时迁移或双写。

## File Structure Plan

```text
vibeCoding/claude/9.9.9/.claude/hooks/_index-bounds.cjs          修改
vibeCoding/codex/9.9.9/.codex/hooks/_index_bounds.py             修改
vibeCoding/{claude,codex}/9.9.9/.../pace/templates/_index.md      修改
vibeCoding/pi-agent/plugin/skills/pace/templates/_index.md        修改
vibeCoding/scripts/tests/athena999/test_state_review.py           修改
.ai_state/architecture/athena-9.9.8.md                            polish 更新
```

## 风险与权衡 (risks & trade-offs)

- 多 sprint 共用文件会扩大单文件写热点；现有 `_index.md` 锁已覆盖 bounds 事务，测试保留混合平台并发检查。
- 历史裸 pointer 可能继续依赖旧位置；本切片只保证新 pointer，不猜测性搬迁冷历史。
- 根文件进入提交差异是预期行为；避免忽略才能保证 pointer 指向可恢复内容。

## 历史决策对齐 (read compound/decision-*.md)

与“退役本地遥测”无冲突：overflow 是 Tier2 状态，不是工具/用量 trace。与 `_index` 字段消费者审计一致：有界索引保留，完整原文移到单一权威 overflow，而不是新增第二状态机。

并行派工、恢复、审查输入绑定按 `~/.agents/skills/pace/references/execution-contracts.md`；本 sprint 仅一个 generator 写共享文件。

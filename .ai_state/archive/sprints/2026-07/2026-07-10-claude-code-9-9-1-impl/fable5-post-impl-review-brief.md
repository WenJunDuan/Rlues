# Fable5 Post-Implementation Review Brief — CC Athena 9.9.1

## 任务

审查并修正已经实现的 CC Athena 9.9.1。不要审查主目录未提交的用户配置；实现只在下列 worktree：

- Worktree: `/Users/mi_manchi/workspace/Rlues-cc-9.9.1-impl`
- Branch: `codex/cc-9.9.1-impl`
- Base commit: `daf591f8c1f3119a971784b152dc7d2cefda2ad7`
- CC 9.9.0 baseline tree: `eb1ab06bae8e9a9bd576643e941c4e5d59360fb1`
- Scope: 34 tracked files (`+1197/-926`) + 11 new files；无 commit/push/merge。

先读：

1. `/Users/mi_manchi/workspace/Rlues/.ai_state/sprints/2026-07-10-claude-code-9-9-1-design/design.md`
2. `/Users/mi_manchi/workspace/Rlues/.ai_state/sprints/2026-07-10-claude-code-9-9-1-impl/runtime-verify.md`
3. Worktree `vibeCoding/claude/9.9.1/RELEASE.md`
4. Worktree `vibeCoding/claude/9.9.1/.claude/settings.json`
5. Worktree `vibeCoding/scripts/test-athena-claude-9.9.1-runtime.cjs`
6. Worktree core hooks: `delivery-gate.cjs`、`evidence-collector.cjs`、`subagent-tracker.cjs`、`pre-bash-guard.cjs`
7. Worktree migration: `skills/athena-migrate/scripts/migrate-9.9.0-to-9.9.1.py`
8. `git -C /Users/mi_manchi/workspace/Rlues-cc-9.9.1-impl diff -- vibeCoding/claude/9.9.1 vibeCoding/scripts`

## 必审维度

1. Claude Code 2.1.197/2.1.206 官方 hook payload 与 settings schema。
2. PostToolUse 成功、PostToolUseFailure 失败、unknown 不升级为 pass。
3. Start→assignment→Stop 唯一链、冻结 sprint、并发 JSONL、跨 sprint 防错投。
4. delivery gate 是否真正 fail-closed；latest passN、PASS-only、roadmap/checklist/evidence/runtime/polish/architecture。
5. Bash guard 是否解析实际命令且不因引用文本误报；path traversal、shell injection、安全权限。
6. native worktree：无 WorktreeCreate/Remove override，`baseRef=head`，红黄区角色 isolation 正确。
7. 7 个 agent 的 model/effort/permission/background/maxTurns/skills 是否真实可用；全局 override 是否彻底移除。
8. migration 三方合并是否只删除精确旧默认，并保留 private hooks、plugins、providers、trust、secrets、用户模型。
9. CC/CX shared schema 与 PACE 语义是否兼容；CC-specific migration 修复不要求字节一致。
10. 测试是否存在假绿、漏测、与实现同源自证或未覆盖并发/错误路径。

## 先复跑

在 worktree 执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 vibeCoding/scripts/validate-athena-9.9.1.py
node vibeCoding/scripts/test-athena-claude-9.9.1-runtime.cjs
PYTHONDONTWRITEBYTECODE=1 python3 vibeCoding/claude/9.9.1/.claude/skills/athena-migrate/tests/test_migrate_991.py
git diff --check
```

预期：`143/0`、`50/0/1`、`8/8`、diff clean。唯一允许 skip：需要真实 Claude 账号调用的 subagent/worktree Agent E2E。

## 修改权限

- 可直接修改 worktree 内 `vibeCoding/claude/9.9.1` 与本发布相关 `vibeCoding/scripts`。
- 禁止修改 `vibeCoding/claude/9.9.0`、`vibeCoding/codex/9.9.1`、真实 `~/.claude`、主目录用户配置。
- 每个 P0/P1 修复必须新增或加强失败用例，然后重跑全部命令。
- 不 commit、不 push、不 merge。

## 输出

将审查结果写入：

`/Users/mi_manchi/workspace/Rlues/.ai_state/sprints/2026-07-10-claude-code-9-9-1-impl/reviews/fable5.md`

只有 `VERDICT: PASS`、P0/P1 清零且总验证重新全绿，才允许进入 polish；当前不允许 release。

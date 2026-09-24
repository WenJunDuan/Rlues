---
sprint_slug: "2026-09-24-s0-gate-hotfix-9-9-9-p1"
path: "Bugfix"
created: "2026-09-24"
roadmap: "athena-10-1"
item: "s0-gate-hotfix-9-9-9-p1"
base_commit: "b8558ab"
---

# Design — S0 · 9.9.9 误拦与过期事实热修

> 电报体。10.1 设计真相见 `roadmap/athena-10-1/design.md`；本片只修 9.9.9 源（CC/CX/Pi），立即可装。

## 背景 (context)

quantum-agent Q12 验收（2026-09-23）未生效 9 条中，3 条每天误拦（#27 承诺闭合、#29 跨仓推送/heredoc 正文、#30 design_changed）；另有过期事实（宪法「CC 无原生 /goal」、Pi README 路径、Pi peer `*`）与 `init-platforms.py` 判端缺陷（worktree 路径含 `.claude` 时测试假红）。

## 当前行为 / 期望行为 / 不变行为

| # | 当前行为 | 期望行为 | 不变行为 |
|---|---|---|---|
| 1 | `git -C <其他仓> push` 与 `cd <其他仓> && git push` 按**当前 cwd** 的 stage 判拦 | 按推送目标目录所在项目的 stage 判；目标无 `.ai_state` 放行；目标含 `$`/反引号或不存在 → 回落 cwd（从严） | 本项目 stage∉{ship, 空} 时推送本项目仍拦；`ATHENA_ALLOW_PUSH=1` 仍放行 |
| 2 | `git commit -F - <<'EOF'` 正文里的 `git push` 被当成命令 | `git`、`gh` 读 stdin 为数据，正文按窄形 heredoc 屏蔽 | `bash`/`sh` 等解释器正文仍分析；非窄形仍按原逻辑；CC==Pi 字节一致 |
| 3 | design.md 在 impl 阶段**首次**落盘即置 `design_changed_after_impl` | 仅当基线 `HEAD` 已有该 design 时才置位 | 基线已有 design 在 impl/review/polish 被改仍置位 |
| 4 | 写集里列出 `vm-pending.md` 路径被当成「承诺记 vm-pending」 | 正则排除紧跟 `.md` 的纯路径；`path=Quick` 且 design 写集含 `vm-pending.md` 时跳过 | 「后续记/登/转/→ vm-pending」五种承诺句式仍拦 |
| 5 | 宪法写「CC 无原生 `/goal`」；Pi README 指向不存在的 `vibeCoding/pi/*`；peer `*` | 删过期断言；路径改 `vibeCoding/pi-agent/*`；peer 钉 `>=0.87 <0.88` | 宪法其余内容不动 |
| 6 | `init-platforms.py` 用 `'.claude' in parts` 判端 | 用包目录名（`parents[3].name`）判端 | 安装态 `~/.claude` 判 CC、`~/.agents`/`.codex` 判 CX |

## 验收标准 (Done Contract)

- AC1: CC/CX `pre-bash-guard` 对 `git -C <无 .ai_state 目录> push`、`cd <该目录> && git push` 在本项目 stage=impl 时放行；对 `git -C <本项目> push`、`git -C "$HOME/x" push` 仍拦。
- AC2: CC/CX/Pi `_shell-lex` 的数据型 consumer 增加 `git`、`gh`；`git commit -F - <<'EOF'` 正文含 `git push` 时 `analyze` 返回无 push；CC 与 Pi 两文件字节一致。
- AC3: CC/CX `design-change-detector` 在 `HEAD` 无该 design 时不置位；`HEAD` 已有时照旧置位。
- AC4: CC/CX `validateVmPendingPromises` 不再把 `vm-pending.md` 纯路径当承诺；Quick 且 design 写集含 `vm-pending.md` 时跳过；原五种承诺句式仍拦。
- AC5: CC `CLAUDE.md` 无「CC 无原生 `/goal`」；`pi-agent` 三份 README 无 `vibeCoding/pi/`；Pi `package.json` peer 为 `>=0.87 <0.88`。
- AC6: CC/CX `init-platforms.py` 在路径含 `/.claude/worktrees/` 的 CX 包内判为 CX。
- AC7: 新增 `scripts/tests/athena999/test_gate_fixes_20260924.py` 覆盖 AC1–AC6；athena999 全量通过。

## 允许写集

`vibeCoding/claude/9.9.9/.claude/{CLAUDE.md,hooks/pre-bash-guard.cjs,hooks/_shell-lex.cjs,hooks/design-change-detector.cjs,hooks/delivery-gate.cjs,skills/athena-init/scripts/init-platforms.py}`、`vibeCoding/codex/9.9.9/.codex/{hooks/pre-bash-guard.py,hooks/_shell_lex.py,hooks/design-change-detector.py,hooks/delivery-gate.py,skills/athena-init/scripts/init-platforms.py}`、`vibeCoding/pi-agent/{README.md,config/README.md,plugin/README.md,plugin/package.json,plugin/extensions/cc-core/{pre-bash-guard.cjs,_shell-lex.cjs}}`、`vibeCoding/scripts/tests/athena999/{test_gate_fixes_20260924.py,test_heredoc_guard.py}`、本 sprint 文书、`_index.md`、`roadmap/athena-10-1/items.yaml`。

## 不做

`承诺闭合` 的「登台账/转台账」扩展句式（会扩大拦截面，与 Q12 #27 最小修法不符，记入 10.1 S2·A4 设计）；Pi 端 delivery-gate（分叉旧版，无该校验，10.1 S2 统一）。

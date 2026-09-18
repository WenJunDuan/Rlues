---
name: grok-exec
description: 用 grok CLI（grok-4.6 xhigh）headless 派施工或只读核实任务：独立 worktree、自动批准、拒读凭据、拒 push、nohup 后台。用户点名让 grok 施工/核实/审查时触发。
---

# grok-exec · grok 4.6 headless 派工

## 何时用
- 用户点名 grok 做施工（Bugfix/Quick 级，合同已写好）或只读核实/审查。
- 不用于需要 CC 原生握手（SubagentStart/assign）的 generator 角色：grok 是外部执行器，证据链按 `compound/2026-09-18-trick-codex-external-executor-evidence-chain.md` 由主仓复跑补齐。

## 派工步骤（写任务）
1. 主仓建 worktree 并软链依赖：
   `git worktree add ../<repo>-grok-<slug> -b grok/<slug> main && ln -s <主仓>/node_modules ../<repo>-grok-<slug>/node_modules`
2. 简报写到 job tmp（不进仓库）：`$CLAUDE_JOB_DIR/tmp/grok-<slug>-brief.md`。内容：合同（AC 原文）、纪律（不读凭据、不 push、不改哪些文件）、记账要求（tdd-evidence.yaml 真实时刻、session-log）、提交粒度、最终回复行数上限、「不输出推理过程」。
3. 启动（必须 `nohup` + `< /dev/null` + `&`；Bash 工具前台 10 分钟上限会杀掉长任务）：
   ```
   nohup grok --cwd <worktree 绝对路径> --prompt-file <brief> -m grok-4.6 --reasoning-effort xhigh --no-plan --always-approve \
     --deny "Read(**/config.json)" --deny "Read(**/*.env)" --deny "Read(**/data/credentials/**)" --deny "Bash(git push:*)" \
     --disable-web-search --output-format json --max-turns 400 < /dev/null > <log> 2>&1 &
   ```
4. 轮询：`ps aux | grep -c "[g]rok --cwd"`（0 = 结束）；`git -C <worktree> log --oneline main..HEAD`；日志末尾 JSON 取 `text` / `stopReason`（要 `end_turn`）/ `num_turns` / `total_cost_usd`。
5. 收尾：grok 会改它 worktree 里的 `.ai_state/_index.md`（分诊写状态）→ 合并时丢弃该 hunk；主仓 rebase/cherry-pick 后重跑 `npm test` / `npm run typecheck` 让 evidence-collector 入账；review 照宪法一轮。

## 只读任务
同一命令，简报明写「把完整报告直接输出到最终回复，不要写文件」，主 agent 落盘。

## 已知坑（2026-09-18 实测）
- `acceptEdits` / `dontAsk`：工具调用一碰确认提示，整会话 `stopReason=cancelled`（第 2 turn 即退，日志只剩一句计划）。不是模型不写，是 headless 无人应答提示。
- `-p` 与 `--prompt-file` 互斥；不带 `--no-plan` 会说一句计划就退。
- `--allow "Bash(git status:*)"` 类白名单在 acceptEdits 下不足以避免提示。
- 探针：`grok --cwd <wt> -p "…创建 probe.txt…" --no-plan --always-approve --output-format json --max-turns 8 < /dev/null`，看 `stopReason` 与文件是否落地。
- 成本参考：Q2d 九条实做 45 turns ≈ $1.24。

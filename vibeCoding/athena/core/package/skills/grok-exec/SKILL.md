---
name: grok-exec
description: 用户点名让 grok 施工或只读核实/审查时用：headless 派外部写者，独立 worktree、拒读凭据、拒 push，交回后由主仓复跑接回。
---

# grok-exec — 外部写者合同

grok 是外部执行器：没有本端子 agent 的门禁挂载，它的自测不算证据；主 agent 负责接回与复跑。通用合同见 pace/references/execution.md「外部写者」。

## 派工

1. 核名：`grok models` 查当前可用最新模型，不沿用记忆里的名字。
2. 建 worktree：`git worktree add ../<repo>-grok-<slug> -b grok/<slug> main`；需要依赖时软链 `node_modules`。
3. 简报放仓库外临时目录，内容：AC 原文；允许写集；纪律（不读凭据、不 push、不改 `.ai_state`、不在仓库任何位置写证据文件）；提交粒度；最终回复行数上限；「不输出推理过程」。Bugfix 附三段式（当前 / 期望 / 不变行为）。
4. 启动（长任务必须后台，前台工具有时限）：
   ```
   nohup grok --cwd <worktree> --prompt-file <brief> -m <核过的模型> --reasoning-effort xhigh --no-plan --always-approve \
     --deny "Read(**/config.json)" --deny "Read(**/*.env)" --deny "Read(**/credentials/**)" --deny "Bash(git push:*)" \
     --disable-web-search --output-format json --max-turns 400 < /dev/null > <log> 2>&1 &
   ```
5. 在 sprint 目录写 `external-writer.json`：`{writer: "grok", model, base, branch, brief}`（A1）。

## 轮询与解析

- 是否结束：`pgrep -f "grok --cwd <worktree>"`；进度：`git -C <worktree> log --oneline main..HEAD`。
- 输出：`--output-format json` 的日志取**最后一个顶层 JSON 对象**，看 `stopReason`（要 `end_turn`）、`num_turns`、`total_cost_usd`、`text`。
- 402 / 余额耗尽：立即停止派工，`athena issue add --type env --text "grok 402 余额耗尽"`，改本端写者。

## 接回顺序

1. `athena sprint start …`（若还没有 sprint）；Bugfix 用三段式 design。
2. 主仓 cherry-pick grok 的提交；丢弃它对 `.ai_state` 的任何改动。
3. 主 agent `athena run --covers … -- <测试/类型检查>` 复跑 → 独立 review → ship。
4. 核对完成后删 worktree 与 `grok/<slug>` 分支。

## 只读任务

同一命令，简报写「完整报告直接输出到最终回复，不写文件」；主 agent 落盘到 sprint log 或 docs。

## 已知坑

- `acceptEdits` / `dontAsk` 碰到确认提示会让整个会话 `cancelled`：headless 用 `--always-approve` + `--deny`。
- `-p` 与 `--prompt-file` 互斥；不带 `--no-plan` 会说完计划就退。
- 探针：`grok --cwd <wt> -p "创建 probe.txt" --no-plan --always-approve --output-format json --max-turns 8 < /dev/null`。

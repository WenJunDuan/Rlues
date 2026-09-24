# HANDOFF · athena-10.1 · S2 起续（2026-09-24）

> 新会话第一步：读本文件 → 读 `.ai_state/roadmap/athena-10-1/{roadmap.md,design.md}` → 开 S2。
> 用户指令（原文）："开 S2 ，全部开完，自己全部做完，定好顺序，全部做完，然后合并代码，并提交"
> = S2→S9 自主做完；合并 athena-10.1→main 并 commit。**不 push、不 install、不删 .runtime**（未授权）。

## 0. 仓库现状

| 项 | 值 |
|---|---|
| 仓库 | Mac `Rlues`（device_bash: `$HOME/mnt/Rlues`） |
| 分支 | `athena-10.1` @ `e7b457b`（S1）；main @ `8903233`（S0+安装记录） |
| _index | idle；`next_action: "S1 完成…下一波 W2：S2 gate-core ∥ S5 prompts-v2"` |
| 工作区脏 | `.ai_state/.snapshots/config-events.jsonl`（hook 噪声，勿提交）；`Claude outputs/`（未跟踪，勿提交） |
| 已完成 | S0（9.9.9 热修，已装机）、S1（单源 `vibeCoding/athena/` + `build.mjs`，dist 与 9.9.9 逐字节一致） |
| S2 进度 | 仅读源码，**零文件写入** |

## 1. 执行顺序（已定）

S2 gate-core → S4 state-v2 → S3 review CLI → S5 prompts-v2 → S6 install/doctor → S7 Pi 0.87 → S8 evals → S9 合并收口。

每片固定流程：`.ai_state/sprints/2026-09-24-sN-<slug>/design.md`（`- ACn:` 锚点）→ 测试红→绿 → general-purpose 子 agent 独立 review（stage tar/diff 进 sprint 目录，审完删）→ evidence.yaml / reviews / session-log → items.yaml 置 done → commit 于 athena-10.1。

## 2. 环境坑（必读）

- VM Python 3.10：跑测试前 `PYTHONPATH=$HOME/shim`（sitecustomize 补 `datetime.UTC` + tomli）。
- 测试须 `GIT_AUTHOR_NAME/EMAIL`、`GIT_COMMITTER_NAME/EMAIL` env。
- py_compile/测试后清 `__pycache__`（validator 拒 cache）；测试加 `sys.dont_write_bytecode=True`。
- VM 内 git 可能留 `.git/index.lock`：删除需 `device_request_delete_permission`（Rlues 已授权过一次，新会话需重请）。
- 云端 node22/py3.11 可做构建验证；**device_commit_files 同 stagedPath 重复提交会回传旧文件 → 每次用新文件名 + sha256 校验**。
- 大文件优先直接在 VM 用 python 写，不走 stage/commit。
- quantum-agent：只读键名/行数；**禁读 config.json / *.env / .token / harness-credential**。

## 3. S2 设计要点（design.md D2/D9，已拍板）

- 单一 JS 核：`vibeCoding/athena/gate/`
  - `hook.cjs` 唯一入口；`platform/{cc,cx,pi}.cjs` 负责 payload 归一 + 输出渲染
  - `lib/`：context(findAiState 止于 git 边界)、frontmatter、tree-sha、shell-lex（移植 `_shell-lex.cjs`）、bash-guard（移植含 S0 逻辑的 pre-bash-guard）、state、evidence、exemptions、advisories
  - `rules/`：H1–H5 硬门 + A1–A10 提示
- 硬门：H1 design-first（≥1 `- ACn:`）；H2 PASS evidence 且 `tree_sha`==当前源树；H3 review.json PASS + tree_sha 匹配；H4 红区 writer 隔离；H5 shell 安全 + push stage
- 豁免 `{key, until, reason}`；熔断：同一 block 连续 3 次 → 放行 + issues.md 追加一行
- `athena run -- <cmd>` → 主仓 `.runtime/evidence/<sprint>.jsonl`
- 安装形态：`~/.athena/<ver>` + `current` 软链；cc/cx hook 配置指向 `~/.athena/current/hook.cjs`；CX 用 node 调同核（D2/D9）；Pi vendored core
- 删死 hook：pace-continuator.cjs/.py、compact-snapshot.cjs/.py、subagent-retry.py
- build：新增 "core" dist 适配；S1 字节相等测试改为 **declared-delta**（expected_changes 清单）
- AC6 偏离须写入 design：携带全部安全 fixture；列出被重写/丢弃的 9.9.9 测试族
- D1：writer-provenance 降为 advisory
- Flags（默认关）：cc_workflows, cc_tasks_sync, grok_adapter, pi_hard_stop, bugfix_test_lock, cross_family_review

## 4. 移植源事实（本会话已读，免重读）

**协议**：CC/CX 阻断 = stdout `{"decision":"block","reason":…}` 或 exit 2 + stderr；SessionStart 注入 = `hookSpecificOutput.additionalContext`。CX matcher：`apply_patch|Edit|Write`、`spawn_agent|Agent`、`Bash|apply_patch|MCP|mcp__.*`。

**subagent-worktree-check.cjs（171 行）**：
- 读 `tool_input.subagent_type`；agent 文件 `~/.claude/agents/<type>.md` frontmatter tools 含 write/edit ⇒ writer；polish-worker 豁免
- harness_target_outside_repo 伴随逻辑（EXEMPT/BLOCKED）
- `hasWorktreeIsolation = tool_input.isolation==='worktree' || agentFm.isolation==='worktree'`
- 规则1：path∈{Refactor,System} ∧ writer ∧ 无隔离 → exit 2
- 规则2：`git worktree list --porcelain` 计数 >1 ∧ writer ∧ 无隔离 → exit 2
- 异常 fail-open（exit 0 + stderr）

**evidence-collector.cjs**：
- cwd = `tool_input.workdir || payload.cwd`；无 .ai_state 或无 `current_sprint_slug` → 返回
- `resultStatus`：`tool_response.exit_code` 整数优先；PostToolUseFailure→fail；CC Bash 无 exit_code：PostToolUse ∧ `interrupted===false` ∧ stdout 为 string → pass；否则 unknown
- 仅 Bash ∧ tool_use_id ∧ `classifyValidation(command)` 才记；`validationStatusPolicy` 不可证 → pass 降级 unknown + result_reason
- `redact()`：sk-/gh[pousr]_ token；`authorization: bearer`；`api_key|token|password|secret|private_key|client_secret|aws_*|database_url` 的 `=`/`:` 值；`--password|--token|--api-key|--secret` 参数；URL `user:pass@`；>1500 字符截断为首 300 + 尾 1200
- 持久化 command 截 500 字符；io.acquire 加锁 + writeAtomic

**_input-binding.cjs（229 行）导出**：`FIELDS, classifyValidation, validationStatusPolicy, required, canonical, digest, git, context, sourceSha256, environment, snapshot, captureBefore, finish, currentRecord`
- VALIDATION_PATTERNS：test（pytest/unittest/npm|pnpm|yarn|bun test/cargo test/go test/mvn test|verify/gradlew test）、lint（eslint/prettier --check/ruff/run lint/clippy/go vet/node --check/git diff --check）、typecheck（tsc/run typecheck|check/cargo check）、build（run build/cargo build/go build/mvn compile/gradlew build/cmake --build）；前缀允许 `VAR=x`、`npx`、`;&|` 之后
- `sourceSha256`：`git ls-files -z -c -o --exclude-standard` 去重排序；跳过 `.ai_state`/`.runtime` 顶层、`.env*`、`*.pem|key|p12`、credentials/secrets 目录；按 `name\0` + deleted/link/executable|file/gitlink 哈希 → **即 10.1 tree_sha 的参考实现**
- `environment`：os type/release/machine + runtime-env.yaml 公共字段（含凭据语法则抛错，placeholder 白名单）
- `captureBefore`：验证命令含 `cd` → 抛错（要求用 workdir）；快照写 `.ai_state/.runtime/evidence-inputs/<sha(tool_use_id)>.json`
- `finish`：前后快照一致 → 输出写 `sprint/evidence/<sha>.txt`，返回 binding_status current + 三 sha + artifact_sha256；否则 unverifiable
- `validationStatusPolicy`：shell-lex scan 分段；末段 `&` → validation_backgrounded；验证管道后出现非 `&&` 运算符 → validation_status_not_reported；管道非末位且之前无 `set -o pipefail` → pipeline_without_pipefail；shell-lex 加载失败 → 不可证（fail-closed）

**delivery-gate（1782 行）**：GENERATOR_PATHS=F/R/S；validateImplEntry（containment、spec-gate、packet 仅 design.md 存在时）；validateShip 顺序见 `vibeCoding/athena/core/pace/stages.yaml`（S1 忠实描述，S2 改写为 H1–H5/A1–A10）。

**pre-bash-guard（568 行，S0 版）**：`pushTarget(command,cwd)`（末个顶层 cd → `git -C` 链）、`REPO_REDIRECT_ENV`、`--git-dir/--work-tree` → strict、`sameProject`（git-common-dir + remote url 归一 `normalizeRemote` + realpath/`unresolvedJoin`）；_shell-lex CONSUMERS 含 git、gh。S0 回归：`vibeCoding/scripts/tests/athena999/test_gate_fixes_20260924.py`（10 test）→ **S2 须把这些 case 迁为新核 fixture**。

## 5. S3–S9 范围速记

- **S4 state-v2**：schema + 模板；CLI `status/sprint/ship/issue/tidy/migrate`；自动归档 + 月度打包；session-start 注入；删 counts/index-updater；`.snapshots`→`.runtime`；`_index` ≤3KB；queue.md、issues.md（bug/gate/upstream/env/debt/question）；`docs/{requirements,research,reports}`；decisions/；sprint 4 文件（design.md, evidence.yaml, review.json, log.md）；compound 并入 pace references。
- **S3 review**：`athena review prepare/accept/show` → review.json；agents/reviewer.md 契约；gate 误拦回归 fixture；CC workflow `athena-review.js`（flag）。
- **S5 prompts-v2**：宪法 ≤2500B 三端共用；core/rules.md 附理由，≤300 行；删 antigravity；并 preferences→init、migrate→setup、checkpoint/issue→status、compound→pace refs；保留 augment/context7/playwright/llm-as-a-verifier；每个 SKILL.md ≤60 行；description 总计 ≤6500 字符；agents 收敛到 4 个 + omitClaudeMd；36 个分叉文件用变量收敛；stages.md 由 stages.yaml 生成。
- **S6**：JS 实现 `athena install/rollback/doctor`；配置合并（settings.json、hooks.json、TOML 标记块）；9.9.9 legacy manifest 安全移除；临时 HOME 往返测试；退役 harness-patches.md、setup-athena.py。
- **S7**：Pi 0.87 适配（`agent_before_settle` 硬停；`shouldStopAfterTurn` 已删）；probe 脚本 + 报告；flag 关，待 Mac 实测。
- **S8**：`evals/run.mjs` + 3 个行为任务定义 + headless runner；真实模型跑需用户 Mac 和预算。
- **S9**：合并 athena-10.1→main + commit；Rlues `.ai_state` 迁 v2；清本地分支；报告剩余发布门（行为 eval、quantum dogfood）未完成。

## 6. 待用户动作（收尾时提醒）

1. quantum-agent `.ai_state/_index.md:86` 的 `harness_target_outside_repo: false` 复位尚未提交，需用户自行提交。
2. 在 Mac 上删除 grok 分支：`git worktree remove ../Rlues-grok-writer-provenance && git worktree remove ../Rlues-grok-q12-review-binding && git branch -D grok/writer-provenance grok/q12-review-binding`。
3. push、以及安装 10.1 到 `~/.athena`，都需用户明确授权。

## 7. Commit 尾注

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Kn9AUUmncseUWLqS4rmSJa
```

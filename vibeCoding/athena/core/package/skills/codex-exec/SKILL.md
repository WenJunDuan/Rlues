---
name: codex-exec
description: 派 codex 当外部写者或只读审查者时用：headless `codex exec`，独立 worktree、简报自包含，提交被沙箱拒时打 bundle 接回，主仓复跑与异族 review。
---

# codex-exec — 外部写者 / 审查者合同

codex 是外部执行器：它的自测不算证据，主 agent 负责接回、复跑与 review。通用合同见 pace/references/execution.md「外部写者」；grok 用 grok-exec。

## 派工（写者）

1. 核名：模型名以用户最新裁定为准（`~/.codex/config.toml` 的缺省不等于本次要用的），在命令里显式 `-m`。
2. 建 worktree（**绝对路径**，相对路径会建进仓库里）：`git worktree add -b <type>/<slug> /abs/<repo>-wt/<slug> main`，进去跑一次依赖安装（`bun install --frozen-lockfile` / `npm ci`）；不软链 `node_modules`。
3. 先 `athena sprint start` 写好 design（AC、允许写集、不做），再 `athena sprint pause`；主仓同一时刻只有一个活跃 sprint。
4. 简报放仓库外（如 `/tmp/<proj>/<slug>.brief.md`），**design 全文内联**，外加：worktree 绝对路径与分支；必读规则文件；只跑哪些测试目录 + 守卫 + typecheck（不跑全量）；纪律（不 athena、不改 `.ai_state`、不 push、不 pkill）；预分配的迁移号；「git 被沙箱拒就 `git commit-tree` 打 bundle，报告 bundle 路径与 commit id」；报告格式（逐 AC / 逐条、用例名、红态证据、测试数、剩余风险）。返工轮附审查原文路径，写明「先写会失败的用例，逐条记录修复前失败」。
5. 启动（后台，完成时通知；不用 nohup / `&`）：
   ```
   cd <worktree> && codex exec -m <model> -c model_reasoning_effort=high -s workspace-write \
     --add-dir <主仓>/.git -C . --output-last-message /tmp/<proj>/<slug>.out.md \
     "$(command cat /tmp/<proj>/<slug>.brief.md)" < /dev/null > /tmp/<proj>/<slug>.log 2>&1
   ```
   - 跨仓写：每个额外 worktree 与其主仓 `.git` 都要 `--add-dir`。
   - 要装新依赖或查 npm：加 `-c sandbox_workspace_write.network_access=true`。
   - `< /dev/null` 必带，否则等 stdin 挂住。
6. 写者数受机器负载限制（本机 ≤3 个同时跑检查）。

## 接回

1. 读 `out.md`。提交通常在 bundle 里（沙箱拒写 `index.lock`）：
   `git -C <wt> fetch -q <bundle> <commit> && git -C <wt> reset -q --mixed <commit>`，确认 `git status` 干净；bundle 若在 worktree 内，接回后删掉。
2. 合主线前确认**没有别的 sprint 的 review packet 绑在当前树上**（packet 绑树，合入会让那边 accept 失败）；有就先等它 accept / ship。
3. 合主线：`git merge --no-ff <branch>`；冲突多为迁移清单 / 迁移列表用例，两边都留并按号排序，改新迁移用例的 `previous`。语义冲突（两刀改同一模块）交 codex 在合并现场解：简报写「只编辑文件，不执行 git 写命令」，主 agent `git add` + commit。
4. 主仓 `athena run --covers ACn -- <命令>` 复跑（或 `athena run --rebind`）→ `athena review prepare` → `athena sprint pause` → 异族 review → `athena review accept` → `athena ship`；ship 前不再改树（`.ai_state` 记账除外）。

## 只读审查

```
codex exec -m <model> -c model_reasoning_effort=high -s read-only -C <repo> \
  --output-last-message /tmp/<proj>/rv-<slug>.md "<审查简报>" < /dev/null > /tmp/<proj>/rv-<slug>.log 2>&1
```
- 简报：packet 路径（输出合同）、**只审某个 diff**（`git diff <merge>^1 <merge>`）、固定检查点、上一轮发现原文路径；「只 P0/P1 阻塞，P2/P3 记债」「发现行 `- [Pn] path:line — text`」「正文不写 P0–P3 字样」「末行 `VERDICT: PASS|CONCERNS|REWORK`」——否则 `athena review accept` 解析失败。
- 规则：reviewer 与写者异族（codex 写 → Claude 审；Claude 写 → codex 审）。codex 拒审安全内容时改用 Claude reviewer。
- 已接受的设计取舍写进 design 注记，并在简报里写明「design 注记里的取舍不算发现」，否则每轮重复报。

## 经验与教训

门禁按 verdict 放行（CONCERNS 也要修完再审）、黑名单补洞要换白名单、迁移号预分配、守卫与开发库坑等，见 `references/lessons.md`。

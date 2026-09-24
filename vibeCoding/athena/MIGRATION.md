# `.ai_state` 迁移指南：v1（9.9.x）→ v2（10.1）

读者：执行迁移的 AI agent。前提：Athena 10.1 已按 `INSTALL.md` 装好（或用 `node vibeCoding/dist/athena/<ver>/cli.cjs` 代替 `athena`）。

**授权**：真实迁移会移动文件、打 tag、暂存改动；先给用户看 dry-run 报告并取得同意。删除 `.runtime` 文件、推送需再次确认。

## 1. 迁移前收口（在 v1 状态里做）

1. 列出 `.ai_state/sprints/` 下每个未归档 sprint，逐个判断：已完成 / 已被取代，还是真要继续。
2. 已完成或已被取代：在它的 `session-log.md` 末尾加 `shipped: <日期> closed — <一句话原因>`，迁移时归档到 `archive/sprints/<月>/`。不加的会标 `paused`，之后要写 `resume_when`。
3. 当前 sprint 已完成：清空 `_index.md` 的 `current_sprint_slug`、`stage`、`path`，否则会原样保留为「当前」。
4. **正在进行的 sprint 先收尾或暂停再迁移**：10.1 门禁要求 `athena run` 证据与 `review.json`，v1 sprint 没有，ship 阶段会被拦。
5. 提交收口改动；工作区必须干净。hook 噪声文件（如 `.ai_state/.snapshots/*`）用 `git stash push -- <文件>` 暂存。
6. 在主 checkout 里做（不是 linked worktree）：`git rev-parse --git-dir` 应等于 `--git-common-dir`。

## 2. 预演

```bash
athena migrate --to 10.1 --dry-run --report /tmp/migrate.md
```

| 报告段 | 看什么 |
|---|---|
| _index | 哪些 v1 字段保留、转入 `.runtime/probe.json`、丢弃 |
| Files | move / pause / keep / untrack；pause 只应剩真要继续的 sprint |
| Lessons to triage | compound 里的 learning / trick 进 `archive/compound/`；要保留的规则由人或 agent 写进项目规范，不自动 |
| issues.md draft | proposals / vm-pending 转成 `issues.draft.md` 行 |
| Untracked/ignored | 跟着目录移动但不入库的文件 |
| Blockers | 仓库代码对将被移动路径的引用。运行时真读 → 先改代码；只是旧版源码 / 旧测试里的字面路径 → `--allow-reads "<理由>"` |

`Blockers` 非 0 不要继续。

## 3. 执行

```bash
athena migrate --to 10.1 --report .ai_state/docs/reports/<日期>-migrate.md [--allow-reads "<理由>"]
```

- 自动打 tag `pre-athena-10.1-state`，只暂存它移动或写入的文件，不提交。
- `.snapshots/` 退出版本库，文件留在 `.runtime/snapshots/`；`.gitignore` 加 `.ai_state/.runtime/`。

## 4. 迁移后

1. `athena status`：路由为 idle 或唯一当前 sprint；无 invalid。
2. `issues.draft.md` 逐行确认写入 `issues.md`（已被 10.1 消解的标 `dropped` 写去向），删 draft；原 `proposals.md` 移到 `archive/legacy/`。
3. 仍 paused 的 sprint：在 design.md 写 `resume_when`。
4. 原本入库、现在被 `.gitignore` 忽略的文件：要保留历史的 `git add -f`。
5. 清空目录（`compound/`、`requirements/`、`sprints/archive/`）与 `.DS_Store`。
6. 提交：`ai-state(10.1): .ai_state 迁移到 v2`，正文写 tag、报告路径、人工决定。
7. `athena tidy --dry-run` 看月结与打包；它会清 `.runtime` 旧文件，删除前征得用户同意。

## 5. 回滚

```bash
git reset --hard pre-athena-10.1-state   # 丢弃该 tag 之后的所有提交与工作区改动：先确认没有别的工作
```

只还原入库文件。之后把报告「Untracked/ignored」段的文件移回原路径（或删除），删 `.ai_state/.runtime/{probe.json,_index.v1.md,snapshots/}`，否则下次 `git add -A` 会提交它们。

该 tag 只对应**状态迁移**那一刻；若迁移前后还有代码提交，用 `git revert` 或只还原 `.ai_state/`（`git checkout pre-athena-10.1-state -- .ai_state`），不要整仓 reset。

## 6. 迁移后的工作方式

| 9.9.x | 10.1 |
|---|---|
| 手写 evidence.yaml / tdd-evidence.yaml | `athena run --covers ACn -- <命令>` |
| review-packet + review-binding | `athena review prepare` → reviewer → `athena review accept` |
| checklist.yaml | design.md 的 `- ACn:` 行 + H2 证据 |
| session-log.md、route-note、cleanup-pass、runtime-verify.md | sprint `log.md` 一行一事（runtime-verify 写 `runtime-verify: PASS\|FAIL\|BLOCKED` 摘要） |
| proposals.md、vm-pending | `athena issue add --type …` |
| compound/ | `decisions/`（ADR）、`docs/research/` |
| 手改 `_index` stage | `athena sprint start / stage / pause / resume / drop`、`athena ship` |

实例：Rlues `.ai_state/docs/reports/2026-09-24-migrate-rlues.md`（63 项移动、7 个旧 sprint 收口）。

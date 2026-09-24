# Athena 10.1 — AI 迁移指南（安装 + 项目 `.ai_state`）

读者：执行迁移的 AI agent。每一步给命令、判据、失败处理。改动前先向用户说明计划；安装、推送、删除 `.runtime` 需用户明确授权。

## 0. 前提

| 检查 | 命令 | 通过条件 |
|---|---|---|
| Node | `node --version` | ≥22 |
| 发行物 | `ls vibeCoding/dist/athena/10.1/cli.cjs`（没有就 `node vibeCoding/athena/build.mjs`） | 存在 |
| Git | 项目是 git 仓库，在主 checkout（不是 linked worktree） | `git rev-parse --git-dir` = `--git-common-dir` |

## 1. 安装（用户授权后）

1. 预演：`node vibeCoding/dist/athena/10.1/cli.cjs install --platform cc,cx --dry-run`，把 write / merge / retire 清单给用户看。
2. 安装：去掉 `--dry-run`。把 `~/.athena/bin` 加进 PATH，之后用 `athena`。
3. 体检：`athena doctor` 必须输出 `doctor: no drift`。
4. 失败或不满意：`athena rollback`（还原被替换、移走、新建的全部文件与 `current` 链接；安装后用户改过的文件留在 `~/.athena/backups/<ts>/after-install/`）。

安装合并而不覆盖：`~/.claude/settings.json`、`~/.codex/hooks.json`、`~/.codex/config.toml` 保留用户键与第三方 hook。

## 2. 项目状态迁移

### 2.1 迁移前收口（v1 状态里做）
1. 列出 `.ai_state/sprints/` 下每个未归档 sprint，逐个判断：已完成/已被取代，还是真的要继续。
2. 已完成或已被取代的：在它的 `session-log.md` 末尾加一行 `shipped: <日期> closed — <一句话原因>`，迁移会把它归档到 `archive/sprints/<月>/`。不加的会被标 `paused`，之后要人写 `resume_when`。
3. 当前 sprint 已完成：把 `_index.md` 的 `current_sprint_slug`、`stage`、`path` 清空，否则它会被原样保留为「当前」。
4. 提交收口改动。工作区必须干净：hook 噪声文件（如 `.ai_state/.snapshots/*`）用 `git stash push -- <文件>` 暂存，不提交。

### 2.2 预演
`athena migrate --to 10.1 --dry-run --report /tmp/migrate.md`，读报告：

| 段 | 看什么 |
|---|---|
| _index | 哪些 v1 字段保留、转入 `.runtime/probe.json`、丢弃 |
| Files | move / pause / keep / untrack 清单；pause 只应剩真要继续的 sprint |
| Lessons to triage | compound 里的 learning / trick 进 `archive/compound/`；值得保留的规则写进 `core/rules.md` 或项目规范，由人或 agent 决定，不自动 |
| issues.md draft | proposals / vm-pending 转成 `issues.draft.md` 行，迁移后确认 |
| Untracked/ignored | 跟着目录移动但仍不入库的文件；所在月份暂不打包 |
| Blockers | 仓库代码里对将被移动路径的引用。真实运行时读取 → 先改代码；只是冻结旧版源码、旧测试里的字面路径 → 用 `--allow-reads "<理由>"` |

### 2.3 执行
`athena migrate --to 10.1 --report .ai_state/docs/reports/<日期>-migrate.md [--allow-reads "<理由>"]`
- 自动打 tag `pre-athena-10.1-state`，并暂存它移动或写入的文件（不碰用户其他改动）。
- `.snapshots/` 退出版本库，文件留在 `.runtime/snapshots/`；`.gitignore` 加 `.ai_state/.runtime/`。

### 2.4 迁移后
1. `athena status`：路由应为 idle 或唯一的当前 sprint；无 invalid。
2. `issues.draft.md`：逐行确认，写进 `issues.md`（已被 10.1 消解的标 `dropped` 并写去向），删 draft；原 `proposals.md` 移到 `archive/legacy/`。
3. 仍 paused 的 sprint：在 design.md 写 `resume_when`（`after <roadmap>/<item>` 或一句人话）。
4. 原本入库、现在被 `.gitignore` 忽略的文件：要保留历史的用 `git add -f`。
5. 检查空目录（`compound/`、`requirements/`、`sprints/archive/`）与 `.DS_Store`，清掉。
6. 提交：`ai-state(10.1): .ai_state 迁移到 v2`，正文列 tag、报告路径、人工决定。
7. `athena tidy --dry-run` 看月结与打包；它也会清理 `.runtime` 旧文件——删除前征得用户同意。

### 2.5 回滚
`git reset --hard pre-athena-10.1-state`：只还原入库文件。之后把报告「Untracked/ignored」段列出的文件移回原路径（或删除），删 `.ai_state/.runtime/{probe.json,_index.v1.md,snapshots/}`，否则下一次 `git add -A` 会把它们提交。

## 3. 新项目

`athena init --dry-run` → `athena init`（主 checkout；已有 v2 会拒绝，v1 会提示走 migrate）。需要跟踪时才初始化，先征得用户同意。

## 4. 迁移后工作方式（与 9.9.x 的差别）

| 9.9.x | 10.1 |
|---|---|
| 手写 evidence.yaml / tdd-evidence.yaml | `athena run --covers ACn -- <命令>` |
| review-packet + review-binding | `athena review prepare` → reviewer → `athena review accept` |
| checklist.yaml / Sisyphus | design.md 的 `- ACn:` 行 + H2 证据 |
| session-log.md、route-note、cleanup-pass | sprint `log.md` 一行一事 |
| proposals.md、vm-pending | `athena issue add --type …` |
| compound/ | `decisions/`（ADR）、`docs/research/` |
| _index 手改 stage | `athena sprint start / stage / pause / resume / drop`、`athena ship` |

参考：Rlues 实跑报告 `.ai_state/docs/reports/2026-09-24-migrate-rlues.md`（63 项移动、7 个旧 sprint 收口、13 条 proposals 转 dropped）。

---
name: athena-init
description: 新项目初始化 .ai_state，或设置项目级偏好（flags、豁免、review_ignore）；用户要求初始化或改 Athena 偏好时用。
disable-model-invocation: true
---

# athena-init（初始化 · 项目偏好）

## 初始化

1. 在主 checkout 跑 `athena init --dry-run` 看将创建的文件，再 `athena init`。
   - 非 git 仓库：先请用户 `git init`；linked worktree：到主 checkout 跑。
   - 已是 v2：直接 `athena status`。是 9.9.x 状态：改走 `athena migrate --to 10.1 --dry-run`（athena-setup）。
2. 生成 `_index.md`（schema athena-state/2）、`issues.md`、`queue.md`、`sprints/`、`roadmap/`、`archive/`，并把 `.ai_state/.runtime/` 加进 `.gitignore`。
3. 初始化随第一次代码提交；首个任务用 `athena sprint start`。

## 项目偏好（写 `_index.md` frontmatter）

| 字段 | 含义 |
|---|---|
| `flags.cross_family_review: true` | reviewer 必须与作者不同模型家族：A10 升为 H3 硬门，同家族或家族未知时 ship 被拦 |
| `flags.bugfix_test_lock: true` | Bugfix 复现测试记红后被改时提示（A9） |
| `flags.cc_workflows: true` | CC 用 `athena-review` workflow 跑独立 review |
| `parallel_writers: N` | 并行写者数；≥2 触发红区隔离（H4） |
| `exemptions: [{key, until, reason}]` | 限时豁免，≤14 天；key 见 pace/references/gates.md |

design.md 的 `review_ignore: [glob]`：从源码树 sha 排除的生成物（如构建产物）；只放确属生成的路径。

旧偏好 `skip_polish` / `skip_runtime_verify` 改为同名豁免（带 until 与 reason）；`default_path`、`preferred_tools`、`network_in_polish` 已无消费者，不再设置。`laav_enabled` 见 llm-as-a-verifier。

## 完成条件

`athena status` 能读出路由；偏好改动后 `athena doctor`（在项目内）不报无效豁免。

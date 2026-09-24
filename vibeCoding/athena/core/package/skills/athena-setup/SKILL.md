---
name: athena-setup
description: 安装、升级、回滚、体检 Athena（CC/CX/Pi 共用核心 ~/.athena），以及把项目 .ai_state 从 9.9.x 迁到 10.1 时使用。
---

# athena-setup

安装与迁移只走 CLI；9.9.x 的安装脚本、harness 补丁台账与迁移 skill 已退役（安装态漂移由 doctor 按 sha 发现）。

| 目的 | 命令 |
|---|---|
| 构建 | `node vibeCoding/athena/build.mjs`（Rlues 仓内） |
| 预演 | `node vibeCoding/dist/athena/10.1/cli.cjs install --platform cc,cx --dry-run` |
| 安装 | 同上去掉 `--dry-run`；之后把 `~/.athena/bin` 加进 PATH，即可用 `athena` |
| 体检 | `athena doctor`（逐文件 sha、current 链接、node、9.9.x 残留、过期豁免） |
| 回滚 | `athena rollback`（还原上次安装替换/移走/新建的全部文件与 current 链接） |
| 项目迁移 | `athena migrate --to 10.1 --dry-run` 看报告 → 工作树干净后去掉 `--dry-run`（自动打 tag，回滚 `git reset --hard <tag>`） |

注意：
- 安装会**合并**而不是覆盖 `~/.claude/settings.json`、`~/.codex/hooks.json`、`~/.codex/config.toml`：用户键与用户 hook 保留，Athena 旧 hook 条目换成 `~/.athena/current/hook.cjs`。
- 9.9.x 装过、10.1 不再有的文件移入 `~/.athena/backups/<ts>/`，不直接删除。
- 安装、推送、删 `.runtime` 大包都需要用户明确授权。

---
name: athena-setup
description: 安装所选 CC/CX Athena 9.9.9 受管资产，保留用户配置；已有旧版用 athena-migrate。
disable-model-invocation: true
---

# Athena setup 9.9.9

按用户选择安装。未指定时当前包默认只选本端（CC 包 `--only cc`，CX 包 `--only cx`）；`--only both` 才同时处理两端。安装不调用另一平台 CLI、账号或模型。本包自包含，不从已装 9.9.8 或本机 `~/.claude` 抄文件。

```bash
# 从未安装的机器：用仓库里的安装器，不要假设 ~/.claude/skills 已存在。
python3 vibeCoding/claude/9.9.9/.claude/skills/athena-setup/scripts/setup-athena.py --help
python3 vibeCoding/claude/9.9.9/.claude/skills/athena-setup/scripts/setup-athena.py --repo-root "$PWD" --only cc --dry-run
python3 vibeCoding/claude/9.9.9/.claude/skills/athena-setup/scripts/setup-athena.py --repo-root "$PWD" --only cc
```

外部包用 `--cc-package` / `--cx-package`。`--home` 用于隔离 fixture，不修改未选平台。

## State policy

| Endpoint state | Action |
|---|---|
| `fresh` | 事务安装所选端；保留已有会话/history/file-history/projects |
| `CC-only` / `CX-only` | 只补缺失端，不动已装端用户配置 |
| `same-version` | 校验受管文件；无内容变化则零写入 |
| `old-version` | 需要 `--migrate`；见 athena-migrate |
| 无效配置 | 拒绝覆盖，要求显式合并 |

## 会话与备份

- **永远保留** 历史会话与聊天：`~/.claude/sessions`、`file-history`、`projects`、`history.jsonl`；`~/.codex/sessions`、`archived_sessions`、`history.jsonl`。安装器不得删除或覆盖这些目录。
- 已安装机器上的成功事务：写入当前 `~/.athena/backups/<id>` 后，删除**更早的**安装器备份（只删带 `transaction.json` 的 Athena 备份）。fresh 且尚无 Athena 时保留备份直到用户确认。
- `--dry-run` 无写入。失败回滚已写文件，保留私有备份。回滚见 athena-migrate `--rollback`。

## Installed assets

- CC: `~/.claude/settings.json`、`CLAUDE.md`、rules、hooks、agents、skills（含 `athena-review/REVIEW.md`、`athena-vm/templates/vm.json.example`、`llm-as-a-verifier`）。
- CX: `~/.codex/config.toml`、`hooks.json`、`AGENTS.md`、hooks、agents、standards。
- CX skills: `~/.agents/skills/<name>/SKILL.md`（[Codex loader](https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core-skills/src/loader.rs#L318-L337)）。

新 HOME 使用选定包默认配置；已有有效配置仅合入受管版本和 hooks，保留 model/effort/provider/权限/插件/第三方和未知字段。受管文件与旧基线相同时才升级；用户改动列出 `preserved_user_overrides`。预览只显示路径，不显示配置值。

## Safety

- 不把整份 release config 覆盖到已装 config。
- 不删除第三方 skills；不操作 hook trust store。
- 不读、不写、不打印密钥。同版重复运行无变化则零写入。源码包 symlink、目标 symlink 和无效配置拒绝。

```bash
python3 vibeCoding/claude/9.9.9/.claude/skills/athena-setup/tests/test_setup_991.py
```

CLI 边界：[Claude Code settings](https://code.claude.com/docs/en/settings)、[Codex config](https://developers.openai.com/codex/config-reference/)。

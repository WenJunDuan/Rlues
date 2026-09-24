# Hotfix — 本机 Athena 9.9.9 同步

- 目标：同步 CC/CX 的 9.9.9 受管补丁，保留会话/对话历史和用户定制；成功验证后删除已核验备份与无效缓存。
- 允许写集：本机 `~/.claude`、`~/.codex`、`~/.agents`、`~/.athena/backups`；本仓仅此恢复记录与 `_index.md`。
- 现场：CLI 为 Claude Code 2.1.270、Codex CLI 0.154.0；安装版本标识均为 9.9.9，迁移预演列出 13 个待同步受管文件，且保留 27 个用户覆盖。
- 完成条件：迁移事务成功；双端保持 9.9.9；预演无待同步受管文件；会话/历史路径仍在；清除已核验备份及安全可再生缓存。
- 备份：安装器将在写入前逐文件备份至 `~/.athena/backups/`；验证完成后按用户授权删除备份。

## 交付

- 迁移事务同步 13 项受管资源；27 项用户定制（模型、agent、提示词等）原样保留。
- 候选校验初次为 59/60：CC agent frontmatter 缺少 `maxTurns: 70`。已将该字段补入源包及本机 7 个 agent，且不改动本机 model/effort 覆盖。
- 复验：`python3 vibeCoding/scripts/validate-athena-9.9.9.py` → 60 PASS / 0 FAIL；迁移预演零待写入；CC/CX 安装态均为 9.9.9；会话与历史路径存在。
- 清理：所有已核验备份、陈旧锁和 Finder 元数据移至系统废纸篓；不删除对话历史、插件缓存、粘贴缓存或安全运行环境。受管 Python 缓存会被运行中的 Codex 自动重建，视为有效缓存保留。

## 2026-09-16 task switch

- 已完成的 Hotfix 保持 `ship / re-route`；无活动 writer 或 worktree。
- 新的独立 Quick 仅修改本机 CC agent 的 `maxTurns`，见 `../2026-09-16-cc-agent-turn-cap/session-log.md`。

shipped: 2026-09-24 closed — Hotfix 已 ship（10.1 迁移前收口）

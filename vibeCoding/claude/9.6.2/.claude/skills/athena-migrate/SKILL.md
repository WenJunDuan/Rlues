---
name: athena-migrate
description: |
  从旧版本 Athena (v9.6.1 或更早) 迁移到 v9.6.2. 备份 + 应用 hotfixes + 新增字段.
effort: low
---

# /athena-migrate — 版本迁移

## 触发

```
/athena-migrate                  # 检测当前版本, 自动迁移
/athena-migrate --from=9.6.1     # 显式声明源版本
/athena-migrate --repair         # 修复损坏的 _index.md
```

## v9.6.1 → v9.6.2 迁移步骤

1. **备份**: `cp .ai_state .ai_state.backup-pre-v962`
2. **更新 frontmatter schema**:
   - 加 `skip_polish`, `platforms_enabled`, `cc_version`, `cx_version`, `ag_callable`
   - 加 `tools_available.*` 字段
   - 加 `platform_features.*` 字段
   - 加 `pointers.latest_cleanup`
   - 加 `fingerprint`
3. **更新 CX 配置** (若用户用 cx):
   - `~/.codex/config.toml`: `[features] hooks=true` → `codex_hooks=true`
   - 移除 `[[hooks.*]]` TOML 块 (转移到 `~/.codex/hooks.json`)
   - 更新 `[[skills.config]]` schema: `name = "..."` → `path = "/abs/path/SKILL.md"`
   - skills 实际位置从 `~/.codex/skills/` 移到 `~/.agents/skills/_athena/`
4. **部署新文件**:
   - rules/ (cc) + standards/ (cx) 5 个文件
   - polish/SKILL.md (cc + cx)
   - polish_worker.toml (cx)
   - architect.toml, pr_explorer.toml, docs_researcher.toml (cx 端新)
   - reviewer.md (cc 端补 parity)

## 验证

```bash
# CC
ls ~/.claude/rules/*.md | wc -l    # 应 = 6 (含 _index.md)
ls ~/.claude/agents/*.md | wc -l   # 应 = 3 (evaluator, generator, reviewer)

# CX
grep "codex_hooks" ~/.codex/config.toml   # 应有
grep -c "\[\[hooks\." ~/.codex/config.toml # 应 = 0
ls ~/.agents/standards/*.md | wc -l        # 应 = 6
ls ~/.agents/skills/_athena/             # 应含 pace polish context7 augment antigravity compound
ls ~/.codex/agents/*.toml | wc -l          # 应 = 7 (evaluator/generator/reviewer/architect/pr_explorer/docs_researcher/polish_worker)
```

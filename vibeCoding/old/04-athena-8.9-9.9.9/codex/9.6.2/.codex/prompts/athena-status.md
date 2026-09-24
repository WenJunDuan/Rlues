---
name: athena-status
description: |
  快速查看当前项目的 Athena 状态: stage, path, sprint, tools_available, 进度.
  无副作用, 只读.
effort: low
---

# /athena-status — 项目状态查询 (v9.6.2)

## 工作流

```bash
# 1. 找 .ai_state
[ -d .ai_state ] || { echo "项目未 init, 先跑 /athena-init"; exit 1; }

# 2. 显示 _index.md frontmatter
cat .ai_state/_index.md | head -50

# 3. 显示最新 review
[ -f .ai_state/details/reviews/sprint-*.md ] && {
  echo "最新 review:"
  ls -t .ai_state/details/reviews/sprint-*.md | head -1 | xargs tail -20
}

# 4. 显示最新 cleanup-pass
ls .ai_state/details/cleanup-pass-*.md 2>/dev/null | tail -1 | xargs -I{} echo "Cleanup: {}"

# 5. git 状态
git status -s
```

## 输出格式

```markdown
## Athena 状态 (v9.6.2)

### 路由
- 路径: Refactor
- Stage: polish
- Sprint: 2

### 平台
- CC: ✓
- CX: ✓ (codex-cli 0.133.0)
- AG: ✗ (未安装)

### 工具
- context7 CLI: ✓
- augment MCP (CC): ✓
- web_search (CC): ✓

### 进度
- Features: 3 (counts.features_count)
- Reviews: 2 (counts.reviews_count)
- Cleanups: 1 (counts.cleanup_count)

### 最新 review
- File: details/reviews/sprint-2.md
- VERDICT: CONCERNS (1 P0 已修, 2 P1 在 polish 处理)

### 下一步
进入 polish 阶段 (Refactor 路径强制), 跑 /polish.
```

## 例外

- 项目未 init: 提示先 `/athena-init`
- _index.md 损坏 / 无法 parse: 提示用 `/athena-migrate --repair`

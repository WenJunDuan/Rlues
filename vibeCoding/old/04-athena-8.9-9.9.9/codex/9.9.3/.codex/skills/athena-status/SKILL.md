---
name: athena-status
description: |
  快速查看当前项目的 Athena 状态: stage / path / sprint / 进度 / 活动 worktree.
  无副作用, 只读. v9.7.0: 由 deprecated prompts/ 迁为 skill.
---

# /athena-status — 项目状态查询 (v9.9.3)

Memory contract: **Tier1 working memory** is ignored as authority; **Tier2 persistent memory** is read from `.ai_state`; **_index.md retrieval router** supplies routed state and pointers.

Status emits `missing authoritative pointer`, `escaping authoritative pointer`, or `stale authoritative pointer` for invalid nonempty targets. It also flags malformed/over-10 `route_history` and `## 当前状态`; required keys are `latest_design`, `latest_review`, `latest_cleanup`, `latest_requirement`.

## 工作流

```bash
# 1. 检查初始化
[ -d .ai_state ] || { echo "项目未 init, 先跑 /athena-init"; exit 1; }

# 2. _index.md frontmatter 摘要
echo "=== 项目状态 ==="
sed -n '/^---$/,/^---$/p' .ai_state/_index.md | head -50

# 3. 当前 sprint
slug=$(grep -oP 'current_sprint_slug:\s*"?\K[^"\n]*' .ai_state/_index.md | head -1)
if [ -n "$slug" ]; then
  echo ""
  echo "=== 当前 sprint: $slug ==="
  ls .ai_state/sprints/$slug/ 2>/dev/null

  # 4. 最新 review
  if [ -d ".ai_state/sprints/$slug/reviews" ]; then
    echo ""
    echo "=== 最新 review ==="
    ls -t .ai_state/sprints/$slug/reviews/*.md 2>/dev/null | head -1 | xargs tail -30 2>/dev/null
  fi

  # 5. cleanup-pass
  if [ -f ".ai_state/sprints/$slug/cleanup-pass.md" ]; then
    echo ""
    echo "=== Cleanup pass ==="
    tail -20 ".ai_state/sprints/$slug/cleanup-pass.md"
  fi
fi

# 5b. 解析四个 authoritative pointers；拒绝 .. / 绝对路径逃逸，核对文件存在，
# latest_review 必须等于当前 sprint 数字最大的 passN.md；history 超过 10 条报 overflow。

# 6. 活动 worktree
echo ""
echo "=== 活动 worktree ==="
grep -oP 'active_worktrees:\s*\K\[.*\]' .ai_state/_index.md | head -1
git worktree list 2>/dev/null

# 7. compound/ 统计
echo ""
echo "=== Compound 沉淀 ==="
for type in learning trick decision explore; do
  count=$(ls .ai_state/compound/*-${type}-*.md 2>/dev/null | wc -l)
  echo "  $type: $count"
done

# 8. roadmap 进度
roadmap=$(grep -oP 'current_roadmap_slug:\s*"?\K[^"\n]*' .ai_state/_index.md | head -1)
if [ -n "$roadmap" ]; then
  echo ""
  echo "=== Roadmap: $roadmap ==="
  cat .ai_state/roadmap/$roadmap/items.yaml 2>/dev/null
fi

# 9. git 状态
echo ""
echo "=== Git ==="
git status -s
git log --oneline -5
```

## 输出示例

```
=== 项目状态 ===
version: "9.9.3"
path: "Feature"
stage: "impl"
current_sprint_slug: "2026-05-25-jwt-refresh"
...

=== 当前 sprint: 2026-05-25-jwt-refresh ===
brainstorm.md  design.md  checklist.yaml  reviews/
subagent-log.md  evidence.yaml  tool-trace.jsonl

=== 活动 worktree ===
["worktree-jwt-refresh-impl"]

=== Compound 沉淀 ===
  learning: 3
  trick: 1
  decision: 5
  explore: 2

=== Roadmap: auth-system ===
[items.yaml]
```

## 不要做

- ❌ 不修改任何文件 (只读)
- ❌ 不触发任何 hook
- ❌ 不调度任何 subagent

## 联动

| 用户问 | 进什么 |
|---|---|
| "现在做到哪了" | /athena-status (这个) |
| "上次 sprint 怎么搞的" | grep .ai_state/sprints/ |
| "为啥之前决定用 X" | grep .ai_state/compound/decision-*.md |
| "回顾整个项目历史" | git log + .ai_state/sprints/ + .ai_state/compound/ |

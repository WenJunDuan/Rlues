---
name: athena-migrate
description: |
  Athena 版本迁移工具. v9.6.4 重写: 含 v9.6.2 → v9.6.4 破坏式重构 (sprints/ + compound/ + 4 新 ai_state 文件 + lessons.md 三选项交互).
effort: medium
---

# /athena-migrate — Athena 版本迁移 (v9.6.4)

## 当前支持迁移

| 来源 → 目标 | 难度 | 破坏性 |
|---|---|---|
| **v9.6.2 → v9.6.4** | 中 | **破坏式** (lessons.md 需用户选择) |

## 工作流 (v9.6.2 → v9.6.4)

### Step 1: 检测与备份

```bash
# 检测当前版本
version=$(grep -oP 'version:\s*"\K[\d.]+' .ai_state/_index.md || echo "unknown")
echo "Current: $version"

# 强制备份
backup_dir=".ai_state.backup-$(date +%Y%m%d-%H%M%S)"
cp -r .ai_state "$backup_dir"
echo "✓ 备份: $backup_dir"
```

### Step 2: 建新目录骨架

```bash
mkdir -p .ai_state/sprints
mkdir -p .ai_state/roadmap
mkdir -p .ai_state/architecture
mkdir -p .ai_state/compound
```

### Step 3: 旧 details/ 迁移

```bash
# v9.6.2 details/ → v9.6.4 sprints/legacy-{date}-v962-merge/
if [ -d .ai_state/details ]; then
  legacy_slug="$(date +%Y-%m-%d)-legacy-v962-merge"
  mkdir -p ".ai_state/sprints/${legacy_slug}/reviews"
  
  # 文件搬迁 (保留全部历史)
  [ -f .ai_state/details/design.md ] && mv .ai_state/details/design.md ".ai_state/sprints/${legacy_slug}/"
  
  # reviews/sprint-N.md → reviews/passN.md (改名)
  for f in .ai_state/details/reviews/sprint-*.md; do
    [ -f "$f" ] || continue
    N=$(basename "$f" | sed 's/sprint-\(.*\)\.md/\1/')
    mv "$f" ".ai_state/sprints/${legacy_slug}/reviews/pass${N}.md"
  done
  
  # cleanup-pass-N.md → cleanup-pass.md (合并若多个)
  cleanup_files=(.ai_state/details/cleanup-pass-*.md)
  if [ ${#cleanup_files[@]} -gt 0 ]; then
    cat .ai_state/details/cleanup-pass-*.md > ".ai_state/sprints/${legacy_slug}/cleanup-pass.md" 2>/dev/null
  fi
  
  # 其他文件 (runtime-events.md / proposals.md 等) 整体搬
  mv .ai_state/details/* ".ai_state/sprints/${legacy_slug}/" 2>/dev/null
  rmdir .ai_state/details
  echo "✓ details/ → sprints/${legacy_slug}/"
fi
```

### Step 4: lessons.md 破坏式重构 (用户三选项交互)

主 agent **必须**询问用户:

```
检测到 v9.6.2 → v9.6.4 迁移. lessons.md ($(wc -l < .ai_state/lessons.md) 行) 处理选项:

[1] 整体保留为单文件:
    → compound/$(date +%Y-%m-%d)-learning-legacy-v962-migration.md
    (推荐: 保留全部历史, 但不分类 doc_type)

[2] 手工逐段拆分:
    → 我引导你, 每段你分类为 learning/trick/decision/explore
    (推荐: 分类后好搜, 但花时间)

[3] 全部丢弃:
    → 删除 lessons.md, compound/ 从空开始
    (注意: 历史经验丢失. 仅当 lessons.md 全是过时垃圾时选)

选 [1/2/3]:
```

#### 选项 1: 整体保留

```bash
today=$(date +%Y-%m-%d)
mv .ai_state/lessons.md ".ai_state/compound/${today}-learning-legacy-v962-migration.md"
# 在文件头加 frontmatter (没有则补)
```

#### 选项 2: 手工拆分

主 agent 读 lessons.md, 按段询问用户:

```
段落 1: "useEffect 依赖项漏掉导致无限循环..."
  分类: [1=learning, 2=trick, 3=decision, 4=explore, s=skip, q=quit]
> 1
  slug (kebab-case): useeffect-deps-infinite-loop
  
✓ 写入 compound/{date}-learning-useeffect-deps-infinite-loop.md (从 templates/learning.md)
```

每段独立一个 compound 文件, 主 agent 引导填模板字段.

#### 选项 3: 全部丢弃

```bash
echo "⚠️ 确认删除 lessons.md? 备份在 ${backup_dir}/lessons.md 仍可恢复. (y/N)"
read confirm
[ "$confirm" = "y" ] && rm .ai_state/lessons.md
```

### Step 5: _index.md frontmatter 升级

```python
# 用 python 脚本 (或 yq) 升级 frontmatter
# 新增字段: current_sprint_slug / current_roadmap_slug / counts.compound / next_action / 等
# 详见 ~/.claude/skills/pace/templates/_index.md
```

主 agent 读旧 `_index.md`, 与新模板合并 (老字段保留 + 新字段填默认值), 提示用户审阅.

### Step 6: 删除旧模板文件

```bash
rm -f .ai_state/lessons.md      # 已迁移
# details/ 已在 Step 3 移除
echo "✓ 旧文件清理"
```

### Step 7: 验证

```bash
# 跑 index-updater 重新扫一遍
node ~/.claude/hooks/index-updater.cjs

# 检查新结构
ls .ai_state/sprints/
ls .ai_state/compound/

echo "✓ 迁移完成. 版本: 9.6.4"
echo "  备份: ${backup_dir}"
echo "  如需回滚: rm -rf .ai_state && mv ${backup_dir} .ai_state"
```

## 不向后兼容的破坏式改动

| 改动 | 影响 |
|---|---|
| `details/` → `sprints/{date}-{slug}/` | 旧路径全失效 |
| `lessons.md` → `compound/{date}-{type}-{slug}.md` | 旧引用全失效 |
| `_index.md.current_sprint = N` (数字) → `current_sprint_slug = "..."` (字符串) | hook + skill 全改 |
| `_index.md.lessons_count` → `counts.compound.{type}` | 4 个分类计数 |
| `_index.md` 新增 8 字段 (current_roadmap_slug / next_action / last_subagent / 等) | 老 frontmatter 不全, 需补 |
| 铁律 12 内容变 (subagent 始终用 + worktree 大功能强制) | 用户使用习惯需调整 |

## 回滚

迁移失败 / 不满意:

```bash
# 备份目录就是回滚点
rm -rf .ai_state
mv .ai_state.backup-{timestamp} .ai_state
echo "✓ 已回滚到 v9.6.2"
```

## 注意

- ⚠️ **本工具仅运行一次**, 完成后再次运行会跳过 (检测 `_index.md.version` 字段)
- ⚠️ 主 agent 必须用 ultrathink 处理本迁移 (复杂度高)
- ⚠️ 选项 2 (手工拆分) 长度: 若 lessons.md > 200 行, 估算 30+ 分钟交互
- ✅ 备份永远不删除 (除非用户明确说删)

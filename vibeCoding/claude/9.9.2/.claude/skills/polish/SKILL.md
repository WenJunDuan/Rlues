---
name: polish
description: |
  PACE polish stage. Refactor/System 路径强制. 5 检查项 + worktree 清理 + 触发 architecture 更新.
  含 finishing-a-development-branch 流程 (借 Superpowers) + compound/ 触发.
---

# /polish — Polish stage (v9.9.1)

## 触发

最新 reviews/passN.md VERDICT = PASS 且 path ∈ {Refactor, System} → 主 agent 进 polish.

或 next_action = "polish" (主 agent 根据 evaluator 返回结果写入).

## 5 检查项

| # | 检查 | 例 |
|---|---|---|
| 1 | 临时代码 / 调试痕迹 | `console.log` / `print` / `debugger` / `TODO/FIXME` |
| 2 | 注释完整性 | 公开 API 缺 docstring / 复杂逻辑缺解释 |
| 3 | 冗余 / 重复代码 | 复制粘贴 / 相似函数 |
| 4 | 低效模式 | N+1 query / 阻塞 IO / 无谓循环 |
| 5 | 过度设计 | YAGNI 违反 / 没必要的抽象 |

## finishing-a-development-branch (借 Superpowers)

polish 完成后 **必须**:

```bash
# Step 1: 跑测试验证
npm test  # 或 pytest / cargo test / ...
# 若失败 → 回 impl

# Step 2: 提示用户选项
echo "polish 完成. 选择:"
echo "  [1] merge 到主分支"
echo "  [2] 创 PR"
echo "  [3] 继续工作 (留 worktree)"
echo "  [4] 丢弃 (回滚 worktree)"
read choice

case "$choice" in
  1) git checkout main && git merge worktree-{slug} ;;
  2) gh pr create --base main ;;
  3) echo "保留 worktree, 主 agent 继续" ;;
  4) git worktree remove --force ../worktree-{slug}
     git branch -D worktree-{slug} ;;
esac

# Step 3: 清理 worktree (若 1/2/4 选择)
[ "$choice" != "3" ] && git worktree remove "$wt_path" 2>/dev/null
```

## 工作流

### Step 1: 执行 polish

主 agent 使用 CC 当前可用的 writable subagent 机制分派有界清理任务. 任务必须写明当前 sprint、worktree、允许写集、5 个检查项、review findings 与验证命令; 不依赖过时的 Python 风格工具伪代码.

worker 修改代码并返回清理摘要; `.ai_state` 产物由主 agent 根据实际 diff 与返回结果复核后落盘.

### Step 2: 写 cleanup-pass.md

从 `templates/sprints/cleanup-pass.md` 复制, 填实际内容. 必含段:
- `## 5 检查项`
- `## Finishing-a-development-branch` (借 Superpowers)
- `## review 意见合并` (P1/P2 处理)
- `## 归档到 compound/` (触发 learning + decision)
- `## VERDICT` (Pass / Concerns)

### Step 3: compound 触发

polish 完成时, 主 agent 询问:

```
本 sprint 产生哪些值得沉淀的经验?
  [1] learning (踩坑教训)
  [2] trick (可复用模式)
  [3] decision (技术决策)
  [4] explore (调研结论)
  [5] 全跳过
  [m] 多选

选: _
```

按选择触发对应 `/compound add {type} {slug}`, 从 `~/.claude/skills/compound/templates/` 模板创建.

### Step 4: architecture 更新触发 (若 ≥5 文件)

```bash
# delivery-gate 会在 ship 前强制检查, 这里主动触发
changed=$(git diff --name-only main...HEAD | sort -u | wc -l | tr -d ' ')
if [ "$changed" -ge 5 ]; then
  echo "改动 $changed 文件, 触发 /architect-doc update"
  read ~/.claude/skills/architect-doc/SKILL.md
fi
```

### Step 5: 推进到 ship

写 `_index.next_action = "ship"`.

主 agent 下一 turn 进 ship stage.

## delivery-gate 验证

ship 时 delivery-gate 会检查:
- `cleanup-pass.md` 存在
- `architecture/` 已更新 (≥5 文件改动时, 铁律[架构])
- `design_changed_after_impl != true`

不满足任一 → block.

## 例外

- `_index.skip_polish = true`: 跳过 polish, 直接 ship (用户自负责)
- 路径 ∈ {Hotfix, Bugfix, Quick, Feature}: 不强制 polish (本身不进 polish stage)

## 关键: polish 不是 review

| 维度 | review | polish |
|---|---|---|
| 目标 | 找问题 | 清扫 + 沉淀 |
| 改代码? | 不改, 只评论 | 改 |
| subagent | reviewer + spec-compliance + evaluator | polish_worker |
| 产出 | reviews/passN.md | cleanup-pass.md + compound/ + architecture/ 更新 |
| worktree? | read-only | 沿用 impl 的 worktree |

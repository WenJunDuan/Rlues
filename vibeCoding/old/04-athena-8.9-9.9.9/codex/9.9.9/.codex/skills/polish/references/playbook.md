# polish · playbook

> 从 SKILL.md 下沉的完整正文 (v9.9.6 渐进披露拆分)。

## finishing-a-development-branch (借 Superpowers)

9.9.9 顺序是 runtime-verify → polish → review → ship。polish 完成后跑测试；**不要**在 polish 阶段 merge / 开 PR / 丢弃 worktree。那些动作只在 review 通过且用户授权 ship 时执行。

## 工作流

### Step 1: 执行 polish

主 agent 用 `spawn_agent` 分派 polish_worker。任务必须写明当前 sprint、绝对 worktree、允许写集、5 个检查项与验证命令。polish 在独立 review 之前，不读取 implementation-review 作为前置。worker 每次任务最多 70 轮，到限返回已完成与剩余工作。

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

按选择触发对应 `/compound add {type} {slug}`, 从 `~/.agents/skills/compound/templates/` 模板创建.

### Step 4: architecture 更新触发 (若 ≥5 文件)

```bash
# delivery-gate 会在 ship 前强制检查, 这里主动触发
changed=$(git diff --name-only main...HEAD | sort -u | wc -l | tr -d ' ')
if [ "$changed" -ge 5 ]; then
  echo "改动 $changed 文件, 触发 /architect-doc update"
  read ~/.agents/skills/architect-doc/SKILL.md
fi
```

### Step 5: 推进到 review

写 `_index.next_action = "review"`.

主 agent 下一 turn 发起一次独立 review。polish 在 review 之前，不在 PASS 之后。

## delivery-gate 验证

ship 时 delivery-gate 会检查:
- `cleanup-pass.md` 存在
- `architecture/` 已更新 (≥5 文件改动时, 铁律[门禁])
- `design_changed_after_impl != true`

不满足任一 → block.

## 关键: polish 不是 review

| 维度 | review | polish |
|---|---|---|
| 目标 | 找问题 | 清扫 + 沉淀 |
| 改代码? | 不改, 只评论 | 改 |
| subagent | 一次独立 reviewer（fallback） | polish_worker |
| 产出 | reviews/implementation-review.md | cleanup-pass.md + compound/ + architecture/ 更新 |
| worktree? | read-only | 沿用 impl 的 worktree |

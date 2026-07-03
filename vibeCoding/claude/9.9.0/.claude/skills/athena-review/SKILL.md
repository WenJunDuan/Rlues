---
name: athena-review
description: |
  PACE review stage 执行 skill. 6 维度 (并行 spawn 3 subagent: reviewer + spec-compliance + evaluator).
  v9.7.0: 清除 Stop hook prompt 类型残留引用 (该 hook 类型已于 v9.6.4-hotfix2 删除, 门禁统一由 delivery-gate 在 ship stage 执行).
effort: high
---

# /athena-review — Review stage (v9.7.0)

## 触发

impl stage 完成 (checklist.yaml 全 completed + tests passing) → 主 agent 进 review.

## 6 维度

| # | 维度 | 由谁负责 |
|---|---|---|
| 1 | Correctness (代码正确) | `reviewer` subagent |
| 2 | Security (安全) | `reviewer` |
| 3 | Test (测试) | `reviewer` |
| 4 | Design 一致 (代码符合 design) | `reviewer` |
| 5 | Quality (质量) | `reviewer` |
| 6 | **Spec Compliance (文档覆盖)** | **`spec-compliance` subagent** |

## 工作流 (3 subagent 并行)

### Step 1: 并行 spawn 3 subagent

```python
# 主 agent 用 Task tool 并行调用
spawn_parallel([
    Task(subagent_type="reviewer", prompt="..."),         # 1-5 维度
    Task(subagent_type="spec-compliance", prompt="..."),  # 6 维度
])
# 等两个完成后, spawn evaluator (后跑, 综合两家)
Task(subagent_type="evaluator", prompt="...")
```

### Step 2: reviewer 输出

写入 `sprints/{slug}/reviews/pass1.md`, 段:
- `## Reviewer (代码层 findings)`
- 按 P0/P1/P2 列 finding

### Step 3: spec-compliance 输出 (借 CodeStable cs-feat-accept + OpenSpec /opsx:verify)

读 `sprints/{slug}/design.md` 提取 `## 验收标准` + `## 实现要点` + `## File Structure Plan`.
Bash `git diff main...HEAD --stat + --name-only`.
逐项对比, 写 `sprints/{slug}/reviews/pass1.md` 段:
- `## Spec Compliance (spec-compliance, {timestamp})`
- `### MISSING (做少了)`
- `### EXTRA (做多了, 分合理 refactor / scope creep)`
- `### DEVIATED (做偏了)`
- `### 总评 (PASS | REWORK)`

### Step 4: evaluator 综合 VERDICT

evaluator 读 reviews/pass1.md 的两段 (reviewer + spec-compliance), 综合给 VERDICT:

| VERDICT | 含义 | 下一步 |
|---|---|---|
| **PASS** | 全部维度合规 | next_action = polish (Refactor/System) 或 ship |
| **CONCERNS** | 有 P1/P2 但可推后 | next_action = polish (Refactor/System) 或 ship |
| **REWORK** | 有 P0 或 MISSING/DEVIATED | next_action = rework_impl |
| **FAIL** | 严重违规 (e.g. 安全漏洞) | next_action = rework_impl, 标 _index.major_issue |

evaluator 写 `_index.next_action`.

## 门禁保障 (v9.7.0 实情)

review stage 本身**不设同步 Stop 门禁** (后台 review agent 异步写产物, 同步等待会死锁).
完整性由 `delivery-gate` hook (Stop, 确定性 command) 在 **ship** stage 强制:
- pass1.md 不存在 → block (若 Stop 输入 background_tasks 显示后台任务仍在跑, 提示等待)
- pass1.md 缺 `## Spec Compliance` 段 → block

## 多轮 review (REWORK 后)

REWORK → 主 agent 回 impl 修, 再进 review:
- 新建 `reviews/pass2.md` (不覆盖 pass1.md)
- evaluator 比 pass1 与 pass2 看是否改善
- ≥3 轮 REWORK 仍不过 → 主 agent 必须征求用户介入

## 不要做

- ❌ 主 agent 自己写 review.md (3 subagent 各自写)
- ❌ 跳过 spec-compliance (ship 时 delivery-gate 会 block)
- ❌ evaluator 早于 reviewer + spec-compliance 跑 (顺序错)
- ❌ 用同一个 reviewer 跑多次 (要换 subagent_type, 借 OMO Metis 多 critic 思想)

## 例外

- 路径 = Hotfix: 跳过 review (没时间)
- 路径 = Bugfix / Quick: 仅跑 reviewer, 不跑 spec-compliance (无 design.md)
- 路径 = Feature / Refactor / System: 全跑 (3 subagent)

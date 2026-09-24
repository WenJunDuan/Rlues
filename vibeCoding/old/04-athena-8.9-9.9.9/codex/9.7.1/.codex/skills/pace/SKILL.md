---
name: pace
description: |
  PACE 路由 + 8 stage 状态机. Athena 项目的中枢. 主 agent 进入任何 sprint 前必读.
  v9.7.0: 热路径精简 (铁律[三原语]). 本文件只保留路由判断; stage 详解 / 编排路由表 / hook 联动下沉 references/, 按需 Read.
effort: high
---

# PACE — Router & State Machine (v9.7.0, Codex)

## 6 路径

主 agent 收到用户输入后, 按改动量 + 紧急度判定路径:

| 路径 | 触发 | stage 流程 | 强制 review? | 强制 polish? | 强制 worktree? |
|---|---|---|---|---|---|
| **Hotfix** | 生产事故, 几分钟修 | impl → ship | ❌ | ❌ | ❌ |
| **Bugfix** | 已知 bug, 单文件 | plan → impl → review → ship | ✅ 单维 | ❌ | ❌ |
| **Quick** | 小改动, ≤3 文件 | plan → impl → review → ship | ✅ 单维 | ❌ | ❌ |
| **Feature** | 新功能, 单模块 | plan → impl → review → ship | ✅ 单维 | ❌ | ❌ (可选) |
| **Refactor** | 改架构, ≥5 文件 | plan → impl → review → polish → ship | ✅ 三维度 | ✅ | ✅ 强制 |
| **System** | 跨模块, 系统级 | plan → design → impl → review → polish → ship | ✅ 三维度 | ✅ | ✅ 强制 |

## 8 Stage 状态机

```
                          (大需求或描述模糊时)
                                ↓
[brainstorm] ──→ [roadmap] ──→ plan ──→ [design] ──→ impl ──→ review ──→ [polish] ──→ ship
                                ↑           (System)              (3 维度)         (Refactor/System)
                                xhigh + critic 多轮
```

## 路由判断 (在 athena-dev 入口)

```python
def route(user_input, ai_state):
    # 1. 显式信号
    if explicit_kws(["想法不清楚", "先 brainstorm", "讨论"]):
        return "brainstorm"
    if explicit_kws(["路线图", "分步推进", "拆分"]):
        return "roadmap"
    if explicit_kws(["bug", "修复"]):
        return "Bugfix"
    if explicit_kws(["重构", "refactor"]):
        return "Refactor"

    # 2. 隐式: 单词级模糊 → brainstorm (铁律[分诊])
    if len(user_input.split()) < 8 and not has_concrete_verb(user_input):
        return "brainstorm"

    # 3. ≥ 3 模块需求 → roadmap (铁律[分诊])
    if mentions_modules(user_input) >= 3:
        return "roadmap"

    # 4. 默认: 按改动量分 Feature/Quick/Hotfix
    return classify_by_scope(user_input)
```

## 写入路由 (铁律[零写入] 红黄绿区)

| 区 | 条件 | 执行者 |
|---|---|---|
| 绿 | 单文件 ≤30 行无跨模块影响, 或 Hotfix/Quick | 主 thread 直接做 |
| 黄 | 单模块 Feature/Bugfix | spawn_agent, worktree 可选 |
| 红 | Refactor/System 或并行 ≥2 写者 | `git worktree add` + `spawn_agent --cwd` 强制 |

## References (按需 Read, 不要预加载)

| 场景 | Read |
|---|---|
| 进入某 stage 前看详细工作流 / 数据目录 | `references/stages.md` |
| 选编排机制 (spawn_agent / multi-agent v2 / Goals) | `references/orchestration.md` |
| 查 hook 联动 / compound 联动 / 项目级例外 | `references/hooks.md` |

## 最小循环提醒

- plan/design: `plan_mode_reasoning_effort = xhigh` 已生效; critic 多轮 (max = `_index.plan_critique_max_rounds`)
- impl: 按红黄绿区路由写入; PostToolUse(Bash) hook 自动写 evidence.yaml (过程证据)
- review: 并行 reviewer + spec-compliance, 后跑 evaluator → VERDICT 写 `_index.next_action`
- ship: delivery-gate 强制门禁 (cleanup-pass / architecture / re-review / spec-compliance)

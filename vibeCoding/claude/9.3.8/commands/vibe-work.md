# /vibe-work — 执行计划

只走执行流程。前提: plan.md 和 feature_list.json 已存在。

## 流程

1. 检查 .ai_state/plan.md 存在 (不存在 → 提示先运行 /vibe-plan)
2. 触发 execute skill (E 阶段)
3. 逐个 Task 执行, 每个含 reflexion
4. 全部完成后提示: "执行完成。用 /vibe-review 进行质量审查。"

## 用法

```
/vibe-work                    # 执行所有 pending Task
/vibe-work T003               # 只执行指定 Task
/vibe-work --parallel         # Path C/D: 并行执行无依赖 Task
```

$ARGUMENTS 可指定 Task ID 或 --parallel 标志。

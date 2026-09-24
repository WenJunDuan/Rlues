---
roadmap_slug: ""
created: ""
trigger: ""                    # brainstorm_converged | user_explicit | main_agent_3_modules_detected
estimated_total_complexity: ""  # S/M/L/XL/XXL
---

# Roadmap — {roadmap_slug}

## 背景

[为什么需要这个 roadmap, 业务驱动 / 技术驱动]

## 总体方案

[一段话描述总体架构和实现思路, 大局观]

## 子 feature 拆分

详见 `items.yaml`. 人读版:

| # | slug | title | 复杂度 | 依赖 |
|---|---|---|---|---|
| 1 | ... | ... | M | (无) |
| 2 | ... | ... | L | ... |

## 推进顺序 (拓扑排序)

1. [无依赖项]
2. [一级依赖项, 可并行]
3. [二级依赖项]

## 风险与权衡

- 风险 1: ...
  - 缓解: ...
- 风险 2: ...

## 历史决策对齐 (读 compound/decision-*.md)

[列出本 roadmap 受影响的已有决策]

## 验收 (整个 roadmap 完成的判定)

- [ ] 所有 items.yaml 中 status = completed
- [ ] 集成测试通过
- [ ] 架构档案更新 (architecture/ 相关子系统档)
- [ ] 产生 compound/learning-*.md 沉淀经验

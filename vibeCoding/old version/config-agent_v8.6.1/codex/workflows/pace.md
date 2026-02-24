# P.A.C.E. v3.0 — 复杂度路由

## 决策树

```
任务输入 → 评估复杂度
  │
  ├─ Path A (Quick Fix) — ≤20行, 单文件, 无架构影响
  │   → 直接 E→V (AGENTS.md 快速通道)
  │
  ├─ Path B (Planned Dev) — 中等, 多文件, 需设计
  │   → R₀→R→D→P→cunzhi[PLAN]→E→T→V→Rev→cunzhi[DONE]
  │
  ├─ Path C (System Dev) — 大型, 多模块, 需架构
  │   → 完整九步, 每阶段 cunzhi, 并行执行
  │
  └─ Path D (Collab Parallel) — 项目级, 跨模块, 多人天
      → 分析→cunzhi[TEAM_PLAN]→collab 并行→合并→cunzhi[TEAM_DONE]
```

## 评估维度

| 维度 | Path A | Path B | Path C | Path D |
|:---|:---|:---|:---|:---|
| 改动行数 | ≤20 | 21-200 | 201-1000 | >1000 |
| 影响文件 | 1 | 2-5 | 6-15 | >15 |
| 架构变更 | 无 | 小调整 | 新模块 | 新系统 |
| 预估时长 | <30min | 30min-6h | 6h-3d | >3d |
| 测试要求 | 现有通过 | 新增单测 | 单测+集成 | 单测+集成+E2E |

## 工具矩阵

| 工具类型 | Path A | Path B | Path C | Path D |
|:---|:---|:---|:---|:---|
| augment-context | ✓ | ✓ | ✓ | ✓ |
| brainstorm skill | — | ✓(R₀b) | ✓(R₀b) | ✓(R₀b) |
| context7 (文档) | — | ✓(R₀b/R) | ✓(R₀b/R/D) | ✓(R₀b/R/D) |
| cunzhi | — | ✓ | ✓(每阶段) | ✓(每阶段) |
| mcp-deepwiki | — | 按需 | ✓ | ✓ |
| chrome-devtools | — | — | ✓ | ✓ |
| desktop-commander | — | — | 按需 | ✓ |
| collab 并行 | — | — | ✓ | ✓ |
| /plan 命令 | — | ✓ | ✓ | ✓ |

## .ai_state 文件更新

所有 Path 都要更新 `.ai_state/`:
- session.md: 需求 + Path + 验收标准
- doing.md: 当前进行中
- plan.md: Path B+ 的实施计划

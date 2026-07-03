---
name: phase-router
description: |
  P.A.C.E. v2.0 complexity routing engine. Analyzes task complexity
  and routes to optimal path (A/B/C/D) with effort level mapping.
  v8.0: Added Path D for Agent Teams, effort parameter integration.
---

# Phase Router (P.A.C.E. v2.0)

## 路由决策树

```
任务输入
  │
  ├─ 单文件 AND <30行变更?
  │   → Path A (effort=low)
  │
  ├─ 2-10文件 OR 30-500行?
  │   → Path B (effort=medium)
  │
  ├─ >10文件 OR >500行 OR 跨模块?
  │   → Path C (effort=high)
  │
  └─ 架构级 AND 可并行拆分 AND (>3独立模块 OR 用户--team)?
      → Path D (effort=max, Agent Teams)
```

## Path A - Quick Fix

```yaml
effort: low
workflow: R1 → E → R2
cunzhi: 仅结束时
duration: 30-60 分钟
todo: 单条任务，直接写入 doing.md
```

## Path B - Planned Development

```yaml
effort: medium
workflow: R1 → I → P → E → R2
cunzhi: plan 确认 + 结束确认
duration: 2-8 小时
todo: 分解为 2-5 个子任务
model_route: 按任务类型选择 (见 model-router skill)
```

## Path C - System Development

```yaml
effort: high (关键阶段 max)
workflow: 完整九步
cunzhi: 每阶段关键节点
duration: 数天
todo: 按九步阶段分解，每步独立任务
model_route: Claude Opus 优先 (推理深度)
```

## Path D - Agent Teams Orchestration

```yaml
effort: max
workflow: Lead 分析 → 拆分子任务 → 并行执行 → 合并 → 验证
cunzhi: Lead 分配前确认 + 合并后确认
duration: 数小时-数天 (但并行加速)
requires: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
todo: 按 teammate 分组
```

### Path D 触发条件 (满足 ≥2 项)

- 涉及 >3 个独立模块/目录
- 前端 + 后端 + 测试可并行
- 预估 >4 小时顺序执行
- 存在独立的研究/调研子任务
- 用户显式 `--team`

### Path D 回退

Agent Teams 不稳定或失败 → 降级到 Path C 顺序执行。

## effort 与 Adaptive Thinking 映射

| P.A.C.E. | effort | 模型行为 |
|:---|:---|:---|
| Path A | low | 可能跳过思考，极速响应 |
| Path B | medium | 适度思考 |
| Path C | high | 几乎总是深度思考 (默认) |
| Path D | max | 最高推理深度，峰值能力 |

## 评估指标

```yaml
file_count: 涉及文件数
code_lines: 预估变更行数
architecture_impact: none / minor / major
module_count: 涉及独立模块数
parallelizable: true / false
```

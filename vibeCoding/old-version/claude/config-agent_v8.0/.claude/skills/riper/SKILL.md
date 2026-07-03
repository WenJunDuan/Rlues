---
name: riper
description: |
  RIPER execution cycle: Research → Innovate → Plan → Execute → Review.
  Core workflow engine for all P.A.C.E. paths.
---

# RIPER Execution Cycle

## 阶段概览

| 阶段 | 代号 | 核心动作 | effort |
|:---|:---|:---|:---|
| R1 | Research | 搜索+理解现有代码 | varies |
| I | Innovate | 设计方案，不写代码 | medium+ |
| P | Plan | 生成 TODO 列表 | medium |
| E | Execute | 写代码，更新 doing.md | varies |
| R2 | Review | 核对 todo vs done | varies |

## R1 - Research (感知)

```
1. sou.search("任务关键词")           # 语义搜索
2. 读取 .ai_state/conventions.md     # 项目约定
3. 读取 .knowledge/ 相关知识          # 知识库
4. 理解现有代码结构和模式
5. 输出: 现状分析
```

禁止: 在 R1 阶段修改任何代码。

## I - Innovate (设计)

```
1. 基于 R1 分析设计方案
2. 考虑数据结构 (Data First!)
3. 评估 trade-off
4. 输出: 方案设计 → .ai_state/plan.md
5. cunzhi [DESIGN_READY] (Path B/C/D)
```

禁止: 在 I 阶段修改任何代码。

## P - Plan (计划)

```
1. 从方案提取任务列表
2. 写入 .ai_state/todo.md
3. 估算 effort 和优先级
4. cunzhi [PLAN_READY] (Path B/C/D)
```

## E - Execute (执行)

```
1. 从 todo.md 取任务 → 移到 doing.md
2. 写代码实现
3. 完成 → 移到 done.md
4. 每个文件修改后立即验证
5. 循环直到 todo.md 清空
```

## R2 - Review (核对)

```
1. 逐项对比 todo.md 和 done.md
2. 未完成项 → 记录原因
3. 运行验证 (vibe-verify)
4. 经验提取 (vibe-learn)
5. cunzhi [TASK_DONE]
```

## 路径与 RIPER 映射

| Path | 使用的阶段 |
|:---|:---|
| A | R1 → E → R2 |
| B | R1 → I → P → E → R2 |
| C | R1 → I → P → E → R2 (每步寸止) |
| D | Lead: R1→I→P, Teams: E, Lead: R2 |

---
description: "VibeCoding 执行阶段：计划排期(P)和执行实现(E)。由 vibecoding-workflow 编排调度，不直接触发。包含 Sprint Contract 协商、任务拆分、编码执行、Reflexion 自查。仅在 workflow 指示进入 P 或 E 阶段时使用。"
name: VibeCoding Execute
---

# 执行阶段

## P 计划排期 (Path B+)

目标：方案 → 可执行的原子任务序列

操作：
1. 将 D 阶段确定的方案拆分为原子任务：
   - 每个任务 ≤ 1 个文件的修改 或 1 个函数的实现
   - 标注任务间依赖关系
   - 标注预估复杂度（简单/中等/复杂）
2. 如 .ai_state/ 存在，写入 feature_list.json：
```json
{
  "features": [
    {"id": 1, "desc": "任务描述", "file": "路径", "status": "pending", "deps": []},
    {"id": 2, "desc": "任务描述", "file": "路径", "status": "pending", "deps": [1]}
  ],
  "completed": 0,
  "total": 5
}
```

### Sprint Contract

P 阶段完成后、E 阶段开始前，向用户确认：

> **Sprint Contract**
> - **范围**: 本次完成任务 #1 ~ #N
> - **排除**: 明确不做的内容
> - **验收标准**: 怎么算完成
> - **预估**: 约 N 个文件修改
>
> 确认后开始编码。Sprint 中不接受范围变更，新需求记入积压。

用户确认后 → 如 .ai_state/ 存在，写 state.json `{"phase":"E",...}` → 进入 E 阶段

## E 执行实现 (All Paths)

目标：按计划逐个完成任务

### Path A (快速修复)

不需要 P 阶段的任务清单，直接：
1. 定位问题代码
2. 修复 / 实现
3. 自检无语法错误
4. 进入 T 阶段

### Path B+ (标准流程)

按 feature_list.json 的任务顺序执行：

```
For each Task:
  1. 先读目标文件，理解现有代码
  2. 编写实现
  3. 确认无语法错误
  4. [Reflexion] 自问：
     - 这段代码是否做了且只做了 Task 描述的事？
     - 有没有"顺手"改了别的东西？
     - 错误处理是否完整？
     - 是否遵循了项目现有代码风格？
  5. 如 .ai_state/ 存在，更新 feature_list.json: status → "done"
  6. 如 .ai_state/ 存在，更新 progress.json: percent → (completed / total * 100)
  7. 继续下一个 Task
```

### 生成策略 (Cursor 原生能力利用)

| 场景 | 策略 |
|------|------|
| 单文件简单修改 | 直接编辑 |
| 多文件协调修改 | 在一轮中完成所有相关文件，保持一致性 |
| Path C/D 复杂任务 | 建议用户使用 /worktree 在隔离分支中开发 |
| 不确定的库 API | 先搜索代码库中的现有用法，再查文档 |

### Sisyphus 规则

任务清单全部完成前不能停止：
- 上下文接近上限 → 保存所有状态到 .ai_state/ → 告知用户：
  "已完成 N/M 个任务，进度已保存。请新开会话后说'继续'恢复。"
- 不要在中间任务半完成时停止。要么完成当前任务再停，要么回退当前任务的修改

### 范围变更处理

Sprint 执行中用户提出新需求：
1. 判断是否属于当前 Sprint 范围
2. 如果不属于 → 记录到 .ai_state/state.json 的 backlog 字段
3. 回复："已记录，当前 Sprint 完成后处理"
4. 继续当前任务

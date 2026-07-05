---
description: "VibeCoding 核心工作流引擎。当用户给出开发任务、功能需求、bug 修复、重构请求时使用。根据已选定的 PACE 路径，编排 RIPER-7 各阶段并调度子 skill 执行。触发词：开发、实现、添加、修改、修复、重构、优化。"
name: VibeCoding Workflow
---

# RIPER-7 阶段编排

本 skill 是调度器。它负责选定 Path 后按顺序引导你读取对应的子 skill 执行各阶段。

## 编排流程

```
Path A (快速):
  1. 读 vibecoding-execute skill → 直接执行 E 阶段
  2. 读 vibecoding-review skill → 执行 T 阶段 (含简化 Quality Gate)
  3. 完成

Path B/C/D (标准+):
  1. 读 vibecoding-plan skill → 执行 R0 → R → D 三个阶段
  2. 读 vibecoding-execute skill → 执行 P → E 阶段
  3. 读 vibecoding-review skill → 执行 T 阶段 + Quality Gate
  4. 执行 V 归档阶段 (本 skill 内完成)
```

## 阶段转换规则

每次阶段转换时，更新 .ai_state/state.json 的对应字段（如 .ai_state/ 存在）：
- `phase`: 设为当前阶段代号
- `path`: 设为 A/B/C/D
- `task`: 一句话任务摘要
- `updated`: 当前 ISO 时间

阶段代号：R0 / R / D / P / E / T / QG / V / idle

## V 归档阶段 (Path B+)

此阶段由本 skill 直接执行，不委托子 skill：

1. 输出变更摘要：
   - 改了什么文件
   - 为什么改
   - 影响范围
2. 建议 git commit message（Conventional Commits 格式）：
   ```
   <type>(<scope>): <description>
   ```
3. 更新 .ai_state/state.json：`{"phase":"idle","task":"","updated":"<ISO时间>"}`
4. 如果过程中有值得记录的经验教训，追加到 .ai_state/lessons.md
5. 更新 .ai_state/progress.json：`{"percent":100,...}`

## 异常处理

- 用户中途要求暂停 → 保存当前状态到 .ai_state/ → 告知恢复方式
- Quality Gate 判定 REWORK → 回到 E 阶段重做对应任务
- Quality Gate 判定 FAIL → 回到 D 阶段重新设计
- 上下文接近上限 → 保存 .ai_state/ → 告知用户新开会话后说"继续"

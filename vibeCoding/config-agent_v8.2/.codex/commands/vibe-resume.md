# vibe-resume

恢复上下文。读取 .ai_state/ 重建工作状态。

## 语法

```
vibe-resume
```

## 流程

```
1. 读 .ai_state/session.md:
   → 项目名 / Path / riper_phase / current_task

2. 读 .ai_state/doing.md:
   有未完成 → "上次在 [阶段] 做 [TASK-N]，继续？"
   无 → 读 todo.md → 下一个任务

3. 读 conventions.md + plan.md

4. 恢复到 session.md 记录的阶段:
   Path A → AGENTS.md 快速通道
   Path B+ → 加载对应 workflow → 跳到记录的阶段
```

---
description: "VibeCoding 断点恢复。从 .ai_state/ 状态文件读取上次进度并恢复执行。当用户说'继续''恢复''接着做''resume''上次做到哪了''继续上次的工作'时触发。"
name: VibeCoding Recovery
---

# 断点恢复

## 恢复流程

### 1. 检查状态文件

检查项目根目录是否存在 .ai_state/ 目录：
- 不存在 → 告知用户："没有找到 VibeCoding 状态文件。你可以说'初始化'来创建。"
- 存在 → 继续

### 2. 读取全部状态

| 文件 | 读取内容 |
|------|---------|
| state.json | phase (上次阶段)、path (路径)、task (任务摘要)、backlog (积压需求) |
| feature_list.json | 已完成/未完成的任务清单 |
| progress.json | 整体进度百分比 |
| quality.json | 上次质量评估（如有） |
| lessons.md | 历史经验（如有） |

### 3. 判断恢复策略

**如果 phase = "idle"**：
- 上次任务已完成。检查 backlog 是否有积压需求
- 有积压 → 向用户展示积压列表，询问是否开始新 Sprint
- 无积压 → 告知用户 "上次任务已完成，没有待恢复的工作。可以给我新任务。"

**如果 phase 为其他值**：向用户确认恢复点

输出格式：
```
📍 上次工作状态
- 阶段: [phase]
- 路径: Path [path]
- 任务: [task]
- 进度: [percent]%
- 已完成: [completed]/[total] 个任务
- 未完成任务:
  - [ ] 任务描述 1
  - [ ] 任务描述 2

从这里继续？
```

### 4. 恢复执行

用户确认后：
1. 更新 state.json 的 lastSession 和 updated 字段
2. 根据 phase 读取对应 skill：
   - R0/R/D → 读 vibecoding-plan skill
   - P/E → 读 vibecoding-execute skill
   - T/QG → 读 vibecoding-review skill
   - V → 读 vibecoding-workflow skill (V 阶段)
3. 从断点位置继续执行

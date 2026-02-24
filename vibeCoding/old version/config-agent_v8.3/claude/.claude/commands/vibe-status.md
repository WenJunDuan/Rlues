---
name: vibe-status
description: 查看当前 VibeCoding 状态 — Path、阶段、进度、检查点历史
allowed-tools: Read, Bash
---

# /vibe-status — 状态查看

## 输出

```markdown
## VibeCoding Status

**Path**: {A/B/C/D}
**阶段**: {R/D/P/E/V/Rev/A}
**需求**: {session.md 中的需求}

### 进度 (doing.md)
☑ 任务1: ...
☑ 任务2: ...
☐ 任务3: ... ← 当前
☐ 任务4: ...

### 检查点历史
- DESIGN_READY: approved (14:30)
- PLAN_APPROVED: approved (15:00)

### 文件状态
- session.md: ✓
- design.md: ✓
- plan.md: ✓
- doing.md: 3/5 完成
- verified.md: 待创建
- review.md: 待创建
```

## 实现

读 `.ai_state/` 下所有文件, 汇总输出。不修改任何文件。

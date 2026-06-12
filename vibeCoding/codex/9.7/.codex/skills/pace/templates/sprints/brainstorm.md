---
sprint_slug: ""
triggered_at: ""               # YYYY-MM-DD HH:MM
trigger_reason: ""             # user_explicit | main_agent_vague_detection | large_requirement
converged: false
next_route: ""                 # plan | roadmap | direct_design (System)
---

# Brainstorm — {sprint_slug}

## 用户最初描述

[原文记录, 不要修饰]

---

## 第 1 轮 · 追问真问题

**AI 追问**: 你想解决的核心问题是什么? (不要停在第一个脱口而出的方案)

**用户回答**:
[用户回应]

---

## 第 2 轮 · 评估方案 / 提出替代

**AI 评估 + 替代**:
- 你提到的方案 A: ✅... / ❌...
- 备选方案 B: ...
- 备选方案 C: ...

**用户选择**:
[用户回应]

---

## 第 N 轮 · ...

[根据需要继续, 每轮加 ## 段]

---

## 收敛

- **真问题**: ...
- **选定方向**: ...
- **关键 insight** (若有, 触发 `/compound add explore` 提示): ...

## 下一步路由

- [ ] plan (单 feature 清晰, 直接进 plan stage)
- [ ] roadmap (大需求, 进 roadmap stage 拆 feature)
- [ ] direct design (System 路径需求清晰)

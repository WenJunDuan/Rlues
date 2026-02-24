---
name: brainstorm
description: R₀b 苏格拉底式需求精炼 — 写代码前激活
context: main
---
# Brainstorm (R₀b 需求精炼)

Path B+ 任务在写代码前**必须**激活本 skill。

## 流程

```
探索项目上下文 → 逐个提问澄清 → 提出 2-3 方案
→ context7 查库文档 → 分段呈现设计 → 用户确认?
  → 否: 修改重呈 → 是: 写入 session.md → 进入 plan-first
```

### 1. 探索上下文
- `augment-context-engine` 搜索相关代码和依赖
- 读 `.ai_state/knowledge.md` 了解历史经验
- 读 `.ai_state/conventions.md` 了解编码规范

### 2. 逐个提问 (苏格拉底式)
- **一次只问一个问题**, 不堆叠
- 优先选择题, 开放题为辅
- 覆盖: 用户目标、使用场景、边界、非功能需求
- YAGNI 原则: 主动砍不必要的功能

### 3. 提出 2-3 个方案
- 每方案: 架构概述 + 优劣 + 复杂度预估
- context7 查依赖库文档验证可行性
- 标注推荐方案及理由

### 4. 分段呈现设计
- 每段 ≤ 200 字, 用户确认后再下一段

### 5. 确认输出
- 写入 `.ai_state/session.md` 设计方案段
- cunzhi `DESIGN_READY` 确认
- 进入 `plan-first` skill

## 铁律
- 设计未确认前**不写任何代码**

---
name: brainstorm
description: R/D 阶段增强 — augment-context-engine 搜代码 + 读 conventions + ADR 输出
context: main
---

# Brainstorm — R/D 阶段编排参数

## 在 SP brainstorming 基础上增加:

1. **先搜后想**: `augment-context-engine` 查现有实现 → 避免重复造轮子
2. **读 conventions**: 读 `.ai_state/conventions.md` 对齐项目规范
3. **读经验**: 读 `.knowledge/` 相关条目 → 复用已有教训
4. **ADR 输出**: 决策记录到 `.ai_state/design.md`:
   ```
   ## ADR-{N}: {决策标题}
   - 状态: proposed | accepted | rejected
   - 背景: {augment 搜索结果摘要}
   - 方案: {2-3 个候选}
   - 决策: {选定方案 + 理由}
   - 后果: {预期影响 + 风险}
   ```
5. **cunzhi DESIGN_READY**: D 阶段结束前暂停确认

## 与 SP brainstorming 分工

SP: 苏格拉底提问法, 方案探索, 设计验证流程
本 Skill: augment 搜索集成, 项目规范对齐, ADR 格式化输出

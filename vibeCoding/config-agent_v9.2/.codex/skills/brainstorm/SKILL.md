---
name: brainstorm
description: 需求精炼与 Spec 生成 — R₀ 阶段使用
---
## 管道位置: R₀ → 产出 design.md → 交给 R

## 流程
1. **访谈**: 向用户提问 (技术细节、边界情况、非功能需求)
2. **发散**: 列出 2-3 个候选方案, 标注优劣
3. **收敛**: 选定方案, 输出 Spec 到 .ai_state/design.md

## Spec 模板
```markdown
# {功能名} Spec

## 需求
- MUST: {必须实现}
- SHOULD: {应该实现}
- COULD: {可以实现}

## 验收标准
- [ ] {条件1}
- [ ] {条件2}

## 选定方案: {名称}
理由: ...
```

---
name: brainstorm
description: 需求精炼与Spec生成 — R₀
context: main
---
## 管道位置: R₀ → design.md → R

1. **访谈**: AskUserQuestion (技术/边界/非功能)
2. **发散**: 2-3候选方案, 标注优劣
3. **收敛**: Spec → design.md

## Spec模板
```markdown
# {功能} Spec
## 需求
- MUST: {必须} / SHOULD: {应该} / COULD: {可以}
## 验收标准
- [ ] {条件}
## 选定方案: {名称}
```

## 例子
```markdown
# JWT认证 Spec
## 需求
- MUST: POST /login 返回 access+refresh token
- MUST: access 15min, refresh 7d
- SHOULD: token黑名单
## 验收标准
- [ ] POST /login 200+tokens
- [ ] 过期→401
- [ ] refresh→新access
```

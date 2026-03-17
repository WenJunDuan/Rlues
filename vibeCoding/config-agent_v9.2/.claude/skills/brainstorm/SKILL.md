---
name: brainstorm
description: 需求精炼与 Spec 生成 — R₀ 阶段使用
context: main
---
## 管道位置: R₀ → 产出 design.md → 交给 R

## 流程
1. **访谈**: 用 AskUserQuestion 向用户提问 (技术细节、边界情况、非功能需求)
2. **发散**: 列出 2-3 个候选方案, 每个方案标注优劣
3. **收敛**: 选定方案, 输出 Spec

## Spec 模板 (写入 .ai_state/design.md)
```markdown
# {功能名} Spec

## 需求
- MUST: {必须实现的功能}
- SHOULD: {应该实现的功能}
- COULD: {可以实现的功能}

## 验收标准
- [ ] {具体可验证的条件1}
- [ ] {具体可验证的条件2}

## 候选方案
### 方案A: {名称}
优势: ... / 劣势: ... / 复杂度: O(...)

## 选定方案: {A/B/C}
理由: ...
```

## 例子
```markdown
# JWT认证 Spec

## 需求
- MUST: 用户登录返回 access_token + refresh_token
- MUST: access_token 15min 过期, refresh_token 7d 过期
- SHOULD: 支持 token 黑名单 (登出即失效)
- COULD: 支持多设备登录管理

## 验收标准
- [ ] POST /login 返回 200 + tokens
- [ ] 过期 token 返回 401
- [ ] refresh 接口返回新 access_token
```

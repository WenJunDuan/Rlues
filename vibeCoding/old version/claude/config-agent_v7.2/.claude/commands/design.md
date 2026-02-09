---
description: 架构与交互设计模式
triggers: ["/design", "设计", "架构"]
loads: ["ar", "ui", "thinking/"]
---

# /design - 架构设计模式

> **Data First**: 在写任何逻辑前，先定义 interface/schema。
> — Linus Torvalds

## 工作流

```
问题分析 → 数据结构设计 → 方案对比 → [DESIGN_FREEZE] → 用户确认
```

## 执行步骤

### 1. 问题分析（第一性原理）
```markdown
需求: "实现用户认证"
↓ 分解
1. 认证的本质是什么？→ 验证身份
2. 需要存储什么？→ 凭证、会话
3. 核心流程？→ 登录、验证、登出
```

### 2. 数据结构设计 (Data First)
```typescript
// 先定义数据，再写逻辑
interface User {
  id: string;
  email: string;
  passwordHash: string;
}

interface Session {
  id: string;
  userId: string;
  expiresAt: Date;
}
```

**自问**: 这是最简的结构吗？

### 3. 方案设计与对比
```markdown
## 方案对比

| 维度 | 方案A | 方案B |
|------|-------|-------|
| 数据结构 | JWT Token | Session表 |
| 复杂度 | 低 | 中 |
| 优点 | 无需存储 | 可控性强 |
| 缺点 | 无法主动失效 | 需要存储 |
| Linus评分 | 4/5 | 3/5 |
```

### 4. Linus审查
- [ ] Data First: 数据结构最简？
- [ ] Naming: 命名准确？
- [ ] Simplicity: 无过度设计？
- [ ] Compatibility: 向后兼容？

### 5. 寸止点
```
输出 [DESIGN_FREEZE]
等待用户选择方案
禁止自作主张
```

## UI设计协作

当涉及UI时，加载 `ui` 角色：

```markdown
## 组件设计
- 结构: [组件层次]
- 状态: Hover/Active/Loading/Error
- 样式: Tailwind配置

## 交互流程
- 用户操作 → 状态变化 → 视觉反馈
```

**协作**: UI设计后需等待AR确认数据结构支持该展示。

## 输出模板

```markdown
## 技术设计文档

### 1. 问题本质
[第一性原理分析]

### 2. 数据结构
[Interface定义]

### 3. 方案对比
[对比表格]

### 4. 推荐方案
[推荐及理由]

### 📋 [DESIGN_FREEZE]
等待用户批准
```

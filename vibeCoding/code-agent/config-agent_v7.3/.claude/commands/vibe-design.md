---
name: vibe-design
aliases: ["/vd"]
description: 架构设计模式，Data First
loads:
  agents: ["ar", "ui"]
  skills: ["thinking/"]
  plugins: ["frontend-design"]
---

# /vibe-design - 架构设计模式

> **Data First**: 在写任何逻辑前，先定义 interface/schema。

## 触发方式

```bash
/vibe-design            # 完整设计
/vibe-design --ui       # 侧重UI设计
/vd                     # 简写
```

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

**自问**: 这是最简的结构吗？能删掉什么？

### 3. 方案对比
```markdown
| 维度 | 方案A | 方案B |
|------|-------|-------|
| 数据结构 | JWT | Session |
| 复杂度 | 低 | 中 |
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

当涉及UI时，加载 `ui` 角色和 `frontend-design` 插件：

```markdown
## 组件设计
- 结构: [组件层次]
- 状态: Hover/Active/Loading/Error
- 样式: Tailwind配置

## 交互流程
用户操作 → 状态变化 → 视觉反馈
```

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
等待用户选择
```

## 与frontend-design插件集成

加载官方 `frontend-design` 插件增强前端设计能力。

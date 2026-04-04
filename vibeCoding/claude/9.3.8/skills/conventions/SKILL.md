---
effort: low
description: >
  当遇到不确定的项目规范、查询 Agent 历史错误模式、或需要更新项目知识库时触发。
---

# Conventions Skill: 项目知识库

## 两个文件

### .ai_state/conventions.md — 项目规范 + Gotchas

记录项目特定的规范和 Agent 易犯的错误。格式:

```markdown
## 项目规范
- API 路由统一前缀 /api/v1
- 错误码使用 ErrorCode enum, 不用硬编码字符串
- 所有时间字段用 ISO 8601 格式

## Gotchas
- ❌ 用 bcrypt.hash(pwd, 10) → ✅ 用项目封装的 hashPassword(pwd), 在 src/utils/crypto.ts
- ❌ 直接写 SQL → ✅ 用 Prisma ORM, 项目不使用 raw SQL
- ❌ 测试中硬编码端口 3000 → ✅ 用 process.env.PORT || 0 让系统分配
```

### .ai_state/lessons.md — 经验教训

记录每次迭代的关键教训。格式:

```markdown
- [2026-04-02] Sprint 1: bcrypt v5 的 hash 函数是异步的, 忘记 await 导致存了 Promise 对象
- [2026-04-02] Sprint 1: Prisma unique 约束错误码是 P2002, 需要特殊处理
```

## 使用规则

1. **读**: 每次进入新阶段时, 检查 conventions.md 的 Gotchas 是否有相关内容
2. **写**: V 阶段归档时更新; 遇到新的坑时立即更新
3. **如果 conventions.md 说了, 就按它做** — 这是项目积累的经验, 优先于通用规范

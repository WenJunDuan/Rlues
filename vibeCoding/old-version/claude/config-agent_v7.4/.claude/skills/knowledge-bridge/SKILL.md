---
name: knowledge-bridge
description: 知识桥接，公司规范索引，反模式库
---

# Knowledge Bridge Skill

知识桥接，连接外部规范和项目约定。

## 外部规范索引

```markdown
## 公司规范（按需配置路径）

- **前端规范**: .claude/references/frontend-standards.md
- **后端规范**: .claude/references/backend-standards.md
- **API规范**: [配置路径]
```

## 反模式库 (Anti-Patterns)

### 通用反模式

```typescript
// ❌ 禁止: 使用 any 类型
const data: any = response.data;

// ✅ 正确: 明确类型
const data: UserResponse = response.data;
```

```typescript
// ❌ 禁止: 硬编码 Secret
const apiKey = 'sk-xxx';

// ✅ 正确: 环境变量
const apiKey = process.env.API_KEY;
```

### 数据库反模式

```typescript
// ❌ 禁止: N+1查询
for (const user of users) {
  const orders = await db.query('...', [user.id]);
}

// ✅ 正确: 批量查询
const orders = await db.query('... WHERE user_id IN (?)', [userIds]);
```

### 安全反模式

```typescript
// ❌ 禁止: SQL拼接
const sql = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ 正确: 参数化查询
const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
```

## 项目约定

在 `project_document/.ai_state/conventions.md` 中记录项目特定约定。

## 规范更新

代码审查意见应沉淀为规则：
1. 发现问题
2. 记录到反模式库
3. 更新自动化检查
4. 形成改进闭环

# 后端代码规范

> **"Data structures, not algorithms, are central to programming."** — Rob Pike

## 核心原则

- **Data First**: 先定义数据结构，再写逻辑
- **简洁至上**: 函数<50行，避免过度抽象
- **安全优先**: 输入验证，参数化查询

---

## 数据结构优先

```typescript
// ✅ 先定义数据
interface User {
  id: string;
  email: string;
  passwordHash: string;
  createdAt: Date;
}

interface CreateUserDTO {
  email: string;
  password: string;
}

// 再写逻辑
function createUser(data: CreateUserDTO): User {
  // ...
}
```

---

## API 设计

### RESTful 规范

```typescript
// 资源命名
GET    /api/users          // 列表
POST   /api/users          // 创建
GET    /api/users/:id      // 详情
PUT    /api/users/:id      // 更新
DELETE /api/users/:id      // 删除

// 嵌套资源
GET    /api/users/:id/orders
```

### 响应格式

```typescript
// 成功
{
  "success": true,
  "data": { ... }
}

// 错误
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required"
  }
}
```

---

## 错误处理

```typescript
// ✅ 好：明确的错误处理
async function getUser(id: string): Promise<User> {
  const user = await db.query('SELECT * FROM users WHERE id = $1', [id]);
  
  if (!user) {
    throw new NotFoundError(`User ${id} not found`);
  }
  
  return user;
}

// ✅ 好：Result类型
type Result<T, E = Error> = 
  | { ok: true; value: T }
  | { ok: false; error: E };
```

---

## 数据库

### 参数化查询

```typescript
// ❌ SQL注入风险
const sql = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ 参数化查询
const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
```

### 避免N+1

```typescript
// ❌ N+1问题
for (const user of users) {
  const orders = await db.query('SELECT * FROM orders WHERE user_id = $1', [user.id]);
}

// ✅ 批量查询
const orders = await db.query('SELECT * FROM orders WHERE user_id = ANY($1)', [userIds]);
```

### 事务处理

```typescript
// ✅ 使用事务
await db.transaction(async (tx) => {
  await tx.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, fromId]);
  await tx.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, toId]);
});
```

---

## 安全

### 输入验证

```typescript
// ✅ 使用验证库
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

function createUser(data: unknown) {
  const parsed = CreateUserSchema.parse(data);
  // ...
}
```

### 密码存储

```typescript
// ✅ 使用bcrypt
import bcrypt from 'bcrypt';

const hash = await bcrypt.hash(password, 10);
const isValid = await bcrypt.compare(password, hash);
```

### 敏感信息

```typescript
// ❌ 硬编码
const apiKey = 'sk-xxx';

// ✅ 环境变量
const apiKey = process.env.API_KEY;
```

---

## 日志

```typescript
// ✅ 结构化日志
logger.info('User created', {
  userId: user.id,
  email: user.email,
  // 不记录密码等敏感信息
});

// ✅ 错误日志
logger.error('Failed to create user', {
  error: error.message,
  stack: error.stack,
});
```

---

## 检查清单

- [ ] 数据结构先定义
- [ ] 函数 <50行
- [ ] 输入已验证
- [ ] 参数化查询
- [ ] 错误处理完整
- [ ] 日志脱敏
- [ ] 环境变量存密钥

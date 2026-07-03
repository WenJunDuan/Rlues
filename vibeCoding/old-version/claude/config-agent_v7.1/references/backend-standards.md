# 后端代码规范

> **"Bad programmers worry about the code. Good programmers worry about data structures."** — Linus Torvalds

## Linus 检查清单

### 设计层面
- [ ] **Data First**: 数据模型是最简的吗？
- [ ] **Naming**: API/函数命名准确？
- [ ] **Simplicity**: 是否过度抽象？
- [ ] **Compatibility**: API向后兼容？

### 代码层面
- [ ] TypeScript 无 `any`
- [ ] 函数 <50行
- [ ] 完整的错误处理
- [ ] 输入验证

---

## 数据模型

### ✅ 好的设计

```typescript
// 最简的数据结构
interface User {
  id: string;
  email: string;
  passwordHash: string;
  createdAt: Date;
}

// 只包含必要字段
interface CreateUserDTO {
  email: string;
  password: string;
}
```

### ❌ 避免的设计

```typescript
// 过度设计
interface User {
  id: string;
  uuid: string;  // 冗余
  email: string;
  emailNormalized: string;  // 可以派生
  emailVerified: boolean;
  emailVerifiedAt: Date;  // 冗余，有值即验证
  // ... 50个字段
}
```

---

## API 设计

### RESTful 原则

```typescript
// 资源命名
GET    /api/users          // 获取列表
GET    /api/users/:id      // 获取单个
POST   /api/users          // 创建
PUT    /api/users/:id      // 更新
DELETE /api/users/:id      // 删除

// 嵌套资源
GET    /api/users/:id/orders
```

### 响应格式

```typescript
// 成功响应
{
  "data": { ... },
  "meta": { "total": 100 }  // 可选
}

// 错误响应
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required"
  }
}
```

---

## 错误处理

### ✅ 好的错误处理

```typescript
// 明确的错误类型
class ValidationError extends Error {
  constructor(
    public field: string,
    message: string
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

// 完整的错误处理
async function createUser(data: CreateUserDTO): Promise<User> {
  // 验证
  if (!data.email) {
    throw new ValidationError('email', 'Email is required');
  }
  
  // 检查重复
  const existing = await db.user.findByEmail(data.email);
  if (existing) {
    throw new ConflictError('User already exists');
  }
  
  // 创建
  return db.user.create(data);
}
```

### ❌ 避免的错误处理

```typescript
// 吞掉错误
try {
  await doSomething();
} catch (e) {
  // 什么都不做
}

// 模糊的错误
throw new Error('Something went wrong');
```

---

## 输入验证

```typescript
// 使用 Zod
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

async function createUser(input: unknown) {
  const data = createUserSchema.parse(input);
  // 继续处理...
}
```

---

## 数据库

### ✅ 好的查询

```typescript
// 参数化查询（防SQL注入）
const user = await db.query(
  'SELECT * FROM users WHERE id = $1',
  [userId]
);

// 只查需要的字段
const users = await db.user.findMany({
  select: { id: true, email: true }
});
```

### ❌ 避免的查询

```typescript
// SQL注入风险
const sql = `SELECT * FROM users WHERE id = ${userId}`;

// N+1 查询
const users = await db.user.findMany();
for (const user of users) {
  user.orders = await db.order.findByUser(user.id); // N次查询
}
```

---

## 安全

### 检查清单
- [ ] 输入验证
- [ ] 参数化查询
- [ ] 密码哈希 (bcrypt)
- [ ] JWT安全配置
- [ ] 敏感数据加密
- [ ] 日志脱敏

### 密码处理

```typescript
import bcrypt from 'bcrypt';

// 哈希密码
const hash = await bcrypt.hash(password, 10);

// 验证密码
const valid = await bcrypt.compare(password, hash);
```

---

## 日志

```typescript
// 结构化日志
logger.info('User created', {
  userId: user.id,
  email: user.email,  // 注意脱敏
});

// 错误日志
logger.error('Failed to create user', {
  error: err.message,
  stack: err.stack,
});
```

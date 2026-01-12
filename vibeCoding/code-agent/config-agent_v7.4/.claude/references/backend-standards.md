# 后端代码规范

## 核心原则

- **Data First**: 先定义数据结构
- **简洁至上**: 函数<50行
- **安全优先**: 输入验证，参数化查询

---

## 数据结构优先

```typescript
// ✅ 先定义数据
interface User {
  id: string;
  email: string;
  passwordHash: string;
}

// 再写逻辑
function createUser(data: CreateUserDTO): User { }
```

---

## API 设计

```typescript
// RESTful
GET    /api/users
POST   /api/users
GET    /api/users/:id
PUT    /api/users/:id
DELETE /api/users/:id
```

---

## 安全

```typescript
// ❌ SQL注入
const sql = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ 参数化
const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);

// ✅ 密码存储
const hash = await bcrypt.hash(password, 10);

// ✅ 环境变量
const apiKey = process.env.API_KEY;
```

---

## 检查清单

- [ ] 数据结构先定义
- [ ] 函数 <50行
- [ ] 输入已验证
- [ ] 参数化查询
- [ ] 错误处理完整

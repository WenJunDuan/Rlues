---
name: code-simplifier
description: 代码简化器，KISS原则执行者，Linus品味守护者
trigger: 开发阶段自动加载
---

# Code Simplifier Skill

> **"Simplicity is the ultimate sophistication."** — Leonardo da Vinci
> **"代码越少，Bug越少。"** — 工程真理

## 核心使命

在开发过程中**主动识别和简化**复杂代码，确保代码符合 Linus 的"品味"标准。

---

## 🎯 简化原则

### 1. 函数简化

```typescript
// ❌ 过长函数 (>50行)
function processUser(data) {
  // ... 100行代码
}

// ✅ 拆分为小函数
function processUser(data) {
  const validated = validateUser(data);
  const normalized = normalizeUser(validated);
  return saveUser(normalized);
}
```

### 2. 条件简化

```typescript
// ❌ 嵌套地狱
if (a) {
  if (b) {
    if (c) {
      doSomething();
    }
  }
}

// ✅ 早返回
if (!a) return;
if (!b) return;
if (!c) return;
doSomething();
```

### 3. 循环简化

```typescript
// ❌ 手动循环
const result = [];
for (let i = 0; i < items.length; i++) {
  if (items[i].active) {
    result.push(items[i].name);
  }
}

// ✅ 声明式
const result = items
  .filter(item => item.active)
  .map(item => item.name);
```

### 4. 类型简化

```typescript
// ❌ 过度类型体操
type DeepPartial<T> = T extends object 
  ? { [P in keyof T]?: DeepPartial<T[P]> } 
  : T;

// ✅ 简单直接（除非真的需要）
interface UserUpdate {
  name?: string;
  email?: string;
}
```

### 5. 抽象简化

```typescript
// ❌ 过度抽象
abstract class AbstractRepositoryFactory<T extends BaseEntity> {
  abstract createRepository(): IRepository<T>;
}

// ✅ 需要时再抽象
function getUsers(): User[] {
  return db.query('SELECT * FROM users');
}
```

---

## 🔍 自动检测规则

开发时自动检测以下问题：

| 检测项 | 阈值 | 动作 |
|:---|:---|:---|
| 函数行数 | >50行 | 建议拆分 |
| 嵌套深度 | >3层 | 建议重构 |
| 参数数量 | >4个 | 建议封装对象 |
| 圈复杂度 | >10 | 建议简化 |
| 重复代码 | >3处 | 建议提取 |
| 魔法数字 | 任意 | 建议常量 |

---

## 📋 简化检查清单

每次代码提交前检查：

### Linus 品味清单
- [ ] **能删吗？** — 这段代码真的需要吗？
- [ ] **能合并吗？** — 两个相似的函数能合一吗？
- [ ] **能简化吗？** — 有更简单的写法吗？
- [ ] **好读吗？** — 3个月后能看懂吗？
- [ ] **好改吗？** — 需求变了容易改吗？

### 代码指标
- [ ] 函数 < 50行
- [ ] 文件 < 300行
- [ ] 嵌套 < 3层
- [ ] 参数 < 5个
- [ ] 无 `any` 类型
- [ ] 无魔法数字

---

## 🔄 简化流程

```
写代码 → 自检 → 发现复杂 → 简化 → 验证 → 提交
                    ↓
              记录到 Memory
              (下次避免)
```

---

## 💾 记忆沉淀

发现的简化模式和反模式，记录到 Memory MCP：

```javascript
memory.add({
  category: "code_pattern",
  content: "避免超过3层嵌套，使用早返回模式",
  tags: ["simplification", "nesting"]
})
```

---

## 🛠️ 重构技巧

### 提取函数
```typescript
// Before
if (user.age >= 18 && user.country === 'US' && user.verified) {
  // ...
}

// After
function canAccess(user: User): boolean {
  return user.age >= 18 && user.country === 'US' && user.verified;
}

if (canAccess(user)) {
  // ...
}
```

### 替换条件为多态
```typescript
// Before
function getArea(shape) {
  if (shape.type === 'circle') return Math.PI * shape.radius ** 2;
  if (shape.type === 'square') return shape.side ** 2;
}

// After
interface Shape { getArea(): number; }
class Circle implements Shape { getArea() { return Math.PI * this.radius ** 2; } }
class Square implements Shape { getArea() { return this.side ** 2; } }
```

### 使用Map替代Switch
```typescript
// Before
switch (status) {
  case 'pending': return '待处理';
  case 'approved': return '已批准';
  case 'rejected': return '已拒绝';
}

// After
const STATUS_MAP = {
  pending: '待处理',
  approved: '已批准',
  rejected: '已拒绝',
};
return STATUS_MAP[status];
```

---

## ⚠️ 不要过度简化

简化有度，以下情况保持原样：

1. **性能关键路径** — 可读性让位于性能
2. **已稳定的遗留代码** — 不破坏正常工作的代码
3. **团队约定的模式** — 遵循项目规范
4. **第三方库的用法** — 按文档来

---

## 📊 简化报告

每次开发完成后，输出简化报告：

```markdown
## 代码简化报告

### 已简化
- `src/auth/login.ts`: 拆分为3个函数，减少30行
- `src/utils/format.ts`: 移除重复代码

### 建议简化
- `src/api/orders.ts:45`: 嵌套4层，建议重构

### 指标
- 平均函数长度: 25行 ✅
- 最大嵌套深度: 2层 ✅
- 重复代码: 0处 ✅
```

---

**触发**: 开发阶段自动加载 | **协作**: LD + QE | **记忆**: 沉淀到 Memory MCP

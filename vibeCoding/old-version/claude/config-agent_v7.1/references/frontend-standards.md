# 前端代码规范

> **"Simple is better than complex."** — The Zen of Python (也适用于前端)

## Linus 检查清单

### 设计层面
- [ ] **Data First**: 状态结构是最简的吗？
- [ ] **Naming**: 组件/变量命名准确？
- [ ] **Simplicity**: 是否过度封装？
- [ ] **Taste**: UI代码清晰易读？

### 代码层面
- [ ] TypeScript 无 `any`
- [ ] 组件 <200行
- [ ] 函数 <50行
- [ ] Props 类型完整

---

## TypeScript

### ✅ 好的实践

```typescript
// 明确的类型定义
interface User {
  id: string;
  email: string;
  name: string;
}

// Props类型
interface ButtonProps {
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}

// 返回类型明确
function formatDate(date: Date): string {
  return date.toISOString();
}
```

### ❌ 避免的实践

```typescript
// any类型
const data: any = response.data;

// 隐式any
function process(data) { }

// 类型断言过多
const user = data as unknown as User;
```

---

## React 组件

### ✅ 好的组件

```tsx
// 简单、单一职责
function UserCard({ user }: { user: User }) {
  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
}

// 清晰的状态管理
function LoginForm() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await login(email);
    } catch (err) {
      setError(err.message);
    }
  };
  
  return (/* ... */);
}
```

### ❌ 避免的组件

```tsx
// 过大的组件 (>200行)
function GodComponent() {
  // 500行代码...
}

// 过度嵌套
function DeepNested() {
  return (
    <div>
      <div>
        <div>
          <div>
            {/* 太深了 */}
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 状态管理

### 原则
- 状态最小化
- 就近原则（能放组件内就放组件内）
- 避免冗余状态

### ✅ 好的状态

```typescript
// 最小状态
const [items, setItems] = useState<Item[]>([]);
// 派生计算
const total = items.reduce((sum, item) => sum + item.price, 0);
```

### ❌ 避免的状态

```typescript
// 冗余状态
const [items, setItems] = useState<Item[]>([]);
const [total, setTotal] = useState(0); // 可以从items派生
```

---

## 样式

### 原则
- 使用语义化类名
- 避免内联样式（除非动态）
- CSS-in-JS 或 Tailwind 保持一致

### ✅ 好的样式

```tsx
// 语义化
<button className="btn btn-primary">Submit</button>

// Tailwind
<button className="px-4 py-2 bg-blue-500 text-white rounded">
  Submit
</button>
```

---

## 错误处理

```tsx
// 边界错误处理
function UserProfile({ userId }: { userId: string }) {
  const { data, error, isLoading } = useUser(userId);
  
  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return <NotFound />;
  
  return <Profile user={data} />;
}
```

---

## 性能

### 检查项
- [ ] 避免不必要的重渲染
- [ ] 大列表使用虚拟化
- [ ] 图片懒加载
- [ ] 代码分割

### Memo 使用原则
```tsx
// 只在确实需要时使用
const ExpensiveComponent = memo(function ExpensiveComponent({ data }) {
  // 复杂计算...
});
```

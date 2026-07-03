# 前端代码规范

> **"The best code is no code at all."** — Jeff Atwood

## 核心原则

- **简洁至上**: 组件<200行，函数<50行
- **可读性**: 代码是给人读的
- **一致性**: 遵循项目既有模式

---

## TypeScript 规范

### 类型定义

```typescript
// ✅ 好：明确的类型
interface User {
  id: string;
  name: string;
  email: string;
}

// ❌ 差：使用any
const data: any = response.data;
```

### 类型守卫

```typescript
function isUser(obj: unknown): obj is User {
  return typeof obj === 'object' && obj !== null && 'id' in obj;
}
```

---

## React 规范

### 组件结构

```typescript
interface UserCardProps {
  user: User;
  onEdit?: (user: User) => void;
}

export function UserCard({ user, onEdit }: UserCardProps) {
  // 1. hooks
  const [isEditing, setIsEditing] = useState(false);
  
  // 2. handlers
  const handleEdit = () => {
    setIsEditing(true);
    onEdit?.(user);
  };
  
  // 3. render
  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <button onClick={handleEdit}>Edit</button>
    </div>
  );
}
```

### Hooks 规范

```typescript
// ✅ 好：自定义Hook
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    fetchUser(userId)
      .then(setUser)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [userId]);
  
  return { user, loading, error };
}
```

### 条件渲染

```typescript
// ✅ 好：清晰的条件渲染
function Content({ loading, error, data }: ContentProps) {
  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return <Empty />;
  return <DataView data={data} />;
}

// ❌ 差：嵌套三元
return loading ? <Spinner /> : error ? <Error /> : data ? <Data /> : null;
```

---

## 状态管理

```typescript
// ✅ 局部状态：useState
const [isOpen, setIsOpen] = useState(false);

// ✅ 全局状态：Zustand/Jotai
const useAuthStore = create((set) => ({
  user: null,
  login: (user) => set({ user }),
}));
```

---

## 性能优化

```typescript
// ✅ memo + useMemo
const MemoizedList = memo(function List({ items }: ListProps) {
  return items.map(item => <Item key={item.id} item={item} />);
});

const expensiveValue = useMemo(() => {
  return items.filter(item => item.active).sort(byDate);
}, [items]);
```

---

## 错误处理

```typescript
// ✅ try-catch + 用户提示
async function handleSubmit(data: FormData) {
  try {
    await submitForm(data);
    toast.success('提交成功');
  } catch (error) {
    toast.error('提交失败，请重试');
    logError(error);
  }
}
```

---

## 检查清单

- [ ] TypeScript 无 any
- [ ] 组件 <200行
- [ ] 无console.log（除调试）
- [ ] 响应式布局OK
- [ ] 错误处理完整
- [ ] 关键逻辑有注释

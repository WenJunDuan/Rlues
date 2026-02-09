# 前端代码规范

## 核心原则

- **简洁至上**: 组件<200行，函数<50行
- **可读性**: 代码是给人读的
- **一致性**: 遵循项目既有模式

---

## TypeScript 规范

```typescript
// ✅ 好：明确的类型
interface User {
  id: string;
  name: string;
}

// ❌ 差：使用any
const data: any = response.data;
```

---

## React 规范

### 组件结构
```typescript
interface Props {
  user: User;
}

export function UserCard({ user }: Props) {
  // 1. hooks
  const [state, setState] = useState();
  
  // 2. handlers
  const handleClick = () => {};
  
  // 3. render
  return <div>{user.name}</div>;
}
```

### Hooks规范
```typescript
// ✅ 自定义Hook
function useUser(id: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchUser(id).then(setUser).finally(() => setLoading(false));
  }, [id]);
  
  return { user, loading };
}
```

---

## 检查清单

- [ ] TypeScript 无 any
- [ ] 组件 <200行
- [ ] 无console.log
- [ ] 响应式布局OK
- [ ] 错误处理完整

# 前端开发规范

## 技术栈
```yaml
框架: React 18+ / Vue 3+ / Next.js
语言: TypeScript (严格模式)
样式: Tailwind CSS / CSS Modules
状态: Zustand / Pinia / Redux Toolkit
测试: Jest / Vitest + Testing Library
```

## 项目结构
```
src/
├── components/      # 可复用组件
│   ├── ui/          # 基础 UI 组件
│   └── features/    # 功能组件
├── pages/           # 页面组件
├── hooks/           # 自定义 Hooks
├── stores/          # 状态管理
├── services/        # API 服务
├── utils/           # 工具函数
├── types/           # 类型定义
└── styles/          # 全局样式
```

## 组件规范

### 命名
```yaml
组件: PascalCase (UserProfile.tsx)
hooks: camelCase + use 前缀 (useAuth.ts)
工具: camelCase (formatDate.ts)
类型: PascalCase + I 前缀可选 (User.ts)
```

### 组件结构
```typescript
// 1. 类型定义
interface Props {
  title: string;
  onClick?: () => void;
}

// 2. 组件实现
export function Component({ title, onClick }: Props) {
  // 3. Hooks
  const [state, setState] = useState();
  
  // 4. 事件处理
  const handleClick = useCallback(() => {
    onClick?.();
  }, [onClick]);
  
  // 5. 渲染
  return <div onClick={handleClick}>{title}</div>;
}
```

### 组件原则
```yaml
单一职责: 一个组件做一件事
组合优于继承: 使用 children 和 props
状态提升: 共享状态放父组件
副作用隔离: 使用 useEffect 管理
```

## TypeScript 规范

### 类型优先
```typescript
// ✓ 明确的类型
function getUser(id: string): Promise<User> { }

// ✗ 避免 any
function process(data: any) { }  // Bad

// ✓ 使用 unknown 替代
function process(data: unknown) { }
```

### 类型定义
```typescript
// 接口用于对象结构
interface User {
  id: string;
  name: string;
}

// 类型别名用于联合/交叉
type Status = 'pending' | 'success' | 'error';
type UserWithRole = User & { role: Role };
```

## 样式规范

### Tailwind 优先
```tsx
// ✓ 使用 Tailwind
<div className="flex items-center gap-4 p-4 bg-white rounded-lg">

// 复杂样式抽取
const buttonStyles = "px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600";
```

### CSS Modules
```typescript
// 用于复杂组件
import styles from './Component.module.css';

<div className={styles.container}>
```

## 状态管理

### 本地状态优先
```yaml
组件状态: useState
复杂组件: useReducer
跨组件: Context / Zustand
服务端: React Query / SWR
```

### Zustand 示例
```typescript
const useStore = create<State>((set) => ({
  count: 0,
  increment: () => set((s) => ({ count: s.count + 1 })),
}));
```

## 性能优化

### React 优化
```typescript
// 记忆化组件
const MemoComponent = memo(Component);

// 记忆化计算
const computed = useMemo(() => expensive(data), [data]);

// 记忆化回调
const handler = useCallback(() => {}, [deps]);
```

### 加载优化
```typescript
// 懒加载组件
const LazyComponent = lazy(() => import('./Heavy'));

// 图片优化
<Image src="..." loading="lazy" />
```

## 测试规范

### 测试文件
```yaml
位置: 同目录 __tests__/ 或 .test.ts
命名: ComponentName.test.tsx
```

### 测试示例
```typescript
describe('Button', () => {
  it('should render with text', () => {
    render(<Button>Click</Button>);
    expect(screen.getByText('Click')).toBeInTheDocument();
  });
  
  it('should call onClick', () => {
    const onClick = jest.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

## 代码质量

### ESLint 配置
```yaml
extends:
  - eslint:recommended
  - plugin:@typescript-eslint/recommended
  - plugin:react-hooks/recommended
```

### 检查清单
```markdown
- [ ] TypeScript 严格模式
- [ ] 无 any 类型
- [ ] 组件职责单一
- [ ] 适当的记忆化
- [ ] 测试覆盖核心逻辑
```

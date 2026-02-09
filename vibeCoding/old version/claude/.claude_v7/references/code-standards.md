# 代码规范参考

## 提交前检查清单

- [ ] TypeScript 无 `any`，类型完整
- [ ] Security: 输入验证？注入风险？
- [ ] 函数 <50行，组件 <200行
- [ ] 完整的错误处理
- [ ] 边界情况已考虑
- [ ] 已通过 `寸止` 请求验收
- [ ] 重要决策已存入 `memory`

## Linus 审查清单

- [ ] **Data First**: 数据结构是最简的吗？
- [ ] **Naming**: 命名准确反映本质？
- [ ] **Simplicity**: 是否过度设计？
- [ ] **Compatibility**: 向后兼容？

## 反模式

### 过度抽象
```typescript
// ❌ 
abstract class AbstractFactory<T> { }

// ✅ 
function createUser(data: CreateUserDTO): User { }
```

### 忽略错误处理
```typescript
// ❌
const data = await fetch('/api').then(r => r.json());

// ✅
const res = await fetch('/api');
if (!res.ok) throw new Error(`HTTP ${res.status}`);
const data = await res.json();
```

### 自作主张
```typescript
// ❌ 发现多个方案直接选择

// ✅ 调用寸止让用户决定
寸止.ask({
  question: "发现两个可行方案",
  options: ["方案A: ...", "方案B: ..."]
})
```

### 使用any
```typescript
// ❌
const data: any = response.data;

// ✅
interface UserResponse {
  id: string;
  name: string;
}
const data: UserResponse = response.data;
```

## 好的模式

### 错误处理
```typescript
// Result 类型
type Result<T, E = Error> = 
  | { ok: true; value: T }
  | { ok: false; error: E };

function parseJSON<T>(json: string): Result<T> {
  try {
    return { ok: true, value: JSON.parse(json) };
  } catch (e) {
    return { ok: false, error: e as Error };
  }
}
```

### 输入验证
```typescript
function createUser(data: unknown): User {
  const parsed = userSchema.safeParse(data);
  if (!parsed.success) {
    throw new ValidationError(parsed.error);
  }
  return userRepository.create(parsed.data);
}
```

### 简洁函数
```typescript
// 单一职责，<50行
function validateEmail(email: string): boolean {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email);
}
```

## 代码注释规范

```typescript
/**
 * @riper: Path B - Collaborative
 * @role: LD (Lead Developer)
 * @complexity: 3 files
 * @principle: SOLID-S
 */
```

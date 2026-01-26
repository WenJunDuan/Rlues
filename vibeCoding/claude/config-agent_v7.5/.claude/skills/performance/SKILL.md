---
name: performance
description: 性能优化技能，识别和解决性能问题
trigger: 性能审查或优化需求时
---

# Performance Skill

> **性能是功能的一部分**
> 用户感知的响应时间决定产品体验

---

## 🎯 性能指标

### 前端指标

| 指标 | 目标 | 说明 |
|:---|:---|:---|
| **FCP** (First Contentful Paint) | < 1.8s | 首次内容渲染 |
| **LCP** (Largest Contentful Paint) | < 2.5s | 最大内容渲染 |
| **FID** (First Input Delay) | < 100ms | 首次输入延迟 |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 累积布局偏移 |
| **TTI** (Time to Interactive) | < 3.8s | 可交互时间 |

### 后端指标

| 指标 | 目标 | 说明 |
|:---|:---|:---|
| **响应时间** | < 200ms | API 响应 |
| **吞吐量** | 根据需求 | QPS |
| **错误率** | < 0.1% | 5xx 错误 |
| **P99 延迟** | < 1s | 99分位延迟 |

---

## 🔍 性能问题检测

### 前端检测清单

```markdown
## 前端性能检查

### 渲染性能
- [ ] 是否有不必要的重渲染？
- [ ] 列表是否使用了虚拟滚动？
- [ ] 大数据是否分页？
- [ ] 是否使用了 memo/useMemo/useCallback？

### 资源加载
- [ ] 图片是否压缩/懒加载？
- [ ] JS/CSS 是否分包？
- [ ] 是否使用了 CDN？
- [ ] 是否启用了缓存？

### 包体积
- [ ] 是否有未使用的依赖？
- [ ] 是否按需加载？
- [ ] 是否 tree-shaking？
```

### 后端检测清单

```markdown
## 后端性能检查

### 数据库
- [ ] 是否有 N+1 查询？
- [ ] 索引是否合理？
- [ ] 是否有慢查询？
- [ ] 是否使用了连接池？

### 缓存
- [ ] 热点数据是否缓存？
- [ ] 缓存策略是否合理？
- [ ] 缓存是否会穿透？

### 并发
- [ ] 是否有竞态条件？
- [ ] 锁粒度是否合适？
- [ ] 是否有死锁风险？
```

---

## 🛠️ 常见优化方案

### 1. N+1 查询优化

```javascript
// ❌ N+1 问题
const users = await User.findAll();
for (const user of users) {
  user.orders = await Order.findByUserId(user.id);
}

// ✅ 批量查询
const users = await User.findAll();
const userIds = users.map(u => u.id);
const orders = await Order.findByUserIds(userIds);
const orderMap = groupBy(orders, 'userId');
users.forEach(u => u.orders = orderMap[u.id] || []);
```

### 2. 循环中的异步优化

```javascript
// ❌ 串行执行
for (const id of ids) {
  await processItem(id);
}

// ✅ 并行执行
await Promise.all(ids.map(id => processItem(id)));

// ✅ 控制并发数
import pLimit from 'p-limit';
const limit = pLimit(5);
await Promise.all(ids.map(id => limit(() => processItem(id))));
```

### 3. React 渲染优化

```javascript
// ❌ 每次都创建新对象
<Component style={{ color: 'red' }} />

// ✅ 提取常量
const style = { color: 'red' };
<Component style={style} />

// ❌ 每次都创建新函数
<Button onClick={() => handleClick(id)} />

// ✅ 使用 useCallback
const handleClick = useCallback(() => {
  // ...
}, [id]);
```

### 4. 列表优化

```javascript
// ❌ 渲染所有项
{items.map(item => <Item key={item.id} {...item} />)}

// ✅ 虚拟滚动（只渲染可见项）
import { FixedSizeList } from 'react-window';
<FixedSizeList
  height={400}
  itemCount={items.length}
  itemSize={50}
>
  {({ index, style }) => (
    <Item style={style} {...items[index]} />
  )}
</FixedSizeList>
```

### 5. 数据库索引

```sql
-- 分析慢查询
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'xxx';

-- 添加索引
CREATE INDEX idx_users_email ON users(email);

-- 复合索引
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
```

### 6. 缓存策略

```javascript
// 读取缓存
async function getUser(id) {
  // 1. 查缓存
  let user = await cache.get(`user:${id}`);
  if (user) return user;
  
  // 2. 查数据库
  user = await db.query('SELECT * FROM users WHERE id = ?', [id]);
  
  // 3. 写缓存
  await cache.set(`user:${id}`, user, { ttl: 3600 });
  
  return user;
}
```

---

## 📊 性能分析工具

### 前端

| 工具 | 用途 |
|:---|:---|
| **Chrome DevTools** | Performance/Network/Memory |
| **Lighthouse** | 综合评分 |
| **Web Vitals** | Core Web Vitals |
| **Bundle Analyzer** | 包体积分析 |

### 后端

| 工具 | 用途 |
|:---|:---|
| **数据库 EXPLAIN** | 查询分析 |
| **APM 工具** | 全链路追踪 |
| **压测工具** | 性能基准 |

---

## 📋 性能优化清单

### 开发时
- [ ] 避免 N+1 查询
- [ ] 循环中不用 await
- [ ] 合理使用 memo
- [ ] 添加必要索引

### 上线前
- [ ] 图片已压缩
- [ ] 资源已压缩
- [ ] 启用 gzip
- [ ] 配置缓存头

### 定期审查
- [ ] 分析慢查询
- [ ] 检查内存使用
- [ ] 评估缓存命中率
- [ ] 关注 P99 延迟

---

## ⚠️ 性能反模式

```javascript
// 记录到 Memory 中避免重复
memory.add({
  category: "forbidden_action",
  content: "禁止在循环中使用单独的 await",
  tags: ["performance", "async"]
})

memory.add({
  category: "forbidden_action",
  content: "禁止 SELECT * 查询大表",
  tags: ["performance", "database"]
})
```

---

## 🎯 优化优先级

```
1. 先测量，后优化
2. 优化影响最大的瓶颈
3. 不要过早优化
4. 权衡收益和复杂度
```

---

**方法**: 测量→分析→优化→验证 | **工具**: DevTools + APM | **原则**: 数据驱动

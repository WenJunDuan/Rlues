---
name: debug
description: 问题诊断和调试技能
trigger: 遇到Bug或异常时
---

# Debug Skill

> **调试是找到问题根因的艺术**
> 系统化方法比盲目尝试更有效

---

## 🔍 调试方法论

### 科学调试法

```
复现 → 隔离 → 定位 → 分析 → 修复 → 验证 → 总结
```

### 二分查找法

```
问题出现
    ↓
在中间点检查
    ↓
问题在前半？─Yes─▶ 检查前半
    │
    No
    ↓
检查后半 ─────▶ 重复直到定位
```

### 橡皮鸭调试法

逐行解释代码在做什么，经常能发现问题。

---

## 📋 调试清单

### 1. 复现问题

```markdown
## 问题复现

### 环境
- OS: [操作系统]
- Node: [版本]
- 浏览器: [如适用]

### 复现步骤
1. [步骤1]
2. [步骤2]
3. [观察到的问题]

### 预期行为
[应该发生什么]

### 实际行为
[实际发生了什么]

### 复现率
[ ] 100% 必现
[ ] 偶现 (约X%)
```

### 2. 收集信息

```markdown
## 收集的信息

### 错误信息
```
[完整错误堆栈]
```

### 相关日志
```
[相关日志片段]
```

### 最近变更
- [最近的代码变更]
- [最近的配置变更]
```

### 3. 形成假设

```markdown
## 假设清单

| # | 假设 | 验证方法 | 结果 |
|---|------|----------|------|
| 1 | [假设1] | [方法] | ⏳ |
| 2 | [假设2] | [方法] | ⏳ |
```

### 4. 验证假设

逐一验证，排除可能性。

### 5. 修复和验证

修复后确保：
- [ ] 原问题已解决
- [ ] 没有引入新问题
- [ ] 相关测试通过

---

## 🛠️ 调试工具

### 前端调试

```javascript
// 断点调试
debugger;

// 日志分组
console.group('User Data');
console.log('id:', user.id);
console.log('name:', user.name);
console.groupEnd();

// 表格展示
console.table(users);

// 性能计时
console.time('fetchUsers');
await fetchUsers();
console.timeEnd('fetchUsers');
```

### Node.js 调试

```bash
# 启动调试器
node --inspect app.js

# 使用 Chrome DevTools
chrome://inspect
```

### 网络调试

```javascript
// 拦截请求
fetch = new Proxy(fetch, {
  apply(target, thisArg, args) {
    console.log('Fetch:', args[0]);
    return target.apply(thisArg, args);
  }
});
```

---

## 🔬 常见问题模式

### 1. undefined/null 错误

```javascript
// 症状
TypeError: Cannot read property 'x' of undefined

// 调试
console.log('object:', object);  // 检查对象
console.log('type:', typeof object);

// 常见原因
- 异步未等待
- 条件渲染时机
- 数据未初始化
```

### 2. 异步问题

```javascript
// 症状
数据不是预期值，有时正确有时错误

// 调试
async function debug() {
  console.log('1. before fetch');
  const data = await fetch(...);
  console.log('2. after fetch', data);
  return data;
}

// 常见原因
- 忘记 await
- 竞态条件
- Promise 未处理
```

### 3. 状态问题

```javascript
// 症状
UI 不更新，状态似乎没变

// 调试
useEffect(() => {
  console.log('state changed:', state);
}, [state]);

// 常见原因
- 直接修改状态（未创建新对象）
- 依赖数组错误
- 闭包陷阱
```

### 4. 性能问题

```javascript
// 症状
页面卡顿，响应慢

// 调试
console.time('operation');
// ... 操作
console.timeEnd('operation');

// 常见原因
- 大量循环
- 频繁重渲染
- 内存泄漏
```

---

## 📊 调试日志模板

```markdown
## 调试记录

### 问题描述
[简述问题]

### 时间线
- HH:MM 发现问题
- HH:MM 开始调试
- HH:MM 定位根因
- HH:MM 修复完成

### 根因分析
[详细分析]

### 解决方案
[如何修复的]

### 预防措施
[如何避免再次发生]

### 耗时
- 复现: X分钟
- 定位: X分钟
- 修复: X分钟
- 总计: X分钟
```

---

## ⚡ 快速排查指南

| 问题类型 | 首先检查 |
|:---|:---|
| 页面白屏 | Console 错误 |
| API 失败 | Network 面板 |
| 数据不对 | 打印变量值 |
| 性能慢 | Performance 面板 |
| 样式问题 | Elements 面板 |
| 状态问题 | React/Vue DevTools |

---

## 🔗 与错误学习协作

调试完成后：

```javascript
// 如果是新类型的问题，记录到 Memory
memory.add({
  category: "lesson_learned",
  content: "[问题描述] 的原因是 [根因]",
  tags: ["debug", "具体问题类型"]
})
```

---

## ⚠️ 调试禁忌

- ❌ 不复现就猜测
- ❌ 一次改多处
- ❌ 忘记删调试代码
- ❌ 不验证就提交
- ❌ 不记录不总结

---

**方法**: 科学调试法 | **工具**: DevTools + 日志 | **输出**: 调试记录 + 教训

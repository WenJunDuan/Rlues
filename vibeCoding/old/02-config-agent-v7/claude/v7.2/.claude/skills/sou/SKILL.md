---
name: sou
description: 语义代码搜索，augment-context-engine
mcp_tool: augment-context-engine
---

# Sou Skill (Augment)

语义代码搜索，R1阶段首选工具。

## 优先级

```
1. sou (augment) — 语义搜索，首选
2. grep — 精确文本匹配
3. read_file — 最后手段
```

## 调用方式

```javascript
// 语义搜索
sou.search("用户认证逻辑")
sou.search("订单状态流转")

// 关键词搜索
sou.search("handleSubmit")
```

## 使用场景

| 场景 | 搜索示例 |
|:---|:---|
| 理解业务逻辑 | `sou.search("订单状态流转")` |
| 定位功能代码 | `sou.search("用户登录处理")` |
| 查找模式 | `sou.search("错误处理方式")` |

## 最佳实践

```javascript
// ✅ 好
sou.search("用户注册验证逻辑")
sou.search("支付回调处理")

// ❌ 差
sou.search("function")  // 太泛
sou.search("const")     // 无意义
```

## 降级

sou不可用时:
```bash
grep -r "关键词" --include="*.ts" ./src
```

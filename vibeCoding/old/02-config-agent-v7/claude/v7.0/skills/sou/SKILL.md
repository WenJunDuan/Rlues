---
name: sou
description: 语义代码搜索，augment-context-engine
mcp_tool: augment-context-engine
---

# Sou Skill (Augment Context Engine)

语义代码搜索，R1阶段首选工具。

## 优先级

```
1. sou (augment-context-engine) — 语义搜索，首选
2. grep — 精确文本匹配
3. read_file — 最后手段
```

## 调用方式

### 语义搜索
```javascript
sou.search("用户认证逻辑")
sou.search("JWT token 验证")
sou.search("数据库连接配置")
```

### 关键词搜索
```javascript
sou.search("handleSubmit")
sou.search("useEffect cleanup")
```

## 使用场景

| 场景 | 搜索示例 |
|:---|:---|
| 理解业务逻辑 | `sou.search("订单状态流转")` |
| 定位功能代码 | `sou.search("用户登录处理")` |
| 查找模式 | `sou.search("错误处理方式")` |
| 接口定义 | `sou.search("API 接口定义")` |

## R1阶段标准流程

```
1. memory.recall(project_path)     // 加载记忆
2. sou.search("<关键词>")          // 语义搜索代码
3. 仅读取直接相关文件，禁止全量扫描
```

## 最佳实践

### ✅ 好的搜索
```javascript
sou.search("用户注册验证逻辑")     // 语义明确
sou.search("支付回调处理")         // 业务相关
```

### ❌ 避免的搜索
```javascript
sou.search("function")            // 太泛
sou.search("const")               // 无意义
```

## 降级方案

sou不可用时:
```bash
grep -r "关键词" --include="*.ts" ./src
find . -name "*.ts" -exec grep -l "关键词" {} \;
```

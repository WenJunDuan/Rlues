---
name: sou
description: 语义代码搜索，augment-context-engine
mcp_tool: augment-context-engine
---

# Sou Skill (Augment Context Engine)

语义代码搜索，R1阶段首选工具。

## 核心理念

> **深度分析**: 先理解上下文，再动手编码

遵循渐进式开发：在着手任何设计或编码工作前，必须完成前期调研。

## 优先级

```
1. sou (augment-context-engine) — 语义搜索，首选
2. grep — 精确文本匹配
3. read_file — 最后手段
```

## 调用方式

```javascript
sou.search("用户认证逻辑")
sou.search("JWT token 验证")
sou.search("数据库连接配置")
```

## R1阶段标准流程

```
1. memory.recall(project_path)     // 加载记忆
2. sou.search("<核心关键词>")      // 理解业务逻辑
3. sou.search("<技术关键词>")      // 理解技术实现
4. 仅读取直接相关文件             // 禁止全量扫描
```

## 搜索策略

### 第一性原理搜索
```javascript
// 先搜问题本质
sou.search("用户权限判断")

// 再搜实现细节
sou.search("权限中间件")
```

### 分层搜索
```javascript
// 1. 业务层
sou.search("订单状态流转")

// 2. 数据层
sou.search("订单表结构")

// 3. 接口层
sou.search("订单API")
```

## 最佳实践

### ✅ 好的搜索
```javascript
sou.search("用户注册验证逻辑")     // 语义明确
sou.search("支付回调处理")         // 业务相关
sou.search("错误处理模式")         // 寻找模式
```

### ❌ 避免的搜索
```javascript
sou.search("function")            // 太泛
sou.search("const")               // 无意义
sou.search("import")              // 无价值
```

## 降级方案

sou不可用时:
```bash
grep -r "关键词" --include="*.ts" ./src
find . -name "*.ts" -exec grep -l "关键词" {} \;
```

---
name: deepwiki
description: 技术文档查询，框架/库研究
mcp_tool: mcp-deepwiki
---

# Deepwiki Skill

技术文档查询，用于框架和库的研究。

## 使用场景

| 场景 | 示例 |
|:---|:---|
| 框架使用 | React Hooks最佳实践 |
| 库API | Prisma查询语法 |
| 配置说明 | Vite配置选项 |
| 最佳实践 | TypeScript类型技巧 |

## 调用方式

```javascript
deepwiki.query("React useEffect cleanup")
deepwiki.query("Prisma relation queries")
deepwiki.query("Next.js App Router")
```

## 使用时机

### I阶段（创新）
```
技术选型时查询:
- 框架特性对比
- 库的优缺点
- 性能考量
```

### E阶段（执行）
```
实现时查询:
- API具体用法
- 配置参数
- 常见问题
```

## 最佳实践

### ✅ 有效查询
```javascript
deepwiki.query("Prisma many-to-many relation")  // 具体问题
deepwiki.query("React 18 concurrent features")   // 版本相关
```

### ❌ 避免的查询
```javascript
deepwiki.query("how to code")    // 太泛
deepwiki.query("best framework") // 主观
```

## 降级方案

mcp-deepwiki不可用时 → Web搜索官方文档

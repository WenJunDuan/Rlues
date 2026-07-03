---
name: deepwiki
description: 技术文档查询，框架/库研究
mcp_tool: mcp-deepwiki
---

# Deepwiki Skill

技术文档查询，用于框架和库的研究。

## 核心理念

> **事实为本**: 以官方文档为准，不依赖过时的记忆

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

### I阶段（技术选型）
```javascript
// 框架对比
deepwiki.query("Next.js vs Remix comparison")

// 库特性
deepwiki.query("Zustand vs Jotai state management")
```

### E阶段（实现细节）
```javascript
// 具体用法
deepwiki.query("Prisma many-to-many relation")

// 配置参数
deepwiki.query("Tailwind CSS custom colors")
```

## 最佳实践

### ✅ 有效查询
```javascript
deepwiki.query("Prisma many-to-many relation")  // 具体问题
deepwiki.query("React 18 concurrent features")   // 版本相关
deepwiki.query("TypeScript satisfies operator")  // 语言特性
```

### ❌ 避免的查询
```javascript
deepwiki.query("how to code")    // 太泛
deepwiki.query("best framework") // 主观
```

## 降级方案

mcp-deepwiki不可用时 → Web搜索官方文档

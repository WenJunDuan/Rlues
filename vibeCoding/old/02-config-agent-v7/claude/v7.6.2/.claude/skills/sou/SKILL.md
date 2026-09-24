# Sou - 语义搜索 MCP

## 概述
Sou 是一个语义代码搜索工具，基于向量嵌入实现智能代码检索。

## 能力
```yaml
语义搜索:
  - 自然语言查询代码
  - 理解代码意图而非仅匹配关键词
  - 跨文件关联分析

代码理解:
  - 找到相关函数/类
  - 识别使用模式
  - 追踪依赖关系
```

## VibeCoding 集成

### 调用时机
```yaml
Research 阶段 (优先):
  - 理解现有代码结构
  - 查找相关实现
  - 识别修改影响范围

Execute 阶段:
  - 查找类似实现参考
  - 确认命名一致性
```

### MCP 调用
```javascript
// 基础搜索
sou_search({
  query: "用户认证相关的函数",
  scope: "src/",
  limit: 10
})

// 带过滤搜索
sou_search({
  query: "处理 JWT token 的代码",
  scope: "src/auth/",
  file_types: [".ts", ".js"],
  limit: 5
})
```

## 使用示例

### 查找功能实现
```javascript
// 查找登录相关代码
sou_search({
  query: "用户登录验证逻辑"
})

// 结果示例:
// [
//   { file: "src/auth/login.ts", line: 45, content: "async function validateLogin..." },
//   { file: "src/middleware/auth.ts", line: 12, content: "export const authMiddleware..." }
// ]
```

### 查找使用模式
```javascript
// 查找某个函数的使用
sou_search({
  query: "调用 validateUser 函数的地方"
})
```

### 查找相似实现
```javascript
// 查找类似的错误处理
sou_search({
  query: "API 错误响应处理模式"
})
```

## 最佳实践

### 查询技巧
```yaml
好的查询:
  - "处理用户认证的函数"
  - "数据库连接配置"
  - "React 组件的状态管理"

差的查询:
  - "function" (太泛)
  - "const a = 1" (太具体)
  - "代码" (无意义)
```

### 与 grep 对比
```yaml
sou 优势:
  - 理解语义，不只是文本匹配
  - 找到相关但用词不同的代码
  - 更智能的排序

grep 优势:
  - 精确匹配
  - 更快（无需向量计算）
  - 支持正则表达式

建议: 先用 sou 探索，再用 grep 精确定位
```

## 配置
```yaml
# orchestrator.yaml
mcp_tools:
  recommended:
    - name: sou
      purpose: "语义搜索"
      fallback: "grep/ripgrep"
```

## 降级策略
若 sou 不可用:
```bash
# 使用 ripgrep
rg "pattern" --type ts

# 使用 grep
grep -r "pattern" src/ --include="*.ts"
```

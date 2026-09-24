# MCP 工具清单

## 概述
VibeCoding 集成的 MCP (Model Context Protocol) 工具列表及使用说明。

## 核心工具

### memory
```yaml
用途: 知识持久化
状态: 必需

功能:
  - 存储技术决策
  - 记录项目经验
  - 跨会话知识保留

调用:
  memory_store({category, title, content, tags})
  memory_search({query, category?, limit?})
  memory_update({id, content})

降级: .ai_state/knowledge.md
```

### sequential-thinking
```yaml
用途: 深度推理
状态: 必需

功能:
  - 多步问题分解
  - 架构决策推理
  - 复杂问题诊断

调用:
  sequential_thinking({
    problem: "问题描述",
    context: "上下文",
    steps: ["步骤1", "步骤2"]
  })

降级: 内置推理流程
```

### sou
```yaml
用途: 语义代码搜索
状态: 推荐

功能:
  - 自然语言搜索代码
  - 语义理解匹配
  - 跨文件关联

调用:
  sou_search({
    query: "搜索内容",
    scope: "目录",
    limit: 10
  })

降级: grep/ripgrep
```

### context7
```yaml
用途: 需求文档分析
状态: 推荐

功能:
  - 解析需求文档
  - 提取关键信息
  - 结构化输出

调用:
  context7_analyze({
    content: "文档内容",
    output_format: "structured"
  })

降级: 手动分析
```

### playwright
```yaml
用途: 浏览器自动化测试
状态: 推荐

功能:
  - E2E 测试
  - 页面交互
  - 截图对比

调用:
  playwright_test({
    url: "测试地址",
    actions: [...]
  })

降级: 手动测试
```

### mcp-shrimp-task-manager
```yaml
用途: 任务管理
状态: 可选

功能:
  - 任务创建追踪
  - 依赖管理
  - 进度可视化

调用:
  shrimp_create_plan({
    project: "项目名",
    tasks: [...]
  })

降级: TODO.md
```

## 寸止工具

### cunzhi (若可用)
```yaml
用途: 专用寸止
优先级: 1

调用:
  cunzhi_pause({
    token: "PLAN_READY",
    summary: {...},
    options: [...]
  })
```

### mcp-feedback-enhanced
```yaml
用途: 通用反馈
优先级: 2

调用:
  mcp_feedback({
    type: "checkpoint",
    stage: "PLAN_READY",
    message: "...",
    require_response: true
  })
```

## 工具优先级

### 必需工具
```
1. memory - 知识管理
2. sequential-thinking - 深度推理
```

### 推荐工具
```
3. sou - 代码搜索
4. context7 - 需求分析
5. playwright - 测试
```

### 可选工具
```
6. mcp-shrimp-task-manager - 任务管理
7. cunzhi - 寸止
```

## 降级策略

### 工具不可用时
```yaml
检测: 调用失败或超时
处理: 自动使用降级方案
记录: 记录到错误日志

示例:
  memory 不可用 → 使用 .ai_state/knowledge.md
  sou 不可用 → 使用 grep/ripgrep
```

### 降级对照表
| 工具 | 降级方案 |
|:---|:---|
| memory | .ai_state/knowledge.md |
| sequential-thinking | 内置推理 |
| sou | grep/ripgrep |
| context7 | 手动分析 |
| playwright | 手动测试 |
| shrimp | TODO.md |

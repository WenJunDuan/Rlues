# Sequential Thinking - 深度推理 MCP

## 概述
Sequential Thinking 是一个支持多步推理的 MCP 工具，用于解决复杂问题。

## 能力
```yaml
多步推理:
  - 分解复杂问题
  - 逐步推导
  - 自我验证

深度分析:
  - 架构决策
  - 算法设计
  - 问题诊断
```

## VibeCoding 集成

### 调用时机
```yaml
Research 阶段:
  - 复杂需求分析
  - 系统边界梳理

Innovate 阶段 (主要):
  - 架构设计决策
  - 技术方案权衡
  - 风险评估

Execute 阶段:
  - 复杂算法实现
  - 难题调试

Review 阶段:
  - 代码质量分析
  - 性能问题诊断
```

### MCP 调用
```javascript
sequential_thinking({
  problem: "问题描述",
  context: "相关上下文",
  constraints: ["约束1", "约束2"],
  steps: [
    "步骤1描述",
    "步骤2描述",
    "步骤3描述"
  ]
})
```

## 使用示例

### 架构设计
```javascript
sequential_thinking({
  problem: "设计一个可扩展的插件系统",
  context: `
    现有系统: Express.js + TypeScript
    需求: 支持第三方插件、热加载
  `,
  constraints: [
    "向后兼容现有 API",
    "插件隔离，不影响主系统",
    "性能开销可控"
  ],
  steps: [
    "分析现有架构和扩展点",
    "调研常见插件系统模式",
    "设计插件接口和生命周期",
    "规划注册、加载、卸载机制",
    "评估安全性和性能影响"
  ]
})
```

### 算法优化
```javascript
sequential_thinking({
  problem: "优化搜索算法，当前 O(n²) 太慢",
  context: `
    数据量: 10万条
    当前实现: 双重循环匹配
    性能要求: <100ms
  `,
  steps: [
    "分析当前算法瓶颈",
    "列举可能的优化方向",
    "评估每种方案的复杂度",
    "选择最优方案并设计实现",
    "验证优化效果"
  ]
})
```

### 问题诊断
```javascript
sequential_thinking({
  problem: "生产环境内存泄漏",
  context: `
    现象: 内存持续增长
    时间: 运行 24h 后明显
    环境: Node.js 18
  `,
  steps: [
    "收集内存使用数据",
    "分析可能的泄漏来源",
    "检查常见泄漏模式",
    "定位具体泄漏代码",
    "验证修复效果"
  ]
})
```

### 重构规划
```javascript
sequential_thinking({
  problem: "重构 500 行的 UserService",
  context: `
    问题: 职责混杂、难以测试
    约束: 不能中断服务
  `,
  steps: [
    "识别当前职责边界",
    "规划拆分方案",
    "确定依赖注入点",
    "设计迁移步骤",
    "规划测试策略"
  ]
})
```

## 最佳实践

### 何时使用
```yaml
使用:
  - 问题复杂，需要多步推理
  - 涉及权衡和决策
  - 需要系统性分析

不使用:
  - 简单直接的问题
  - 只需要查找信息
  - 执行标准流程
```

### 步骤设计
```yaml
好的步骤:
  - 每步有明确目标
  - 步骤间有逻辑关系
  - 步骤粒度适中

差的步骤:
  - "想一想" (太模糊)
  - "解决问题" (太笼统)
  - 20个步骤 (太多)
```

## 配置
```yaml
# orchestrator.yaml
mcp_tools:
  required:
    - name: sequential-thinking
      purpose: "深度推理"
      fallback: "skills/thinking/SKILL.md"
```

## 降级策略
若 MCP 不可用，使用内置推理:
```markdown
## 思考过程

### 步骤 1: [标题]
[分析内容]

### 步骤 2: [标题]
[分析内容]

### 结论
[最终结论]
```

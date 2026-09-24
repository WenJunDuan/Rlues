# Research (R1) - 感知理解阶段

## 目标
深入理解需求和现有代码，为后续阶段建立准确的上下文。

## 执行步骤

### 1. 需求分析
```yaml
输入: 用户描述/需求文档
输出: 结构化需求理解

MCP增强:
  - context7: 解析复杂需求文档
  - memory: 查询历史相关决策
```

### 2. 代码探索
```yaml
动作: 读取相关文件

MCP增强:
  - sou: 语义搜索相关代码
    示例: sou_search("用户认证相关的代码")
  
本地工具:
  - grep/ripgrep: 关键词搜索
  - find: 文件定位
```

### 3. 依赖分析
```yaml
识别:
  - 直接依赖文件
  - 间接影响模块
  - 外部依赖包

工具:
  - 读取 import/require 语句
  - 检查 package.json
```

### 4. 上下文记录
```yaml
输出到: .ai_state/active_context.md

内容:
  - 需求摘要
  - 涉及文件列表
  - 关键发现
  - 风险识别
```

## MCP 工具使用

### sou - 语义搜索
```javascript
// 搜索相关代码
sou_search({
  query: "处理用户登录的函数",
  scope: "src/",
  limit: 10
})
```

### context7 - 需求分析
```javascript
// 解析需求文档
context7_analyze({
  content: "用户需求描述...",
  output_format: "structured"
})
```

### memory - 知识查询
```javascript
// 查询历史决策
memory_search({
  query: "之前关于认证的设计决策",
  limit: 5
})
```

## 输出模板
```markdown
## 需求理解

### 核心需求
[一句话描述]

### 涉及文件
- `path/to/file1.ts` - 需要修改的原因
- `path/to/file2.ts` - 需要修改的原因

### 依赖关系
- 依赖: [列表]
- 被依赖: [列表]

### 风险点
- [风险1]
- [风险2]

### 下一步
进入 [I/P] 阶段
```

## 质量检查
- [ ] 是否理解了核心需求
- [ ] 是否识别了所有相关文件
- [ ] 是否发现潜在风险
- [ ] 是否记录到 active_context.md

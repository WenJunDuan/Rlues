# Path A: 快速修复

## 适用条件
- 单文件修改
- 代码量 < 30行
- 无架构变更

## 流程: R → P → E → R2

### R (Research) - 感知理解
**加载**: `skills/riper/research.md`

1. 读取目标文件
2. 理解修改需求
3. 识别影响范围

**MCP 增强**:
```
若需搜索代码 → 调用 sou MCP
若需理解上下文 → 调用 context7 MCP
```

### P (Plan) - 生成计划
**加载**: `skills/riper/plan.md`

1. 生成简要 TODO.md
2. 更新 kanban.md (TODO栏)

**输出格式**:
```markdown
## TODO.md
- [ ] [文件名] 修改描述
```

**无需寸止** - Path A 计划简单，直接执行

### E (Execute) - 执行开发
**加载**: `skills/riper/execute.md`

1. 执行修改
2. 更新 kanban.md (DOING → DONE)

**MCP 增强**:
```
代码生成 → 可调用 codex (若配置)
代码精简 → 参考 skills/code-quality/SKILL.md
```

**执行规范**:
- 使用 str_replace 精确修改
- 保持最小变更原则
- 遵循 Linus 品味清单

### R2 (Review) - 验证闭环
**加载**: `skills/riper/review.md`

1. 验证修改结果
2. 检查无副作用
3. 更新状态文件

**MCP 增强**:
```
若有测试 → 调用 playwright MCP
```

**寸止**: `[TASK_DONE]`
```
调用 cunzhi MCP 或 mcp-feedback
等待用户验收
```

## 时间预估
- 总耗时: 5-15分钟
- 无中间等待点

# Path B: 计划开发

## 适用条件
- 2-10 个文件
- 需要设计但不跨模块
- 有明确边界的功能开发

## 流程: R → I → P → E → R2

### R (Research) - 感知理解
**加载**: `skills/riper/research.md`

1. 分析需求范围
2. 识别涉及文件
3. 理解现有架构

**MCP 增强**:
```yaml
需求分析: context7 MCP
代码搜索: sou MCP
深度理解: sequential-thinking MCP
```

**输出**: 需求理解摘要 (记录到 active_context.md)

### I (Innovate) - 方案设计
**加载**: `skills/riper/innovate.md`

1. 设计实现方案
2. 选择技术路线
3. 识别风险点

**MCP 增强**:
```yaml
复杂设计: sequential-thinking MCP (深度推理)
架构决策: 参考 references/backend-standards.md 或 frontend-standards.md
```

**输出**: 设计方案 (可选记录到 .ai_state/design.md)

### P (Plan) - 生成计划
**加载**: `skills/riper/plan.md`

1. 拆解任务为 TODO 列表
2. 确定执行顺序
3. 更新 kanban.md

**MCP 增强**:
```yaml
任务管理: mcp-shrimp-task-manager (若可用)
知识存储: memory MCP (记录计划决策)
```

**输出格式**:
```markdown
## TODO.md
### Phase 1: 基础实现
- [ ] [file1.ts] 任务描述
- [ ] [file2.ts] 任务描述

### Phase 2: 集成测试
- [ ] [test.ts] 测试描述
```

**寸止**: `[PLAN_READY]`
```
调用 cunzhi MCP
输出: 计划摘要 + 确认请求
等待用户确认后继续
```

### E (Execute) - 执行开发
**加载**: `skills/riper/execute.md`

按 TODO 顺序执行:

1. **每个任务**:
   - 移动到 DOING
   - 执行修改
   - 移动到 DONE

2. **代码质量**:
   - 加载 `skills/code-quality/SKILL.md`
   - 应用 Linus 品味清单
   - 保持简洁

**MCP 增强**:
```yaml
代码生成: codex (若配置，用于大量样板代码)
代码精简: 参考 skills/code-quality/SKILL.md
重构优化: sequential-thinking (复杂重构时)
```

**执行规范**:
- 先读后写
- 最小变更
- 保持一致性

### R2 (Review) - 验证闭环
**加载**: `skills/riper/review.md`

1. 逐项验证 TODO 完成情况
2. 运行相关测试
3. 检查代码质量

**MCP 增强**:
```yaml
测试执行: playwright MCP (E2E测试)
代码检查: 本地 lint/type-check
```

**验证清单**:
- [ ] 所有 TODO 完成
- [ ] 测试通过
- [ ] 无 TypeScript 错误
- [ ] 符合代码规范

**寸止**: `[TASK_DONE]`
```
调用 cunzhi MCP
输出: 完成摘要 + 验证结果
等待用户验收
```

## 时间预估
- 总耗时: 30分钟 - 2小时
- 1个等待点: PLAN_READY

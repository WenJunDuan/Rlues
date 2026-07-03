# Path C: 系统开发

## 适用条件
- 超过 10 个文件
- 跨模块/跨系统
- 需要架构设计
- 多阶段交付

## 流程: R → I → P → [E → R2]×n

### R (Research) - 深度感知
**加载**: `skills/riper/research.md`

1. 全面分析需求
2. 梳理系统边界
3. 识别依赖关系
4. 评估技术风险

**MCP 增强** (必须使用):
```yaml
需求分析: context7 MCP
代码搜索: sou MCP
深度理解: sequential-thinking MCP
知识查询: memory MCP (查历史决策)
```

**输出**: 
- 需求分析文档 → active_context.md
- 系统边界图 → 可选输出

### I (Innovate) - 架构设计
**加载**: `skills/riper/innovate.md`

1. 设计系统架构
2. 定义模块边界
3. 确定接口契约
4. 规划技术选型

**MCP 增强** (强烈推荐):
```yaml
架构推理: sequential-thinking MCP (多步推理)
参考规范: 
  - references/backend-standards.md
  - references/frontend-standards.md
知识存储: memory MCP (存储架构决策)
```

**角色协作** (可选):
```yaml
架构评审: agents/architect.md
产品对齐: agents/product.md
```

**输出**:
- 架构设计文档 → .ai_state/architecture.md
- 模块划分 → .ai_state/modules.md

**寸止**: `[DESIGN_FREEZE]`
```
调用 cunzhi MCP
输出: 架构设计摘要 + 模块划分 + 技术选型
等待用户确认设计方案
```

### P (Plan) - 分阶段规划
**加载**: `skills/riper/plan.md`

1. 按模块拆解任务
2. 定义阶段里程碑
3. 确定依赖顺序
4. 估算每阶段工作量

**MCP 增强**:
```yaml
任务管理: mcp-shrimp-task-manager (推荐)
知识存储: memory MCP
```

**输出格式**:
```markdown
## TODO.md

### Phase 1: 核心基础 [预计: 2小时]
- [ ] [core/base.ts] 基础类型定义
- [ ] [core/utils.ts] 工具函数
里程碑: 核心模块可用

### Phase 2: 业务实现 [预计: 3小时]
- [ ] [features/xxx.ts] 功能实现
- [ ] [features/yyy.ts] 功能实现
里程碑: 主要功能完成

### Phase 3: 集成测试 [预计: 1小时]
- [ ] [tests/integration.ts] 集成测试
- [ ] [tests/e2e.ts] E2E测试
里程碑: 测试通过
```

**寸止**: `[PLAN_READY]`
```
调用 cunzhi MCP
输出: 完整计划 + 阶段划分 + 时间估算
等待用户确认计划
```

### E → R2 循环 (每阶段)

#### E (Execute) - 阶段执行
**加载**: `skills/riper/execute.md`

执行当前阶段的所有 TODO:

1. 按顺序执行任务
2. 保持代码质量
3. 及时更新状态

**MCP 增强**:
```yaml
代码生成: codex (大量样板代码)
代码精简: skills/code-quality/SKILL.md
重构优化: sequential-thinking (复杂逻辑)
```

**质量检查点**:
- 每完成一个文件 → 本地验证
- 复杂修改 → 应用 Linus 品味清单
- 重构时 → 加载 skills/code-quality/SKILL.md

#### R2 (Review) - 阶段验证
**加载**: `skills/riper/review.md`

1. 验证阶段目标达成
2. 运行相关测试
3. 检查代码质量
4. 确认里程碑

**MCP 增强**:
```yaml
测试执行: playwright MCP
代码分析: 本地工具 (lint/type-check)
```

**阶段验证清单**:
- [ ] 阶段 TODO 全部完成
- [ ] 单元测试通过
- [ ] 类型检查通过
- [ ] 里程碑目标达成

**寸止**: `[PHASE_DONE]`
```
调用 cunzhi MCP
输出: 
  - 阶段完成摘要
  - 下一阶段预览
  - 是否继续确认
等待用户确认后进入下一阶段
```

### 最终验收

所有阶段完成后:

1. 全量回归测试
2. 整体代码审查
3. 文档更新

**寸止**: `[TASK_DONE]`
```
调用 cunzhi MCP
输出:
  - 项目完成总结
  - 所有阶段成果
  - 建议后续优化
等待用户最终验收
```

## 时间预估
- 总耗时: 数小时到数天
- 多个等待点: DESIGN_FREEZE, PLAN_READY, PHASE_DONE×n, TASK_DONE

## 错误恢复
若任意阶段失败:
1. 记录错误到 errors.md
2. 调用 `[VERIFICATION_FAILED]` 寸止
3. 等待用户决策: 重试/回滚/跳过

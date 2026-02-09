# Review (R2) - 验证闭环阶段

## 目标
验证所有任务正确完成，确保质量达标，形成闭环。

## 核心原则
1. **逐项核对**: 每个 TODO 都要验证
2. **多维检查**: 功能/类型/测试/规范
3. **客观记录**: 验证结果写入状态文件
4. **闭环完整**: 未通过不能结束

## 验证流程

### 1. TODO 核对
```yaml
检查每个任务:
  - [x] 文件已修改
  - [x] 改动符合需求
  - [x] kanban 状态正确
```

### 2. 代码质量检查
```yaml
自动检查:
  - TypeScript: tsc --noEmit
  - Lint: eslint .
  - Format: prettier --check

手动检查:
  - 逻辑正确性
  - 边界条件
  - 错误处理
```

### 3. 测试验证
```yaml
单元测试: npm test / jest
集成测试: 相关测试用例
E2E测试: playwright (若配置)
```

### 4. 结果记录
```yaml
输出到: .ai_state/active_context.md

内容:
  - 完成任务数
  - 验证结果
  - 发现的问题
```

## MCP 工具使用

### playwright - E2E 测试
```javascript
// 浏览器测试
playwright_test({
  url: "http://localhost:3000",
  actions: [
    { type: "click", selector: "#login" },
    { type: "fill", selector: "#email", value: "test@example.com" },
    { type: "assert", selector: ".welcome", text: "Welcome" }
  ]
})
```

### memory - 记录学习
```javascript
// 记录项目经验
memory_store({
  category: "project_learning",
  title: "Feature X 开发总结",
  content: "经验教训...",
  tags: ["learning", "feature-x"]
})
```

## 验证清单

### Path A (快速修复)
```markdown
- [ ] 修改已完成
- [ ] 功能正确
- [ ] 无类型错误
- [ ] 无副作用
```

### Path B (计划开发)
```markdown
- [ ] 所有 TODO 完成
- [ ] 单元测试通过
- [ ] 类型检查通过
- [ ] Lint 检查通过
- [ ] 功能符合需求
```

### Path C (系统开发)
```markdown
阶段验证:
- [ ] 阶段目标达成
- [ ] 里程碑完成
- [ ] 相关测试通过
- [ ] 代码质量达标

最终验证:
- [ ] 全部阶段完成
- [ ] 集成测试通过
- [ ] E2E 测试通过
- [ ] 性能达标
- [ ] 文档更新
```

## 代码审查要点

### 功能正确性
```
- 是否实现了需求
- 边界条件处理
- 错误场景覆盖
```

### 代码质量
```
- 命名清晰
- 逻辑简洁
- 无重复代码
- 适当注释
```

### 可维护性
```
- 模块边界清晰
- 依赖关系合理
- 易于测试
- 易于扩展
```

## 问题处理

### 发现问题时
```yaml
小问题:
  - 直接修复
  - 更新状态
  - 继续验证

大问题:
  - 记录到 errors.md
  - 触发 [VERIFICATION_FAILED]
  - 等待用户决策
```

### 验证失败处理
```
[VERIFICATION_FAILED]

问题: [描述]
影响: [范围]
建议: 
  1. 重试修复
  2. 回滚变更
  3. 跳过继续

等待用户选择...
```

## 寸止输出

### 阶段完成 (Path C)
```
[PHASE_DONE]

## Phase N 验证通过

### 完成情况
- 任务: 5/5 完成
- 测试: 全部通过
- 质量: 达标

### 下一阶段
Phase N+1: [名称]
预计: [时间]

继续执行？[Y/n]
```

### 任务完成 (所有路径)
```
[TASK_DONE]

## 任务验证通过

### 完成摘要
- 修改文件: N 个
- 新增代码: N 行
- 测试状态: 通过

### 验证结果
- [x] 功能正确
- [x] 类型检查
- [x] Lint 检查
- [x] 测试通过

### 后续建议
- [可选优化点]

请验收确认。
```

## 经验沉淀

### 完成后记录
```yaml
记录到 Memory MCP:
  - 技术决策及原因
  - 遇到的问题和解决方案
  - 可复用的模式
  - 需要避免的坑

降级: 记录到 .ai_state/knowledge.md
```

# Plan (P) - 任务规划阶段

## 目标
将设计方案拆解为可执行的 TODO 列表，确保可追踪、可验证。

## 核心原则
1. **原子化**: 每个 TODO 独立可完成
2. **可验证**: 每个 TODO 有明确完成标准
3. **有序性**: TODO 按依赖顺序排列
4. **可估算**: 标注预计耗时

## 执行步骤

### 1. 任务拆解
```yaml
输入: 设计方案
输出: TODO 列表

拆解原则:
  - 每个任务对应具体文件
  - 任务粒度: 15-60分钟可完成
  - 复杂任务继续拆分
```

### 2. 依赖排序
```yaml
分析:
  - 哪些任务必须先完成
  - 哪些任务可以并行
  - 关键路径在哪里

工具:
  - mcp-shrimp-task-manager (若可用)
```

### 3. 阶段划分 (Path C)
```yaml
划分依据:
  - 功能边界
  - 里程碑节点
  - 验证点

每阶段:
  - 独立可验证
  - 有明确里程碑
  - 标注预计时间
```

### 4. 更新状态
```yaml
文件更新:
  - TODO.md: 完整任务列表
  - kanban.md: 初始化 TODO 栏
```

## MCP 工具使用

### mcp-shrimp-task-manager
```javascript
// 创建任务计划
shrimp_create_plan({
  project: "feature-name",
  tasks: [
    { name: "任务1", file: "file1.ts", estimate: "30min" },
    { name: "任务2", file: "file2.ts", estimate: "45min", depends: ["任务1"] }
  ]
})
```

### memory - 存储计划
```javascript
// 记录计划决策
memory_store({
  category: "project_plan",
  title: "Feature X 开发计划",
  content: "任务拆解和排序依据...",
  tags: ["plan", "feature-x"]
})
```

## TODO.md 格式规范

### Path A (简单)
```markdown
## TODO

- [ ] [filename.ts] 修改描述
```

### Path B (标准)
```markdown
## TODO

### 实现任务
- [ ] [file1.ts] 任务描述 (~30min)
- [ ] [file2.ts] 任务描述 (~45min)

### 测试任务
- [ ] [test.ts] 测试描述 (~15min)

**预计总耗时**: 1.5小时
```

### Path C (分阶段)
```markdown
## TODO

### Phase 1: 基础设施 [预计: 2小时]
- [ ] [core/types.ts] 类型定义 (~30min)
- [ ] [core/utils.ts] 工具函数 (~30min)
- [ ] [core/base.ts] 基类实现 (~60min)
**里程碑**: 核心模块可导入使用

### Phase 2: 功能实现 [预计: 3小时]
- [ ] [features/a.ts] 功能A (~90min)
- [ ] [features/b.ts] 功能B (~90min)
**里程碑**: 主要功能可用

### Phase 3: 集成验证 [预计: 1小时]
- [ ] [tests/unit.ts] 单元测试 (~30min)
- [ ] [tests/e2e.ts] E2E测试 (~30min)
**里程碑**: 全部测试通过

**预计总耗时**: 6小时
```

## kanban.md 初始化
```markdown
## Kanban

### TODO
- [ ] 任务1
- [ ] 任务2
- [ ] 任务3

### DOING

### DONE
```

## 寸止点
计划生成后触发 `[PLAN_READY]`:
```
输出内容:
  - 任务总数
  - 阶段数 (Path C)
  - 预计总耗时
  - 首要任务预览

等待: 用户确认计划
确认后: 进入 Execute 阶段
```

## 质量检查
- [ ] 每个 TODO 有明确文件
- [ ] 任务粒度合适 (15-60min)
- [ ] 依赖顺序正确
- [ ] 有时间估算
- [ ] kanban.md 已更新

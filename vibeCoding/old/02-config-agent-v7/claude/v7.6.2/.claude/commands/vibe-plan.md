# /vibe-plan

## 用途
仅生成开发计划，不执行

## 语法
```bash
/vibe-plan <任务描述>
```

## 与 /vibe-code 的区别
| 指令 | 流程 | 输出 |
|:---|:---|:---|
| /vibe-code | R→I→P→E→R2 完整执行 | 代码变更 |
| /vibe-plan | R→I→P 只到规划 | TODO.md |

## 执行流程

### 1. Research 阶段
```yaml
加载: skills/research.md

执行:
  - 分析需求
  - 理解现有代码
  - 识别影响范围

MCP:
  - sou: 代码搜索
  - context7: 需求分析
```

### 2. Innovate 阶段 (若复杂)
```yaml
加载: skills/innovate.md

执行:
  - 设计方案
  - 技术决策
  - 风险评估

MCP:
  - sequential-thinking: 方案推理
```

### 3. Plan 阶段
```yaml
加载: skills/plan.md

执行:
  - 拆解任务
  - 排列顺序
  - 估算时间
  - 更新文件

输出:
  - TODO.md
  - kanban.md
```

### 4. 寸止
```yaml
触发: [PLAN_READY]

输出:
  - 任务总数
  - 阶段划分
  - 预计时间
  - 首要任务

等待: 用户决策
  - 执行 → 调用 /vibe-code --continue
  - 修改 → 根据反馈调整
  - 取消 → 清理状态
```

## 输出示例
```markdown
## [PLAN_READY] 计划生成完成

### 任务描述
实现用户搜索功能

### 分析结果
- 涉及文件: 4 个
- 推荐路径: Path B
- 复杂度: 中等

### TODO 列表
#### Phase 1: 后端 API
- [ ] [api/search.ts] 搜索接口 (~30min)
- [ ] [services/search.ts] 搜索服务 (~45min)

#### Phase 2: 前端组件
- [ ] [components/SearchBar.tsx] 搜索栏 (~30min)
- [ ] [components/SearchResults.tsx] 结果列表 (~45min)

### 预计时间
约 2.5 小时

### 选项
1. 确认执行
2. 修改计划
3. 取消任务
```

## 使用场景

### 预览工作量
```bash
/vibe-plan "添加多语言支持"
# 查看需要做什么，再决定是否执行
```

### 分享计划
```bash
/vibe-plan "重构数据库层"
# 生成计划后可以分享给团队讨论
```

### 迭代规划
```bash
/vibe-plan "实现新功能"
# 反复调整直到计划满意
# 然后 /vibe-code --continue
```

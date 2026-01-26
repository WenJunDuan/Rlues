# Path B: 计划开发

## 适用条件
- 2-10 个文件
- 需要设计但不跨模块
- 有明确边界的功能开发

## 简化九步
```
需求创建 → 需求审查 → 方案设计 → 方案审查 → 开发实施 → 代码提交 → 完成归档
   1          2          3          4          6          7          9
```

## 流程详解

### 1. 需求创建
```yaml
Agent: requirement-mgr
Skills:
  - knowledge-base (项目背景/规范)
  - experience (类似需求经验)
  - riper/research (需求分析)
  - service-analysis (服务理解)

动作:
  - 深入理解需求
  - 检索相关知识和经验
  - 分析技术约束
  - 生成需求文档

输出: .ai_state/requirements/REQ-xxx.md
```

### 2. 需求审查
```yaml
Agent: requirement-mgr
寸止点: [REQ_READY]

输出:
  - 需求摘要
  - 功能点列表
  - 验收标准
  - 技术约束

等待: 用户确认需求理解正确
```

### 3. 方案设计
```yaml
Agent: design-mgr
Skills:
  - knowledge-base (架构规范/技术栈)
  - experience (架构决策经验)
  - service-analysis (现有架构)
  - riper/innovate (方案设计)
  - thinking (深度推理)

动作:
  - 设计技术方案
  - 模块划分
  - 接口设计
  - 技术选型

输出: .ai_state/designs/DESIGN-xxx.md
```

### 4. 方案审查
```yaml
Agent: design-mgr
寸止点: [DESIGN_READY]

输出:
  - 架构概览
  - 模块划分
  - 技术选型及原因
  - 风险评估

等待: 用户确认设计方案
```

### 6. 开发实施
```yaml
Agent: impl-executor
Skills:
  - knowledge-base (代码规范/安全)
  - experience (编码经验)
  - riper/plan (任务规划)
  - riper/execute (代码实现)
  - code-quality (质量检查)

寸止点: [PLAN_READY]

动作:
  - 生成 TODO 列表
  - 按计划编码
  - 保持代码质量

输出:
  - TODO.md
  - 代码变更
```

### 7. 代码提交
```yaml
Agent: impl-executor
Skills:
  - riper/review (代码审查)
  - code-quality (规范检查)

动作:
  - 逐项验证 TODO
  - 运行测试
  - 提交代码
```

### 9. 完成归档
```yaml
Agent: experience-mgr
Skills:
  - experience (经验沉淀)
  - cunzhi (寸止)

寸止点: [TASK_DONE]

动作:
  - 沉淀有价值经验
  - 更新文档
  - 归档任务

输出:
  - 经验文档 (如有)
  - 完成摘要
```

## 时间预估
- 总耗时: 30分钟 - 2小时
- 寸止点: 4个

## 寸止点汇总
| Token | 步骤 | 说明 |
|:---|:---|:---|
| [REQ_READY] | 2 | 需求确认 |
| [DESIGN_READY] | 4 | 方案确认 |
| [PLAN_READY] | 6 | 计划确认 |
| [TASK_DONE] | 9 | 最终确认 |

## 知识库/经验集成
```yaml
需求阶段:
  - 检索项目背景
  - 检索类似需求经验

设计阶段:
  - 检索架构规范
  - 检索技术决策经验

开发阶段:
  - 检索代码规范
  - 检索编码经验和陷阱

完成阶段:
  - 沉淀新经验
```

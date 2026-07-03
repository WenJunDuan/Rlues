# 九步工作流

## 概述
VibeCoding v7.7 的完整开发流程，涵盖从需求到归档的全生命周期。

## 流程图
```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ 需求   │ → │ 需求   │ → │ 方案   │ → │ 方案   │ → │ 环境   │
│ 创建   │   │ 审查   │   │ 设计   │   │ 审查   │   │ 搭建   │
└────────┘   └────────┘   └────────┘   └────────┘   └────────┘
    1            2            3            4            5
    
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ 开发   │ → │ 代码   │ → │ 版本   │ → │ 完成   │
│ 实施   │   │ 提交   │   │ 发布   │   │ 归档   │
└────────┘   └────────┘   └────────┘   └────────┘
    6            7            8            9
```

## 详细步骤

### 1. 需求创建
```yaml
负责 Agent: requirement-mgr
触发 Skill: riper/research, knowledge-base

动作:
  - 理解用户需求
  - 检索知识库和经验
  - 生成需求文档 (REQ-xxx.md)
  - 分析技术约束
  - 评估影响范围

输出:
  - .ai_state/requirements/REQ-xxx.md
  - 更新 kanban.md
```

### 2. 需求审查
```yaml
负责 Agent: requirement-mgr
寸止点: [REQ_READY]

动作:
  - 检查需求完整性
  - 确认理解正确
  - 等待用户确认

输出:
  - 需求摘要
  - 功能点列表
  - 验收标准
  
等待: 用户确认后进入下一步
```

### 3. 方案设计
```yaml
负责 Agent: design-mgr
触发 Skill: riper/innovate, service-analysis

动作:
  - 基于需求设计方案
  - 分析现有架构
  - 设计模块和接口
  - 技术选型
  - 评估风险

输出:
  - .ai_state/designs/DESIGN-xxx.md
```

### 4. 方案审查
```yaml
负责 Agent: design-mgr
寸止点: [DESIGN_READY]

动作:
  - 检查设计完整性
  - 确认技术可行性
  - 等待用户确认

输出:
  - 架构概览
  - 技术选型
  - 风险评估
  
等待: 用户确认后进入下一步
```

### 5. 环境搭建
```yaml
负责 Agent: impl-executor
触发 Skill: (按需)

动作:
  - 准备开发环境
  - 安装依赖
  - 配置工具
  - 创建分支

输出:
  - 环境就绪确认
  
注意: 简单项目可跳过此步
```

### 6. 开发实施
```yaml
负责 Agent: impl-executor
触发 Skill: riper/plan, riper/execute, code-quality

动作:
  - 生成 TODO 列表
  - 按计划编码
  - 检索编码经验
  - 保持代码质量
  - 更新进度

寸止点:
  - [PLAN_READY]: TODO 生成后 (Path B/C)
  - [PHASE_DONE]: 阶段完成后 (Path C)

输出:
  - 代码变更
  - 更新 kanban.md
```

### 7. 代码提交
```yaml
负责 Agent: impl-executor
触发 Skill: riper/review, code-quality

动作:
  - 代码自审
  - 运行测试
  - 检查规范
  - 提交代码

输出:
  - Git commit
  - 测试报告
```

### 8. 版本发布
```yaml
负责 Agent: impl-executor
寸止点: [RELEASE_READY]

动作:
  - 准备发布清单
  - 执行发布流程
  - 验证发布结果

输出:
  - 发布确认
  
等待: 用户确认发布
```

### 9. 完成归档
```yaml
负责 Agent: experience-mgr + impl-executor
触发 Skill: experience
寸止点: [TASK_DONE]

动作:
  - 沉淀经验
  - 更新文档
  - 归档任务
  - 清理状态

输出:
  - 经验文档 (EXP-xxx.md)
  - 任务归档
  
等待: 用户最终确认
```

## 路径简化

### Path A (快速修复)
```
需求创建 → 开发实施 → 代码提交 → 完成归档
   1           6           7           9
   
跳过: 2(需求审查), 3-4(方案), 5(环境), 8(发布)
寸止: [TASK_DONE]
```

### Path B (计划开发)
```
需求创建 → 需求审查 → 方案设计 → 方案审查 → 开发实施 → 代码提交 → 完成归档
   1          2          3          4          6          7          9
   
跳过: 5(环境), 8(发布)
寸止: [REQ_READY], [DESIGN_READY], [PLAN_READY], [TASK_DONE]
```

### Path C (系统开发)
```
完整九步
寸止: 全部
```

## 寸止点汇总

| Token | 步骤 | 说明 |
|:---|:---|:---|
| `[REQ_READY]` | 2 | 需求确认 |
| `[DESIGN_READY]` | 4 | 方案确认 |
| `[PLAN_READY]` | 6 | 计划确认 |
| `[PHASE_DONE]` | 6 | 阶段确认 (Path C) |
| `[RELEASE_READY]` | 8 | 发布确认 |
| `[TASK_DONE]` | 9 | 最终确认 |

## 状态流转
```yaml
任务状态:
  created → analyzing → designing → planned → developing → testing → releasing → completed → archived

每个状态对应的步骤:
  created: 1
  analyzing: 2
  designing: 3-4
  planned: 6 (TODO生成后)
  developing: 6 (编码中)
  testing: 7
  releasing: 8
  completed: 9
  archived: 9 (最终)
```

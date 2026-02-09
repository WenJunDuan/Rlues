# Path C: 系统开发

## 适用条件
- 超过 10 个文件
- 跨模块/跨系统
- 需要完整架构设计
- 多阶段交付

## 完整九步
```
需求创建 → 需求审查 → 方案设计 → 方案审查 → 环境搭建 
    → 开发实施 → 代码提交 → 版本发布 → 完成归档
```

## 流程详解

### 1. 需求创建
```yaml
Agent: requirement-mgr
Skills:
  - knowledge-base (全面检索)
  - experience (深度检索)
  - riper/research (深度分析)
  - service-analysis (系统理解)

动作:
  - 全面分析需求
  - 梳理系统边界
  - 识别依赖关系
  - 评估技术风险
  - 生成完整需求文档

输出: 
  - .ai_state/requirements/REQ-xxx.md
  - 系统边界图
```

### 2. 需求审查
```yaml
Agent: requirement-mgr
寸止点: [REQ_READY]

输出:
  - 需求分析报告
  - 功能清单
  - 非功能需求
  - 验收标准
  - 风险识别

等待: 用户确认
```

### 3. 方案设计
```yaml
Agent: design-mgr
Skills:
  - knowledge-base (架构规范)
  - experience (架构经验)
  - service-analysis (系统分析)
  - riper/innovate (架构设计)
  - thinking (深度推理)

动作:
  - 设计系统架构
  - 定义模块边界
  - 设计接口契约
  - 规划技术选型
  - 评估风险

输出:
  - .ai_state/designs/DESIGN-xxx.md
  - 架构图
  - 接口文档
```

### 4. 方案审查
```yaml
Agent: design-mgr
寸止点: [DESIGN_READY]

输出:
  - 架构设计摘要
  - 模块划分表
  - 技术选型决策
  - 风险评估报告
  - 实施计划预览

等待: 用户确认设计
```

### 5. 环境搭建
```yaml
Agent: impl-executor
Skills:
  - knowledge-base (环境规范)

动作:
  - 准备开发环境
  - 安装依赖
  - 配置工具链
  - 创建开发分支
  - 设置 CI/CD (如需)

输出:
  - 环境就绪确认
```

### 6. 开发实施 (分阶段)
```yaml
Agent: impl-executor
Skills:
  - knowledge-base (代码规范)
  - experience (编码经验)
  - riper/plan (分阶段规划)
  - riper/execute (代码实现)
  - riper/review (阶段验证)
  - code-quality (质量检查)

寸止点:
  - [PLAN_READY]: TODO 生成后
  - [PHASE_DONE]: 每阶段完成后

动作:
  - 按模块拆解任务
  - 定义阶段里程碑
  - 逐阶段开发
  - 阶段验证

输出:
  - 分阶段 TODO.md
  - 阶段代码
  - 阶段测试
```

### 7. 代码提交
```yaml
Agent: impl-executor
Skills:
  - riper/review (完整审查)
  - code-quality (全面检查)

动作:
  - 全量代码审查
  - 集成测试
  - 提交代码
  - 创建 PR

输出:
  - Git commits
  - 测试报告
  - PR 链接
```

### 8. 版本发布
```yaml
Agent: impl-executor
寸止点: [RELEASE_READY]

动作:
  - 准备发布清单
  - 执行发布流程
  - 验证发布结果
  - 监控发布状态

输出:
  - 发布清单
  - 发布验证结果

等待: 用户确认发布
```

### 9. 完成归档
```yaml
Agent: experience-mgr
Skills:
  - experience (深度沉淀)
  - cunzhi (寸止)

寸止点: [TASK_DONE]

动作:
  - 全面沉淀经验
  - 更新架构文档
  - 归档任务
  - 清理临时文件

输出:
  - 经验文档 (多条)
  - 完成报告
  - 建议后续优化
```

## 时间预估
- 总耗时: 数小时到数天
- 寸止点: 6个以上

## 寸止点汇总
| Token | 步骤 | 说明 |
|:---|:---|:---|
| [REQ_READY] | 2 | 需求确认 |
| [DESIGN_READY] | 4 | 方案确认 |
| [PLAN_READY] | 6 | 计划确认 |
| [PHASE_DONE] | 6 | 阶段确认 (多次) |
| [RELEASE_READY] | 8 | 发布确认 |
| [TASK_DONE] | 9 | 最终确认 |

## 阶段划分示例
```markdown
## TODO.md

### Phase 1: 核心基础 [预计: 2小时]
- [ ] 类型定义
- [ ] 工具函数
- [ ] 基类实现
**里程碑**: 核心模块可用

### Phase 2: 业务实现 [预计: 4小时]
- [ ] 功能A实现
- [ ] 功能B实现
**里程碑**: 主要功能完成

### Phase 3: 集成测试 [预计: 2小时]
- [ ] 单元测试
- [ ] 集成测试
- [ ] E2E测试
**里程碑**: 测试通过

### Phase 4: 发布准备 [预计: 1小时]
- [ ] 文档更新
- [ ] 发布配置
**里程碑**: 准备发布
```

## 知识库/经验深度集成
```yaml
全流程检索:
  每个阶段开始前自动检索相关知识和经验

深度沉淀:
  - 架构决策记录
  - 技术选型原因
  - 问题解决方案
  - 最佳实践发现
  - 踩坑教训

示例:
  "本次开发沉淀 5 条经验:"
  "- EXP-101: 微服务拆分决策"
  "- EXP-102: 缓存策略选择"
  "- ..."
```

## 错误恢复
```yaml
若阶段失败:
  1. 记录错误到 errors.md
  2. 触发 [VERIFICATION_FAILED]
  3. 等待用户决策: 重试/回滚/跳过
  4. 沉淀错误经验
```

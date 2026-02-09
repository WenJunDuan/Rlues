# 多AI协调 (Multi-AI Coordination)

## 概述
VibeCoding 支持多个 AI 引擎协作，通过 `.ai_state/` 文件系统实现状态共享和任务交接。

## 支持的引擎
```yaml
配置: orchestrator.yaml → engines

引擎:
  claude:
    优势: 推理、架构、复杂逻辑
    技能: 内置
    
  codex:
    优势: 代码生成、重构
    技能: skills/codex/SKILL.md
    
  gemini:
    优势: 长上下文、多模态
    技能: skills/gemini/SKILL.md
```

## 协调架构
```
┌─────────────────────────────────────────────┐
│              orchestrator.yaml               │
│         (引擎配置、路径规则、调度策略)          │
└──────────────────┬──────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌────────┐   ┌────────┐    ┌────────┐
│ Claude │   │ Codex  │    │ Gemini │
└────┬───┘   └────┬───┘    └───┬────┘
     │            │            │
     └────────────┼────────────┘
                  ▼
         ┌───────────────┐
         │  .ai_state/   │
         │ (状态共享层)   │
         └───────────────┘
```

## 状态共享

### handoff.md - 交接文档
```markdown
# AI 交接文档

## 当前状态
- 引擎: claude
- 阶段: Execute
- 任务: 实现用户认证

## 已完成
- [x] 需求分析
- [x] 架构设计
- [x] 任务规划

## 进行中
- [ ] 实现登录 API

## 上下文
### 技术决策
- 认证方案: JWT + Redis
- 框架: Express.js

### 注意事项
- token 过期时间: 24h
- 需要处理刷新逻辑

## 交接给
- 建议引擎: codex (大量 CRUD 代码)
- 任务: 实现 CRUD 接口
```

### 共享文件
```yaml
状态同步:
  - session.lock: 当前会话
  - active_context.md: 上下文
  - TODO.md: 任务列表
  - kanban.md: 进度状态

知识共享:
  - errors.md: 错误经验
  - knowledge.md: 本地知识
```

## 交接协议

### 交接触发
```yaml
触发条件:
  1. 用户显式切换 (/switch codex)
  2. 任务类型更适合其他引擎
  3. 当前引擎遇到限制

不自动切换:
  - 引擎选择权在用户
  - AI 只建议，不强制
```

### 交接流程
```
1. 当前引擎完成当前任务
2. 更新 handoff.md
3. 调用寸止 [TASK_DONE] 或 [PHASE_DONE]
4. 建议切换（如需要）
5. 用户确认切换
6. 新引擎读取 handoff.md 恢复
```

### 交接清单
```markdown
交接前检查:
- [ ] 所有状态文件已更新
- [ ] handoff.md 已写入
- [ ] 当前任务已完成或明确标记
- [ ] 关键上下文已记录
```

## 引擎选择建议

### Claude 适合
```yaml
- 复杂推理
- 架构设计
- 代码审查
- 需求分析
- 问题诊断
```

### Codex 适合
```yaml
- 大量样板代码
- CRUD 实现
- 代码补全
- 重复模式生成
```

### Gemini 适合
```yaml
- 长文档分析
- 多文件理解
- 图像相关任务
- 大上下文处理
```

## 协作模式

### 串行协作
```
Claude (分析/设计)
    ↓
Codex (代码生成)
    ↓
Claude (审查/优化)
```

### 并行协作 (未来)
```yaml
注意: 当前版本不支持真正并行
建议: 分任务串行执行
```

## 配置示例

### orchestrator.yaml
```yaml
engines:
  primary: claude
  available:
    - name: claude
      strengths: [reasoning, architecture]
    - name: codex
      strengths: [code-generation]
      skill_path: skills/codex/SKILL.md

multi_ai:
  enabled: true
  coordination_file: .ai_state/handoff.md
  state_sync: .ai_state/
```

## 最佳实践

### 状态一致性
```yaml
每次操作后:
  - 更新 kanban.md
  - 更新 active_context.md
  - 必要时更新 handoff.md
```

### 交接质量
```yaml
好的交接:
  - 上下文完整
  - 决策有记录
  - 待办清晰
  - 注意事项明确

差的交接:
  - 只有代码没有上下文
  - 不清楚做了什么
  - 不知道下一步
```

### 冲突处理
```yaml
若发现状态不一致:
  1. 以最新时间戳为准
  2. 记录冲突到 errors.md
  3. 必要时请求用户裁决
```

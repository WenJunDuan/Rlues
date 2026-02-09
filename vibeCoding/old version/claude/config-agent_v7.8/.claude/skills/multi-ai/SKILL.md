---
name: multi-ai
description: |
  Multi-AI coordination for Claude Code, Codex CLI, and Gemini CLI.
  Handles task delegation, context handoff, and result synchronization
  across different AI engines. Works with orchestrator.yaml.
---

# Multi-AI Coordination Skill

## Supported Engines

| Engine | Strengths | Use For |
|:---|:---|:---|
| Claude Code | 推理, 规划, 审查 | 架构设计, 代码审查 |
| Codex CLI | 代码生成, 补全 | 快速实现, 重构 |
| Gemini CLI | 长上下文, 多模态 | 文档处理, 大文件 |

## Coordination Protocol

### Task Delegation
```yaml
vibe-code --engine=codex "实现用户登录"
  ↓
1. Claude 生成任务规范
2. Codex 执行代码生成
3. Claude 审查结果
4. 合并到主分支
```

### Context Handoff
```yaml
Format:
  task_spec: 任务描述
  context_files: 相关文件列表
  constraints: 约束条件
  expected_output: 期望输出
```

### Lock Mechanism
```yaml
.ai_state/meta/session.lock:
  engine: claude
  task_id: REQ-001
  started: 2025-01-23T15:00:00Z
  status: active
```

## Engine Selection

```yaml
Auto-Selection:
  单文件快速修改 → Codex
  复杂推理任务 → Claude
  长文档处理 → Gemini
  代码审查 → Claude

User Override:
  --engine=claude
  --engine=codex
  --engine=gemini
```

## orchestrator.yaml

```yaml
engines:
  claude:
    priority: 1
    capabilities: [reasoning, planning, review]
  codex:
    priority: 2
    capabilities: [code_generation, completion]
  gemini:
    priority: 3
    capabilities: [long_context, multimodal]

routing:
  default: claude
  code_only: codex
  document: gemini
```

## Commands

```bash
/vibe-code --engine=codex "task"
/vibe-code --engine=gemini "task"
```

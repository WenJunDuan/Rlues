---
name: agent-teams
description: Path D 并行分工模板 — Agent Teams 任务分配、上下文传递、结果合并
context: main
---

# Agent Teams — Path D 并行分工

> 仅 Path D 使用。前置条件: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

## 角色模板

### 标准四人组
```yaml
Researcher:
  focus: "调研 + 技术验证"
  tools: [augment-context-engine, mcp-deepwiki, web_search]
  output: ".ai_state/research-{topic}.md"

Architect:
  focus: "方案设计 + 接口定义"
  tools: [augment-context-engine]
  output: ".ai_state/design.md"
  depends_on: [Researcher]

Implementer:
  focus: "编码 + 测试"
  tools: [augment-context-engine, context7]
  output: "src/ + tests/"
  depends_on: [Architect]

Reviewer:
  focus: "审查 + 安全 + 经验沉淀"
  tools: [code-review, security-guidance]
  output: ".ai_state/review.md + .knowledge/"
  depends_on: [Implementer]
```

### 并行开发组 (大型任务)
```yaml
Lead:
  role: "协调, 不写代码"
  分配: "拆解 plan.md 任务 → 分配给 Worker"
  监控: "inbox 收汇报, 处理冲突"

Worker_1..N:
  role: "独立实现分配的任务"
  约束: "只改自己负责的文件"
  汇报: "完成后 inbox → Lead"
```

## 上下文传递协议

Agent Teams 各 agent 有独立 context。
共享状态通过 `.ai_state/` 文件系统:

```
Lead 写入 → .ai_state/plan.md (任务分配)
Worker 读取 → .ai_state/plan.md (自己的任务)
Worker 写入 → .ai_state/worker-{N}-progress.md
Lead 读取 → .ai_state/worker-*-progress.md (汇总)
```

## 启动命令 (Claude Code)

```bash
# 在 CLAUDE.md 或交互中触发
"用 Agent Teams 模式开发这个功能"
→ PACE 判定 Path D
→ 读本 Skill
→ Lead 创建任务分配
→ Task tool 启动 Worker subagents
```

## Codex CLI 替代

Codex 无原生 Agent Teams。替代方案:
1. `codex --mode plan` 拆解任务
2. 多终端各跑 `codex` 实例
3. 手动协调 (通过 .ai_state/ 文件)
4. 或: MCP server 模式 + Agents SDK hand-off

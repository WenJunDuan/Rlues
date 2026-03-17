---
name: agent-teams
description: 多代理并行 — Path C/D 的 E 阶段
context: main
---
## 前提
.claude/agents/ 下定义了 builder/validator/explorer/e2e-runner/security-auditor
所有子代理遵循 CLAUDE.md 的思维协议。

## 编排
1. 读 plan.md → 识别无依赖任务组
2. Agent(builder) × N (background: true, worktree 隔离)
3. Agent(validator) 检查每个 builder 产出
4. Agent(explorer) 跨模块调研 (只读)

## 规则
- 无依赖→并行, 有依赖→串行
- 同文件不并行修改
- SubagentStop hook 自动审查产出 (LLM-as-Judge)
- 合并后运行完整测试套件

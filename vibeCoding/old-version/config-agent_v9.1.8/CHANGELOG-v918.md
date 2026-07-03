# VibeCoding Kernel v9.1.8 — CHANGELOG

## 来源

- obra/superpowers (95K stars): 两阶段审查, 子代理隔离, TDD强制
- Oh My OpenCode (Sisyphus): 不完成不停止, Plan Consultant, LSP/AST
- Anthropic Best Practices: hooks强制 > CLAUDE.md建议
- CC v2.1.76: ${CLAUDE_SKILL_DIR}, effort/maxTurns, StopFailure

## 变更

### P0: 两阶段 Micro-Review (superpowers)

E阶段每Task: Spec合规→代码质量。Path B自检, C+用validator
spec-reviewer-prompt.md + quality-reviewer-prompt.md

### P0: systematic-debugging Skill (superpowers)

4阶段: 复现→根因→防御修复→验证。Bug需求自动激活
禁止: 看报错就改 / 只修症状 / 不测

### P0: 子代理上下文隔离 + maxTurns (superpowers+CC)

只传Task文本+文件+conventions, 不传对话历史
effort/maxTurns frontmatter控制

### P1: 通用代码标准 (用户需求)

code-review SKILL.md + LLM-Judge prompt hook
审查时花token, 非SessionStart
函数<50/注释WHY/类型严格/无空catch/命名/DRY

### P1: CC平台新特性

StopFailure hook / ${CLAUDE_SKILL_DIR} / /debug / Opus 64k

### P1: Sisyphus循环 (OMO)

E阶段: plan.md [ ]→执行→[x]→重复直到无[ ]
PostCompact: 提示继续未完成
SessionStart: 显示未完成数量

### P1: Plan Review (OMO Prometheus/Metis)

P阶段plan产出后审查: "初级工程师能执行?"
Path B自审, C+ Agent(validator)

### P2: 工具箱扩展 (OMO)

LSP diagnostics + ast-grep (标注"如可用")
permissions新增 Bash(ast-grep \*)

## 文件统计

| 包    | 文件 | 行数 | vs v9.1.7 |
| ----- | ---- | ---- | --------- |
| CC    | 41   | 740  | +新特性   |
| Codex | 29   | 265  | +新特性   |

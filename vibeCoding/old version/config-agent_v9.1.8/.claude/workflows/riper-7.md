# RIPER-7 v9.1.8

## 每阶段进入前
1. 核心问题? 2. 项目有类似? → augment 3. API确定? → context7/deepwiki 4. knowledge+lessons有经验?

---

## R₀ 需求精炼 (Path B+)
**技能**: brainstorm → AskUserQuestion 访谈
**产出**: .ai_state/design.md (MUST/SHOULD/COULD + 验收标准)
**门控**: cunzhi [DESIGN_DIRECTION]

## R 技术调研 (Path B+)
**动手**: augment搜代码 + context7查库
**产出**: design.md 追加技术方案

## D 方案定稿 (Path B+)
**问**: 接口最小? 错误处理完整? 更简单方案?
**产出**: design.md 定稿
**门控**: cunzhi [DESIGN_LOCKED]

## P 计划制定 (Path B+)
**技能**: plan-first → 分解Task
**产出**: .ai_state/plan.md

### Plan Review (P内嵌)
产出后、确认前审查:
- Path B: 自审 — "初级工程师能执行?" 粒度2-5min? 依赖? 文件? 验收?
- Path C+: Agent(validator) 审查
- 不合格 → 改plan再审

**门控**: cunzhi [PLAN_CONFIRMED]
**CC**: /plan {摘要}

## E 执行实现 (All Paths)
铁律 #2 → tdd skill

### Sisyphus 循环 (不完成不停止)
```
重复:
  1. 读 plan.md → 第一个 [ ]
  2. 执行 Task (RED→GREEN→REFACTOR)
  3. Micro-review: spec合规 + 代码质量
     Path B: 自检 | Path C+: Agent(validator) + ${CLAUDE_SKILL_DIR}/spec-reviewer-prompt.md
  4. 不合格 → 当场修复
  5. [x] + commit + status.md
  → 直到无 [ ]
```

**工具**: /effort high (复杂Task)
**子代理 (C+)**: Agent(builder) 实现, Agent(explorer) 调研

## T 测试验证 (All Paths)
**全局审查** — 跨Task集成+安全
**技能**: verification → 全量测试 + 覆盖率
**技能**: code-review → 审查 (含通用质量标准)
**可选**: LSP diagnostics / ast-grep
**子代理 (C+)**: Agent(validator)
**产出**: .ai_state/quality.md

## V 交付归档 (Path B+)
**技能**: kaizen → knowledge.md + lessons.md
**门控**: cunzhi [DELIVERY_CONFIRMED]

---

## 工具箱
| 工具 | 用途 |
|------|------|
| augment-context-engine | 搜项目代码 |
| mcp-deepwiki / context7 | 查库文档 |
| cunzhi MCP | 人工确认 |
| Agent(builder/validator/explorer) | 子代理 (C+) |
| /effort high | 提升推理深度 |
| /plan {摘要} | 规划模式 |
| /loop {间隔} {cmd} | 持续监控 |
| /debug | 调试会话 |
| LSP diagnostics | 类型信息 (如可用) |
| ast-grep | AST搜索 (如可用) |

## 状态文件
status.md(全程) / design.md(R₀→D) / plan.md(P→V) / quality.md(T) / conventions.md / knowledge.md / lessons.md

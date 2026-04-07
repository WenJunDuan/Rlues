---
name: plan
effort: high
description: >
  需求分析和设计规划。当进入 R₀/R/D/P 阶段、或需要设计方案时触发。
---

# Plan Skill: 需求 → 设计 → Sprint Contract

## 当前状态
!`cat .ai_state/project.json 2>/dev/null | head -5`
!`cat .ai_state/design.md 2>/dev/null | head -3 || echo '(design.md 不存在)'`

---

## R₀ 需求精炼

**目标:** 把用户说的变成可验收的 Spec。

如果需求清晰 (如 "给 API 加 rate limiting") → 跳到技术调研。
如果需求模糊 → superpowers brainstorming skill 会自动激活, 引导用户逐步明确。

**无论用什么方式精炼, 最终必须:**
1. 写入 .ai_state/design.md: 需求摘要 + MUST/SHOULD/COULD + 验收标准
2. 每条验收标准必须可测试 (如 "无效邮箱输入时返回 400")
3. 明确列出**不做什么**

**约束:**
- superpowers brainstorming 可能把设计写到 `docs/superpowers/plans/` → 必须整理到 .ai_state/design.md
- 验收标准不能是模糊的 "用户体验好" → 必须可测试

**用户确认:** cunzhi MCP DESIGN_READY 检查点 (如可用), 或直接问用户确认 design.md。

---

## R 技术调研

**目标:** 验证关键技术可行, 排除风险。

1. Grep 搜索项目中的相关实现
2. augment-context-engine 做语义搜索 (如可用) — 跨文件关联分析
3. `npx ctx7 resolve {{库名}}` 查关键库 API
4. 读 .ai_state/lessons.md — 有没有踩过相关的坑
5. 追加到 design.md: 接口签名 + 依赖版本 + 已知风险和缓解方案

---

## D 方案定稿

**目标:** 锁定方案, 用户确认。

审查方式 (选一):
- @evaluator 独立评审 → VERDICT: APPROVED/REVISE
- `/review` (CC 内置) 快速审查

**约束:** `/codex:adversarial-review` 只能审查代码变更, D 阶段没有代码, **不要用**。

审查通过后 → 从 design.md 的验收标准生成 Sprint Contract:

**用户确认:** cunzhi MCP SPRINT_CONTRACT 检查点 (如可用), 或直接问用户确认。

```markdown
# tasks.md 示例
## 待办
- [ ] F001/T001: 创建 User model — 验收: schema 含 email(unique), passwordHash, createdAt
- [ ] F001/T002: 实现 POST /api/register — 验收: 有效输入注册成功, 无效输入返回 400
- [ ] F002/T001: 实现 POST /api/login — 验收: 正确凭据返回 token, 错误凭据返回 401
```

写入 .ai_state/tasks.md → 用户确认。

---

## P 计划排期

**目标:** 确定依赖和执行顺序。

1. 标注 Task 间依赖 (如 T002 依赖 T001)
2. 确定执行顺序
3. 为每个 Task 规划测试策略
4. 补充到 tasks.md

**产出:** tasks.md 完整的 Task 清单 + 执行顺序
**门控:** tasks.md 非空 → 进入 E 阶段

## Gotchas

- ❌ 验收标准写 "用户体验好" → ✅ 写 "输入无效邮箱时显示错误提示"
- ❌ 跳过技术调研直接写方案 → ✅ 至少 Grep 搜索 + 查一个关键库文档
- ❌ 生成 100 个 Task → ✅ 一个 Sprint 控制在 5-15 个 Task

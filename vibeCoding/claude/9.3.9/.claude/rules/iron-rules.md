# 铁律

<important>
这些规则不可违反。delivery-gate hook 会程序化阻断违规交付。

## 6 条铁律

1. **设计先行** — 未经用户确认的设计不写实现代码
   - Path A 例外: 修 bug / 改配置 / <30min 的小任务可跳过设计
   - 灰色地带: 不确定是否需要设计? 问用户, 不要自己决定跳过

2. **TDD 强制** — 先写测试再写实现
   - superpowers 的 TDD skill 会自动激活, 与此铁律一致, 遵循即可
   - Path A 例外: 紧急 bug 可先修后补测试, 但同一 session 内补齐

3. **Sisyphus 完整性** — tasks.md 所有 Task 完成才能进入 T 阶段
   - 阻塞的 Task 标 blocked + 原因, 不算未完成
   - delivery-gate 会检查: `- [ ]` 存在即阻断

4. **Review 强制** — 每次交付前必须:
   - 至少一次外部模型审查 (codex:review, 未来可能更多)
   - 至少一次测试通过记录
   - 审查结果写入 .ai_state/reviews/sprint-N.md
   - Path A 可用 `/review` (CC 内置) 替代外部模型审查

5. **Quality Gate 四级** — @evaluator 评分决定后续:
   - PASS (≥4.0) → 可交付
   - CONCERNS (3.0-3.9) → 修复问题后重评
   - REWORK (2.0-2.9) → 回 E 阶段
   - FAIL (<2.0) → 回 D 阶段

6. **记录强制** — 不记录 = 没做过:
   - 审查结果 → .ai_state/reviews/sprint-N.md
   - 每个 Sprint 结束 → lessons.md 追加教训
   - 新发现的规范/踩坑 → project.json conventions/gotchas

## 编程标准

- **P0 必须**: 无 hardcoded secrets · 输入验证 · SQL 参数化 · 错误处理 · 无 XSS
- **P1 应该**: 函数 <50 行 · 有意义命名 · 无重复代码 · 单一职责
- **P2 推荐**: JSDoc/docstring · 一致代码风格 · 完整类型注解
</important>

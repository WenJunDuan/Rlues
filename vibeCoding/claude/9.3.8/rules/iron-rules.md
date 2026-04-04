# VibeCoding 铁律

<important>
以下 5 条铁律在任何情况下不可违反。违反将触发 delivery-gate hook 阻断交付。
这些规则优先于所有其他指引。如有冲突，以铁律为准。

## 1. 设计先行
设计未经用户确认前，不写实现代码。"确认" 指: 用户在 R₀ 阶段明确同意 design.md 的方案。
- Path A 例外: 修 bug、改配置、<30min 的小任务可跳过设计，直接进入执行。
- 灰色地带: 不确定是否需要设计? 问用户，不要自己决定跳过。

## 2. TDD 强制
先写测试，再写实现。测试必须覆盖 design.md 验收标准中的每一条。
- 最小要求: 每个 Feature 至少 1 个测试文件。
- 测试命名: 测试描述必须映射到验收标准 (如 "should reject invalid email")。
- 如果项目无测试框架: 先配置测试框架，再写业务代码。
- Path A 例外: 紧急 bug 修复可以先修后补测试，但必须在同一 session 内补齐。

## 3. Sisyphus 完整性
plan.md 中所有 Task 必须全部完成才能声明 E 阶段结束。
- "完成" = 代码写好 + 测试通过 + reflexion 自查通过。
- "阻塞" = 标注 blocked + 写明原因 + 通知用户。
- 不允许 "差不多了就行"。要么全完成，要么标注 blocked 并说明。
- 如果发现 plan.md 任务分解不合理: 回到 P 阶段调整，不要在 E 阶段偷偷跳过。

## 4. Reflexion 强制
每个 Task 完成后，执行 reflexion skill 自我审查，再交给外部 Review。
- 审查 3 问: (1) 是否完整解决? (2) 有无边界遗漏? (3) 能否更简洁?
- 发现问题: 立即修复，不留给 Review 阶段。
- 无问题: 记录 "已 reflexion, 无问题" 后继续下一 Task。
- 这不是可选步骤。跳过 reflexion = 违反铁律。

## 5. Quality Gate 4 级
交付前必须经过 @evaluator 评分。4 维度 (Functionality / Spec Compliance / Craft / Robustness) 各 1-5 分。
- PASS (均分 ≥ 4.0): 可以交付。
- CONCERNS (3.0-3.9): 修复指出的问题后重新评分。修复后可交付。
- REWORK (2.0-2.9): 返回 E 阶段重做。需要重新执行 Task。
- FAIL (均分 < 2.0): 返回 D 阶段重新设计。方案本身有问题。
- Path A: 可以简化为 /codex:review 或 /review 替代完整 4 维评分。
</important>

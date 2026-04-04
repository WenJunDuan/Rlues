---
effort: high
description: >
  当代码写完需要审查、需要评估质量、或被 /vibe-review 命令调用时触发。
  编排多个审查工具, 产出综合评分和 VERDICT。
---

# Review Skill: 质量审查

## 你的目标

用多个审查工具独立验证代码质量, 产出 quality.json 综合评分和 VERDICT。
核心原则: **写代码的模型不应该独自审查自己的代码** — 所以用 Codex 跨模型审查。

---

## 前置检查

1. .ai_state/feature_list.json 中是否有 "done" 状态的 Feature (没有 → 先完成执行)
2. .ai_state/state.json stage 应更新为 "T"
3. 确认当前 Path (从 state.json 读取), 决定审查深度

---

## 审查工具编排

### Path A (快速) — 选一种即可

```
方案 1: /codex:review                    # Codex 标准审查
方案 2: /review                           # CC 内置审查
```

Path A 不需要 @evaluator 评分, 审查通过就可交付。

### Path B (标准) — 按顺序执行

```
步骤 1: /codex:review --background       # Codex 标准审查 (必做, 后台运行)
步骤 2: /codex:status                    # 等待审查完成 (轮询直到 completed)
步骤 3: /codex:result                    # 取回审查结果 (保存, 后续传给 @evaluator)
步骤 4: @evaluator 综合评分              # 独立 agent 评审 (必做)
        → 委托时附上: design.md + feature_list.json + codex:result 审查结果
        → 产出: quality.json + VERDICT
```

**重要:** 必须等 /codex:result 拿到审查结果后, 再调 @evaluator。
@evaluator 需要 Codex 的审查结果作为评分输入。

### Path C (复杂) — 全部执行

```
步骤 1: /codex:review --background       # 标准审查 (后台)
步骤 2: /codex:adversarial-review --background  # 对抗审查 (后台, 可与步骤 1 并行)
        → 可聚焦: /codex:adversarial-review --background challenge the auth token design
步骤 3: /codex:status                    # 等待步骤 1+2 全部完成
        /codex:result                    # 取回两次审查结果
步骤 4: npx ecc-agentshield scan         # 安全扫描
        → 深度扫描: npx ecc-agentshield scan --opus --stream
步骤 5: @evaluator 综合评分              # 综合所有审查结果 (含 codex:result + ECC 输出)
```

### Path D (系统) — 全部 + 前端 E2E

```
步骤 1-5: 同 Path C (review + adversarial + status/result + ECC + @evaluator)

步骤 6 (如有前端): playwright-skill      # E2E 测试
        → 按 playwright-skill 指引执行浏览器自动化测试
```

---

## @evaluator 评审流程

委托 @evaluator 时, 提供以下上下文:
1. .ai_state/design.md — 验收标准
2. .ai_state/feature_list.json — 完成情况
3. 代码变更摘要 (git diff 或文件列表)
4. 前置审查结果 (/codex:review 和 adversarial-review 的输出)

@evaluator 按 4 维度评分:

| 维度 | 权重 | 评分标准 |
|------|------|---------|
| Functionality (功能完整性) | 30% | 验收标准逐条检查 |
| Spec Compliance (规范符合度) | 30% | 对照 design.md 方案 |
| Craft (代码工艺) | 20% | 命名、结构、可维护性 |
| Robustness (健壮性) | 20% | 异常处理、边界、安全 |

评分后更新 .ai_state/quality.json:
```json
{
  "scores": {
    "functionality": 4,
    "spec_compliance": 5,
    "craft": 3,
    "robustness": 4
  },
  "average": 4.0,
  "verdict": "PASS",
  "issues": [],
  "recommendations": ["给 validateToken 加 JSDoc"]
}
```

---

## VERDICT 判定和后续动作

| VERDICT | 均分 | 动作 |
|---------|------|------|
| **PASS** | ≥ 4.0 | → 进 V 阶段归档, 可以交付 |
| **CONCERNS** | 3.0 - 3.9 | → 修复 issues 列表中的问题 → 重新 @evaluator 评分 |
| **REWORK** | 2.0 - 2.9 | → 回 E 阶段, 重做对应 Task → 重新走 T 阶段 |
| **FAIL** | < 2.0 | → 回 D 阶段, 方案本身有问题需要重新设计 |

CONCERNS 修复后重新评分, 循环直到 PASS 或用户决定接受。

---

## V 归档 (Review 通过后)

VERDICT = PASS 后, 执行归档:

1. 更新 .ai_state/conventions.md:
   - 新发现的 Gotchas (如 "这个库的 v3 API 和 v2 不兼容, 注意版本")
   - 项目特定规范 (如 "API 错误码统一用 ErrorCode enum")

2. 更新 .ai_state/lessons.md:
   - 本次开发的关键教训
   - 什么做得好, 什么下次可以改进

3. 重置 state.json:
   ```json
   {"path": "", "stage": "", "sprint": 2}
   ```

4. 告知用户: "Sprint 1 完成, 交付了 F001 (用户注册) + F002 (用户登录)。"

---

## Gotchas

- ❌ 只用 /review 自审就交付 → ✅ Path B+ 必须有跨模型审查 (/codex:review)
- ❌ adversarial-review 不指定方向 → ✅ 给方向效果更好: "challenge the caching design"
- ❌ @evaluator CONCERNS 就放过 → ✅ CONCERNS 必须修复后重新评分
- ❌ 安全扫描发现问题不修复 → ✅ P0 安全问题必须修复 (见 code-standards.md)
- ❌ 忘记更新 quality.json → ✅ @evaluator 的评分必须写入 quality.json, delivery-gate 会检查
- ❌ 跳过 V 归档 → ✅ 归档积累的 Gotchas 和教训是下次迭代的关键输入

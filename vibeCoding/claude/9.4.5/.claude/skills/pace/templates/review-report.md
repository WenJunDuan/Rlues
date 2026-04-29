# Sprint N 审查报告

## Step 1: 测试结果
<!-- 命令 + 实际输出 (不是"已跑通") -->

## Step 2: /codex:review (Feature+, Quick 可选)
<!-- 必须有以下证据之一, 防伪装 (铁律 4 反空跑):
     - codex job ID
     - codex CLI 真实命令行输出
     - 不可用时明示 "codex unavailable, 已记 ~/.claude/lessons/draft-*.md"
     -->

## Step 3: /codex:adversarial-review (System)
<!-- 同上证据要求 -->

## Step 4: ECC 扫描 (System)
<!-- npx ecc-agentshield scan 实际输出摘要 -->

## Step 5: Claude 审查
<!-- /review 输出 -->

## Step 6: @evaluator 评分

| 维度 | 分数 | 证据 |
|------|------|------|
| Functionality | /5 | (代码行号) |
| Spec Compliance | /5 | (代码行号 vs design.md) |
| Boundary Adherence | /5 | (是否越出 design.md 的 File Structure Plan) |
| Craft | /5 | (代码行号) |
| Robustness | /5 | (边界用例覆盖) |
| **均分** | **/5** | |

## VERDICT:

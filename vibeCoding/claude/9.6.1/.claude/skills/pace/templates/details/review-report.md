# Sprint N 审查报告

## Step 1: 测试结果

<!-- 命令 + 实际输出 (不是"已跑通"). 标签必须 executed. -->

## Step 2: /codex:review (Feature+, Quick 可选)

<!-- 必须有以下证据之一, 防伪装 (铁律 4 反空跑 + 铁律 6 完成度证据):
     - codex job ID
     - codex CLI 真实命令行输出片段
     - 不可用时明示 "codex unavailable" + 完整 stderr
     标签必须 executed. -->

## Step 3: /codex:adversarial-review (System)

<!-- 同上证据要求. -->

## Step 4: ECC 扫描 (System)

<!-- npx ecc-agentshield scan 实际输出摘要. 标签 executed. -->

## Step 5: Claude 审查 (/review 内置)

<!-- /review 输出. -->

## Step 6: @evaluator 评分

| 维度 | 分数 | 证据 (file:line 或 命令输出) | 标签 |
|------|------|------------------------------|------|
| Functionality | /5 |  | executed / inspected / assumed |
| Spec Compliance | /5 |  | executed / inspected / assumed |
| Boundary Adherence | /5 |  | executed / inspected / assumed |
| Craft | /5 |  | executed / inspected / assumed |
| Robustness | /5 |  | executed / inspected / assumed |
| **均分** | **/5** | | |

均分 = F×0.25 + SC×0.25 + B×0.15 + C×0.15 + R×0.20

**标签规约 (铁律 10/11)**:
- `executed` — 跑过 / 读过 / 验证过
- `inspected` — 查过文档但没跑
- `assumed` — 经验判断未验证
- 跨边界 (生产/schema/API/数据/安全) 仅接受 `executed`, 否则 REWORK

## Step 7: 矛盾决议 (铁律 12, 仅在外内审冲突时填)

<!--
当 /codex:review 与 /review 给出竞争方案 → 二选一, 不折中.
模板:

**冲突点**: <一句话描述>
- 方案 A (/codex:review): <描述>
- 方案 B (/review): <描述>
**采纳**: <A 或 B>
**弃用**: <另一个>
**技术理由**: <为什么; 引用代码行号或测试结果>
**标签**: executed | inspected | assumed
-->

## VERDICT:

<!-- PASS (均分≥4.0 且所有维度≥3) | CONCERNS (均分≥3.0 有维度=2) | REWORK (均分<3.0 或任一=1, 或跨边界 assumed) | FAIL (多维度=1 或安全/Boundary 大幅越界) -->

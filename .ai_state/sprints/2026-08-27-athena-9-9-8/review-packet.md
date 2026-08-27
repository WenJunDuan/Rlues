---
schema_version: 1
sprint_slug: "2026-08-27-athena-9-9-8"
mode: "implementation"
generated_from: "design.md (rev2)"
source_design_sha256: "1a2b9f303355386e1f2d40b100968aadf9c87e9ec5b8357f2f632d424b9a69a5"
created: "2026-08-27"
author_does_not_review: true
implementer: "grok (planned)"
reviewer_constraint: "must not be implementer session"
output: "reviews/implementation-review.md"
design_challenge_completed: "reviews/design-review.md (CONCERNS, findings folded into rev2)"
---

# Review Packet — Athena 9.9.8 (implementation)

从 design.md rev2 派生。reviewer 读本 packet + 最终 diff + evidence summary；只有矛盾时按"定位"列 anchor 定点打开 design。设计挑战已完成，勿重开。

## Contract

| ID | 必须成立 | 定位 |
|---|---|---|
| AC1 | 作者不自审；Feature 无固定 design review；R/S 独立挑战从派生 packet 开始 | 按风险收费 |
| AC2 | packet ≤80 行；design hash 与 AC 集合机械可验，陈旧/漏/重 → fail closed | Review contract |
| AC3 | 一次 review 请求一份 result；**异步里程碑**：发起轮正常结束，Stop 对 await-review-result 放行 | Review 异步时序 |
| AC4 | harness 内部可多 agent；diff 变化只触发目标复核；**同因 ×2 新 P0 → 交还用户** | 目标流程 |
| AC5 | 会改代码的 polish 在 review 前；review 后代码再变 → ship block | 目标流程 |
| AC6 | result 结构化 frontmatter，含 `review_run_id` + `native_output_ref`；转录不得增删定级 | 结果落盘规则 |
| AC7 | 路径仪式与表一致；hook 红 block / 黄 warning / 绿 async，安全真边界不降级 | Hook 严格度 |
| AC8 | 同事件最多一个同步 blocker；read-only 无手工绑定；rg fixture 通过；"tasks 全绿"改指 checklist.yaml | Hook 严格度、职责边界 |
| AC9 | `_index` ≤12KiB、列表 ≤10 项、**单条 ≤160B 溢出搬运不丢弃**；archive 默认排除；telemetry 出 Git | ai_state 三层 |
| AC10 | canonical/安装态/target 分开；migration 保留用户 model/effort；降档先 eval | 模型与 effort |
| AC11 | 对照**冻结 baseline**（度量口径归类）：成功率/安全不降，控制面 tokens ↓≥40%，占比 ≤1/3 | 度量口径 |
| AC12 | 无第二状态树/人工 catalog/26 skill 合并；packet ≤80 行不复制散文 | 发布边界 |
| AC13 | impl-entry 完成 V1–V3 版本重验并更新 `_index` 版本字段；CX 0.146+ 特性 V2 通过前非唯一路径 | 版本 pin |

## Review 维度（一次多维，不排轮次）

Spec coverage · Correctness · Security · Test risk · Over-engineering · Evidence（本 sprint 为 System，必核）。
机械项（测试执行、文件越界、evidence 存在、hash 一致）由 gate 判，reviewer 不复跑账本。

## 实现期重点核查面

1. 异步 review 时序：发起→结束→完成通知→落盘 与"通知丢失"两个 fixture 是否真实在场并通过（AC3）。
2. gate 的 hash 逻辑：packet_sha256 / reviewed_diff_sha256 现场重算，而非信任 frontmatter 自报（AC2/AC5/AC6）。
3. hook 重分级没有把安全红区降级：删的只是标题计数/critic 协议，rm/push/测试失败等 block 仍在（AC7）。
4. 切片 3 顺序：baseline 冻结先于 telemetry 迁移/retention，且 baseline 目录豁免 retention（AC11）。
5. migration 不覆盖用户安装态 model/effort/output-style（AC10）。
6. 旧协议残留：live emitter 无 critic/evaluator/spec-compliance 调度、无 2+1/passN 话术（AC1/AC3/AC8）。
7. 双端语义对齐但不伪造对称：CX 侧逐文件核对，不抄 CC 文件名/字段（AC8/AC13）。
8. `_index` 更新 hook 的搬运逻辑：溢出进 sprint 文档，审计链无丢失（AC9）。

## 输出约束

- 写入 `reviews/implementation-review.md`；reviewer 必须不是实现者会话。
- frontmatter 按 design「一次多维 review」schema（含 verdict、finding_counts、review_run_id、native_output_ref）。
- Findings 按 P0/P1/P2/INFO 排序，每条给 AC、文件/行、可执行修正；最多 10 条。
- 单独列 `MISSING / EXTRA / DEVIATED`；不复述 contract。
- 最后一行必须是 `VERDICT: PASS|CONCERNS|REWORK|FAIL`。
- 只此一轮；若需返工，findings 交还实现者，复核按 AC4 终止规则执行。

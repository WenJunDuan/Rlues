---
name: athena-review
description: PACE 实现后一次原生多维 review。进入 review stage 时触发。不要跑 critic/evaluator/spec-compliance。
---

# /athena-review — Review (v9.9.8)

## 触发

impl 完成且测试通过。Refactor/System：先 runtime-verify，再完成会改代码的 polish，最后才 review。

## 一次请求（异步里程碑）

Athena 只发起 **一次** review 请求：

| 端 | 入口 |
|---|---|
| CC | `/code-review`（`/review` 为其别名，2.1.223+）+ `REVIEW.md` + sprint packet |
| CX | 原生 `/review`；不可用则单个只读 reviewer agent |
| 皆无 | 单个 reviewer，schema 相同 |

官方 harness 内部可并行多个 reviewer，不计入 Athena 轮次。

发起后本轮 **正常结束**，设 `_index.next_action = await-review-result`。Stop / continuator 对该信号 **放行且不注入续跑**。完成通知轮：校验并写入 `reviews/implementation-review.md`。

## 维度

Spec coverage · Correctness · Security · Test risk · Over-engineering · Evidence（R/S）

测试是否执行、越界、hash 由 gate 判。

## 结果

单文件 `reviews/implementation-review.md`，YAML frontmatter 含 `review_run_id`、`native_output_ref`、`packet_sha256`、`reviewed_diff_sha256`、`verdict`。缺任一字段 ship block。转录不得改定级。

目标复核：diff hash 变了才再审 open findings。**同因新 P0 ×2 → 交还用户**，禁止无界 passN。

## 禁止

- spawn critic / evaluator / spec-compliance
- 同轮死等后台 `/code-review`
- 主 agent 编造 findings（无 native_output_ref）

## 例外

- Hotfix：默认可跳过
- Quick：用户或风险触发才跑
- Bugfix / Feature / R/S：一次 review

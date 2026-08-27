---
name: athena-review
description: PACE 实现后一次原生多维 review。进入 review stage 时触发。不要跑 critic/evaluator/spec-compliance。
---

# /athena-review — Review (v9.9.8, Codex)

## 触发

impl 完成且测试通过。Refactor/System：先 runtime-verify，再完成会改代码的 polish，最后才 review。

## 一次请求（异步里程碑）

Athena 只发起 **一次** review 请求：

| 端 | 入口 |
|---|---|
| CX | 原生 `/review` 若可用；否则单个只读 `reviewer` agent |
| 无原生 | 同一 schema 的单个 reviewer |

发起后本轮正常结束，`next_action=await-review-result`。Stop 对该信号放行、不续跑。完成通知轮落盘 `reviews/implementation-review.md`。

CX `/export` 在版本 pin V2 通过前 **不是** 唯一 `native_output_ref` 路径；fallback 把 reviewer 原始返回写入 `reviews/_native/{review_run_id}.md`。

## 维度 / 禁止 / 例外

与 CC 端语义相同：一次多维、gate 判机械项、同因 P0×2 终止、不 spawn 旧三角色。

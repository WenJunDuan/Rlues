---
name: athena-review
description: PACE 实现后一次独立多维 review。进入 review stage 时触发；优先本端原生入口，fallback 为一个只读 reviewer。
---

# /athena-review — Review（9.9.9, Codex）

impl 与必要验证完成后进入；Refactor/System 先 runtime-verify → polish → review。阶段义务以 [PACE stages](../pace/references/stages.md#review) 为准。

稳定审查提示在本 skill 的 [REVIEW.md](REVIEW.md)。reviewer 每次任务最多 70 轮，到限返回进度；CX 当前为指令约束，非原生硬限。可选 `/llm-as-a-verifier` 只排序，不能当 VERDICT。

## 一次调用

优先当前可用原生 `/review`；否则用一个只读 reviewer/独立上下文。CX-only 足够，不要求另一平台或不同模型家族。独立能力不可用则保留未完成状态。
先按 [execution-contracts](../pace/references/execution-contracts.md#cx-原生绑定命令) 用本端 Python `review-binding.py prepare` 采集 run/packet/实际输入；原生派发后以保存的原始工具结果 JSON 执行 `bind`，收到完成结果后执行 `accept`。不手改绑定记录或编造 receipt，CX 不需要 Node/CC。

同步调用直接接收结果。只有真实异步入口才写 `next_action=await-review-result`；Stop 放行不续跑，通过平台通知/等待/回读接续，等待期间不重复派发。

输出 `reviews/implementation-review.md`；fallback 原文存 `reviews/_native/{review_run_id}.md`，不伪造 reviewer 未返回的元数据。`/export` 仅在本机入口实际可用时作为一种原文来源。

`accept` 会持久记录 PASS/CONCERNS/REWORK/FAIL，接收成功不等于审查通过；只有当前绑定有效的 PASS 可交付。旧请求结束或失效后才可 `supersede`，复核使用新的独立目标，脚本不取消原生任务。

## 审查范围

一轮覆盖 Spec coverage、Correctness、Security、Test risk、Over-engineering，R/S 加 Evidence。同因新 P0 第二次复核仍出现则交还用户。仅当前匹配的 PASS 进入 ship；其余按 findings 返回对应阶段。不调用 critic/evaluator/spec-compliance。

---
sprint_slug: "2026-09-20-contract-parser-diagnostics"
result: PASS
polish_commit: "d7e6786"
---

# Cleanup Pass — contract parser diagnostics

polish-worker（唯一 writer，主仓串行）五项检查，主 agent 复核产物与测试后落盘。

| 项 | 结论 |
|---|---|
| 临时代码/调试残留 | 无发现（命中项均为业务文本：报错文案中的「TODO 占位」与 PLACEHOLDER 注释；CX print(json.dumps) 是 hook stdout 协议） |
| 注释 | 基本完备；补 1 条 acceptanceHeadHint「两处报错共用同一句提示」说明，三端逐字同步 |
| 冗余 | 1 处真问题：「未识别到验收小节; 可接受标题…」在 spec-gate 与 packet 两处 × 三端共 6 份拷贝，intra-end 漂移无测试可拦 → 折叠进 acceptanceHeadHint 单一来源（原 acceptanceHeadList 重命名吸收） |
| 低效 | 生产码无发现；测试 CC 探针 per-case spawn node 为跨端探测固有成本，不改（风险>收益） |
| 过度设计 | 删 3 处：acceptanceSections 的 String() 边界内死防御（恢复三端对称）；测试探针清单中无消费者的 ACCEPTANCE_HEAD_ALIASES 项；随之而死的非函数分支。保留 stripInlineCode 内 String()（基线 extractAcIds 强转下沉，动它=改基线契约）、resolved.found 的 OR 累积（spec-gate 两层报错真实消费）、TDD_RECORD_FIELDS（3 消费者） |

主 agent 复核：67/67 绿（含 PiSameSourceParity 文本相等）；行为零变化有独立证据——旧版（fd9d1d0）与现版 CX gate 同进程对三条消息逐字比对 SAME，CC/Pi 经 cc==cx 断言链传递。改动面 4 文件均在写集内；三端 exports、Pi 既有分叉、模板、gate-contracts 未动。

---
schema_version: 1
sprint_slug: "2026-08-27-athena-9-9-8"
mode: "independent-design-challenge"
generated_from: "design.md"
source_design_sha256: "4d40949729d9e6c4ce366ddf2e3acd82808b91278e2c421e2b5ad706fe88fb53"
created: "2026-08-27"
author_does_not_review: true
output: "reviews/design-review.md"
---

# Review Packet — Athena 9.9.8

这是从 `design.md` 派生的独立挑战材料，不是第二份设计。请基于下表判断；只有需要核对证据时，才打开“定位”列指定章节，不要从头复述 design。

## Contract

| ID | 必须成立 | 定位 |
|---|---|---|
| AC1 | 作者不自审；Feature 无固定 design review，R/S 或用户显式要求才独立挑战 | 目标流程、验收标准 |
| AC2 | packet ≤80 行，design hash 与 AC 集合可机械验证 | Review contract |
| AC3 | 实现后一次 Athena review 请求、一份结果；无默认 2+1/passN | 一次多维 review |
| AC4 | 允许官方 review 内部多 agent；代码变化只触发目标复核 | 目标流程 |
| AC5 | 会改代码的 polish 在最终 review 前，review 绑定 exact diff | 目标流程、实现切片 1 |
| AC6 | 结果为结构化 frontmatter；gate 不数 Markdown 标题 | 一次多维 review |
| AC7 | 路径按风险收费；hook 仅红区 block，黄区 warning、绿区 async/fail-open | Hook 严格度 |
| AC8 | CC/CX 同事件最多一个同步 blocker；只读角色不手工绑定；quote/regex fixture 通过 | Hook 严格度、PACE 与 harness 边界 |
| AC9 | `_index` 有界、archive 默认排除、catalog 可重建、telemetry 出 Git | `ai_state` 三层 |
| AC10 | canonical/安装态/target 分开；迁移保留用户 effort，降档先 eval | 模型与 effort |
| AC11 | 双端验证且控制面 tokens 降 ≥40%，质量/安全不降 | 验收标准 |
| AC12 | 无第二状态树/人工 catalog；packet ≤80 行且不复制设计散文 | 发布边界 |

## 必须攻击的假设

1. “一次 review 请求”是否只是把三次读取藏进一个自定义 mega-agent，而没有真正利用 CC/CX 原生 review？
2. packet 由作者派生时，gate 是否真的能抓到漏 AC、旧 hash 与手工篡改？
3. polish 前移是否与现有 ship/architecture 义务冲突，或产生 review 后仍改代码的后门？
4. 取消 Feature 固定 design review 是否仍满足设计先行，而没有把独立性误当成所有路径的门禁？
5. `_index` 12 KiB、archive 与 runtime catalog 是否可实现且没有形成第二真相源或断链？
6. token 目标能否被现有 telemetry 可靠测量；“控制面 token”是否有清晰口径？
7. canonical 文件面是否完整覆盖 root prompt、skills、agents、hooks、templates、SessionStart、continuator 与 validator？
8. 官方事实与 Athena 本地选择是否分清，尤其是 Anthropic 的 layered review 与本地的一次调用？
9. 「未来槽」是否把 `athena-vm` 从 runtime-verify 矩阵删掉，或把 LLM-as-a-Verifier 写成 ship/VERDICT 门禁、默认代理？
10. hook 红/黄/绿是否真能阻止安全降级，同时消除无害 `rg` 解析误判、只读 agent 账本和 PostToolUse 记账造成的阻断/续跑？

## 输出约束

- 写入 `reviews/design-review.md`；reviewer 必须不是设计作者会话。
- Findings 按 P0/P1/P2/INFO 排序，每条给出 AC、design 章节和可执行修正；最多 8 条。
- 单独列 `MISSING / EXTRA / DEVIATED`，但不要复述全部 contract。
- 最后一行必须是 `VERDICT: PASS|CONCERNS|REWORK|FAIL`。
- 只完成这一轮，不自行开启第二轮；若需返工，用 findings 明确交还作者。

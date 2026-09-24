---
name: llm-as-a-verifier
description: 可选 LLM-as-a-Verifier。测试已绿且有多个合格 diff 时做 best-of-N 排序；不是 ship 门禁，不替代 test/review/VM。
---

# /llm-as-a-verifier — 可选排序器 (v9.9.9)

9.9.8 把 LaaV 留作 opt-in 槽（[design B](https://arxiv.org/abs/2607.05391)、[llm-as-a-verifier](https://github.com/llm-as-a-verifier/llm-as-a-verifier)）。本版提供可调用 skill 与脚本，**默认关闭**，不进入 PACE 默认链，不新建 stage。

## 何时用

同时满足：

1. `_index.laav_enabled = true`（`/athena-preferences` 写入），或用户本轮显式要求排序
2. 相关测试已绿
3. 面前有 **≥2 个合格候选**（独立 worktree / 补丁 / 实现变体）
4. 发生在 runtime-verify 之后、一次独立 review **之前**

缺任一条件 → skip，写明原因。不要为了用 LaaV 去生成多余候选。

## 怎么用

```bash
python3 ~/.claude/skills/llm-as-a-verifier/scripts/rank.py \
  --packet .ai_state/sprints/<slug>/review-packet.md \
  --candidate a.diff --candidate b.diff \
  --output .ai_state/.runtime/verifier_rank.json
```

- 后端必须能返回 score token 的 **logprobs**（OpenAI-compatible / Gemini / DeepSeek）。用 `ATHENA_LAAV_BASE_URL` + `ATHENA_LAAV_API_KEY`（或该 URL 对应的官方 key env）。
- Claude / 无 logprobs 的自定义网关 → 脚本 exit 0 且 `status: skipped`，**不得**用 1–5 离散分冒充 LaaV。
- 评分标准 = 当前 `review-packet.md` 的 Done checks，禁止另造「感觉更好」。
- 输出只排序。`reviewer` 可以读 `verifier_rank`，**不能**把它写成 VERDICT。delivery-gate / 测试 / VM 实跑仍是法律。

## 硬边界

1. 不替换 review、不替换 VM、不为 LaaV 新建 PACE stage。
2. 不改全局 `ANTHROPIC_BASE_URL`；独立端口/独立 base URL，fresh install 默认关。
3. 未校准前只记 ignored `.runtime` telemetry，不作为选实现的强制依据。
4. 秘密不进 hash 输入、不进对话。

细则与校准记录见 [playbook](references/playbook.md)。模板：[verifier_rank.json](templates/verifier_rank.json)。

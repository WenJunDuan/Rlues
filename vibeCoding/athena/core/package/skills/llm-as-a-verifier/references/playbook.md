# LLM-as-a-Verifier · playbook

论文原义不是普通 LLM-as-judge。做法是细粒度分数（如 1–20）+ score token 的 logprob 期望 + 重复抽样，用来 **best-of-N 排序** 和进度估计，不是 PASS/FAIL。出处：[arXiv 2607.05391](https://arxiv.org/abs/2607.05391)、[llm-as-a-verifier](https://github.com/llm-as-a-verifier/llm-as-a-verifier)、[TurboAgent](https://github.com/llm-as-a-verifier/TurboAgent)。离散 rubric 可用 [OpenAI Graders](https://developers.openai.com/api/reference/resources/graders) 作对照，但不能冒充 logprob verifier。

## 配置

| 变量 | 作用 |
|---|---|
| `ATHENA_LAAV_BASE_URL` | OpenAI-compatible Chat Completions 根，例如 `https://api.openai.com/v1` |
| `ATHENA_LAAV_API_KEY` | 该后端的 key；也接受 `OPENAI_API_KEY` 回退 |
| `ATHENA_LAAV_MODEL` | 可选；默认 `gpt-4.1-mini` |
| `_index.laav_enabled` | 项目开关，默认缺省 = false |

Claude Code 当前 OpenAI 兼容层忽略 `logprobs`。用 Claude 当 verifier 只能 skip。CX 自定义 gateway 若无 logprobs，整段 skip。

## 协议

1. 主 agent 确认测试绿、候选 ≥2、开关打开。
2. 每个候选提供统一 diff 或受控补丁路径；脚本读取 packet 的 Done checks 作为 rubric。
3. 对每个候选请求一次 completion：`logprobs=true`，`top_logprobs≥5`，要求模型只输出 `SCORE=<integer 1-20>`。
4. 用 `SCORE=` 后第一个整数 token 的概率质量期望作为分；失败/无 logprobs → 该候选 `unscored`。
5. 写入 `.ai_state/.runtime/verifier_rank.json`（Git ignored runtime）。`ranked` 按期望分降序。
6. 继续 Athena 一次独立 review。reviewer 可读排名，gate 不读。

## 校准（相信排名之前）

用历史 PASS/FAIL 与人工 review 建小型 gold set，记录 pairwise accuracy、翻转率、成本和 verifier/author 同家族偏差。阈值未达到前 `status` 只能是 `telemetry` 或 `skipped`，不能是 `trusted`。

## 失败形态

| 情况 | 结果 |
|---|---|
| 未配置后端 | `skipped` / `not_configured` |
| HTTP 或 JSON 失败 | `skipped` / `backend_error`；stderr 给调用方 |
| 响应无 logprobs | `skipped` / `logprobs_unavailable` |
| 单候选 | `skipped` / `need_two_candidates` |
| 开关关闭 | `skipped` / `disabled` |

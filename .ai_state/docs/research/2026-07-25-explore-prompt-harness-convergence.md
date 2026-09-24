---
doc_type: explore
slug: "prompt-harness-convergence"
created: "2026-07-25"
sprint_slug: "2026-07-25-athena-9-9-6-prompt-engineering"
status: accepted
---

# Explore — Prompt harness convergence

## 问题

Claude Code、Codex 与 Pi/Trellis/Superpowers/grill-me/OpenSpec/Spec Kit/GSD 的最新做法，对 Athena 下一版最稳定的共同启示是什么？

## 可复用结论

1. **平台越强，根 prompt 越应变薄。** 默认工具、memory、multi-agent、worktree 和 shell 说明由 host 提供；根 prompt 只保留项目政策与成功边界。
2. **procedure 用 skill，mechanism 用 hook。** 需要判断的流程放渐进披露 skill；必须执行的机械约束放 gate，并用真实 wire/schema 验证。
3. **description 只是 trigger index。** 把完整流程塞进 description 会抢先支配正文，也会挤爆 Codex 初始 catalog 预算。
4. **一次只解决一个最高价值未知。** grill-me 的价值不是多问，而是 repo-first、单问题、带推荐答案，并只持久化蒸馏后的决定。
5. **按任务注入上下文，不注入整套历史。** Trellis/GSD 的优势可映射到 Athena sprint pointers 和 bounded `_index`，无需第二状态树。
6. **skill 要像代码一样做 RED→GREEN→REFACTOR。** 先观察没有 skill/prompt 时的失败，再写最小规则，最后用压力场景堵住真实漏洞。
7. **双端共享语义，不共享假 API。** source contract 可以共用，但 CC/CX 的 agent、hook、worktree 和权限 adapter 必须保持真实不对称。
8. **长期真相与 host recall 分层。** Claude auto memory / Codex memories 可辅助召回；交付、gate、决策仍只信 `.ai_state`。

## Athena 9.9.6 映射

- shared policy/stage/role/skill contracts；
- CC/CX adapters；
- skill catalog ≤6500 chars；
- `_index` ≤4 KiB + dated capability snapshot；
- prompt A/B eval；
- 平台默认省略、角色模型显式。

## 不采用

- 新建 `.trellis` / `openspec` / `.planning` 状态树；
- 再装一套全局 brainstorm/TDD/review bootstrap；
- 为省字删除 PACE gate；
- 默认开放无限 agent 拓扑；
- 以 star 数或社区口碑替代官方配置合同与本地行为测试。

## 来源

- https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md
- https://github.com/mattpocock/skills/blob/main/README.md
- https://github.com/mindfold-ai/trellis
- https://github.com/obra/superpowers
- https://github.com/Fission-AI/OpenSpec
- https://github.github.com/spec-kit/
- https://github.com/gsd-build/get-shit-done
- https://developers.openai.com/api/docs/guides/latest-model
- https://github.com/anthropics/claude-code/releases/tag/v2.1.219

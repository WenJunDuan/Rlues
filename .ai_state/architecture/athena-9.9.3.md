# Athena 9.9.3 current architecture

9.9.3 延续 `pace` 控制平面 + `.ai_state` 数据平面双内核，在不新增 gate/skill 的前提下加入反过度工程规则与 per-turn stage breadcrumb。

- CX breadcrumb 优先 canonical `~/.agents/skills`，旧 `~/.codex/skills` 仅 fallback；CC/CX 总上下文不超过 10 行。
- unresolved over-engineering finding 使 evaluator VERDICT 上限为 CONCERNS。
- validator 锁定 committed 9.9.2 baseline，覆盖 tracked/untracked drift、双端 runtime 与 exact Codex 0.144.1 fresh setup/doctor/prompt-input。
- `harness-iteration-v1.1.md` 是包根分发文档，不自动安装；双端内置 skill 维持 26。
- 验证基线: CX 67/67、CC 107/107、validator 223/223。

---
doc_type: learning
slug: "canonical-install-path-runtime"
created: "2026-07-14"
sprint_slug: "2026-07-14-athena-9-9-3-review-fixes"
status: accepted
---

# Canonical install path needs runtime coverage

Codex setup 正确安装到 `~/.agents/skills`，但 consumer 读取 deprecated `~/.codex/skills` 时会静默失效。安装路径合同必须用 fresh HOME 执行“安装 → 调用 consumer”，并在 canonical/deprecated 同时存在时断言 canonical 优先。

官方来源: https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/core-skills/src/loader.rs#L318-L337

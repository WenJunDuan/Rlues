# Codex platform contract (Athena 9.9.6 DRAFT)

This cold-path reference records host-specific facts. It is not a renderer,
shared contract, runtime capability schema, or second state tree.

## Supported host and provider

- Floor: Codex CLI/App 0.145.0.
- `model_provider = "openai"` selects Codex's built-in provider.
- `model = "gpt-5.6-sol"` is the release model selection.
- ChatGPT login and OpenAI API keys use the built-in provider.
- The fresh template omits `openai_base_url`, allowing the built-in provider to
  select its official endpoint. Migration preserves an existing non-empty
  gateway/base URL; the release tree never stores credentials or an empty URL.

WSL acknowledgement, `[desktop]`, plugins, `approval_policy`, `sandbox_mode`,
and `web_search` remain explicit user-surface defaults in the adapter and must
be merged without overwriting a user's choices.

The adapter also preserves the 9.9.3 1M context, 900K auto-compact threshold,
Memories behavior, and unstable-feature warning preference. Stable features
that are already on by default and redundant per-skill `enabled=true` entries
remain omitted.

## Multi-Agent V2 split

`[features.multi_agent_v2]` owns the explicit V2 enablement, concurrent-thread
limit, and spawn metadata visibility carried by this adapter. This template has
no current general agent field to set, so it omits `[agents]`; role definitions
remain in `.codex/agents/*.toml`.

V1-only `max_depth` and compatibility `job_max_runtime_seconds` are not V2
gates. Athena nesting remains a policy and runtime-test responsibility through
PACE orchestration and the spawn-binding handshake.

Codex 0.145 function-tool hooks expose `spawn_agent` to PreToolUse and also
match it as `Agent`. Athena uses that native path for the red-zone worktree
pre-check, with SubagentStart audit evidence as defense in depth.

## GPT-5.6 gateway risk

openai/codex#31882 reproduces Responses-Lite and collaboration-tool 400 errors
with GPT-5.6 Sol on Azure OpenAI using Codex 0.144.0. The issue is still an
upstream report, not proof that every custom `openai_base_url` fails. Exact
0.145.0 dogfood must cover the configured gateway, and Sol's `code_mode_only`
path must prove Bash/apply_patch hook dispatch before release. Until then,
gateway users should use a provider/model combination their endpoint supports.

## Native execution boundaries

Codex agents, tools, hooks, plugins, login surfaces, and sandbox semantics are
host-native. Claude Code fields and hook events must not be copied to simulate
configuration parity. PACE aligns workflow outcomes, not platform vocabulary.

## Deferred release proof

The final release must prove exact 0.145.0/current-stable CLI and App startup,
all authentication and gateway-preservation surfaces, V2 behavior, skill
invocation, state budgets, migration, rollback, and runtime gates. This DRAFT
does not claim that proof exists.

Official reference:

- https://developers.openai.com/codex/config-reference/
- https://learn.chatgpt.com/docs/hooks
- https://github.com/openai/codex/issues/31882

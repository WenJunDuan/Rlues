# Claude Code platform contract (Athena 9.9.6 DRAFT)

This cold-path reference records host-specific facts. It is not injected on
every prompt and does not create a shared contract or capability state tree.

## Supported host

- Floor: Claude Code 2.1.219.
- The release template keeps the main session on the official `model: best`
  alias, which currently resolves to `opus`.
- No global subagent model override is set. `CLAUDE_CODE_SUBAGENT_MODEL`
  outranks both call parameters and agent frontmatter, so setting it would
  disable the role matrix; the release template must leave it unset.
- Role model and effort live in each agent's frontmatter: `architect` and
  `critic` use `fable`; `evaluator`, `generator`, `reviewer`,
  `spec-compliance`, `polish-worker` use `opus`. The root session uses `xhigh`;
  agent frontmatter may override it. `ANTHROPIC_DEFAULT_FABLE_MODEL` is pinned only to keep the
  `fable` alias resolvable for the plan/design review tier.
- Dated Anthropic model IDs are not release defaults for `opus` or `sonnet`.

## User-owned configuration

Fresh-install permission mode is `default`. Upgrade logic must preserve
an installed user's permission mode, allow/deny policy, credentials, plugins,
and other user preferences. The adapter keeps its worktree, required hooks, and
plugin declarations. It ships `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` as
a privacy-conservative default that migration must not overwrite when the user
already chose a value. The template also retains the 9.9.3 attribution and
installation-check choices and updates API timeout to 600 seconds. Tool Search
is default-on and therefore omitted. `settings.proxy.json` contains the local
6152/6153 overlay but is inactive unless explicitly loaded; credentials never
belong in the release tree.

## Native execution boundaries

Claude Code agents, hooks, matchers, permission modes, and skill invocation
controls are host-native. Codex names or event shapes must not be copied here to
manufacture symmetry. PACE policy aligns outcomes only.

Hooks may enforce only observable host events. Spec and delivery contract read
failures remain fail-closed; startup, breadcrumb, and restore diagnostics may
fail open as specified by PACE.

## Deferred release proof

The final release must prove alias resolution on exact 2.1.219 and current
stable, controlled skill invocation, hook payloads, state budgets, migration,
rollback, and runtime gates. This DRAFT does not claim that proof exists.

Official references:

- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/model-config

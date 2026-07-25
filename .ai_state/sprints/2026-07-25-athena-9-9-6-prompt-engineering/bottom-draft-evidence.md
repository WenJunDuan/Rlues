# Athena 9.9.6 Bottom Draft Evidence

## Scope

- Review root: `/Users/mi_manchi/workspace/Rlues`
- Branch: `main`; temporary `codex/athena-9.9.6-draft` worktree/branch removed after exact hash transfer
- Status: uncommitted, not pushed, not released
- Writes: `.gitignore`, `vibeCoding/claude/9.9.6/`, `vibeCoding/codex/9.9.6/`

## Complete fork proof

- Pre-migration normalized manifests matched:
  - CC: 116 files, SHA-256 `7d9f036aa2bb715dbe14fad56ddef49eeb140975a62c6065beac19ed569144c4`
  - CX: 113 files, SHA-256 `c9e293a43ca1e4fc0d68da2b37bca619c65f128cf3b6f9677eb61ccd70005b31`
- Post-migration target inventory:
  - CC: 130 files after bounded-hook, skill-playbook, proxy-overlay and contract updates
  - CX: 133 files after bounded-hook, skill-playbook, agent-policy and contract updates
- Both 9.9.3 roots are Git-diff clean.
- Historical CX CHANGELOG suffix is byte-identical to 9.9.3: 30,413 bytes, SHA-256 `fbb885f730266679d5c2291076377bc311e49c1937e06532a727f8cc8f4aa8bc`.

## Main-thread verification

- JSON/TOML/Python parse: `2 / 10 / 25` PASS.
- Node hook syntax: `17` PASS.
- Skill discovery inventory: `26` CC + `26` CX.
- Exact Codex binary: `codex-cli 0.145.0`.
- Exact Codex config load: `CODEX_HOME=<temp> codex features list` exited 0; `multi_agent_v2 stable true`.
- Git ignore boundary: root `.claude/` remains ignored; nested CC/CX release adapters are trackable.
- Denylists: no Fable/Sonnet agent frontmatter、dated CC pins、旧 Sonnet subagent override、timeout/tool-search/install/traffic defaults；新的全局 subagent override 明确为 `opus`。CX 无 custom provider、manual context/compact metadata、memories、manual skills、V1 depth/no-op fields。
- Forbidden architecture: no shared contract tree, renderer, runtime-capabilities schema, second state tree, or tracked test/eval tree.

## Corrective audit

- Replaced invalid planned CC `defaultMode = manual` with official valid `default`; migration preserves any existing official mode.
- Removed alias-only CX `[agents] max_threads`; V2 concurrency remains under `[features.multi_agent_v2]`.
- Restored 9.9.3-and-earlier historical CHANGELOG below the 9.9.6 DRAFT section.
- User override: CC main `model=best`，无全局 subagent override；architect/critic=Fable，其余五个 packaged agents=Opus；effort 保持 3×xhigh + 4×high。

## Deferred (not claimed complete)

CC exact 2.1.219/current-stable alias runtime; CX App/auth/gateway behavior; controlled skill invocation; bounded state injection and retention; N9/N10; migration/rollback; N≥3 A/B; runtime-verify; review 2+1; polish; architecture update; commit/push/release.

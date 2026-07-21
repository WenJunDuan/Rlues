# Route note: merge branches and diagnose TUN/Tailscale

- Date: 2026-07-21
- Candidate A (selected): Quick/ship — fast-forward the only local topic branch into `main`, then validate the Mihomo YAML and inspect TUN/Tailscale routing.
- Candidate B: Refactor/System — use an isolated worktree and full runtime verification. Rejected because the branch is a one-commit, two-hook change and the requested network diagnosis can be performed read-only against the existing configuration.
- Evidence: `git branch -a -vv` shows only `main` plus `fix/gate-generator-chain-role`; `git rev-list --left-right --count main...fix/gate-generator-chain-role` is `0 1`, so the merge is a reversible fast-forward. The working tree has unrelated user edits in `.ai_state/`, `.gitignore`, and `clash/mihomo_sparkle.yaml`.
- Trade-off: preserve the four existing uncommitted files and do not push to `origin`; merge only the topic branch that is ahead of `main`.
- Acceptance: `main` contains commit `935cd9f`; YAML parses; TUN excludes Tailscale CIDRs and rules send Tailscale processes/domains/CIDRs to `DIRECT`; report any remaining runtime conflict as requiring host route/interface evidence.
- Exit/re-route: if merge touches the dirty files or YAML validation fails, stop before further mutation and report the exact conflict/error.

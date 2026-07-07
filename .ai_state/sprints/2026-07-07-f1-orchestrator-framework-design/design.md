# F1 Design — Fullstack Delivery Skills Framework

- Sprint: `2026-07-07-f1-orchestrator-framework-design`
- Path: System
- Source: `design-brief.md` from quantum/Claude handoff, 2026-07-07
- Scope: 9.9.0 skills package design and first implementation skeleton

## Round 1

### Decision 1: 14-Step Loop Maps Onto PACE, Not A Second State Machine

The delivery loop remains a PACE specialization. `_index.md` is the only durable state authority; `biz-delivery-loop` may write stage artifacts and suggest next action, but it must not maintain an independent workflow state file.

| User step | PACE owner | Artifact / evidence |
|---|---|---|
| Accept requirement list | `athena-requirements` | `requirements/{slug}.md` |
| Split Sprint | `roadmap` | `roadmap/{slug}/items.yaml`, `roadmap.md` |
| Freeze API contract | `design` | `contracts/openapi.yaml`, contract notes |
| HTML mockup + screenshot | `design` | mockup HTML, screenshot, CP1 record |
| Frontend demo with mock data | `impl` + `runtime-verify` | demo files, dev-server evidence |
| DB table design + DDL | `design` / `impl` via `db-schema-gen` | table design `.md`, executable `.sql` |
| Backend code | `impl` via `scaffold-module-gen` | generated module files, compile evidence |
| Unit tests + debug | `runtime-verify` via `unit-test-gen` | test report |
| FE/BE integration | `runtime-verify` | contract diff and real API evidence |
| Review trio | `review` | `reviews/pass1.md` |
| Playwright + security tests | `runtime-verify` | E2E and security evidence |
| Requirement reconciliation | `spec-compliance` | requirement status table |
| Delivery report | pre-`ship` | `delivery-report.md` |
| User publish instruction | `ship` | commit/push/release evidence |

Alternative rejected: a standalone `biz-loop-state.yaml`. It would duplicate `_index.md`, compete with hooks, and make rollback semantics ambiguous.

### Decision 2: Checkpoints Split Into Machine Gates And Human Confirmations

Machine gates use evidence files and real commands. Human confirmations are explicit stop points; they do not get simulated by a passing command.

| CP | Type | Pass signal | Fail rollback target | Loop limit |
|---|---|---|---|---|
| CP1 mockup confirmed | Human | user confirmation recorded | design mockup/contracts | 3 |
| CP2 demo running | Machine | dev server health + screenshot/smoke evidence | frontend impl | 3 |
| CP3 schema reviewed | Human | user approval of table design + DDL | DB design | 3 |
| CP4 backend gate | Machine | compile/tests/security gates pass | backend impl | 3 |
| CP5 delivery accepted | Human | user accepts report and release target | failing stage named in report | 3 |

Machine gates check evidence, not log strings. This absorbs the S2 lesson where grep-based delivery gates produced false positives.

Alternative rejected: always rollback to Sprint start. That wastes valid work and hides which contract failed.

### Decision 3: Eight Skills Stay System-Agnostic

The package owns reusable procedures; each target project owns its Convention Pack.

| Skill | Responsibility | Required input | Output | Boundary |
|---|---|---|---|---|
| `scaffold-module-gen` | backend/business module generation | Convention Pack templates + validation command | compile-ready module | no live data reads |
| `scaffold-page-gen` | frontend page/demo generation | frontend Convention Pack + API contract | runnable mock/demo page | no backend implementation |
| `db-schema-gen` | schema design package | entity/permission/data-domain requirements + DB conventions | table design md + DDL sql | no direct DB mutation by default |
| `unit-test-gen` | unit/integration test loop | test conventions + changed files | tests + debug report | no E2E browser tests |
| `security-test` | static/dynamic security checks | security checklist + runtime-env when dynamic | security report | no broad pentest |
| `playwright-e2e` | delivery E2E wrapper | runtime-env + acceptance flows | Playwright tests + evidence | delegates browser mechanics to `playwright` |
| `project-data-reader` | live read-only business data | MCP endpoint / capability manifest | structured read result | no source generation |
| `biz-delivery-loop` | PACE orchestration | requirements + roadmap + skill outputs | checkpoints + delivery report | no parallel state machine |

Alternative rejected: one giant `fullstack-delivery` skill containing all implementation details. Separate triggerable skills keep context small and match Codex skill discovery.

### Decision 4: Delivery Report Is Machine-Parseable Frontmatter Plus Markdown

The report schema uses YAML frontmatter for automation and Markdown tables for human review. Required sections: requirement completion, FE/BE/unit/E2E/security tests, model/token usage, leftover issues, and human confirmations.

Alternative rejected: free-form final prose only. It is readable, but cannot support later evidence cross-checks.

### Decision 5: Token Usage Lands In `token-usage.yaml`

Design target: extend evidence collection with a sprint-local usage accumulator:

```yaml
sprint: 2026-07-07-example
totals:
  input_tokens: 0
  output_tokens: 0
  reasoning_tokens: 0
by_stage:
  impl:
    gpt-5.5:
      calls: 0
      input_tokens: 0
      output_tokens: 0
      reasoning_tokens: 0
```

CC can read usage from transcript/subagent usage blocks. CX support must be verified against current hook payloads before implementation; if unavailable, record `unknown` rather than inventing numbers.

Alternative rejected: infer token use from elapsed time or model name. That produces false precision.

### Decision 6: Runtime Environment Is A Convention Pack Contract

Skills must read `runtime-env` declarations instead of guessing commands, ports, profiles, or teardown:

```yaml
runtime-env:
  frontend:
    command: "bun dev --host 127.0.0.1 --port 5173"
    port: 5173
    health_url: "http://127.0.0.1:5173/"
    teardown: "pkill -f 'bun dev'"
  backend:
    command: "mvn spring-boot:run -Dspring-boot.run.profiles=dev"
    port: 8080
    health_url: "http://127.0.0.1:8080/actuator/health"
  database:
    command: "docker compose up -d postgres"
    health_command: "docker compose exec postgres pg_isready"
```

Alternative rejected: hard-coded quantum commands inside skills. That violates the Rlues/project split.

### Decision 7: CC/CX Stay Symmetric, Config Differences Stay Explicit

Both `vibeCoding/claude/9.9.0/.claude/skills` and `vibeCoding/codex/9.9.0/.codex/skills` receive the same skill content. Codex additionally needs `config.toml` registration for discoverability in this package.

Alternative rejected: only patch installed `~/.codex` / `~/.claude`. The versioned package is the source of truth.

## Implementation Slice

This Sprint implements the package-level skill skeletons and shared reference schemas:

- Add `scaffold-page-gen`
- Add `db-schema-gen`
- Add `unit-test-gen`
- Add `security-test`
- Add `playwright-e2e`
- Add `biz-delivery-loop` with checkpoint/report/runtime-env references
- Register all eight fullstack-delivery skills in Codex `config.toml`

Out of scope for this slice:

- Hook implementation for token aggregation
- Delivery-gate code changes
- Real quantum FE/BE Convention Pack edits
- End-to-end drill against live quantum projects

# F6 Runtime Verify

## /goal 完成条件

- Run Rlues F2-F5 regression scripts.
- Run F6 drill script.
- Run local quantum repo checks that do not require secrets.
- Record missing dynamic E2E prerequisites as blockers.

## 测试场景 (实跑)

| 场景 | 类型 | 命令 | 实际输出 | 判定 |
|---|---|---|---|---|
| F2 scaffold-page-gen | regression | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-scaffold-page-gen.py` | `scaffold-page-gen regression ok` | PASS |
| F3 db/unit | regression | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-db-unit-gen.py` | `db-schema-gen and unit-test-gen regression ok` | PASS |
| F4 security/e2e | regression | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-security-e2e.py` | `security-test and playwright-e2e regression ok` | PASS |
| F5 delivery loop | regression | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-biz-delivery-loop.py` | `biz-delivery-loop and project-data-reader regression ok` | PASS |
| quantum-front | repo test | `bun test` | `15 pass, 0 fail` | PASS |
| quantum-cowork | repo test | `bun test` | `1460 pass, 0 fail` | PASS |
| quantum-backend MCP | repo test | `mvn -pl quantum-mcp -am test` | `BUILD SUCCESS`; `quantum-mcp` tests `12 run, 0 failures` | PASS |
| backend single-module probe | repo test | `mvn -pl quantum-mcp test` | failed resolving local reactor dependencies with `${revision}` artifacts | EXPECTED BLOCKER; use `-am` |
| F6 contract drill | drill | `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test-end-to-end-drill.py` | `static-ok-dynamic-blocked`; checks ok for frontend runtime-env, backend convention pack, backend MCP manifest, cowork MCP provider; failures `[]` | PASS |

## Blocked Dynamic Cases

- `quantum-backend/docs/ai/convention-pack/runtime-env.md` is absent, so the drill cannot safely infer a live server command or health URL.
- OAuth/test account handoff for the MCP endpoint is not present in repo-safe docs.
- `quantum-cowork/docs/ai` is absent, so cowork runtime contract is represented only by local MCP provider tests.
- `quantum-cowork` remote fetch failed over HTTPS credentials, so remote freshness cannot be proven from this machine.

## 自测自改记录

- Initial backend command `mvn -pl quantum-mcp test` was too narrow and failed on reactor dependency resolution.
- Re-ran with `mvn -pl quantum-mcp -am test`; reactor built local dependencies and passed.

## Reflect

F6 can truthfully close the skill roadmap as a static contract and local test drill. A true live FE/BE/MCP business flow remains blocked by runtime environment and credential/test-account inputs outside Rlues.

## VERDICT

PASS with dynamic E2E blockers documented.

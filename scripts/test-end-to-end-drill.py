#!/usr/bin/env python3
"""F6 contract drill across Rlues skills and the local quantum repos.

The script intentionally separates static readiness from dynamic runtime E2E.
It exits successfully when the local contracts are inspectable and reports
dynamic blockers as data instead of pretending a live stack was exercised.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUANTUM = Path("/Users/mi_manchi/workspace/quantum")
FRONT_PACK = QUANTUM / "quantum-front/docs/ai/convention-pack"
BACKEND_PACK = QUANTUM / "quantum-backend/docs/ai/convention-pack"
BACKEND_MCP = QUANTUM / "quantum-backend/quantum-mcp"
COWORK = QUANTUM / "quantum-cowork"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=20)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def add_check(checks: list[dict[str, str]], name: str, status: str, detail: str) -> None:
    checks.append({"name": name, "status": status, "detail": detail})


def main() -> int:
    checks: list[dict[str, str]] = []
    blockers: list[str] = []
    failures: list[str] = []

    if FRONT_PACK.exists():
        runtime_env = FRONT_PACK / "runtime-env.md"
        if runtime_env.exists():
            text = read(runtime_env)
            required = ["dev_command", "port", "health_url", "teardown"]
            missing = [item for item in required if item not in text]
            if missing:
                failures.append(f"frontend runtime-env missing keys: {', '.join(missing)}")
            else:
                add_check(checks, "frontend-runtime-env", "ok", str(runtime_env))
        else:
            failures.append(f"missing frontend runtime-env: {runtime_env}")
    else:
        failures.append(f"missing frontend convention pack: {FRONT_PACK}")

    if BACKEND_PACK.exists():
        add_check(checks, "backend-convention-pack", "ok", str(BACKEND_PACK))
        backend_runtime = BACKEND_PACK / "runtime-env.md"
        if backend_runtime.exists():
            add_check(checks, "backend-runtime-env", "ok", str(backend_runtime))
        else:
            blockers.append("backend runtime-env.md absent; cannot derive safe live server command/health URL")
    else:
        failures.append(f"missing backend convention pack: {BACKEND_PACK}")

    manifest_service = BACKEND_MCP / "src/main/java/com/alpha/mcp/manifest/CapabilityManifestService.java"
    manifest_test = BACKEND_MCP / "src/test/java/com/alpha/mcp/manifest/CapabilityManifestServiceTest.java"
    if manifest_service.exists() and manifest_test.exists():
        service_text = read(manifest_service)
        expected_tools = ["system.user.search", "system.dept.tree", "system.role.list"]
        missing_tools = [tool for tool in expected_tools if tool not in service_text]
        if missing_tools:
            failures.append(f"backend manifest missing tools: {', '.join(missing_tools)}")
        elif '"readOnly", true' not in service_text:
            failures.append("backend manifest tools are not declared readOnly=true")
        else:
            add_check(checks, "backend-mcp-manifest", "ok", str(manifest_service))
    else:
        failures.append("backend quantum-mcp manifest service or test is missing")

    cowork_pkg = COWORK / "package.json"
    cowork_mcp_test = COWORK / "src/tests/mcp.test.ts"
    cowork_ai_docs = COWORK / "docs/ai"
    if cowork_pkg.exists() and cowork_mcp_test.exists():
        pkg_text = read(cowork_pkg)
        if "@modelcontextprotocol/sdk" not in pkg_text:
            failures.append("quantum-cowork package.json lacks @modelcontextprotocol/sdk")
        else:
            add_check(checks, "cowork-mcp-provider", "ok", str(cowork_mcp_test))
    else:
        blockers.append("quantum-cowork docs/ai runtime contract absent; only local MCP provider tests are available")
    if not cowork_ai_docs.exists():
        blockers.append("quantum-cowork docs/ai runtime contract absent; local provider tests only")

    test_account_doc = BACKEND_PACK / "runtime-env.md"
    if not test_account_doc.exists():
        blockers.append("repo-safe OAuth/test account handoff absent; cannot complete MCP auth flow")

    cowork_fetch = run(["git", "fetch", "origin", "main", "--prune"], COWORK)
    if cowork_fetch.returncode == 0:
        add_check(checks, "cowork-remote-fetch", "ok", "origin/main refreshed")
    else:
        blockers.append("quantum-cowork remote fetch failed; cannot verify remote freshness")

    status = "ok" if not blockers else "static-ok-dynamic-blocked"
    payload = {
        "status": "failed" if failures else status,
        "checks": checks,
        "dynamic_blockers": blockers,
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Regression checks for biz-delivery-loop and project-data-reader resources."""
from __future__ import annotations

import filecmp
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = {
    "biz-delivery-loop": {
        "cx": ROOT / "vibeCoding/codex/9.9.0/.codex/skills/biz-delivery-loop",
        "cc": ROOT / "vibeCoding/claude/9.9.0/.claude/skills/biz-delivery-loop",
        "validator": "scripts/check_delivery_loop_contract.py",
        "refs": [
            "references/checkpoint-protocol.md",
            "references/delivery-report-schema.md",
            "references/orchestration-contract.md",
            "references/runtime-env-contract.md",
        ],
    },
    "project-data-reader": {
        "cx": ROOT / "vibeCoding/codex/9.9.0/.codex/skills/project-data-reader",
        "cc": ROOT / "vibeCoding/claude/9.9.0/.claude/skills/project-data-reader",
        "validator": "scripts/check_capability_manifest.py",
        "refs": ["references/capability-manifest-contract.md"],
    },
}


def run(cmd: list[str], *, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=30)
    if result.returncode != expect:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise AssertionError(f"{cmd} returned {result.returncode}, expected {expect}")
    return result


def purge_generated_bytecode(skill_dir: Path) -> None:
    for path in skill_dir.rglob("__pycache__"):
        shutil.rmtree(path)


def assert_skill_source_parity(skill_name: str) -> None:
    cx_skill = SKILLS[skill_name]["cx"]
    cc_skill = SKILLS[skill_name]["cc"]
    purge_generated_bytecode(cx_skill)
    purge_generated_bytecode(cc_skill)
    comparison = filecmp.dircmp(cx_skill, cc_skill, ignore=["__pycache__"])
    mismatches: list[str] = []

    def walk(cmp: filecmp.dircmp, prefix: str = "") -> None:
        for name in cmp.left_only:
            mismatches.append(f"only in CX: {prefix}{name}")
        for name in cmp.right_only:
            mismatches.append(f"only in CC: {prefix}{name}")
        for name in cmp.diff_files:
            mismatches.append(f"content differs: {prefix}{name}")
        for name, child in cmp.subdirs.items():
            walk(child, f"{prefix}{name}/")

    walk(comparison)
    if mismatches:
        raise AssertionError(f"{skill_name} CC/CX source parity failed:\n" + "\n".join(mismatches))


def valid_manifest() -> dict:
    return {
        "schema": "project-capability-manifest",
        "version": 1,
        "service": "quantum-backend",
        "transport": "streamable-http",
        "endpoint": "http://127.0.0.1:8080/mcp",
        "auth": {
            "type": "oauth2-pkce",
            "protected_resource_metadata_url": "http://127.0.0.1:8080/.well-known/oauth-protected-resource",
        },
        "identity": {"passthrough": True, "token_cache": "agent-managed"},
        "capabilities": [
            {
                "name": "system.user.list",
                "mode": "read",
                "tool": "readUsers",
                "permission": "system:user:list",
                "data_scope": "target-enforced",
                "audit": True,
                "redaction": ["phone", "email"],
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            }
        ],
    }


def main() -> int:
    for skill_name, meta in SKILLS.items():
        for side in ("cx", "cc"):
            skill_dir = meta[side]
            for rel in [*meta["refs"], meta["validator"]]:
                if not (skill_dir / rel).exists():
                    raise AssertionError(f"missing {skill_dir / rel}")
        assert_skill_source_parity(skill_name)

    for side in ("cx", "cc"):
        skill_dir = SKILLS["biz-delivery-loop"][side]
        result = run(["python3", str(skill_dir / "scripts/check_delivery_loop_contract.py"), str(skill_dir)])
        if json.loads(result.stdout)["status"] != "ok":
            raise AssertionError(result.stdout)

    with tempfile.TemporaryDirectory(prefix="capability-manifest-") as tmp:
        manifest = Path(tmp) / "manifest.json"
        manifest.write_text(json.dumps(valid_manifest(), ensure_ascii=False), encoding="utf-8")
        script = SKILLS["project-data-reader"]["cx"] / "scripts/check_capability_manifest.py"
        run(["python3", str(script), str(manifest)])

        write_manifest = valid_manifest()
        write_manifest["capabilities"][0]["mode"] = "write"
        manifest.write_text(json.dumps(write_manifest, ensure_ascii=False), encoding="utf-8")
        run(["python3", str(script), str(manifest)], expect=1)

        secret_manifest = valid_manifest()
        secret_manifest["auth"]["access_token"] = "do-not-store"
        manifest.write_text(json.dumps(secret_manifest, ensure_ascii=False), encoding="utf-8")
        run(["python3", str(script), str(manifest)], expect=1)

        no_scope_manifest = valid_manifest()
        del no_scope_manifest["capabilities"][0]["data_scope"]
        manifest.write_text(json.dumps(no_scope_manifest, ensure_ascii=False), encoding="utf-8")
        run(["python3", str(script), str(manifest)], expect=1)

    for skill_name in SKILLS:
        assert_skill_source_parity(skill_name)

    print("biz-delivery-loop and project-data-reader regression ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

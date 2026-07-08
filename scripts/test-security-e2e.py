#!/usr/bin/env python3
"""Regression checks for security-test and playwright-e2e skill resources."""
from __future__ import annotations

import filecmp
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUANTUM_FRONT_PACK = Path("/Users/mi_manchi/workspace/quantum/quantum-front/docs/ai/convention-pack")
QUANTUM_BACKEND_PACK = Path("/Users/mi_manchi/workspace/quantum/quantum-backend/docs/ai/convention-pack")

SKILLS = {
    "security-test": {
        "cx": ROOT / "vibeCoding/codex/9.9.0/.codex/skills/security-test",
        "cc": ROOT / "vibeCoding/claude/9.9.0/.claude/skills/security-test",
        "profile": "security",
        "refs": ["references/security-test-contract.md", "references/quantum-security-adapter.md"],
    },
    "playwright-e2e": {
        "cx": ROOT / "vibeCoding/codex/9.9.0/.codex/skills/playwright-e2e",
        "cc": ROOT / "vibeCoding/claude/9.9.0/.claude/skills/playwright-e2e",
        "profile": "e2e",
        "refs": ["references/e2e-convention-pack.md", "references/quantum-e2e-adapter.md"],
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


def assert_validator_ok(skill_dir: Path, profile: str) -> None:
    script = skill_dir / "scripts/check_security_e2e_pack.py"
    result = run(
        [
            "python3",
            str(script),
            "--frontend-pack",
            str(QUANTUM_FRONT_PACK),
            "--backend-pack",
            str(QUANTUM_BACKEND_PACK),
            "--profile",
            profile,
        ]
    )
    payload = json.loads(result.stdout)
    if payload["status"] != "ok":
        raise AssertionError(result.stdout)


def run_validator(script: Path, frontend_pack: Path, backend_pack: Path, profile: str, *, expect: int = 0) -> None:
    run(
        [
            "python3",
            str(script),
            "--frontend-pack",
            str(frontend_pack),
            "--backend-pack",
            str(backend_pack),
            "--profile",
            profile,
        ],
        expect=expect,
    )


def main() -> int:
    if not QUANTUM_FRONT_PACK.exists():
        raise AssertionError(f"missing quantum-front pack: {QUANTUM_FRONT_PACK}")
    if not QUANTUM_BACKEND_PACK.exists():
        raise AssertionError(f"missing quantum-backend pack: {QUANTUM_BACKEND_PACK}")

    for skill_name, meta in SKILLS.items():
        assert_validator_ok(meta["cx"], meta["profile"])
        assert_validator_ok(meta["cc"], meta["profile"])
        assert_skill_source_parity(skill_name)
        for side in ("cx", "cc"):
            skill_dir = meta[side]
            for rel in [*meta["refs"], "scripts/check_security_e2e_pack.py"]:
                if not (skill_dir / rel).exists():
                    raise AssertionError(f"missing {skill_dir / rel}")

    script = SKILLS["security-test"]["cx"] / "scripts/check_security_e2e_pack.py"
    run_validator(script, QUANTUM_FRONT_PACK, QUANTUM_BACKEND_PACK, "all")

    with tempfile.TemporaryDirectory(prefix="security-e2e-front-") as tmp:
        broken_front = Path(tmp) / "front"
        shutil.copytree(QUANTUM_FRONT_PACK, broken_front)
        (broken_front / "runtime-env.md").unlink()
        run_validator(script, broken_front, QUANTUM_BACKEND_PACK, "e2e", expect=1)

    with tempfile.TemporaryDirectory(prefix="security-e2e-runtime-") as tmp:
        broken_front = Path(tmp) / "front"
        shutil.copytree(QUANTUM_FRONT_PACK, broken_front)
        runtime_env = broken_front / "runtime-env.md"
        runtime_env.write_text(runtime_env.read_text(encoding="utf-8").replace("health_url", "health"), encoding="utf-8")
        run_validator(script, broken_front, QUANTUM_BACKEND_PACK, "e2e", expect=1)

    with tempfile.TemporaryDirectory(prefix="security-e2e-back-") as tmp:
        broken_back = Path(tmp) / "back"
        shutil.copytree(QUANTUM_BACKEND_PACK, broken_back)
        (broken_back / "validate.md").unlink()
        run_validator(script, QUANTUM_FRONT_PACK, broken_back, "security", expect=1)

    with tempfile.TemporaryDirectory(prefix="security-e2e-perm-") as tmp:
        broken_back = Path(tmp) / "back"
        shutil.copytree(QUANTUM_BACKEND_PACK, broken_back)
        controller_template = broken_back / "templates/Controller.java.tmpl"
        controller_template.write_text(
            controller_template.read_text(encoding="utf-8").replace("@RequiresPermission", "@Permission"),
            encoding="utf-8",
        )
        run_validator(script, QUANTUM_FRONT_PACK, broken_back, "security", expect=1)

    with tempfile.TemporaryDirectory(prefix="security-e2e-access-") as tmp:
        broken_front = Path(tmp) / "front"
        shutil.copytree(QUANTUM_FRONT_PACK, broken_front)
        validate_md = broken_front / "validate.md"
        validate_md.write_text(validate_md.read_text(encoding="utf-8").replace("access-guard-exempt", "access-exempt"), encoding="utf-8")
        run_validator(script, broken_front, QUANTUM_BACKEND_PACK, "security", expect=1)

    for skill_name in SKILLS:
        assert_skill_source_parity(skill_name)

    print("security-test and playwright-e2e regression ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Regression checks for db-schema-gen and unit-test-gen skill resources."""
from __future__ import annotations

import filecmp
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUANTUM_BACKEND_PACK = Path("/Users/mi_manchi/workspace/quantum/quantum-backend/docs/ai/convention-pack")

SKILLS = {
    "db-schema-gen": {
        "cx": ROOT / "vibeCoding/codex/9.9.0/.codex/skills/db-schema-gen",
        "cc": ROOT / "vibeCoding/claude/9.9.0/.claude/skills/db-schema-gen",
        "profile": "db",
        "refs": ["references/backend-db-convention-pack.md", "references/quantum-backend-adapter.md"],
    },
    "unit-test-gen": {
        "cx": ROOT / "vibeCoding/codex/9.9.0/.codex/skills/unit-test-gen",
        "cc": ROOT / "vibeCoding/claude/9.9.0/.claude/skills/unit-test-gen",
        "profile": "test",
        "refs": ["references/backend-test-convention-pack.md", "references/quantum-backend-adapter.md"],
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
    script = skill_dir / "scripts/check_backend_pack.py"
    result = run(["python3", str(script), str(QUANTUM_BACKEND_PACK), "--profile", profile])
    payload = json.loads(result.stdout)
    if payload["status"] != "ok":
        raise AssertionError(result.stdout)


def main() -> int:
    if not QUANTUM_BACKEND_PACK.exists():
        raise AssertionError(f"missing quantum-backend pack: {QUANTUM_BACKEND_PACK}")

    for skill_name, meta in SKILLS.items():
        assert_validator_ok(meta["cx"], meta["profile"])
        assert_validator_ok(meta["cc"], meta["profile"])
        assert_skill_source_parity(skill_name)
        for side in ("cx", "cc"):
            skill_dir = meta[side]
            for rel in [*meta["refs"], "scripts/check_backend_pack.py"]:
                if not (skill_dir / rel).exists():
                    raise AssertionError(f"missing {skill_dir / rel}")

    all_profile_script = SKILLS["db-schema-gen"]["cx"] / "scripts/check_backend_pack.py"
    run(["python3", str(all_profile_script), str(QUANTUM_BACKEND_PACK), "--profile", "all"])

    with tempfile.TemporaryDirectory(prefix="backend-pack-db-") as tmp:
        broken = Path(tmp) / "pack"
        shutil.copytree(QUANTUM_BACKEND_PACK, broken)
        (broken / "db-conventions.md").unlink()
        run(["python3", str(all_profile_script), str(broken), "--profile", "db"], expect=1)

    with tempfile.TemporaryDirectory(prefix="backend-pack-test-") as tmp:
        broken = Path(tmp) / "pack"
        shutil.copytree(QUANTUM_BACKEND_PACK, broken)
        (broken / "test-conventions.md").unlink()
        run(["python3", str(all_profile_script), str(broken), "--profile", "test"], expect=1)

    with tempfile.TemporaryDirectory(prefix="backend-pack-g5-") as tmp:
        broken = Path(tmp) / "pack"
        shutil.copytree(QUANTUM_BACKEND_PACK, broken)
        validate_md = broken / "validate.md"
        validate_md.write_text(validate_md.read_text(encoding="utf-8").replace("G5a", "G5x"), encoding="utf-8")
        run(["python3", str(all_profile_script), str(broken), "--profile", "db"], expect=1)

    with tempfile.TemporaryDirectory(prefix="backend-pack-g6-") as tmp:
        broken = Path(tmp) / "pack"
        shutil.copytree(QUANTUM_BACKEND_PACK, broken)
        test_md = broken / "test-conventions.md"
        test_md.write_text(
            test_md.read_text(encoding="utf-8").replace("updateShouldThrowConflictWhenVersionMismatch", "updateShouldHandleConflict"),
            encoding="utf-8",
        )
        run(["python3", str(all_profile_script), str(broken), "--profile", "test"], expect=1)

    for skill_name in SKILLS:
        assert_skill_source_parity(skill_name)

    print("db-schema-gen and unit-test-gen regression ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

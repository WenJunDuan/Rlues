#!/usr/bin/env python3
"""Regression checks for scaffold-page-gen skill resources."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CX_SKILL = ROOT / "vibeCoding/codex/9.9.0/.codex/skills/scaffold-page-gen"
CC_SKILL = ROOT / "vibeCoding/claude/9.9.0/.claude/skills/scaffold-page-gen"
QUANTUM_FRONT_PACK = Path("/Users/mi_manchi/workspace/quantum/quantum-front/docs/ai/convention-pack")


def run(cmd: list[str], *, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=30)
    if result.returncode != expect:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise AssertionError(f"{cmd} returned {result.returncode}, expected {expect}")
    return result


def assert_validator_ok(skill_dir: Path) -> None:
    script = skill_dir / "scripts/check_frontend_pack.py"
    result = run(["python3", str(script), str(QUANTUM_FRONT_PACK)])
    payload = json.loads(result.stdout)
    if payload["status"] != "ok":
        raise AssertionError(result.stdout)


def main() -> int:
    if not QUANTUM_FRONT_PACK.exists():
        raise AssertionError(f"missing quantum-front pack: {QUANTUM_FRONT_PACK}")

    assert_validator_ok(CX_SKILL)
    assert_validator_ok(CC_SKILL)

    with tempfile.TemporaryDirectory(prefix="scaffold-page-pack-") as tmp:
        broken = Path(tmp) / "pack"
        shutil.copytree(QUANTUM_FRONT_PACK, broken)
        (broken / "validate.md").unlink()
        run(["python3", str(CX_SKILL / "scripts/check_frontend_pack.py"), str(broken)], expect=1)

    for skill_dir in (CX_SKILL, CC_SKILL):
        for rel in [
            "references/frontend-convention-pack.md",
            "references/quantum-front-adapter.md",
            "scripts/check_frontend_pack.py",
        ]:
            if not (skill_dir / rel).exists():
                raise AssertionError(f"missing {skill_dir / rel}")

    print("scaffold-page-gen regression ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

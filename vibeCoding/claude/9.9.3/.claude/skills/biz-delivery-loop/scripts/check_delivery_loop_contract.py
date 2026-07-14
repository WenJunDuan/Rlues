#!/usr/bin/env python3
"""Validate biz-delivery-loop skill contracts."""
from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FILES = [
    "SKILL.md",
    "references/checkpoint-protocol.md",
    "references/delivery-report-schema.md",
    "references/orchestration-contract.md",
    "references/runtime-env-contract.md",
]

SKILL_MARKERS = [
    "quantum-codegen",
    "quantum-data",
    "_index.md",
]
CHECKPOINT_MARKERS = ["checkpoints.yaml", "checkpoint_id", "evidence_required", "fail_target", "rollback_target", "issue_path", "CP1", "CP2", "CP3", "CP4", "CP5"]
REPORT_MARKERS = ["token_usage_path", "token_usage_status", "requirements_total", "runtime_env_warnings", "fe_tests", "be_tests", "e2e_tests", "security_tests", "blocked_dynamic_cases", "capability_reads", "model_usage", "manual_confirmations"]
RUNTIME_MARKERS = ["frontend", "backend", "database", "test_accounts", "health_url", "teardown", "external: true"]
ORCHESTRATION_MARKERS = ["Single State Authority", "Skill Chain", "Checkpoint Rules", "Evidence Rules", "Blocking Conditions", "blocked_dynamic_cases"]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_markers(content: str, markers: list[str], errors: list[str], label: str) -> None:
    for marker in markers:
        if marker not in content:
            errors.append(f"{label} missing marker: {marker}")


def validate(skill_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not skill_dir.exists() or not skill_dir.is_dir():
        return [f"skill directory not found: {skill_dir}"], warnings

    for rel in REQUIRED_FILES:
        if not (skill_dir / rel).is_file():
            errors.append(f"missing required file: {rel}")
    if errors:
        return errors, warnings

    check_markers(read(skill_dir / "SKILL.md"), SKILL_MARKERS, errors, "SKILL.md")
    check_markers(read(skill_dir / "references/checkpoint-protocol.md"), CHECKPOINT_MARKERS, errors, "checkpoint-protocol.md")
    check_markers(read(skill_dir / "references/delivery-report-schema.md"), REPORT_MARKERS, errors, "delivery-report-schema.md")
    check_markers(read(skill_dir / "references/runtime-env-contract.md"), RUNTIME_MARKERS, errors, "runtime-env-contract.md")
    check_markers(read(skill_dir / "references/orchestration-contract.md"), ORCHESTRATION_MARKERS, errors, "orchestration-contract.md")
    return errors, warnings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: check_delivery_loop_contract.py <biz-delivery-loop-skill-dir>\n")
        return 2

    skill_dir = Path(argv[1]).expanduser().resolve()
    errors, warnings = validate(skill_dir)
    result = {
        "skill_dir": str(skill_dir),
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

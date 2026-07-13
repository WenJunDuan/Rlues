#!/usr/bin/env python3
"""Validate a quantum-codegen (mode=page) frontend Convention Pack."""
from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FILES = [
    "conventions.md",
    "runtime-env.md",
    "validate.md",
    "templates/access.ts.tmpl",
    "templates/api.ts.tmpl",
    "templates/index.tsx.tmpl",
    "templates/mock.ts.tmpl",
    "templates/model.ts.tmpl",
    "templates/route-registration.md",
    "templates/search-schema.ts.tmpl",
]

REQUIRED_VALIDATE_MARKERS = ["bunx tsc", "bun run lint", "bun run build", "G1", "G2", "G3", "G4", "G5", "G6"]

REQUIRED_RUNTIME_MARKERS = ["dev_command", "port", "health_url", "teardown"]

PLACEHOLDER_REQUIREMENTS = {
    "templates/access.ts.tmpl": ["{{Entity}}", "{{entity}}", "{{module}}"],
    "templates/api.ts.tmpl": ["{{Entity}}", "{{entity}}", "{{module}}"],
    "templates/index.tsx.tmpl": ["{{Entity}}", "{{entity}}", "{{module}}", "{{entityLabel}}"],
    "templates/mock.ts.tmpl": ["{{Entity}}", "{{entity}}"],
    "templates/model.ts.tmpl": ["{{Entity}}", "{{entity}}"],
    "templates/route-registration.md": ["{{Entity}}", "{{entity}}", "{{module}}"],
    "templates/search-schema.ts.tmpl": ["{{Entity}}", "{{entity}}"],
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate(pack_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not pack_dir.exists() or not pack_dir.is_dir():
        return [f"pack directory not found: {pack_dir}"], warnings

    for rel in REQUIRED_FILES:
        if not (pack_dir / rel).is_file():
            errors.append(f"missing required file: {rel}")

    if errors:
        return errors, warnings

    conventions = read(pack_dir / "conventions.md")
    for marker in ["Convention Pack", "权限", "Mock", "路由", "apiClient"]:
        if marker not in conventions:
            warnings.append(f"conventions.md missing marker: {marker}")

    validate_md = read(pack_dir / "validate.md")
    for marker in REQUIRED_VALIDATE_MARKERS:
        if marker not in validate_md:
            errors.append(f"validate.md missing marker: {marker}")

    runtime_env = read(pack_dir / "runtime-env.md")
    for marker in REQUIRED_RUNTIME_MARKERS:
        if marker not in runtime_env:
            errors.append(f"runtime-env.md missing marker: {marker}")

    for rel, placeholders in PLACEHOLDER_REQUIREMENTS.items():
        content = read(pack_dir / rel)
        for placeholder in placeholders:
            if placeholder not in content:
                errors.append(f"{rel} missing placeholder {placeholder}")

    return errors, warnings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: check_frontend_pack.py <convention-pack-dir>\n")
        return 2

    pack_dir = Path(argv[1]).expanduser().resolve()
    errors, warnings = validate(pack_dir)
    result = {
        "pack_dir": str(pack_dir),
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

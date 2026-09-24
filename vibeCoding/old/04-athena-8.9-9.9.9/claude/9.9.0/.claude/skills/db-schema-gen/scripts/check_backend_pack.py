#!/usr/bin/env python3
"""Validate backend Convention Pack resources for db-schema-gen and unit-test-gen."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BASE_FILES = ["conventions.md", "validate.md"]
DB_FILES = ["db-conventions.md", "templates/ddl.sql.tmpl", "templates/schema-design.md.tmpl"]
TEST_FILES = ["test-conventions.md", "templates/test-report.md.tmpl"]

DB_VALIDATE_MARKERS = ["G5", "G5a", "G5b", "G5c", "G5d", "G5e", "docs/db/<module>-schema-design.md", "deploy/sql/<module>-ddl.sql"]
TEST_VALIDATE_MARKERS = ["G6", "G6a", "G6b", "G6c", "G6d", "G6e", "writeEndpointsShouldRequirePermissionCode"]

DB_CONVENTION_MARKERS = ["PostgreSQL", "int8", "version", "deleted", "dept_id", "docs/db/{module}-schema-design.md", "deploy/sql/{module}-ddl.sql"]
TEST_CONVENTION_MARKERS = [
    "JUnit5",
    "Mockito",
    "AssertJ",
    "MockMvcBuilders.standaloneSetup",
    "selectByIdShouldRejectOutOfScopeEntity",
    "updateShouldRejectOutOfScopeEntity",
    "@RequiresPermission",
    "mvn -pl <module> test",
    "listEndpointShouldValidatePageQueryArgument",
    "updateShouldThrowConflictWhenVersionMismatch",
]

PLACEHOLDER_REQUIREMENTS = {
    "templates/ddl.sql.tmpl": ["{{module}}", "{{Entity}}", "{{table}}"],
    "templates/schema-design.md.tmpl": ["{{module}}", "{{Entity}}", "{{entity}}", "{{table}}"],
    "templates/test-report.md.tmpl": ["{{module}}", "{{Entity}}", "{{date}}", "{{rounds}}", "{{tests_total}}"],
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def required_files(profile: str) -> list[str]:
    files = list(BASE_FILES)
    if profile in ("db", "all"):
        files.extend(DB_FILES)
    if profile in ("test", "all"):
        files.extend(TEST_FILES)
    return files


def validate_markers(pack_dir: Path, profile: str, errors: list[str]) -> None:
    validate_md = read(pack_dir / "validate.md")
    if profile in ("db", "all"):
        for marker in DB_VALIDATE_MARKERS:
            if marker not in validate_md:
                errors.append(f"validate.md missing DB marker: {marker}")
        db_md = read(pack_dir / "db-conventions.md")
        for marker in DB_CONVENTION_MARKERS:
            if marker not in db_md:
                errors.append(f"db-conventions.md missing marker: {marker}")
    if profile in ("test", "all"):
        for marker in TEST_VALIDATE_MARKERS:
            if marker not in validate_md:
                errors.append(f"validate.md missing test marker: {marker}")
        test_md = read(pack_dir / "test-conventions.md")
        for marker in TEST_CONVENTION_MARKERS:
            if marker not in test_md:
                errors.append(f"test-conventions.md missing marker: {marker}")


def validate_placeholders(pack_dir: Path, profile: str, errors: list[str]) -> None:
    for rel, placeholders in PLACEHOLDER_REQUIREMENTS.items():
        if profile == "db" and rel == "templates/test-report.md.tmpl":
            continue
        if profile == "test" and rel != "templates/test-report.md.tmpl":
            continue
        content = read(pack_dir / rel)
        for placeholder in placeholders:
            if placeholder not in content:
                errors.append(f"{rel} missing placeholder {placeholder}")


def validate(pack_dir: Path, profile: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not pack_dir.exists() or not pack_dir.is_dir():
        return [f"pack directory not found: {pack_dir}"], warnings

    for rel in required_files(profile):
        if not (pack_dir / rel).is_file():
            errors.append(f"missing required file: {rel}")

    if errors:
        return errors, warnings

    conventions = read(pack_dir / "conventions.md")
    for marker in ["DataScope", "RequiresPermission", "BaseEntity"]:
        if marker not in conventions:
            warnings.append(f"conventions.md missing marker: {marker}")

    validate_markers(pack_dir, profile, errors)
    validate_placeholders(pack_dir, profile, errors)
    return errors, warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_dir")
    parser.add_argument("--profile", choices=["db", "test", "all"], default="all")
    args = parser.parse_args(argv[1:])

    pack_dir = Path(args.pack_dir).expanduser().resolve()
    errors, warnings = validate(pack_dir, args.profile)
    result = {
        "pack_dir": str(pack_dir),
        "profile": args.profile,
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

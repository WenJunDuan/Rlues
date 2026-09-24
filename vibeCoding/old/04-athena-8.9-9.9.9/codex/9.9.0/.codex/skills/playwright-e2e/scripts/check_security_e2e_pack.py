#!/usr/bin/env python3
"""Validate Convention Pack inputs for security-test and playwright-e2e."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


FRONTEND_FILES = ["conventions.md", "validate.md", "runtime-env.md"]
BACKEND_FILES = [
    "conventions.md",
    "validate.md",
    "templates/Controller.java.tmpl",
    "templates/ServiceImpl.java.tmpl",
    "templates/menu-permission.sql.tmpl",
]

RUNTIME_MARKERS = ["dev_command", "port", "health_url", "teardown"]
FRONTEND_VALIDATE_SECURITY_MARKERS = ["G1", "G2", "G3", "G4", "G5", "G6", "access-guard-exempt", "VITE_FEATURE_MOCK"]
FRONTEND_CONVENTION_SECURITY_MARKERS = ["hasPermission", "ensureRouteAccess", "VITE_FEATURE_MOCK"]
BACKEND_VALIDATE_SECURITY_MARKERS = ["G1", "G2", "G3", "G4", "data-scope-exempt", "menu-permission.sql"]
BACKEND_CONTROLLER_SECURITY_MARKERS = ["@RequiresPermission", "@SystemLog"]
BACKEND_SERVICE_SECURITY_MARKERS = ["@DataScope", "assertReadable", "assertWritable", "assertInDataScope"]
E2E_MARKERS = [
    "page-registry.tsx",
    "backendComponent",
    "fullPath",
    "apiClient",
    "hasPermission",
    "bun run build",
    "bun run lint",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_files(pack_dir: Path, files: list[str], errors: list[str], label: str) -> None:
    if not pack_dir.exists() or not pack_dir.is_dir():
        errors.append(f"{label} pack directory not found: {pack_dir}")
        return
    for rel in files:
        if not (pack_dir / rel).is_file():
            errors.append(f"{label} pack missing required file: {rel}")


def check_markers(source: str, markers: list[str], errors: list[str], label: str) -> None:
    for marker in markers:
        if marker not in source:
            errors.append(f"{label} missing marker: {marker}")


def validate_runtime(frontend_pack: Path, errors: list[str]) -> None:
    runtime_env = read(frontend_pack / "runtime-env.md")
    check_markers(runtime_env, RUNTIME_MARKERS, errors, "frontend runtime-env.md")


def validate_security(frontend_pack: Path, backend_pack: Path, errors: list[str]) -> None:
    check_markers(read(frontend_pack / "validate.md"), FRONTEND_VALIDATE_SECURITY_MARKERS, errors, "frontend validate.md")
    check_markers(read(frontend_pack / "conventions.md"), FRONTEND_CONVENTION_SECURITY_MARKERS, errors, "frontend conventions.md")
    check_markers(read(backend_pack / "validate.md"), BACKEND_VALIDATE_SECURITY_MARKERS, errors, "backend validate.md")
    check_markers(read(backend_pack / "templates/Controller.java.tmpl"), BACKEND_CONTROLLER_SECURITY_MARKERS, errors, "backend Controller.java.tmpl")
    check_markers(read(backend_pack / "templates/ServiceImpl.java.tmpl"), BACKEND_SERVICE_SECURITY_MARKERS, errors, "backend ServiceImpl.java.tmpl")


def validate_e2e(frontend_pack: Path, backend_pack: Path, errors: list[str], warnings: list[str]) -> None:
    frontend_source = "\n".join([read(frontend_pack / "conventions.md"), read(frontend_pack / "validate.md")])
    backend_source = "\n".join([read(backend_pack / "conventions.md"), read(backend_pack / "validate.md")])
    check_markers(frontend_source, E2E_MARKERS, errors, "frontend e2e contract")
    check_markers(backend_source, ["menu-permission.sql", "@RequiresPermission"], errors, "backend e2e contract")
    if not (backend_pack / "runtime-env.md").exists():
        warnings.append("backend runtime-env.md not present; dynamic full-stack E2E/security must be reported blocked")


def validate(frontend_pack: Path, backend_pack: Path, profile: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    require_files(frontend_pack, FRONTEND_FILES, errors, "frontend")
    require_files(backend_pack, BACKEND_FILES, errors, "backend")
    if errors:
        return errors, warnings

    validate_runtime(frontend_pack, errors)
    if profile in ("security", "all"):
        validate_security(frontend_pack, backend_pack, errors)
    if profile in ("e2e", "all"):
        validate_e2e(frontend_pack, backend_pack, errors, warnings)
    return errors, warnings


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend-pack", required=True)
    parser.add_argument("--backend-pack", required=True)
    parser.add_argument("--profile", choices=["security", "e2e", "all"], default="all")
    args = parser.parse_args(argv[1:])

    frontend_pack = Path(args.frontend_pack).expanduser().resolve()
    backend_pack = Path(args.backend_pack).expanduser().resolve()
    errors, warnings = validate(frontend_pack, backend_pack, args.profile)
    result = {
        "frontend_pack": str(frontend_pack),
        "backend_pack": str(backend_pack),
        "profile": args.profile,
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

#!/usr/bin/env python3
"""Validate a project-data-reader Capability Manifest JSON file."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


AUTH_TYPES = {"oauth2-pkce", "device-flow", "preauthorized"}
TRANSPORTS = {"streamable-http", "sse", "stdio"}
FORBIDDEN_SECRET_KEYS = {"token", "access_token", "refresh_token", "password", "cookie", "secret", "api_key"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


def contains_forbidden_secret(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).lower() in FORBIDDEN_SECRET_KEYS or contains_forbidden_secret(item) for key, item in value.items())
    if isinstance(value, list):
        return any(contains_forbidden_secret(item) for item in value)
    return False


def validate(manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if manifest.get("schema") != "project-capability-manifest":
        errors.append("schema must be project-capability-manifest")
    if not isinstance(manifest.get("version"), int):
        errors.append("version must be an integer")
    if not manifest.get("service"):
        errors.append("service is required")
    if manifest.get("transport") not in TRANSPORTS:
        errors.append(f"transport must be one of {sorted(TRANSPORTS)}")
    if not manifest.get("endpoint"):
        errors.append("endpoint is required")

    auth = manifest.get("auth")
    if not isinstance(auth, dict) or auth.get("type") not in AUTH_TYPES:
        errors.append(f"auth.type must be one of {sorted(AUTH_TYPES)}")
    identity = manifest.get("identity")
    if not isinstance(identity, dict) or identity.get("passthrough") is not True:
        errors.append("identity.passthrough must be true")
    if contains_forbidden_secret(manifest):
        errors.append("manifest must not contain static secrets or tokens")

    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("capabilities must be a non-empty list")
        return errors, warnings

    seen: set[str] = set()
    for index, capability in enumerate(capabilities):
        label = f"capabilities[{index}]"
        if not isinstance(capability, dict):
            errors.append(f"{label} must be an object")
            continue
        name = capability.get("name")
        if not name:
            errors.append(f"{label}.name is required")
        elif name in seen:
            errors.append(f"duplicate capability name: {name}")
        else:
            seen.add(str(name))
        if capability.get("mode") != "read":
            errors.append(f"{label}.mode must be read")
        for key in ["tool", "permission", "data_scope", "input_schema", "output_schema"]:
            if key not in capability:
                errors.append(f"{label}.{key} is required")
        if capability.get("audit") is not True:
            errors.append(f"{label}.audit must be true")
        if "redaction" not in capability:
            errors.append(f"{label}.redaction is required")
        elif not isinstance(capability.get("redaction"), list):
            errors.append(f"{label}.redaction must be a list")

    return errors, warnings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: check_capability_manifest.py <manifest.json>\n")
        return 2

    path = Path(argv[1]).expanduser().resolve()
    try:
        manifest = load_json(path)
        errors, warnings = validate(manifest)
    except Exception as exc:  # noqa: BLE001 - emit deterministic JSON for malformed input.
        errors, warnings = [str(exc)], []

    result = {
        "manifest": str(path),
        "status": "ok" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

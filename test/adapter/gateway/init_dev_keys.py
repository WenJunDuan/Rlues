"""Generate development API keys for adapter gateway access policy."""

from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path
from typing import Any, Dict, List


def _load_policy(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _clean_keys(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    result: List[str] = []
    for item in values:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if value:
            result.append(value)
    return result


def _generate_key(prefix: str) -> str:
    token = secrets.token_urlsafe(24)
    return f"{prefix}-{token}"


def _resolve_key(explicit_value: str | None, prefix: str) -> str:
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip()
    return _generate_key(prefix)


def _parse_args() -> argparse.Namespace:
    default_path = Path(__file__).with_name("http_access.json")
    parser = argparse.ArgumentParser(description="Generate development API keys for adapter gateway.")
    parser.add_argument("--config", default=str(default_path), help="Path to http_access.json")
    parser.add_argument("--public-key", default=None, help="Optional explicit public key")
    parser.add_argument("--internal-key", default=None, help="Optional explicit internal key")
    parser.add_argument("--rotate", action="store_true", help="Rotate keys even if policy already has keys")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config_path = Path(args.config).expanduser().resolve()

    policy = _load_policy(config_path)
    auth = policy.get("auth") if isinstance(policy.get("auth"), dict) else {}

    current_public = _clean_keys(auth.get("public_api_keys"))
    current_internal = _clean_keys(auth.get("internal_api_keys"))

    if args.rotate or not current_public:
        public_keys = [_resolve_key(args.public_key, "pub")]
    else:
        public_keys = current_public

    if args.rotate or not current_internal:
        internal_keys = [_resolve_key(args.internal_key, "int")]
    else:
        internal_keys = current_internal

    auth["header"] = auth.get("header") if isinstance(auth.get("header"), str) and auth.get("header", "").strip() else "X-Adapter-Key"
    auth["public_api_keys"] = public_keys
    auth["internal_api_keys"] = internal_keys
    policy["auth"] = auth

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "config_path": str(config_path),
                "public_api_key": public_keys[0] if public_keys else "",
                "internal_api_key": internal_keys[0] if internal_keys else "",
                "public_key_count": len(public_keys),
                "internal_key_count": len(internal_keys),
                "rotated": bool(args.rotate),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

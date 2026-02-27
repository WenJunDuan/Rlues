"""Generate development API keys into .env environment variables."""

from __future__ import annotations

import argparse
import json
import os
import secrets
from pathlib import Path
from typing import List, Optional


def _generate_key(prefix: str) -> str:
    token = secrets.token_urlsafe(24)
    return f"{prefix}-{token}"


def _resolve_key(explicit_value: str | None, prefix: str) -> str:
    if isinstance(explicit_value, str) and explicit_value.strip():
        return explicit_value.strip()
    return _generate_key(prefix)


def _default_env_path() -> Path:
    configured = os.getenv("ADAPTER_ENV_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / ".env"


def _split_csv(value: str | None) -> List[str]:
    if value is None:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _load_env_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def _read_env_value(lines: List[str], key: str) -> Optional[str]:
    prefix = f"{key}="
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _upsert_env_value(lines: List[str], key: str, value: str) -> List[str]:
    prefix = f"{key}="
    next_line = f"{prefix}{value}"
    for idx, line in enumerate(lines):
        if line.startswith(prefix):
            lines[idx] = next_line
            return lines
    lines.append(next_line)
    return lines


def _parse_args() -> argparse.Namespace:
    default_path = _default_env_path()
    parser = argparse.ArgumentParser(description="Generate development API keys into .env.")
    parser.add_argument("--env", default=str(default_path), help="Path to .env")
    parser.add_argument("--public-key", default=None, help="Optional explicit public key")
    parser.add_argument("--internal-key", default=None, help="Optional explicit internal key")
    parser.add_argument("--rotate", action="store_true", help="Rotate keys even if .env already has keys")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    env_path = Path(args.env).expanduser().resolve()
    lines = _load_env_lines(env_path)

    current_public = _split_csv(_read_env_value(lines, "ADAPTER_PUBLIC_API_KEYS"))
    current_internal = _split_csv(_read_env_value(lines, "ADAPTER_INTERNAL_API_KEYS"))

    if args.public_key is not None:
        public_keys = [_resolve_key(args.public_key, "pk-dev")]
    elif args.rotate or not current_public:
        public_keys = [_generate_key("pk-dev")]
    else:
        public_keys = current_public

    if args.internal_key is not None:
        internal_keys = [_resolve_key(args.internal_key, "ik-dev")]
    elif args.rotate or not current_internal:
        internal_keys = [_generate_key("ik-dev")]
    else:
        internal_keys = current_internal

    lines = _upsert_env_value(lines, "ADAPTER_PUBLIC_API_KEYS", ",".join(public_keys))
    lines = _upsert_env_value(lines, "ADAPTER_INTERNAL_API_KEYS", ",".join(internal_keys))

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "env_path": str(env_path),
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

"""Unified adapter configuration loader.

All externally editable runtime configuration is consolidated into a single JSON:
`config.json` (override with `ADAPTER_CONFIG_PATH`).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.json"


@dataclass(frozen=True)
class AdapterConfig:
    data: Dict[str, Any]
    source: str


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_adapter_config() -> AdapterConfig:
    configured_path = os.getenv("ADAPTER_CONFIG_PATH")
    config_path = Path(configured_path).expanduser() if configured_path else DEFAULT_CONFIG_PATH
    raw = _load_json(config_path)
    source = str(config_path) if config_path.exists() else "defaults"
    return AdapterConfig(data=raw, source=source)

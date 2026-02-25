"""SDK access policy loader (config + env overrides)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


PLUGIN_BASH_TOOL = "Bash(python3 .claude/plugins/*/main.py *)"


@dataclass(frozen=True)
class SdkAccessPolicy:
    setting_sources: List[str]
    permission_mode: Optional[str]
    sandbox: bool
    allowed_tools: List[str]
    source: str

    def redacted(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "setting_sources": self.setting_sources,
            "permission_mode": self.permission_mode,
            "sandbox": self.sandbox,
            "allowed_tools": list(self.allowed_tools),
        }


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _str_list(value: Any, default: List[str]) -> List[str]:
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if isinstance(item, str) and item.strip()]
        if cleaned:
            return cleaned
    return list(default)


def _str_value(value: Any) -> Optional[str]:
    if isinstance(value, str):
        text = value.strip()
        return text if text else None
    return None


def _bool_value(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _env_bool(name: str) -> Optional[bool]:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return None


def _env_csv(name: str) -> Optional[List[str]]:
    raw = os.getenv(name)
    if raw is None:
        return None
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items if items else None


def load_sdk_access_policy() -> SdkAccessPolicy:
    default_path = Path(__file__).resolve().parents[1] / "gateway" / "http_access.json"
    config_path = Path(os.getenv("ADAPTER_HTTP_ACCESS_CONFIG", str(default_path)))
    raw = _load_json(config_path)
    sdk = raw.get("sdk", {})
    sdk_map = sdk if isinstance(sdk, dict) else {}

    setting_sources = _str_list(sdk_map.get("setting_sources"), ["project"])
    permission_mode = _str_value(sdk_map.get("permission_mode"))
    sandbox = _bool_value(sdk_map.get("sandbox"), True)
    allowed_tools = _str_list(sdk_map.get("allowed_tools"), ["Read", "Grep", "Glob", "Task"])
    enable_plugin_bash = _bool_value(sdk_map.get("enable_plugin_bash"), False)

    env_setting_sources = _env_csv("ADAPTER_SDK_SETTING_SOURCES")
    if env_setting_sources is not None:
        setting_sources = env_setting_sources
    env_permission_mode = _str_value(os.getenv("ADAPTER_SDK_PERMISSION_MODE"))
    if env_permission_mode is not None:
        permission_mode = env_permission_mode
    env_sandbox = _env_bool("ADAPTER_SDK_SANDBOX")
    if env_sandbox is not None:
        sandbox = env_sandbox
    env_allowed_tools = _env_csv("ADAPTER_SDK_ALLOWED_TOOLS")
    if env_allowed_tools is not None:
        allowed_tools = env_allowed_tools
    env_enable_plugin_bash = _env_bool("ADAPTER_SDK_ENABLE_PLUGIN_BASH")
    if env_enable_plugin_bash is not None:
        enable_plugin_bash = env_enable_plugin_bash

    if enable_plugin_bash and PLUGIN_BASH_TOOL not in allowed_tools:
        allowed_tools = list(allowed_tools) + [PLUGIN_BASH_TOOL]

    if not allowed_tools:
        allowed_tools = ["Read", "Grep", "Glob", "Task"]

    source = str(config_path) if config_path.exists() else "defaults"
    return SdkAccessPolicy(
        setting_sources=setting_sources,
        permission_mode=permission_mode,
        sandbox=sandbox,
        allowed_tools=allowed_tools,
        source=source,
    )


SDK_ACCESS = load_sdk_access_policy()

"""HTTP exposure and access control policy loader."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

from ..core.config_loader import load_adapter_config


PUBLIC_SCOPE = "public"
INTERNAL_SCOPE = "internal"
SUPPORTED_SCOPES = {PUBLIC_SCOPE, INTERNAL_SCOPE}

DEFAULT_FEATURES: Dict[str, Dict[str, Any]] = {
    "audit": {
        "command": "/audit",
        "instruction": "review",
        "enabled": True,
        "expose_http": True,
        "scope": PUBLIC_SCOPE,
    },
}

DEFAULT_ENDPOINTS: Dict[str, Dict[str, Any]] = {
    "health": {"enabled": True, "scope": PUBLIC_SCOPE},
    "feature_submit": {"enabled": True, "scope": PUBLIC_SCOPE},
    "task_query": {"enabled": True, "scope": PUBLIC_SCOPE},
    "task_events": {"enabled": True, "scope": PUBLIC_SCOPE},
    "task_compliance": {"enabled": True, "scope": PUBLIC_SCOPE},
    "feature_query": {"enabled": True, "scope": PUBLIC_SCOPE},
    "feature_events": {"enabled": True, "scope": PUBLIC_SCOPE},
    "feature_compliance": {"enabled": True, "scope": PUBLIC_SCOPE},
    "history_list": {"enabled": True, "scope": INTERNAL_SCOPE},
    "history_delete": {"enabled": True, "scope": INTERNAL_SCOPE},
    "logs_list": {"enabled": True, "scope": INTERNAL_SCOPE},
    "logs_archive": {"enabled": True, "scope": INTERNAL_SCOPE},
    "runtime_queue": {"enabled": True, "scope": INTERNAL_SCOPE},
    "runtime_exposure": {"enabled": True, "scope": INTERNAL_SCOPE},
    "legacy_task_submit": {"enabled": False, "scope": INTERNAL_SCOPE},
    "legacy_task_query": {"enabled": False, "scope": INTERNAL_SCOPE},
    "legacy_task_events": {"enabled": False, "scope": INTERNAL_SCOPE},
    "legacy_task_compliance": {"enabled": False, "scope": INTERNAL_SCOPE},
}


@dataclass(frozen=True)
class FeatureAccess:
    command: str
    instruction: str
    enabled: bool
    expose_http: bool
    scope: str


@dataclass(frozen=True)
class EndpointAccess:
    enabled: bool
    scope: str


@dataclass(frozen=True)
class HttpAccessPolicy:
    features: Dict[str, FeatureAccess]
    endpoints: Dict[str, EndpointAccess]
    auth_header: str
    public_api_keys: frozenset[str]
    internal_api_keys: frozenset[str]
    source: str

    def command_by_feature(self) -> Dict[str, str]:
        return {
            feature: policy.command
            for feature, policy in self.features.items()
            if policy.enabled
        }

    def feature_policy(self, feature: str) -> Optional[FeatureAccess]:
        return self.features.get(feature)

    def endpoint_policy(self, endpoint: str) -> EndpointAccess:
        default = EndpointAccess(enabled=False, scope=INTERNAL_SCOPE)
        return self.endpoints.get(endpoint, default)

    def authorize(self, scope: str, api_key: Optional[str]) -> Tuple[bool, str]:
        token = (api_key or "").strip()
        checked_scope = scope if scope in SUPPORTED_SCOPES else INTERNAL_SCOPE

        if checked_scope == INTERNAL_SCOPE:
            if not self.internal_api_keys:
                return False, "internal api keys not configured"
            if not token:
                return False, "missing api key for internal endpoint"
            if token in self.internal_api_keys:
                return True, ""
            return False, "invalid api key for internal endpoint"

        # Public scope.
        accepted_keys = self.public_api_keys | self.internal_api_keys
        if not accepted_keys:
            return False, "public api keys not configured"
        if token in accepted_keys:
            return True, ""
        if not token:
            return False, "missing api key for public endpoint"
        return False, "invalid api key for public endpoint"

    def redacted(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "auth": {
                "header": self.auth_header,
                "public_key_count": len(self.public_api_keys),
                "internal_key_count": len(self.internal_api_keys),
            },
            "features": {
                feature: {
                    "command": policy.command,
                    "instruction": policy.instruction,
                    "enabled": policy.enabled,
                    "expose_http": policy.expose_http,
                    "scope": policy.scope,
                }
                for feature, policy in self.features.items()
            },
            "endpoints": {
                endpoint: {"enabled": policy.enabled, "scope": policy.scope}
                for endpoint, policy in self.endpoints.items()
            },
        }


def _normalize_scope(value: Any, default: str) -> str:
    text = str(value).strip().lower() if value is not None else default
    return text if text in SUPPORTED_SCOPES else default


def _bool_value(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _str_value(value: Any, default: str) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
    return default


def _str_set(values: Any) -> frozenset[str]:
    if not isinstance(values, list):
        return frozenset()
    cleaned = [str(item).strip() for item in values if isinstance(item, str) and item.strip()]
    return frozenset(cleaned)


def _parse_csv_keys(value: Optional[str]) -> frozenset[str]:
    if value is None:
        return frozenset()
    parts = [chunk.strip() for chunk in value.split(",")]
    return frozenset([part for part in parts if part])


def _merge_overrides(base: Dict[str, Dict[str, Any]], override: Any) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {k: dict(v) for k, v in base.items()}
    if not isinstance(override, Mapping):
        return merged
    for key, item in override.items():
        if not isinstance(key, str) or not isinstance(item, Mapping):
            continue
        existing = merged.get(key, {})
        next_value = dict(existing)
        next_value.update(item)
        merged[key] = next_value
    return merged


def _feature_access(values: Mapping[str, Any]) -> FeatureAccess:
    command = _str_value(values.get("command"), "/audit")
    if not command.startswith("/"):
        command = f"/{command}"
    instruction = _str_value(values.get("instruction"), "review").strip("/")
    if not instruction:
        instruction = "review"
    return FeatureAccess(
        command=command,
        instruction=instruction,
        enabled=_bool_value(values.get("enabled"), True),
        expose_http=_bool_value(values.get("expose_http"), True),
        scope=_normalize_scope(values.get("scope"), PUBLIC_SCOPE),
    )


def _endpoint_access(values: Mapping[str, Any]) -> EndpointAccess:
    return EndpointAccess(
        enabled=_bool_value(values.get("enabled"), True),
        scope=_normalize_scope(values.get("scope"), INTERNAL_SCOPE),
    )


def load_http_access_policy() -> HttpAccessPolicy:
    config = load_adapter_config()
    root = config.data
    gateway_raw = root.get("gateway")
    if isinstance(gateway_raw, dict):
        raw = gateway_raw
    elif any(key in root for key in ("auth", "features", "endpoints")):
        # Backward compatible with legacy gateway-only JSON.
        raw = root
    else:
        raw = {}

    feature_blob = _merge_overrides(DEFAULT_FEATURES, raw.get("features"))
    endpoint_blob = _merge_overrides(DEFAULT_ENDPOINTS, raw.get("endpoints"))

    features: Dict[str, FeatureAccess] = {}
    for feature, values in feature_blob.items():
        if not isinstance(feature, str):
            continue
        features[feature] = _feature_access(values)

    endpoints: Dict[str, EndpointAccess] = {}
    for endpoint, values in endpoint_blob.items():
        if not isinstance(endpoint, str):
            continue
        endpoints[endpoint] = _endpoint_access(values)

    auth = raw.get("auth", {})
    auth_map = auth if isinstance(auth, dict) else {}
    auth_header = _str_value(auth_map.get("header"), "X-Adapter-Key")

    public_api_keys = _str_set(auth_map.get("public_api_keys"))
    internal_api_keys = _str_set(auth_map.get("internal_api_keys"))

    env_public_keys = _parse_csv_keys(os.getenv("ADAPTER_PUBLIC_API_KEYS"))
    if env_public_keys:
        public_api_keys = env_public_keys
    env_internal_keys = _parse_csv_keys(os.getenv("ADAPTER_INTERNAL_API_KEYS"))
    if env_internal_keys:
        internal_api_keys = env_internal_keys

    source = config.source
    return HttpAccessPolicy(
        features=features,
        endpoints=endpoints,
        auth_header=auth_header,
        public_api_keys=public_api_keys,
        internal_api_keys=internal_api_keys,
        source=source,
    )


HTTP_ACCESS = load_http_access_policy()

"""Local LLM client MVP with unified response envelope."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List


PLUGIN = "llm_client"
ALLOWED_ROLES = {"system", "user", "assistant"}


def _resp(ok: bool, code: str, message: str, data: Dict[str, Any]) -> dict:
    return {"ok": ok, "code": code, "message": message, "data": data, "meta": {"plugin": PLUGIN}}


def _normalize_model(model: str | None) -> str:
    if isinstance(model, str) and model.strip():
        return model.strip()
    return "local-mvp"


def complete(messages: list, model: str | None = None) -> dict:
    data: Dict[str, Any] = {"messages": messages, "model": model}

    if not isinstance(messages, list) or not messages:
        return _resp(False, "LLM_INVALID_MESSAGES", "messages must be non-empty array", data)

    normalized: List[dict] = []
    for idx, item in enumerate(messages):
        if not isinstance(item, dict):
            return _resp(False, "LLM_INVALID_MESSAGES", f"messages[{idx}] must be object", data)
        role = item.get("role")
        content = item.get("content")
        if role not in ALLOWED_ROLES:
            return _resp(False, "LLM_INVALID_ROLE", f"messages[{idx}].role invalid", data)
        if not isinstance(content, str):
            return _resp(False, "LLM_INVALID_CONTENT", f"messages[{idx}].content must be string", data)
        normalized.append({"role": role, "content": content.strip()})

    last_user = ""
    for item in reversed(normalized):
        if item["role"] == "user":
            last_user = item["content"]
            break

    if not last_user:
        last_user = normalized[-1]["content"]

    answer = f"[MVP] {last_user[:400]}"
    payload = {
        "model": _normalize_model(model),
        "answer": answer,
        "usage": {
            "input_messages": len(normalized),
            "input_chars": sum(len(x["content"]) for x in normalized),
            "output_chars": len(answer),
        },
    }
    return _resp(True, "OK", "completion generated", payload)


def extract_structured(text: str, schema: dict) -> dict:
    data: Dict[str, Any] = {"text": text, "schema": schema}

    if not isinstance(text, str):
        return _resp(False, "LLM_INVALID_TEXT", "text must be string", data)
    if not isinstance(schema, dict):
        return _resp(False, "LLM_INVALID_SCHEMA", "schema must be object", data)

    stripped = text.strip()
    parsed: Dict[str, Any] | None = None
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict):
                parsed = obj
        except json.JSONDecodeError:
            parsed = None

    if parsed is None:
        parsed = {}
        pairs = re.findall(r"([A-Za-z0-9_]+)\s*[:=]\s*([^\n,;]+)", stripped)
        for k, v in pairs:
            parsed[k] = v.strip().strip("\"'")

    required = schema.get("required", [])
    if isinstance(required, list):
        for field in required:
            if field not in parsed:
                parsed[field] = None

    return _resp(True, "OK", "structured extraction finished", {"structured": parsed, "missing_filled": True})


def summarize(text: str, max_tokens: int = 256) -> dict:
    data: Dict[str, Any] = {"text": text, "max_tokens": max_tokens}

    if not isinstance(text, str):
        return _resp(False, "LLM_INVALID_TEXT", "text must be string", data)
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        return _resp(False, "LLM_INVALID_MAX_TOKENS", "max_tokens must be positive integer", data)

    # Approximate token limit with 4 chars/token in MVP mode.
    max_chars = max_tokens * 4
    compact = re.sub(r"\s+", " ", text).strip()
    summary = compact[:max_chars]
    if len(compact) > max_chars:
        summary = summary.rstrip() + "..."

    return _resp(
        True,
        "OK",
        "summary generated",
        {"summary": summary, "input_chars": len(compact), "output_chars": len(summary), "max_tokens": max_tokens},
    )


if __name__ == "__main__":
    import sys

    try:
        action = "complete"
        raw_args = "{}"
        if len(sys.argv) > 1:
            first = sys.argv[1].strip()
            if first.startswith("{"):
                raw_args = first
            else:
                action = first
                raw_args = sys.argv[2] if len(sys.argv) > 2 else "{}"

        args = json.loads(raw_args) if raw_args else {}
        if not isinstance(args, dict):
            args = {}

        if action == "complete":
            result = complete(messages=args.get("messages", []), model=args.get("model"))
        elif action == "extract_structured":
            result = extract_structured(text=args.get("text", ""), schema=args.get("schema", {}))
        elif action == "summarize":
            max_tokens = args.get("max_tokens", 256)
            if not isinstance(max_tokens, int):
                max_tokens = 256
            result = summarize(text=args.get("text", ""), max_tokens=max_tokens)
        else:
            result = _resp(False, "LLM_INVALID_ACTION", "supported actions: complete|extract_structured|summarize", {"action": action})

        print(json.dumps(result, ensure_ascii=False))
    except Exception as exc:  # pragma: no cover
        print(
            json.dumps(
                _resp(False, "LLM_RUNTIME_ERROR", "llm_client runtime error", {"error": str(exc)}),
                ensure_ascii=False,
            )
        )
        raise SystemExit(1)

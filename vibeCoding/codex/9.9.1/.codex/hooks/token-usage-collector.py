#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.1 · Codex Stop hook (token-usage-collector)

职责:
  1. 从 Stop/SubagentStop hook payload 或 transcript_path/agent_transcript_path 指向的 JSONL 中递归提取 usage/token_count
  2. 按 sprint 写入 sprints/{slug}/token-usage.yaml
  3. 无 usage 字段时写明 no_usage_found, 不猜 token

平台边界:
  - Codex hooks: https://developers.openai.com/codex/hooks
  - Codex session JSONL 里可见 event_msg/token_count, 但 Stop payload 不保证给 transcript_path;
    因此本 hook 是 best-effort, 不可证实时记录 unknown/no_usage_found.

非阻塞: 任何异常 exit 0.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

EXIT_SUCCESS = 0
TOKEN_FIELDS = {
    "input_tokens",
    "cached_input_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
}


def find_ai_state(cwd: Path) -> Path | None:
    current = cwd
    for _ in range(5):
        candidate = current / ".ai_state"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            return None
        current = current.parent
    return None


def read_field(idx_path: Path, field: str) -> str:
    try:
        content = idx_path.read_text(encoding="utf-8")
        match = re.search(rf'^{field}:\s*["\']?([^"\n]*)["\']?', content, re.MULTILINE)
        return match.group(1).strip() if match else ""
    except Exception:
        return ""


def as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def normalize_usage(raw: dict[str, Any]) -> dict[str, int]:
    usage = {field: as_int(raw.get(field, 0)) for field in TOKEN_FIELDS}
    if not usage["cached_input_tokens"]:
        usage["cached_input_tokens"] = (
            usage["cache_creation_input_tokens"] + usage["cache_read_input_tokens"]
        )
    if not usage["total_tokens"]:
        usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]
    return usage


def has_usage_shape(raw: Any) -> bool:
    return isinstance(raw, dict) and any(k in raw for k in TOKEN_FIELDS)


def fingerprint(record: dict[str, Any]) -> str:
    stable = {k: v for k, v in record.items() if k not in {"stage", "fingerprint"}}
    if "_fingerprint_timestamp" in stable:
        stable["timestamp"] = stable.pop("_fingerprint_timestamp")
    body = json.dumps(stable, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def make_record(
    *,
    platform: str,
    stage: str,
    source_type: str,
    source_id: str,
    timestamp: str,
    model: str,
    usage: dict[str, int],
) -> dict[str, Any]:
    display_timestamp = timestamp or dt.datetime.now(dt.UTC).isoformat()
    record = {
        "platform": platform,
        "stage": stage or "unknown",
        "source_type": source_type,
        "source_id": source_id,
        "timestamp": display_timestamp,
        "_fingerprint_timestamp": timestamp or "",
        "model": model or "unknown",
        **usage,
    }
    record["fingerprint"] = fingerprint(record)
    record.pop("_fingerprint_timestamp", None)
    return record


def usage_from_text_block(text: str) -> list[dict[str, int]]:
    usage_blocks: list[dict[str, int]] = []
    for match in re.finditer(r"<usage>(.*?)</usage>", text, flags=re.DOTALL | re.IGNORECASE):
        raw = match.group(1).strip()
        parsed: dict[str, Any] | None = None
        try:
            value = json.loads(raw)
            if isinstance(value, dict):
                parsed = value.get("usage") if isinstance(value.get("usage"), dict) else value
        except Exception:
            parsed = None
        if parsed and has_usage_shape(parsed):
            usage_blocks.append(normalize_usage(parsed))
            continue

        fields: dict[str, int] = {}
        for field in TOKEN_FIELDS | {"subagent_tokens"}:
            field_match = re.search(rf"\b{field}\b\s*[:=]\s*(\d+)", raw)
            if field_match:
                fields[field] = as_int(field_match.group(1))
        if raw.isdigit():
            fields["total_tokens"] = as_int(raw)
        if "subagent_tokens" in fields and "total_tokens" not in fields:
            fields["total_tokens"] = fields["subagent_tokens"]
        if fields:
            usage_blocks.append(normalize_usage(fields))
    return usage_blocks


def collect_from_obj(
    obj: Any,
    *,
    platform: str,
    stage: str,
    source_type: str,
    source_id: str,
    timestamp: str = "",
    model: str = "",
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(obj, list):
        for item in obj:
            records.extend(
                collect_from_obj(
                    item,
                    platform=platform,
                    stage=stage,
                    source_type=source_type,
                    source_id=source_id,
                    timestamp=timestamp,
                    model=model,
                )
            )
        return records

    if isinstance(obj, str):
        for usage in usage_from_text_block(obj):
            records.append(
                make_record(
                    platform=platform,
                    stage=stage,
                    source_type=source_type,
                    source_id=source_id,
                    timestamp=timestamp,
                    model=model,
                    usage=usage,
                )
            )
        return records

    if not isinstance(obj, dict):
        return records

    current_ts = str(obj.get("timestamp") or obj.get("ts") or timestamp or "")
    current_model = str(obj.get("model") or model or "")

    payload = obj.get("payload")
    if isinstance(payload, dict) and payload.get("type") == "token_count":
        info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
        usage_raw = info.get("last_token_usage")
        if has_usage_shape(usage_raw):
            records.append(
                make_record(
                    platform=platform,
                    stage=stage,
                    source_type=source_type,
                    source_id=source_id,
                    timestamp=current_ts,
                    model=current_model,
                    usage=normalize_usage(usage_raw),
                )
            )

    usage_raw = obj.get("usage")
    if has_usage_shape(usage_raw):
        records.append(
            make_record(
                platform=platform,
                stage=stage,
                source_type=source_type,
                source_id=source_id,
                timestamp=current_ts,
                model=current_model,
                usage=normalize_usage(usage_raw),
            )
        )

    for value in obj.values():
        if isinstance(value, (dict, list, str)):
            records.extend(
                collect_from_obj(
                    value,
                    platform=platform,
                    stage=stage,
                    source_type=source_type,
                    source_id=source_id,
                    timestamp=current_ts,
                    model=current_model,
                )
            )
    return records


def collect_from_transcript(
    path_value: str,
    *,
    platform: str,
    stage: str,
    source_type: str = "transcript_path",
) -> list[dict[str, Any]]:
    path = Path(path_value).expanduser()
    if not path.exists() or not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue
            records.extend(
                collect_from_obj(
                    item,
                    platform=platform,
                    stage=stage,
                    source_type=source_type,
                    source_id=str(path),
                )
            )
    return records


def read_existing_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        start = re.match(r'^\s*- fingerprint:\s*"([^"]+)"', line)
        if start:
            if current:
                records.append(current)
            current = {"fingerprint": start.group(1)}
            continue
        if current is None:
            continue
        field = re.match(r"^\s{4}([\w_]+):\s*(.*)$", line)
        if not field:
            continue
        key, raw = field.group(1), field.group(2).strip()
        if key in TOKEN_FIELDS:
            current[key] = as_int(raw)
        else:
            try:
                current[key] = json.loads(raw)
            except Exception:
                current[key] = raw.strip('"')
    if current:
        records.append(current)
    return records


def quote(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def yaml_scalar(value: int | None) -> str:
    return "null" if value is None else str(value)


def acquire_lock(path: Path):
    lock_path = path.with_suffix(path.suffix + ".lock")
    deadline = time.time() + 5
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            return fd, lock_path
        except FileExistsError:
            if time.time() >= deadline:
                raise TimeoutError(f"timeout acquiring {lock_path}")
            time.sleep(0.05)


def atomic_write(path: Path, content: str) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)


def write_usage_yaml(path: Path, *, sprint_slug: str, records: list[dict[str, Any]], note: str = "") -> None:
    totals = {field: 0 for field in TOKEN_FIELDS}
    by_model: dict[str, dict[str, int]] = {}
    by_stage: dict[str, dict[str, dict[str, int]]] = {}
    for record in records:
        stage = str(record.get("stage") or "unknown")
        model = str(record.get("model") or "unknown")
        bucket = by_model.setdefault(model, {"calls": 0, **{field: 0 for field in TOKEN_FIELDS}})
        stage_bucket = by_stage.setdefault(stage, {})
        stage_model_bucket = stage_bucket.setdefault(model, {"calls": 0, **{field: 0 for field in TOKEN_FIELDS}})
        bucket["calls"] += 1
        stage_model_bucket["calls"] += 1
        for field in TOKEN_FIELDS:
            value = as_int(record.get(field, 0))
            totals[field] += value
            bucket[field] += value
            stage_model_bucket[field] += value

    lines = [
        f"sprint_slug: {sprint_slug}",
        f"updated_at: {quote(dt.datetime.now(dt.UTC).isoformat())}",
        f"status: {quote('ok' if records else 'no_usage_found')}",
        "totals:",
    ]
    for field in sorted(TOKEN_FIELDS):
        lines.append(f"  {field}: {yaml_scalar(totals[field] if records else None)}")
    lines.append("by_model:")
    if by_model:
        for model in sorted(by_model):
            lines.append(f"  {quote(model)}:")
            for key, value in by_model[model].items():
                lines.append(f"    {key}: {value}")
    else:
        lines.append("  {}")
    lines.append("by_stage:")
    if by_stage:
        for stage in sorted(by_stage):
            lines.append(f"  {quote(stage)}:")
            for model in sorted(by_stage[stage]):
                lines.append(f"    {quote(model)}:")
                for key, value in by_stage[stage][model].items():
                    lines.append(f"      {key}: {value}")
    else:
        lines.append("  {}")
    lines.append("records:")
    if records:
        for record in records:
            lines.append(f"  - fingerprint: {quote(record['fingerprint'])}")
            for key in [
                "platform",
                "stage",
                "source_type",
                "source_id",
                "timestamp",
                "model",
                *sorted(TOKEN_FIELDS),
            ]:
                value = record.get(key, 0)
                if isinstance(value, int):
                    lines.append(f"    {key}: {value}")
                else:
                    lines.append(f"    {key}: {quote(value)}")
    else:
        lines.append("  []")
    lines.append("notes:")
    if note:
        lines.append(f"  - {quote(note)}")
    else:
        lines.append("  []")
    atomic_write(path, "\n".join(lines) + "\n")


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        cwd = Path(payload.get("cwd") or os.getcwd())
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS

        idx = ai_state / "_index.md"
        sprint_slug = read_field(idx, "current_sprint_slug")
        stage = read_field(idx, "stage")
        if not sprint_slug:
            return EXIT_SUCCESS

        sprint_dir = ai_state / "sprints" / sprint_slug
        sprint_dir.mkdir(parents=True, exist_ok=True)
        out = sprint_dir / "token-usage.yaml"

        records: list[dict[str, Any]] = []
        seen_transcript_paths: set[str] = set()
        transcript_fields = [
            ("transcript_path", "transcript_path"),
            ("session_path", "transcript_path"),
            ("agent_transcript_path", "agent_transcript_path"),
        ]
        for field, source_type in transcript_fields:
            transcript_path = str(payload.get(field) or "")
            if not transcript_path:
                continue
            resolved = str(Path(transcript_path).expanduser())
            if resolved in seen_transcript_paths:
                continue
            seen_transcript_paths.add(resolved)
            records.extend(
                collect_from_transcript(
                    transcript_path,
                    platform="cx",
                    stage=stage,
                    source_type=source_type,
                )
            )

        records.extend(
            collect_from_obj(
                payload,
                platform="cx",
                stage=stage,
                source_type="hook_payload",
                source_id=str(payload.get("hook_event_name") or payload.get("event") or "Stop"),
            )
        )

        lock_fd, lock_path = acquire_lock(out)
        try:
            existing = read_existing_records(out)
            seen = {str(record.get("fingerprint", "")) for record in existing if record.get("fingerprint")}
            deduped: list[dict[str, Any]] = list(existing)
            local_seen = set(seen)
            for record in records:
                fp = str(record.get("fingerprint", ""))
                if fp and fp not in local_seen:
                    local_seen.add(fp)
                    deduped.append(record)

            note = ""
            if not deduped:
                note = "No usage fields found in Codex hook payload/transcript_path; keep token totals unknown."
            write_usage_yaml(out, sprint_slug=sprint_slug, records=deduped, note=note)
        finally:
            os.close(lock_fd)
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass
        return EXIT_SUCCESS
    except Exception as exc:
        sys.stderr.write(f"[token-usage-collector] non-blocking: {exc}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())

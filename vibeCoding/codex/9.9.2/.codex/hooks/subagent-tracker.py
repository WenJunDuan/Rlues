#!/usr/bin/env python3
"""Athena v9.9.2 Codex raw subagent lifecycle recorder.

Codex 0.144.1 SubagentStart/SubagentStop payloads provide the real
``agent_id`` and ``agent_type``; SubagentStop provides no exit status.  This
hook therefore appends the raw lifecycle identity only.  It never consults the
assignment ledger, invents assignment metadata, or advances workflow state.
The main thread records its ledger row after the native-v2 spawn handshake,
and the ship gate joins the two ledgers by ``agent_id + sprint_slug``.

Schema source:
https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/hooks/schema/generated/subagent-stop.command.input.schema.json
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

EVENTS = {"SubagentStart", "SubagentStop"}


def find_ai_state(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for _ in range(8):
        candidate = current / ".ai_state"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def payload_cwd(payload: dict[str, Any]) -> Path:
    value = payload.get("cwd")
    if isinstance(value, str) and value.strip():
        return Path(value).expanduser()
    return Path.cwd()


def read_sprint_slug(index_path: Path) -> str:
    try:
        content = index_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(
        r'^current_sprint_slug:\s*["\']?([^"\n]*)["\']?', content, re.MULTILINE
    )
    return match.group(1).strip() if match else ""


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except (json.JSONDecodeError, OSError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}

        event = payload.get("hook_event_name")
        agent_id = payload.get("agent_id")
        agent_type = payload.get("agent_type")
        if event not in EVENTS:
            return 0
        if not isinstance(agent_id, str) or not agent_id.strip():
            sys.stderr.write("[subagent-tracker] ignored lifecycle event without agent_id\n")
            return 0
        if not isinstance(agent_type, str) or not agent_type.strip():
            sys.stderr.write("[subagent-tracker] ignored lifecycle event without agent_type\n")
            return 0

        ai_state = find_ai_state(payload_cwd(payload))
        if ai_state is None:
            return 0
        sprint_slug = read_sprint_slug(ai_state / "_index.md")
        if not sprint_slug:
            sys.stderr.write("[subagent-tracker] no current_sprint_slug; lifecycle event not persisted\n")
            return 0

        record = {
            "schema_version": 1,
            "event": event,
            "agent_id": agent_id.strip(),
            "agent_type": agent_type.strip(),
            "sprint_slug": sprint_slug,
            "timestamp": dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z"),
        }
        sprint_dir = ai_state / "sprints" / sprint_slug
        sprint_dir.mkdir(parents=True, exist_ok=True)
        with (sprint_dir / "subagent-events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        return 0
    except Exception as exc:
        # Logging remains best-effort; missing lifecycle evidence cannot satisfy
        # the fail-closed ship gate.
        sys.stderr.write(f"[subagent-tracker] non-blocking error: {exc}\n")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

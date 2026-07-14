#!/usr/bin/env python3
"""Athena v9.9.3 fail-closed ship gate for Codex.

For Feature/Refactor/System delivery, the gate parses the main thread's
assignment ledger and the hook's raw native lifecycle ledger independently,
then joins them only by ``agent_id + sprint_slug``.  Assignment rows own
task/role; event rows own agent_type.  A Start never proves completion, an
isolated Stop is invalid, and every generator's latest event must be Stop.
Checklist, passing evidence, and the final review verdict are independent.

The hook blocks by returning ``{"decision":"block","reason":"..."}`` at exit
0, as required by the Codex Stop protocol.  Once an Athena project is at ship,
parse or validation errors are fail-closed.  This is a workflow guardrail, not
a security boundary.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXIT_SUCCESS = 0
REFACTOR_SYSTEM = {"Refactor", "System"}
GENERATOR_PATHS = {"Feature", "Refactor", "System"}
VALID_STAGES = {
    "brainstorm",
    "roadmap",
    "plan",
    "design",
    "impl",
    "runtime-verify",
    "review",
    "polish",
    "ship",
}
VALID_PATHS = {"Hotfix", "Bugfix", "Quick", "Feature", "Refactor", "System"}
ASSIGNMENT_STRING_FIELDS = ("agent_id", "task_name", "role", "sprint_slug", "timestamp")
EVENT_STRING_FIELDS = ("agent_id", "agent_type", "sprint_slug", "timestamp")


class GateError(RuntimeError):
    pass


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


def parse_frontmatter(content: str) -> dict[str, str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise GateError(".ai_state/_index.md lacks opening frontmatter delimiter")
    try:
        closing = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise GateError(".ai_state/_index.md lacks closing frontmatter delimiter") from exc
    result: dict[str, str] = {}
    for raw_line in lines[1:closing]:
        if raw_line[:1].isspace():
            continue  # nested YAML is not needed by this gate
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([\w.-]+)\s*:\s*(.*)$", line)
        if not match:
            raise GateError(f"malformed top-level index frontmatter line: {raw_line!r}")
        key, value = match.group(1), match.group(2).strip()
        if key in result:
            raise GateError(f"duplicate index frontmatter field: {key}")
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        result[key] = value
    return result


def block(reason: str) -> int:
    message = f"[delivery-gate] {reason.strip()}"
    sys.stderr.write(message + "\n")
    print(json.dumps({"decision": "block", "reason": message}, ensure_ascii=False))
    return EXIT_SUCCESS


def require_file(path: Path, label: str) -> str:
    if not path.is_file():
        raise GateError(f"missing {label}: {path}")
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"cannot read {label}: {exc}") from exc
    if not content.strip():
        raise GateError(f"empty {label}: {path}")
    return content


def parse_timestamp(value: str, label: str) -> dt.datetime:
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise GateError(f"{label} has invalid timestamp {value!r}") from exc
    if parsed.tzinfo is None:
        raise GateError(f"{label} timestamp must include a timezone: {value!r}")
    return parsed.astimezone(dt.UTC)


def validate_schema_version(value: Any, label: str) -> None:
    version = value.get("schema_version") if isinstance(value, dict) else None
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise GateError(f"{label}.schema_version must be integer 1")


def validate_string_fields(value: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        field_value = value.get(field)
        if not isinstance(field_value, str) or not field_value.strip():
            raise GateError(f"{label}.{field} must be a non-empty string")


def validate_assignment_record(value: Any, label: str, sprint_slug: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GateError(f"{label} must be a JSON object")
    expected = {"schema_version", *ASSIGNMENT_STRING_FIELDS}
    if set(value) != expected:
        raise GateError(f"{label} must use assignment schema v1 fields {sorted(expected)}")
    validate_schema_version(value, label)
    validate_string_fields(value, ASSIGNMENT_STRING_FIELDS, label)
    if value["sprint_slug"] != sprint_slug:
        raise GateError(
            f"{label}.sprint_slug={value['sprint_slug']!r} does not match {sprint_slug!r}"
        )
    value = dict(value)
    value["_parsed_timestamp"] = parse_timestamp(value["timestamp"], label)
    return value


def validate_event_record(value: Any, label: str, sprint_slug: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GateError(f"{label} must be a JSON object")
    expected = {"schema_version", "event", *EVENT_STRING_FIELDS}
    if set(value) != expected:
        raise GateError(f"{label} must use raw event schema v1 fields {sorted(expected)}")
    validate_schema_version(value, label)
    validate_string_fields(value, EVENT_STRING_FIELDS, label)
    if value["event"] not in {"SubagentStart", "SubagentStop"}:
        raise GateError(f"{label}.event must be SubagentStart or SubagentStop")
    if value["sprint_slug"] != sprint_slug:
        raise GateError(
            f"{label}.sprint_slug={value['sprint_slug']!r} does not match {sprint_slug!r}"
        )
    value = dict(value)
    value["_parsed_timestamp"] = parse_timestamp(value["timestamp"], label)
    return value


def read_jsonl(path: Path, label: str, sprint_slug: str, *, kind: str) -> list[dict[str, Any]]:
    content = require_file(path, label)
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        if not raw_line.strip():
            continue
        row_label = f"{label} line {line_number}"
        try:
            value = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise GateError(f"malformed {row_label}: {exc.msg}") from exc
        if kind == "assignment":
            record = validate_assignment_record(value, row_label, sprint_slug)
        elif kind == "event":
            record = validate_event_record(value, row_label, sprint_slug)
        else:
            raise GateError(f"internal error: unknown JSONL kind {kind!r}")
        records.append(record)
    if not records:
        raise GateError(f"{label} contains no records")
    return records


def join_key(record: dict[str, Any]) -> tuple[str, str]:
    return record["agent_id"], record["sprint_slug"]


# P0-3 对齐 CC: 标题匹配用显式边界 lookahead (兼容中文标题与编号前缀), 不依赖 \\b.
ACCEPTANCE_HEAD = re.compile(
    r"^#{2,3}\s*\**\s*(?:\d+[.)]\s*)?(?:acceptance criteria|验收标准)(?=$|[\s*:：()（）\[\]【】·—-])",
    re.I,
)
PLACEHOLDER_PREFIXES = ("todo", "tbd", "fixme", "wip", "placeholder", "待定", "待补", "占位", "暂定")
PLACEHOLDER_PHRASES = ("works correctly", "works as expected", "功能正常", "正常工作", "n/a")
AC_LABEL = re.compile(r"(?:^|[^A-Za-z0-9])(AC\d+)(?![0-9])")


def is_placeholder_criterion(text: str) -> bool:
    """design §4.3: placeholder rejection is semantic (prefix/substring)."""
    t = re.sub(r"[.。!！;；,，]+$", "", text.strip().lower()).strip()
    if not t:
        return True
    if any(t.startswith(prefix) for prefix in PLACEHOLDER_PREFIXES):
        return True
    return any(t == phrase or phrase in t for phrase in PLACEHOLDER_PHRASES)


def acceptance_criteria(text: str) -> list[str]:
    item = re.compile(r"^\s*(?:[-*]|\d+[.)]|\[[ xX]\])\s+\S")
    nexthead = re.compile(r"^#{1,6}\s")
    found: list[str] = []
    in_sec = False
    for raw in text.splitlines():
        if ACCEPTANCE_HEAD.match(raw.strip()):
            in_sec = True
            continue
        if not in_sec:
            continue
        if nexthead.match(raw):
            in_sec = False
            continue
        if item.match(raw):
            t = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", raw)
            t = re.sub(r"^\[[ xX]\]\s+", "", t).strip()
            if t and not is_placeholder_criterion(t):
                found.append(t)
    return found


def parse_utc_timestamp(value: str, label: str) -> dt.datetime:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = dt.datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise GateError(f"{label} 必须是 UTC ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise GateError(f"{label} 必须带 UTC 时区")
    return parsed.astimezone(dt.UTC)


def parse_authorization_record(path: Path) -> dict[str, str]:
    content = require_file(path, "spec-gate user authorization")
    result: dict[str, str] = {}
    for raw_line in content.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line[:1].isspace():
            raise GateError("spec-gate user authorization must be a flat YAML mapping")
        match = re.fullmatch(r"([A-Za-z0-9_]+)\s*:\s*(.*?)\s*", raw_line)
        if not match:
            raise GateError(f"malformed spec-gate user authorization line: {raw_line!r}")
        key, value = match.group(1), match.group(2)
        if key in result:
            raise GateError(f"duplicate spec-gate user authorization field: {key}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        result[key] = value
    expected = {
        "schema_version",
        "kind",
        "sprint_slug",
        "path",
        "reason",
        "decision",
        "authorization_source",
        "authorized_by",
        "authorized_at",
        "expiry",
        "removal_condition",
    }
    if set(result) != expected:
        raise GateError(
            "spec-gate user authorization must use exact schema fields "
            f"{sorted(expected)}"
        )
    return result


def spec_gate_exception_active(
    fm: dict[str, str], sprint_slug: str, path_type: str, sprint_dir: Path
) -> bool:
    """Validate the design §H sprint-local user authorization contract."""
    if not fm.get("spec_gate_exception") or fm.get("spec_gate_exception") != sprint_slug:
        return False
    fields = {
        key: (fm.get(key) or "").strip()
        for key in (
            "spec_gate_exception_path",
            "spec_gate_exception_reason",
            "spec_gate_exception_authorized_by",
            "spec_gate_exception_authorized_at",
            "spec_gate_exception_expiry",
            "spec_gate_exception_removal_condition",
            "spec_gate_exception_emergency_hotfix",
            "spec_gate_exception_authorization_ref",
        )
    }
    if any(not value for value in fields.values()):
        raise GateError(
            "spec_gate_exception requires path/reason/authorized_by/authorized_at/expiry/"
            "removal_condition/emergency_hotfix/authorization_ref; missing fields fail closed"
        )
    reason = fields["spec_gate_exception_reason"]
    removal = fields["spec_gate_exception_removal_condition"]
    if is_placeholder_criterion(reason) or is_placeholder_criterion(removal):
        raise GateError("spec_gate_exception reason/removal_condition cannot be placeholders")
    if fields["spec_gate_exception_path"] != path_type or path_type not in GENERATOR_PATHS:
        raise GateError("spec_gate_exception_path must exactly match current Feature/Refactor/System path")
    authorized_by = fields["spec_gate_exception_authorized_by"]
    if not re.fullmatch(r"user:[A-Za-z0-9][A-Za-z0-9._-]{1,63}", authorized_by):
        raise GateError("spec_gate_exception_authorized_by must be user:<stable-label>; generic user/self fails")
    if fields["spec_gate_exception_emergency_hotfix"].lower() != "false":
        raise GateError("Feature/Refactor/System spec exception must set emergency_hotfix=false")
    authorized_at = parse_utc_timestamp(fields["spec_gate_exception_authorized_at"], "spec_gate_exception_authorized_at")
    expiry_at = parse_utc_timestamp(fields["spec_gate_exception_expiry"], "spec_gate_exception_expiry")
    now = dt.datetime.now(dt.UTC)
    if authorized_at > now:
        raise GateError("spec_gate_exception_authorized_at cannot be in the future")
    if expiry_at <= now:
        raise GateError(f"spec_gate_exception 已于 {fields['spec_gate_exception_expiry']} 过期; 移除或重新授权")
    ref = fields["spec_gate_exception_authorization_ref"]
    if not re.fullmatch(r"user-authorizations/[A-Za-z0-9][A-Za-z0-9._-]*\.yaml", ref):
        raise GateError("spec_gate_exception_authorization_ref must be user-authorizations/<id>.yaml")
    auth_path = (sprint_dir / ref).resolve()
    try:
        auth_path.relative_to(sprint_dir.resolve())
    except ValueError as exc:
        raise GateError("spec_gate_exception_authorization_ref escapes current sprint") from exc
    record = parse_authorization_record(auth_path)
    expected = {
        "schema_version": "1",
        "kind": "spec_gate_exception_authorization",
        "sprint_slug": sprint_slug,
        "path": path_type,
        "reason": reason,
        "decision": "approve",
        "authorization_source": "user_prompt",
        "authorized_by": authorized_by,
        "authorized_at": fields["spec_gate_exception_authorized_at"],
        "expiry": fields["spec_gate_exception_expiry"],
        "removal_condition": removal,
    }
    if record != expected:
        raise GateError("spec-gate user authorization record does not exactly match frontmatter")
    return True


def resolve_acceptance_criteria(sprint_dir: Path, ai_state: Path) -> list[str]:
    """design §4.2/§4.3: 标准必须来自本 sprint design.md, 或 design 显式链接的
    requirements 档 — 不接受任意 requirements/*.md."""
    design = sprint_dir / "design.md"
    if not design.is_file():
        return []
    design_text = design.read_text(encoding="utf-8", errors="replace")
    own = acceptance_criteria(design_text)
    if own:
        return own
    for match in re.finditer(r"requirements/([A-Za-z0-9][A-Za-z0-9._-]*\.md)", design_text):
        linked = ai_state / "requirements" / match.group(1)
        if not linked.is_file():
            continue
        from_linked = acceptance_criteria(linked.read_text(encoding="utf-8", errors="replace"))
        if from_linked:
            return from_linked
    return []


def validate_spec_gate(
    sprint_dir: Path,
    ai_state: Path,
    fm: dict[str, str],
    sprint_slug: str,
    *,
    allow_exception: bool,
) -> list[str]:
    """spec-gate 主门禁在 impl 入口 (design §4.2); ship 处复核 (design §4.4)."""
    if spec_gate_exception_active(fm, sprint_slug, fm.get("path", ""), sprint_dir):
        if allow_exception:
            return []
        raise GateError("active Feature+ spec_gate_exception must be removed before ship")
    criteria = resolve_acceptance_criteria(sprint_dir, ai_state)
    if not criteria:
        raise GateError(
            "spec-gate: design.md (或其显式链接的 requirements 档) 缺机器可识别的验收标准段 "
            "(## Acceptance Criteria / ## 验收标准 + ≥1 条可观测项); 占位符/TODO/泛化陈述不算"
        )
    return criteria


def evidence_field(block: str, key: str) -> str:
    matches = re.findall(rf"(?m)^\s+{re.escape(key)}\s*:\s*([^#\n]+)", block)
    if len(matches) > 1:
        raise GateError(f"evidence record has duplicate {key}")
    return matches[0].strip().strip('"\'') if matches else ""


def parse_evidence_records(path: Path) -> list[dict[str, Any]]:
    content = require_file(path, "evidence.yaml")
    items = list(re.finditer(r"(?m)^\s*-\s+tool_use_id\s*:\s*([^#\n]*)", content))
    records: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        end = items[index + 1].start() if index + 1 < len(items) else len(content)
        block = content[item.start():end]
        covers_raw = evidence_field(block, "covers")
        covers = []
        if covers_raw:
            value = covers_raw.strip()
            if not (value.startswith("[") and value.endswith("]")):
                raise GateError("evidence covers must be an inline AC list")
            covers = [part.strip().strip('"\'').upper() for part in value[1:-1].split(",") if part.strip()]
            if any(not re.fullmatch(r"AC\d+", label) for label in covers):
                raise GateError("evidence covers contains an invalid AC label")
        records.append(
            {
                "tool_use_id": item.group(1).strip().strip('"\''),
                "ac_id": evidence_field(block, "ac_id").upper(),
                "covers": covers,
                "result": evidence_field(block, "result").lower(),
                "source": evidence_field(block, "source").lower(),
                "command_or_artifact": evidence_field(block, "command_or_artifact"),
                "observed_at": evidence_field(block, "observed_at"),
                "summary": evidence_field(block, "summary"),
                "exit_code": evidence_field(block, "exit_code"),
                "output_artifact": evidence_field(block, "output_artifact"),
                "artifact_sha256": evidence_field(block, "artifact_sha256"),
                "implementation_commit": evidence_field(block, "implementation_commit"),
            }
        )
    return records


def review_explicitly_accepts(review_content: str, label: str) -> bool:
    """Accept only an exact positive AC result, never prose containing PASS."""
    negative = re.compile(r"\b(?:NOT\s+SATISFIED|MISSING|DEVIATED|FAIL(?:ED)?|REWORK|DOES\s+NOT\s+PASS|NOT\s+PASS)\b", re.I)
    positive = re.compile(
        rf"(?:^|\|)\s*{re.escape(label)}\s*(?:\||:|[-—])\s*(?:SATISFIED|PASS)\s*(?:\||$)",
        re.I,
    )
    return any(not negative.search(line) and positive.search(line) for line in review_content.splitlines())


def validate_ac_mapping(
    sprint_dir: Path,
    criteria: list[str],
    records: list[dict[str, Any]],
    review_path: Path,
    review_content: str,
    reviewed_commit: str,
) -> None:
    """Require one admissible explicit PASS record per labeled AC."""
    labels: set[str] = set()
    for criterion in criteria:
        for match in AC_LABEL.finditer(criterion):
            labels.add(match.group(1).upper())
    if not labels:
        return
    missing: list[str] = []
    for label in sorted(labels):
        # Meta-acceptance is mechanically derived by this gate. Requiring a
        # future review/evidence row for AC11/AC12 would be circular.
        if label in {"AC11", "AC12"}:
            continue
        admissible = False
        for record in records:
            mapped = record["ac_id"] == label or label in record["covers"]
            if not mapped or record["result"] != "pass":
                continue
            required = ("source", "command_or_artifact", "observed_at", "summary")
            if any(not record[field] for field in required):
                continue
            try:
                parse_utc_timestamp(record["observed_at"], f"evidence {record['tool_use_id']} observed_at")
            except GateError:
                continue
            source = record["source"]
            if source == "command":
                output = (sprint_dir / record["output_artifact"]).resolve()
                try:
                    output.relative_to(sprint_dir.resolve())
                except (ValueError, TypeError):
                    continue
                if (
                    record["exit_code"] != "0"
                    or not re.fullmatch(r"[0-9a-f]{64}", record["artifact_sha256"])
                    or record["implementation_commit"] != reviewed_commit
                    or not output.is_file()
                ):
                    continue
                output_bytes = output.read_bytes()
                output_text = output_bytes.decode("utf-8", errors="replace")
                admissible = (
                    hashlib.sha256(output_bytes).hexdigest() == record["artifact_sha256"]
                    and record["command_or_artifact"] in output_text
                    and re.search(r"(?im)^exit_code:\s*0\s*$", output_text) is not None
                    and record["summary"] in output_text
                )
            elif source == "artifact":
                artifact = (sprint_dir / record["command_or_artifact"]).resolve()
                try:
                    artifact.relative_to(sprint_dir.resolve())
                except ValueError:
                    continue
                admissible = artifact.is_file()
            elif source == "review":
                candidate = (sprint_dir / record["command_or_artifact"]).resolve()
                admissible = (
                    candidate == review_path.resolve()
                    and "## Spec Compliance" in review_content
                    and "## Evidence Cross-Check" in review_content
                    and final_review_verdict(review_content) == "PASS"
                    and review_explicitly_accepts(review_content, label)
                )
            if admissible:
                break
        if not admissible:
            missing.append(label)
    if missing:
        raise GateError(
            f"spec-gate ship 复核: 验收标准 {', '.join(missing)} 缺 admissible per-AC PASS evidence "
            "(unknown/checklist-only/missing artifact/stale review do not count)"
        )


def validate_meta_acceptance(
    criteria: list[str], review_content: str, sprint_dir: Path, cwd: Path
) -> None:
    labels = {match.group(1).upper() for item in criteria for match in AC_LABEL.finditer(item)}
    if "AC11" in labels and final_review_verdict(review_content) != "PASS":
        raise GateError("AC11 requires the latest bound evaluator verdict PASS")
    if "AC12" not in labels:
        return
    cleanup = require_file(sprint_dir / "cleanup-pass.md", "cleanup-pass.md")
    if not re.search(r"\bPASS\b|completed|完成", cleanup, re.I):
        raise GateError("AC12 requires completed polish/cleanup evidence")
    worktrees = git_text(git_root(cwd), ["worktree", "list", "--porcelain"], "worktree readiness")
    active = len(re.findall(r"(?m)^worktree\s+", worktrees))
    if active != 1:
        raise GateError(f"AC12 requires no extra active worktree; found {active}")


def validate_generator_chain(sprint_dir: Path, sprint_slug: str) -> None:
    assignments = read_jsonl(
        sprint_dir / "subagent-assignments.jsonl",
        "subagent assignments",
        sprint_slug,
        kind="assignment",
    )
    events = read_jsonl(
        sprint_dir / "subagent-events.jsonl",
        "subagent events",
        sprint_slug,
        kind="event",
    )

    assignments_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for assignment in assignments:
        key = join_key(assignment)
        if key in assignments_by_key:
            raise GateError(
                f"ambiguous assignments for agent_id={key[0]!r}, sprint_slug={key[1]!r}"
            )
        assignments_by_key[key] = assignment

    events_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for event in events:
        key = join_key(event)
        if key not in assignments_by_key:
            lifecycle = "unbound SubagentStart" if event["event"] == "SubagentStart" else "orphan SubagentStop"
            raise GateError(f"{lifecycle}: agent_id={key[0]!r}, sprint_slug={key[1]!r}")
        events_by_key.setdefault(key, []).append(event)

    generator_keys = [key for key, row in assignments_by_key.items() if row["role"] == "generator"]
    if not generator_keys:
        raise GateError("no role=generator assignment found")

    for key, assignment in assignments_by_key.items():
        matching = events_by_key.get(key, [])
        if not matching:
            if assignment["role"] == "generator":
                raise GateError(f"generator {key[0]!r} has no lifecycle events")
            raise GateError(f"assignment {key[0]!r} has no lifecycle events")
        starts = [event for event in matching if event["event"] == "SubagentStart"]
        stops = [event for event in matching if event["event"] == "SubagentStop"]
        if len(starts) > 1:
            raise GateError(f"ambiguous SubagentStart events for agent_id={key[0]!r}")
        if not starts:
            raise GateError(f"isolated SubagentStop for agent_id={key[0]!r}; no matching Start")
        if not stops:
            raise GateError(f"agent_id={key[0]!r} has no SubagentStop")
        agent_types = {event["agent_type"] for event in matching}
        if len(agent_types) != 1:
            raise GateError(f"inconsistent agent_type lifecycle for agent_id={key[0]!r}")
        latest_event = max(matching, key=lambda row: row["_parsed_timestamp"])
        if latest_event["event"] != "SubagentStop":
            raise GateError(
                f"agent_id={key[0]!r} latest lifecycle event is {latest_event['event']}, not SubagentStop"
            )
        if latest_event["_parsed_timestamp"] < starts[0]["_parsed_timestamp"]:
            raise GateError(f"agent_id={key[0]!r} Stop precedes Start")
        if latest_event["_parsed_timestamp"] < assignment["_parsed_timestamp"]:
            raise GateError(
                f"agent_id={key[0]!r} Stop precedes the bound assignment handshake"
            )


def validate_checklist(path: Path) -> None:
    content = require_file(path, "checklist.yaml")
    task_ids = re.findall(r"(?m)^\s*-\s+id\s*:\s*[^#\n]+", content)
    statuses = [
        value.strip().strip('"\'').lower()
        for value in re.findall(r"(?m)^\s+status\s*:\s*([^#\n]+)", content)
    ]
    if not task_ids:
        raise GateError("checklist.yaml has no tasks")
    if len(statuses) < len(task_ids):
        raise GateError("checklist.yaml has tasks without status")
    incomplete = [status for status in statuses if status != "completed"]
    if incomplete:
        raise GateError(f"checklist.yaml is incomplete: statuses={incomplete}")


def validate_evidence(path: Path) -> list[dict[str, Any]]:
    content = require_file(path, "evidence.yaml")
    if not re.search(r"(?m)^collected_evidence\s*:\s*(?:#.*)?$", content):
        raise GateError("evidence.yaml lacks collected_evidence list")
    item_matches = list(
        re.finditer(r"(?m)^\s*-\s+tool_use_id\s*:\s*([^#\n]*)", content)
    )
    if not item_matches:
        raise GateError("evidence.yaml contains no evidence records")
    all_result_lines = re.findall(r"(?m)^\s+result\s*:\s*([^#\n]+)", content)
    if len(all_result_lines) != len(item_matches):
        raise GateError("evidence.yaml must contain exactly one result per evidence record")
    normalized_all = [value.strip().strip('"\'').lower() for value in all_result_lines]
    if any(value == "fail" or value.startswith("fail (") for value in normalized_all):
        raise GateError("evidence.yaml contains failing evidence")
    results: list[str] = []
    for index, item_match in enumerate(item_matches):
        evidence_id = item_match.group(1).strip().strip('"\'')
        if not evidence_id or evidence_id in {"[]", "null", "~"}:
            raise GateError("evidence.yaml contains an empty tool_use_id")
        block_end = item_matches[index + 1].start() if index + 1 < len(item_matches) else len(content)
        item_block = content[item_match.end() : block_end]
        raw_results = re.findall(r"(?m)^\s+result\s*:\s*([^#\n]+)", item_block)
        if len(raw_results) != 1:
            raise GateError(f"evidence {evidence_id!r} must have exactly one result")
        result = raw_results[0].strip().strip('"\'').lower()
        if result == "pass":
            results.append("pass")
        elif result == "unknown":
            results.append("unknown")
        elif result == "fail" or result.startswith("fail ("):
            results.append("fail")
        else:
            raise GateError(f"evidence {evidence_id!r} has unsupported result {result!r}")
    if "pass" not in results:
        raise GateError("evidence.yaml has no explicit passing evidence (unknown alone is insufficient)")
    return parse_evidence_records(path)


def final_review_verdict(content: str) -> str:
    verdicts: list[str] = []
    for raw_line in content.splitlines():
        # Strip every "*" (not just leading/trailing) so the evaluator's own bold
        # template line "**判定**: PASS" parses; also accept the Chinese "判定:" label.
        line = raw_line.replace("*", "").strip()
        match = re.fullmatch(r"(?:Evaluator\s+)?VERDICT\s*:\s*([A-Za-z][A-Za-z _-]*?)\.?", line, re.I)
        if not match:
            match = re.fullmatch(r"判定\s*:\s*([A-Za-z][A-Za-z _-]*?)\.?", line, re.I)
        if match:
            verdicts.append(re.sub(r"\s+", " ", match.group(1).strip()).upper())
    if not verdicts:
        raise GateError("reviews/pass1.md has no explicit VERDICT line")
    return verdicts[-1]


def select_latest_review(reviews_dir: Path) -> Path:
    if not reviews_dir.is_dir():
        raise GateError(f"missing reviews directory: {reviews_dir}")
    try:
        candidates = [path for path in reviews_dir.iterdir() if path.is_file()]
    except OSError as exc:
        raise GateError(f"cannot read reviews directory: {exc}") from exc

    numbered: list[tuple[int, Path]] = []
    for path in candidates:
        match = re.fullmatch(r"pass([1-9]\d*)\.md", path.name)
        if match:
            numbered.append((int(match.group(1)), path))
            continue
        if path.name.startswith("pass") and path.name.endswith(".md"):
            raise GateError(f"malformed numbered review filename: {path.name!r}")
    if not numbered:
        raise GateError("reviews directory has no numbered passN.md review")
    return max(numbered, key=lambda item: item[0])[1]


def validate_review(path: Path, path_type: str) -> str:
    content = require_file(path, f"latest review {path.name}")
    verdict = final_review_verdict(content)
    if verdict != "PASS":
        raise GateError(f"latest review {path.name} VERDICT is {verdict!r}, expected PASS")
    if "## Spec Compliance" not in content:
        raise GateError(f"latest review {path.name} lacks ## Spec Compliance")
    if "## Evidence Cross-Check" not in content:
        raise GateError(f"latest review {path.name} lacks ## Evidence Cross-Check")
    return content


def git_text(cwd: Path, args: list[str], label: str) -> str:
    try:
        run = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise GateError(f"review freshness git check unavailable ({label}): {exc}") from exc
    if run.returncode != 0:
        raise GateError(
            f"review freshness git check failed ({label}): "
            f"{(run.stderr or run.stdout).strip()}"
        )
    return run.stdout


def parse_review_manifest(path: Path) -> tuple[str, str, dict[str, str]]:
    content = require_file(path, "review-manifest.yaml")
    implementation_commit = ""
    files: dict[str, str] = {}
    in_files = False
    schema_version = ""
    index_governance = ""
    for raw in content.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  "):
            if not in_files:
                raise GateError("review-manifest has nested values outside files")
            match = re.fullmatch(r"\s{2}(['\"]?)(.+?)\1\s*:\s*(['\"])([0-9a-f]{64})\3\s*", raw)
            if not match:
                raise GateError(f"malformed review-manifest file hash line: {raw!r}")
            key = match.group(2)
            if key in files:
                raise GateError(f"duplicate review-manifest path: {key}")
            files[key] = match.group(4)
            continue
        in_files = False
        match = re.fullmatch(r"([A-Za-z0-9_]+)\s*:\s*(.*?)\s*", raw)
        if not match:
            raise GateError(f"malformed review-manifest line: {raw!r}")
        key, value = match.group(1), match.group(2).strip().strip('"\'')
        if key == "schema_version":
            schema_version = value
        elif key == "implementation_commit":
            implementation_commit = value
        elif key == "index_governance_sha256":
            index_governance = value
        elif key == "files" and not value:
            in_files = True
        else:
            raise GateError(f"unsupported review-manifest field: {key}")
    if (
        schema_version != "1"
        or not re.fullmatch(r"[0-9a-f]{40}", implementation_commit)
        or not re.fullmatch(r"[0-9a-f]{64}", index_governance)
    ):
        raise GateError(
            "review-manifest requires schema_version=1, a 40-hex implementation_commit, "
            "and a 64-hex index_governance_sha256"
        )
    required = {
        "design.md",
        "checklist.yaml",
        "evidence.yaml",
        "runtime-verify.md",
        "rework-notes.md",
        "cleanup-pass.md",
        "tdd-evidence.yaml",
        "architecture/ARCHITECTURE.md",
        "architecture/athena-9.9.3.md",
    }
    if set(files) != required:
        raise GateError(f"review-manifest files must be exactly {sorted(required)}")
    return implementation_commit, index_governance, files


INDEX_GOVERNANCE_FIELDS = (
    "path",
    "current_sprint_slug",
    "skip_polish",
    "skip_runtime_verify",
    "skip_architecture_check",
    "skip_impl_subagent_check",
    "plan_critique_disabled",
    "plan_critique_min_rounds",
)


def index_governance_sha256(fm: dict[str, str]) -> str:
    protected = {key: fm.get(key, "") for key in INDEX_GOVERNANCE_FIELDS}
    body = json.dumps(protected, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def validate_index_governance(sprint_dir: Path, fm: dict[str, str]) -> None:
    _, expected, _ = parse_review_manifest(sprint_dir / "review-manifest.yaml")
    if expected != index_governance_sha256(fm):
        raise GateError("review-manifest index governance does not match protected _index fields")


def validate_review_binding(
    review_content: str,
    review_path: Path,
    sprint_dir: Path,
    ai_state: Path,
    cwd: Path,
    fm: dict[str, str],
) -> str:
    design_matches = re.findall(r"(?m)^Reviewed design sha256:\s*([0-9a-f]{64})\s*$", review_content)
    commit_matches = re.findall(r"(?m)^Reviewed implementation commit:\s*([0-9a-f]{40})\s*$", review_content)
    manifest_matches = re.findall(r"(?m)^Reviewed state manifest sha256:\s*([0-9a-f]{64})\s*$", review_content)
    if len(design_matches) != 1 or len(commit_matches) != 1 or len(manifest_matches) != 1:
        raise GateError(
            "latest PASS review must contain exactly one design, implementation commit, "
            "and state-manifest binding"
        )
    design_path = sprint_dir / "design.md"
    design_digest = hashlib.sha256(require_file(design_path, "design.md").encode("utf-8")).hexdigest()
    if design_matches[0] != design_digest:
        raise GateError("Reviewed design sha256 does not match current authoritative design.md")
    reviewed_commit = commit_matches[0]
    manifest_path = sprint_dir / "review-manifest.yaml"
    manifest_bytes = require_file(manifest_path, "review-manifest.yaml").encode("utf-8")
    if hashlib.sha256(manifest_bytes).hexdigest() != manifest_matches[0]:
        raise GateError("Reviewed state manifest sha256 does not match review-manifest.yaml")
    manifest_commit, manifest_governance, manifest_files = parse_review_manifest(manifest_path)
    if manifest_commit != reviewed_commit:
        raise GateError("review-manifest implementation_commit does not match final review binding")
    if manifest_governance != index_governance_sha256(fm):
        raise GateError("review-manifest index governance does not match protected _index fields")
    for name, expected_hash in manifest_files.items():
        target = ai_state / name if name.startswith("architecture/") else sprint_dir / name
        if not target.is_file():
            raise GateError(f"review-manifest target missing: {name}")
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected_hash:
            raise GateError(f"review-manifest hash mismatch: {name}")
    root_text = git_text(cwd, ["rev-parse", "--show-toplevel"], "repository root").strip()
    if not root_text:
        raise GateError("review freshness cannot determine Git repository root")
    root = Path(root_text)
    git_text(root, ["cat-file", "-e", f"{reviewed_commit}^{{commit}}"], "reviewed commit exists")
    git_text(root, ["merge-base", "--is-ancestor", reviewed_commit, "HEAD"], "reviewed commit ancestor")
    changed: set[str] = set()
    for args, label in (
        (["diff", "--name-only", f"{reviewed_commit}..HEAD"], "committed drift"),
        (["diff", "--name-only"], "working drift"),
        (["diff", "--name-only", "--cached"], "staged drift"),
        (["ls-files", "--others", "--exclude-standard"], "untracked drift"),
    ):
        changed.update(line.strip() for line in git_text(root, args, label).splitlines() if line.strip())
    implementation_drift = sorted(path for path in changed if not path.startswith(".ai_state/"))
    if implementation_drift:
        raise GateError(
            "unreviewed implementation drift after Reviewed implementation commit: "
            + ", ".join(implementation_drift[:8])
        )
    sprint_rel = str(sprint_dir.relative_to(root)).replace("\\", "/")
    allowed_exact = {
        ".ai_state/_index.md",
        *(f"{sprint_rel}/{name}" for name in manifest_files if not name.startswith("architecture/")),
        f"{sprint_rel}/review-manifest.yaml",
        f"{sprint_rel}/ship-receipt.md",
        f"{sprint_rel}/session-log.md",
        f"{sprint_rel}/subagent-assignments.jsonl",
        f"{sprint_rel}/subagent-events.jsonl",
        f"{sprint_rel}/subagent-log.md",
        f"{sprint_rel}/token-usage.jsonl",
        f"{sprint_rel}/tool-trace.jsonl",
        ".ai_state/architecture/ARCHITECTURE.md",
        ".ai_state/architecture/athena-9.9.3.md",
    }
    state_drift = sorted(
        file for file in changed
        if file.startswith(".ai_state/")
        and file not in allowed_exact
        and not file.startswith(f"{sprint_rel}/reviews/")
        and not file.startswith(f"{sprint_rel}/evidence/")
        and not file.startswith(f"{sprint_rel}/user-authorizations/")
    )
    if state_drift:
        raise GateError("unreviewed .ai_state drift outside post-review allowlist: " + ", ".join(state_drift[:8]))
    return reviewed_commit


def validate_tdd_evidence(path: Path) -> None:
    content = require_file(path, "tdd-evidence.yaml")
    records = list(re.finditer(r"(?m)^\s*-\s+test_file\s*:\s*([^#\n]+)", content))
    if not records:
        raise GateError("tdd-evidence.yaml contains no red-to-green records")
    for index, item in enumerate(records):
        end = records[index + 1].start() if index + 1 < len(records) else len(content)
        block = content[item.start():end]
        values = {key: evidence_field(block, key) for key in (
            "red_command", "red_summary", "red_observed_at", "implementation_files",
            "implementation_observed_at", "green_command", "green_summary", "green_observed_at",
        )}
        if any(not value for value in values.values()):
            raise GateError("tdd-evidence record is missing red/implementation/green fields")
        red = parse_utc_timestamp(values["red_observed_at"], "tdd red_observed_at")
        implementation = parse_utc_timestamp(
            values["implementation_observed_at"], "tdd implementation_observed_at"
        )
        green = parse_utc_timestamp(values["green_observed_at"], "tdd green_observed_at")
        if not red < implementation < green:
            raise GateError(
                "tdd-evidence timestamps must satisfy red < implementation < green"
            )


def git_lines(cwd: Path, args: list[str]) -> tuple[bool, set[str]]:
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError) as exc:
        sys.stderr.write(f"[delivery-gate] git {' '.join(args)} unavailable: {exc}\n")
        return False, set()
    if result.returncode != 0:
        return False, set()
    return True, {line.strip() for line in result.stdout.splitlines() if line.strip()}


def git_root(cwd: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return cwd
    return Path(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else cwd


def changed_file_count(cwd: Path) -> int:
    root = git_root(cwd)
    files: set[str] = set()
    any_ok = False
    probes = (
        ["diff", "--name-only", "main...HEAD"],
        ["diff", "--name-only", "master...HEAD"],
        ["diff", "--name-only"],
        ["diff", "--name-only", "--cached"],
        ["ls-files", "--others", "--exclude-standard"],
    )
    for args in probes:
        ok, lines = git_lines(root, args)
        any_ok = any_ok or ok
        files |= lines
    if not any_ok:
        # Every git probe failed: the change set is unknowable, so fail closed
        # (report an over-threshold count) rather than silently skip the gate.
        return sys.maxsize
    return len(files)


def truthy(value: str) -> bool:
    return value.strip().lower() == "true"


def yaml_scalar(raw_value: str) -> str:
    value = raw_value.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.strip()


def validate_roadmap_items(ai_state: Path, roadmap_slug: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", roadmap_slug):
        raise GateError(f"invalid current_roadmap_slug {roadmap_slug!r}")
    path = ai_state / "roadmap" / roadmap_slug / "items.yaml"
    content = require_file(path, f"roadmap/{roadmap_slug}/items.yaml")

    slug_matches = re.findall(r"(?m)^roadmap_slug\s*:\s*([^#\n]*)", content)
    if len(slug_matches) != 1 or yaml_scalar(slug_matches[0]) != roadmap_slug:
        raise GateError("roadmap items.yaml has missing or mismatched roadmap_slug")
    total_matches = re.findall(r"(?m)^total_items\s*:\s*([^#\n]*)", content)
    if len(total_matches) != 1:
        raise GateError("roadmap items.yaml must have exactly one total_items")
    try:
        total_items = int(yaml_scalar(total_matches[0]))
    except ValueError as exc:
        raise GateError("roadmap items.yaml total_items must be an integer") from exc
    if total_items < 1:
        raise GateError("roadmap items.yaml must contain at least one item")
    item_headers = re.findall(r"(?m)^items\s*:\s*(?:#.*)?$", content)
    if len(item_headers) != 1:
        raise GateError("roadmap items.yaml must have exactly one items list")

    item_matches = list(re.finditer(r"(?m)^\s+-\s+slug\s*:\s*([^#\n]*)", content))
    if len(item_matches) != total_items:
        raise GateError(
            f"roadmap items.yaml total_items={total_items} but parsed {len(item_matches)} items"
        )
    seen_slugs: set[str] = set()
    for index, item_match in enumerate(item_matches):
        item_slug = yaml_scalar(item_match.group(1))
        if not item_slug:
            raise GateError("roadmap items.yaml contains an item with empty slug")
        if item_slug in seen_slugs:
            raise GateError(f"roadmap items.yaml contains duplicate item slug {item_slug!r}")
        seen_slugs.add(item_slug)
        block_end = item_matches[index + 1].start() if index + 1 < len(item_matches) else len(content)
        item_block = content[item_match.end() : block_end]
        status_matches = re.findall(r"(?m)^\s+status\s*:\s*([^#\n]*)", item_block)
        if len(status_matches) != 1:
            raise GateError(f"roadmap item {item_slug!r} must have exactly one status")
        status = yaml_scalar(status_matches[0]).lower()
        if status != "completed":
            raise GateError(
                f"roadmap item {item_slug!r} status is {status or 'missing'!r}; ship requires completed"
            )


def validate_existing_policy(
    *,
    ai_state: Path,
    sprint_dir: Path,
    fm: dict[str, str],
    cwd: Path,
    review_content: str,
    review_path: Path | None,
) -> None:
    path_type = fm.get("path", "")

    roadmap_slug = fm.get("current_roadmap_slug", "")
    if roadmap_slug:
        validate_roadmap_items(ai_state, roadmap_slug)

    if path_type == "Bugfix":
        require_file(sprint_dir / "fix-note.md", "fix-note.md")

    if path_type in REFACTOR_SYSTEM:
        if not truthy(fm.get("skip_runtime_verify", "false")):
            runtime = require_file(sprint_dir / "runtime-verify.md", "runtime-verify.md")
            if "## 测试场景" not in runtime and "## Test Scenarios" not in runtime:
                raise GateError("runtime-verify.md lacks an executed test-scenarios section")
        require_file(sprint_dir / "cleanup-pass.md", "cleanup-pass.md")

        if not truthy(fm.get("skip_architecture_check", "false")) and changed_file_count(cwd) >= 5:
            architecture = ai_state / "architecture" / "ARCHITECTURE.md"
            require_file(architecture, "architecture/ARCHITECTURE.md")

    if path_type in GENERATOR_PATHS and not truthy(fm.get("plan_critique_disabled", "false")):
        design = sprint_dir / "design.md"
        design_content = require_file(design, "design.md")
        rounds = len(re.findall(r"Critic Findings", design_content))
        try:
            configured = int(fm.get("plan_critique_min_rounds", "0") or "0")
        except ValueError:
            raise GateError("plan_critique_min_rounds must be an integer")
        minimum = configured if configured > 0 else (2 if path_type in REFACTOR_SYSTEM else 1)
        if rounds < minimum:
            raise GateError(f"design.md has {rounds} Critic Findings rounds; expected at least {minimum}")

    # Keep the value used so static review cannot accidentally remove the
    # evidence cross-check after validate_review has accepted it.
    if path_type in REFACTOR_SYSTEM and "## Evidence Cross-Check" not in review_content:
        raise GateError("review evidence cross-check missing")


def is_implementation_write(payload: dict[str, Any]) -> bool:
    if payload.get("hook_event_name") != "PreToolUse":
        return False
    tool = str(payload.get("tool_name", "")).lower()
    if tool not in {"edit", "write", "multiedit", "apply_patch"}:
        return False
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return True
    candidates = [
        str(tool_input.get(key, ""))
        for key in ("file_path", "path", "patch")
        if tool_input.get(key)
    ]
    if not candidates:
        return True
    paths = re.findall(r"(?:\*\*\* (?:Update|Add) File:|^)([^\n]+)", "\n".join(candidates), re.M)
    if not paths:
        paths = candidates
    return any(".ai_state/" not in path.replace("\\", "/") for path in paths)


def main() -> int:
    ai_state: Path | None = None
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except (json.JSONDecodeError, OSError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}

        cwd = payload_cwd(payload)
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS
        index_path = ai_state / "_index.md"
        if not index_path.is_file():
            return block("Athena .ai_state exists but _index.md is missing")
        try:
            index_content = index_path.read_text(encoding="utf-8")
        except OSError as exc:
            return block(f"cannot read .ai_state/_index.md: {exc}")
        try:
            fm = parse_frontmatter(index_content)
        except GateError as exc:
            return block(str(exc))
        stage = fm.get("stage", "")
        if not stage:
            return block(".ai_state/_index.md has no non-empty stage")
        if stage not in VALID_STAGES:
            return block(f"unknown Athena stage {stage!r}")
        if is_implementation_write(payload) and stage in {"design", "impl"}:
            path_type = fm.get("path", "")
            if path_type in GENERATOR_PATHS:
                sprint_slug = fm.get("current_sprint_slug", "")
                if not sprint_slug:
                    return block("implementation write requires current_sprint_slug for the spec gate")
                try:
                    validate_spec_gate(
                        ai_state / "sprints" / sprint_slug,
                        ai_state,
                        fm,
                        sprint_slug,
                        allow_exception=True,
                    )
                except GateError as exc:
                    return block(str(exc))
        if stage == "impl":
            # design §4.2 主门禁: Feature/Refactor/System 在 impl 阶段必须已有
            # 机器可识别验收标准; ship 段复核是纵深防御 (design §4.4).
            if fm.get("path", "") in GENERATOR_PATHS:
                impl_sprint_slug = fm.get("current_sprint_slug", "")
                if not impl_sprint_slug:
                    return block("impl stage requires current_sprint_slug for the spec gate")
                try:
                    validate_spec_gate(
                        ai_state / "sprints" / impl_sprint_slug,
                        ai_state,
                        fm,
                        impl_sprint_slug,
                        allow_exception=True,
                    )
                except GateError as exc:
                    return block(str(exc))
                except Exception as exc:
                    return block(f"unexpected impl spec-gate error (fail-closed): {exc}")
            return EXIT_SUCCESS
        if stage != "ship":
            return EXIT_SUCCESS

        sprint_slug = fm.get("current_sprint_slug", "")
        if not sprint_slug:
            return block("ship stage requires current_sprint_slug")
        sprint_dir = ai_state / "sprints" / sprint_slug

        try:
            # Governance binding is checked before trusting path/skip/critic
            # fields, so mutating System→Quick cannot bypass the release gate.
            validate_index_governance(sprint_dir, fm)
            path_type = fm.get("path", "")
            if path_type not in VALID_PATHS:
                raise GateError(f"ship stage has unknown Athena path {path_type!r}")
            review_content = ""
            review_path: Path | None = None
            if path_type in GENERATOR_PATHS:
                spec_criteria = validate_spec_gate(
                    sprint_dir, ai_state, fm, sprint_slug, allow_exception=False
                )
                if not truthy(fm.get("skip_impl_subagent_check", "false")):
                    validate_generator_chain(sprint_dir, sprint_slug)
                validate_checklist(sprint_dir / "checklist.yaml")
                evidence_records = validate_evidence(sprint_dir / "evidence.yaml")
                validate_tdd_evidence(sprint_dir / "tdd-evidence.yaml")
                review_path = select_latest_review(sprint_dir / "reviews")
                review_content = validate_review(review_path, path_type)
                reviewed_commit = validate_review_binding(
                    review_content, review_path, sprint_dir, ai_state, cwd, fm
                )
                validate_ac_mapping(
                    sprint_dir,
                    spec_criteria,
                    evidence_records,
                    review_path,
                    review_content,
                    reviewed_commit,
                )
            validate_existing_policy(
                ai_state=ai_state,
                sprint_dir=sprint_dir,
                fm=fm,
                cwd=cwd,
                review_content=review_content,
                review_path=review_path,
            )
            if path_type in GENERATOR_PATHS:
                validate_meta_acceptance(spec_criteria, review_content, sprint_dir, cwd)
        except GateError as exc:
            return block(str(exc))
        except Exception as exc:
            return block(f"unexpected ship validation error (fail-closed): {exc}")
        return EXIT_SUCCESS
    except Exception as exc:
        if ai_state is not None:
            return block(f"unexpected Athena validation error (fail-closed): {exc}")
        sys.stderr.write(f"[delivery-gate] non-Athena preflight error: {exc}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())

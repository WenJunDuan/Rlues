"""Athena 9.9.8 _index.md bounds: ≤12 KiB, lists ≤10, item ≤160 bytes.

Overflow is copied to sprints/{slug}/index-overflow.md, never dropped.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ITEM_MAX_BYTES = 160
INDEX_MAX_BYTES = 12 * 1024
LIST_MAX = 10


def byte_len(text: str) -> int:
    return len(str(text).encode("utf-8"))


def utf8_prefix(text: str, max_bytes: int) -> str:
    end = len(text)
    while end > 0 and byte_len(text[:end]) > max_bytes:
        end -= 1
    return text[:end]


def summarize(full: str, pointer: str) -> str:
    suffix = f" →{pointer}"
    budget = ITEM_MAX_BYTES - byte_len(suffix)
    if budget < 1:
        return utf8_prefix(pointer, ITEM_MAX_BYTES)
    compact = re.sub(r"\s+", " ", str(full)).strip()
    return utf8_prefix(compact, budget) + suffix


def split_quoted_list(inner: str) -> list[str]:
    items: list[str] = []
    cur = ""
    quote = ""
    escaped = False
    raw = inner.strip()
    if not raw:
        return items
    for char in raw:
        if escaped:
            cur += char
            escaped = False
            continue
        if char == "\\" and quote == '"':
            escaped = True
            cur += char
            continue
        if quote:
            cur += char
            if char == quote:
                quote = ""
            continue
        if char in {'"', "'"}:
            quote = char
            cur += char
            continue
        if char == ",":
            items.append(cur.strip())
            cur = ""
            continue
        cur += char
    if cur.strip():
        items.append(cur.strip())
    return items


def unquote(item: str) -> str:
    text = item.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1].replace('\\"', '"')
    return text


def read_slug(content: str) -> str:
    match = re.search(r'^current_sprint_slug:\s*"?([^"\n]*)"?', content, re.M)
    return match.group(1).strip() if match else ""


def spill_path(ai_state: Path, slug: str) -> Path:
    if slug:
        return ai_state / "sprints" / slug / "index-overflow.md"
    return ai_state / "index-overflow.md"


def next_id(existing: str, prefix: str) -> int:
    nums = [int(n) for n in re.findall(rf"^## {re.escape(prefix)}-(\d+)", existing, re.M)]
    return max(nums) + 1 if nums else 0


class Spiller:
    def __init__(self, ai_state: Path, slug: str) -> None:
        self.path = spill_path(ai_state, slug)
        self.body = ""
        if self.path.is_file():
            self.body = self.path.read_text(encoding="utf-8")
        if not self.body:
            self.body = (
                f"# _index overflow — {slug or 'project'}\n\n"
                "Full items moved off `_index.md` (AC9). Do not delete.\n"
            )

    def pointer(self, ident: str) -> str:
        return f"index-overflow.md#{ident}"

    def spill(self, prefix: str, full: str) -> str:
        ident = f"{prefix}-{next_id(self.body, prefix)}"
        self.body += f"\n## {ident}\n\n{full}\n"
        return ident

    def flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.body, encoding="utf-8")


def enforce_route_history(content: str, spiller: Spiller) -> str:
    match = re.search(r"^route_history:\s*\[(.*)\]\s*(?:#.*)?$", content, re.M)
    if not match:
        return content
    values = [unquote(item) for item in split_quoted_list(match.group(1))]
    extra = values[:-LIST_MAX] if len(values) > LIST_MAX else []
    values = values[-LIST_MAX:]
    for full in extra:
        spiller.spill("rh", full)
    next_values = []
    for full in values:
        if byte_len(full) <= ITEM_MAX_BYTES:
            next_values.append(full)
            continue
        ident = spiller.spill("rh", full)
        next_values.append(summarize(full, spiller.pointer(ident)))
    rendered = "[" + ", ".join(json.dumps(item, ensure_ascii=False) for item in next_values) + "]"
    return re.sub(
        r"^route_history:\s*\[.*\]\s*(?:#.*)?$",
        f"route_history: {rendered}  # re-route ≤10, item ≤160B",
        content,
        count=1,
        flags=re.M,
    )


def enforce_bullet_section(content: str, heading: str, spill_prefix: str, spiller: Spiller) -> str:
    match = re.search(
        rf"^({re.escape(heading)}[^\n]*\n)([\s\S]*?)(?=^## |\Z)",
        content,
        re.M,
    )
    if not match:
        return content
    header, body = match.group(1), match.group(2)
    prefix: list[str] = []
    items: list[str] = []
    suffix: list[str] = []
    seen = False
    for line in body.split("\n"):
        if re.match(r"^\s*-\s+", line):
            seen = True
            items.append(re.sub(r"^\s*-\s+", "", line))
        elif not seen:
            prefix.append(line)
        else:
            suffix.append(line)
    overflow_count = max(0, len(items) - LIST_MAX)
    keep_count = LIST_MAX - 1 if overflow_count else LIST_MAX
    keep, extra = items[:keep_count], items[keep_count:]
    archive_id = ""
    if extra:
        archive_id = spiller.spill(
            spill_prefix,
            "\n\n".join(f"### archived-{i}\n{item}" for i, item in enumerate(extra)),
        )
    out = []
    for full in keep:
        if byte_len(full) <= ITEM_MAX_BYTES:
            out.append(f"- {full}")
            continue
        if "index-overflow.md#" in full:
            out.append(f"- {utf8_prefix(full, ITEM_MAX_BYTES)}")
            continue
        ident = spiller.spill(spill_prefix, full)
        out.append(f"- {summarize(full, spiller.pointer(ident))}")
    if archive_id:
        label = heading.replace("## ", "").split()[0]
        out.append(f"- older {label} →{spiller.pointer(archive_id)}")
    new_body = "\n".join([*prefix, *out, *suffix])
    return content[: match.start()] + header + new_body + content[match.end():]


def enforce_index_bounds(content: str, ai_state: Path) -> str:
    spiller = Spiller(ai_state, read_slug(content))
    next_content = enforce_route_history(content, spiller)
    next_content = enforce_bullet_section(next_content, "## 当前状态", "st", spiller)
    next_content = enforce_bullet_section(next_content, "## 历史", "hi", spiller)
    spiller.flush()
    return next_content

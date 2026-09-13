#!/usr/bin/env python3
"""Opt-in LLM-as-a-Verifier ranking. Never a ship gate or PASS/FAIL verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


SCORE_RE = re.compile(r"SCORE\s*=\s*(\d{1,2})")
DEFAULT_MODEL = "gpt-4.1-mini"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, action="append", dest="candidates", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--index", type=Path, default=Path(".ai_state/_index.md"))
    return parser.parse_args()


def enabled(index: Path) -> bool:
    if os.environ.get("ATHENA_LAAV_FORCE") == "1":
        return True
    if not index.is_file():
        return False
    text = index.read_text(encoding="utf-8")
    return bool(re.search(r"(?m)^laav_enabled:\s*true\b", text))


def write_result(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def skip(output: Path, reason: str, packet_sha: str, ranked: list | None = None) -> int:
    write_result(
        output,
        {
            "schema_version": 1,
            "status": "skipped",
            "reason": reason,
            "packet_sha256": packet_sha,
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "backend": {
                "base_url_host": urlparse(os.environ.get("ATHENA_LAAV_BASE_URL", "")).hostname or "",
                "model": os.environ.get("ATHENA_LAAV_MODEL", DEFAULT_MODEL),
                "logprobs": False,
            },
            "ranked": ranked or [],
        },
    )
    print(f"laav skipped: {reason}")
    return 0


def token_score(token: str) -> int | None:
    text = token.strip()
    if text.isdigit():
        value = int(text)
        return value if 1 <= value <= 20 else None
    if len(text) == 1 and "A" <= text.upper() <= "T":
        return ord(text.upper()) - ord("A") + 1
    return None


def expected_score(logprobs: dict) -> tuple[float | None, str | None]:
    """Expected score from logprobs only. Missing alternatives are unscored, not a discrete fallback."""
    content = logprobs.get("content") or []
    blob = "".join(str(item.get("token", "")) for item in content)
    match = SCORE_RE.search(blob)
    letter = re.search(r"SCORE\s*=\s*([A-Ta-t])\b", blob)
    target = match.group(1) if match else (letter.group(1) if letter else None)
    if not target:
        return None, None
    token_blob = ""
    for item in content:
        token_blob += str(item.get("token", ""))
        if target not in token_blob:
            continue
        top = item.get("top_logprobs") or []
        total = 0.0
        weighted = 0.0
        for alt in top:
            value = token_score(str(alt.get("token", "")))
            if value is None:
                continue
            prob = math.exp(float(alt.get("logprob", -99)))
            weighted += value * prob
            total += prob
        if total <= 0:
            return None, None
        return weighted / total, target
    return None, None


def complete(base_url: str, api_key: str, model: str, prompt: str) -> dict:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "max_tokens": 8,
            "logprobs": True,
            "top_logprobs": 5,
            "messages": [
                {
                    "role": "system",
                    "content": "Score the candidate against the rubric. Reply with only SCORE=<integer 1-20>.",
                },
                {"role": "user", "content": prompt},
            ],
        }
    ).encode()
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60, context=ssl.create_default_context()) as response:
        return json.loads(response.read().decode())


def main() -> int:
    args = parse_args()
    packet = args.packet.read_text(encoding="utf-8")
    packet_sha = sha256_text(packet)
    candidates = args.candidates
    if not enabled(args.index):
        return skip(args.output, "disabled", packet_sha)
    if len(candidates) < 2:
        return skip(args.output, "need_two_candidates", packet_sha)
    base_url = os.environ.get("ATHENA_LAAV_BASE_URL", "").strip()
    api_key = os.environ.get("ATHENA_LAAV_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    model = os.environ.get("ATHENA_LAAV_MODEL", DEFAULT_MODEL)
    if not base_url or not api_key:
        return skip(args.output, "not_configured", packet_sha)

    ranked = []
    saw_logprobs = False
    try:
        for path in candidates:
            diff = path.read_text(encoding="utf-8", errors="replace")[:12000]
            prompt = "Rubric (Done checks):\n" + packet[:8000] + "\n\nCandidate diff:\n" + diff
            data = complete(base_url, api_key, model, prompt)
            choice = (data.get("choices") or [{}])[0]
            logprobs = (choice.get("logprobs") or {}) if isinstance(choice, dict) else {}
            score, token = expected_score(logprobs) if logprobs else (None, None)
            if logprobs.get("content"):
                saw_logprobs = True
            ranked.append(
                {
                    "id": path.stem,
                    "path": str(path),
                    "expected_score": score,
                    "raw_score_token": token,
                    "unscored_reason": None if score is not None else "logprobs_unavailable",
                }
            )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError, OSError):
        return skip(args.output, "backend_error", packet_sha)

    scored = [row for row in ranked if row["expected_score"] is not None]
    if not saw_logprobs or not scored:
        return skip(args.output, "logprobs_unavailable", packet_sha, ranked)

    ranked.sort(key=lambda row: (-1 if row["expected_score"] is None else -float(row["expected_score"])))
    write_result(
        args.output,
        {
            "schema_version": 1,
            "status": "ranked",
            "reason": "logprob_expected_score",
            "packet_sha256": packet_sha,
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "backend": {
                "base_url_host": urlparse(base_url).hostname or "",
                "model": model,
                "logprobs": True,
            },
            "ranked": ranked,
        },
    )
    print("laav ranked " + ", ".join(row["id"] for row in ranked))
    return 0


if __name__ == "__main__":
    sys.exit(main())

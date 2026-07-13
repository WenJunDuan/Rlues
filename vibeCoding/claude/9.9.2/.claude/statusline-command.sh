#!/usr/bin/env bash
set -euo pipefail

payload="$(cat)"

STATUSLINE_PAYLOAD="$payload" python3 - <<'PY'
import json
import os
import subprocess
import sys


def read_payload():
    try:
        return json.loads(os.environ.get("STATUSLINE_PAYLOAD") or "{}")
    except Exception:
        return {}


def first_text(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


data = read_payload()
model = data.get("model") if isinstance(data.get("model"), dict) else {}
workspace = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
context = data.get("context_window") if isinstance(data.get("context_window"), dict) else {}

cwd = first_text(workspace.get("current_dir"), data.get("cwd"), os.getcwd())
project = os.path.basename(cwd.rstrip(os.sep)) if cwd else ""
display_model = first_text(model.get("display_name"), model.get("id"), str(data.get("model") or "Claude"))

branch = ""
if cwd:
    try:
        branch = subprocess.check_output(
            ["git", "-C", cwd, "branch", "--show-current"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=0.25,
        ).strip()
    except Exception:
        branch = ""

context_label = ""
used_percentage = context.get("used_percentage")
try:
    if used_percentage is not None:
        context_label = f"{float(used_percentage):.0f}% ctx"
except Exception:
    context_label = ""

parts = ["Athena", display_model]
for value in (project, branch, context_label):
    if value:
        parts.append(value)

sys.stdout.write(" | ".join(parts) + "\n")
PY

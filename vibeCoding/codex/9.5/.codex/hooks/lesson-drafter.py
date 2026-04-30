#!/usr/bin/env python3
"""
VibeCoding PostToolUse hook (Codex)

工具失败 → 自动起草 ~/.codex/lessons/draft-*.md
触发条件: exit_code != 0 + permission denied 字样 + spawn_agent 放弃信号
输出: 写文件副作用, 不阻塞工作流 (无 stdout JSON)

安全: cmd / blob 写盘前过 redact (token/secret/key 脱敏, v9.4.5-hotfix 修复)
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# redact 工具 (同目录的 _redact.py)
sys.path.insert(0, str(Path(__file__).parent))
from _redact import redact


FAILURE_PATTERNS = [
    (re.compile(r"permission\s+(denied|to use Bash has been denied)", re.IGNORECASE), "permission"),
    (re.compile(r"command\s+not\s+found", re.IGNORECASE), "tool-missing"),
    (re.compile(r"无\s*Bash\s*工具", re.IGNORECASE), "subagent-bash"),
    (re.compile(r"请\s*(您|你)\s*(直接|手动)", re.IGNORECASE), "lazy-fallback"),
    (re.compile(r"Hook JSON output validation failed", re.IGNORECASE), "hook-schema"),
    (re.compile(r"sandbox\s+(violation|denied|blocked)", re.IGNORECASE), "sandbox-block"),
    (re.compile(r"spawn_agent\s+(failed|error)", re.IGNORECASE), "spawn-fail"),
    (re.compile(r"agent_runtime_error", re.IGNORECASE), "agent-runtime"),
    (re.compile(r"approval_policy", re.IGNORECASE), "approval-flow"),
]


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    blob_parts = []
    for k in ("tool_response", "tool_output", "stderr"):
        v = event.get(k)
        if v is None:
            continue
        if isinstance(v, str):
            blob_parts.append(v)
        else:
            blob_parts.append(json.dumps(v))

    blob = "\n".join(blob_parts)
    if not blob.strip():
        sys.exit(0)

    hit = next(((p, t) for p, t in FAILURE_PATTERNS if p.search(blob)), None)
    if not hit:
        sys.exit(0)

    pattern, topic = hit

    home = Path.home()
    lessons_dir = home / ".codex" / "lessons"
    lessons_dir.mkdir(parents=True, exist_ok=True)
    (lessons_dir / "archive").mkdir(exist_ok=True)

    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    fname = lessons_dir / f"draft-{date}-{topic}-{time_str}.md"

    # 取项目状态
    project_info = ""
    try:
        sd = Path(os.environ.get("PWD") or os.getcwd()) / ".ai_state"
        p = json.loads((sd / "project.json").read_text(encoding="utf-8"))
        if p.get("path"):
            project_info = f"{p['path']}/{p.get('stage', '-')}/sprint{p.get('sprint', 0)}"
    except Exception:
        pass

    tool_name = event.get("tool_name", "unknown")
    cmd_raw = ""
    if event.get("tool_input"):
        cmd_raw = (event["tool_input"].get("command", "") if isinstance(event["tool_input"], dict) else "")
    cmd = redact(cmd_raw)
    blob_short_raw = blob[:2000] + ("\n...(truncated)" if len(blob) > 2000 else "")
    blob_short = redact(blob_short_raw)

    content = f"""---
date: {date}
context: {topic}
severity: warning
status: unresolved
auto_drafted: true
session_id: {event.get('session_id', 'unknown')}
project: {project_info or '-'}
platform: codex
---

# 自动起草: {topic} 触发 (Codex)

## 触发场景

- 工具: {tool_name}
- 命令/参数: `{cmd[:200]}`
- 时间: {now.isoformat()}
- 当前 PACE: {project_info or '(无)'}

## 完整输出

```
{blob_short}
```

## 现象
<!-- 用户补全: 看到的具体行为 -->

## 根因
<!-- 用户补全 / 待 Codex 后续调研 -->

## 已尝试方案
<!-- 用户补全 -->

## 当前 workaround
<!-- 用户补全 -->

## 相关
- VibeCoding 版本: 9.4.5-codex
- 用 /lesson-curator 审阅本 draft 后改名落档 (改成 {date}-{{slug}}.md 格式)
- 7 天未确认会自动归档到 archive/
"""

    try:
        fname.write_text(content, encoding="utf-8")
        sys.stderr.write(f"[lesson-drafter] 起草: {fname.name} ({topic})\n")

        try:
            sd = Path(os.environ.get("PWD") or os.getcwd()) / ".ai_state"
            if sd.exists():
                line = json.dumps({
                    "ts": now.isoformat(),
                    "hook": "lesson-drafter",
                    "topic": topic,
                    "draft": fname.name,
                }) + "\n"
                with open(sd / "hook-trace.jsonl", "a") as f:
                    f.write(line)
        except Exception:
            pass
    except Exception as e:
        sys.stderr.write(f"[lesson-drafter] 起草失败: {e}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()

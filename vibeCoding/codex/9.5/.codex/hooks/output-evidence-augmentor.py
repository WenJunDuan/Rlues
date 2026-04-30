#!/usr/bin/env python3
"""
VibeCoding output-evidence-augmentor (Codex v9.5)
PostToolUse hook, 改写当前 tool 输出 (updatedToolOutput)
策略与 CC 端一致: ring buffer + review 阶段 + Edit 类工具
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


HOME = Path.home()
STATE_DIR = HOME / '.codex' / 'state'
RING_FILE = STATE_DIR / 'recent-tool-uses.jsonl'
RING_SIZE = 50


def append_ring(entry):
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with RING_FILE.open('a') as f:
            f.write(json.dumps(entry) + '\n')
        lines = RING_FILE.read_text(encoding='utf-8').split('\n')
        lines = [l for l in lines if l]
        if len(lines) > RING_SIZE:
            RING_FILE.write_text('\n'.join(lines[-RING_SIZE:]) + '\n', encoding='utf-8')
    except Exception:
        pass


def read_ring():
    try:
        lines = RING_FILE.read_text(encoding='utf-8').split('\n')
        out = []
        for l in lines:
            if not l:
                continue
            try:
                out.append(json.loads(l))
            except Exception:
                pass
        return out
    except Exception:
        return []


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = event.get('tool_name', 'unknown')
    response = event.get('tool_response', '')
    response_str = response if isinstance(response, str) else json.dumps(response)
    has_error = bool(re.search(r'error|fail', response_str, flags=re.IGNORECASE))
    is_subagent = bool(re.search(r'spawn|agent|skill|task|reviewer|evaluator|generator',
                                 tool, flags=re.IGNORECASE))

    append_ring({
        'ts': datetime.now(timezone.utc).isoformat(),
        'tool': tool,
        'has_error': has_error,
        'is_subagent_tool': is_subagent,
    })

    # Codex 端 Edit 等价是 apply_patch / write_file / edit_file
    if not re.search(r'apply_patch|write|edit', tool, flags=re.IGNORECASE):
        sys.exit(0)

    project_dir = Path(os.environ.get('PWD') or os.getcwd())
    sd = project_dir / '.ai_state'
    project_json = sd / 'project.json'
    if not project_json.is_file():
        sys.exit(0)

    try:
        p = json.loads(project_json.read_text(encoding='utf-8'))
    except Exception:
        sys.exit(0)

    if p.get('stage') != 'review':
        sys.exit(0)
    if p.get('path') not in ('Feature', 'Refactor', 'System'):
        sys.exit(0)

    ring = read_ring()
    recent = ring[-30:]
    has_reviewer_evidence = any(e.get('is_subagent_tool') for e in recent)
    if has_reviewer_evidence:
        sys.exit(0)

    augmented = response_str + (
        '\n\n---\n'
        '💡 Hermes 提示 (review 阶段证据检查):\n'
        f'本次 {tool} 在 review 阶段执行, 但近 30 个 tool_use 中未见 spawn_agent reviewer 调用记录。\n'
        f'路径 "{p.get("path", "")}" 要求外部审查 (Feature+ 必须). 完成度证据要求 (AGENTS.md): '
        '跨 worker 审查必须有 child agent thread ID + report_agent_job_result 输出。\n'
        '建议: 完成本次操作后 spawn_agent reviewer 跑一次, 再写入 reviews/sprint-N.md。\n'
        '此提示是 hint, 不阻止当前 tool 执行。'
    )

    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'PostToolUse',
            'updatedToolOutput': augmented,
        }
    }))
    sys.stderr.write(f'[output-evidence-augmentor] review 阶段 {tool} 缺 reviewer 证据, 已追加提示\n')
    sys.exit(0)


if __name__ == '__main__':
    main()

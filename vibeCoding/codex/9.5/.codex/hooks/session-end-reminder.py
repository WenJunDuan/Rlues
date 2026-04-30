#!/usr/bin/env python3
"""
VibeCoding session-end-reminder (Codex)

注: Codex 当前没有 SessionEnd hook (单事件 notification 系统). 
本 hook 不在 Codex 端注册到独立事件, 由 Stop hook 在 sprint 完成时 (stage="ship") 调用以达到等价效果。
保留此文件作为脚本可被其他 hook include。
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    project_dir = Path(os.environ.get('PWD') or os.getcwd())
    sd = project_dir / '.ai_state'
    if not (sd / 'project.json').is_file():
        return

    try:
        p = json.loads((sd / 'project.json').read_text(encoding='utf-8'))
    except Exception:
        return

    if not p.get('path') or not p.get('stage'):
        return

    # 检查 tasks.md 完成数
    done_count = 0
    try:
        t = (sd / 'tasks.md').read_text(encoding='utf-8')
        done_count = len([l for l in t.split('\n') if l.startswith('- [x]')])
    except Exception:
        pass

    # 检查 git 未提交修改
    has_uncommitted = False
    try:
        r = subprocess.run(['git', 'status', '--porcelain'],
                         capture_output=True, text=True, timeout=5,
                         cwd=str(project_dir))
        has_uncommitted = bool(r.stdout.strip())
    except Exception:
        pass

    if done_count > 0 and has_uncommitted:
        msg = (f"Sprint {p.get('sprint', 0)} 已完成 {done_count} 个 task, "
               f"但有未提交修改。建议: git status → 检查 → git commit (铁律 5)。")
        sys.stderr.write(f"[session-end-reminder] {done_count} done, uncommitted\n")
        print(json.dumps({'systemMessage': 'VibeCoding: ' + msg}))


if __name__ == '__main__':
    main()

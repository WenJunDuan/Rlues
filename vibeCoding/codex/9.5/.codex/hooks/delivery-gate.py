#!/usr/bin/env python3
"""
VibeCoding delivery-gate v9.5 (Codex)

升级: 状态机硬化, 全 stage 转换条件检查 (不止 review→ship)

Codex Stop hook 协议:
- {"continue": false, "stopReason": "..."} → 让 Codex 用 reason 作为新 prompt 继续
- {"systemMessage": "..."} → soft warn
- 无输出 → 放行
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# === 状态机转换规则 ===
STAGE_EXIT_RULES = {
    'plan': {
        'require': [
            {'check': 'file', 'target': 'design.md'},
            {'check': 'file', 'target': 'tasks.md'},
            {'check': 'has-pending-task', 'desc': 'tasks.md 没有 - [ ] 待办'},
            {'check': 'has-section', 'target': 'design.md', 'section': 'File Structure Plan',
             'desc': 'design.md 缺 ## File Structure Plan 段'},
            {'check': 'scenario-conditional', 'scenario': 'modify-existing', 'target': 'change-plan.md',
             'desc': 'modify-existing 场景: change-plan.md 必须存在 (图 06: 改已有项目先勘察)'},
        ],
    },
    'design': {
        'require': [
            {'check': 'file', 'target': 'design.md'},
            {'check': 'has-section', 'target': 'design.md', 'section': 'File Structure Plan'},
            {'check': 'file', 'target': 'tasks.md'},
            {'check': 'tasks-have-boundary', 'desc': 'tasks.md 中 task 缺 _Boundary:_ 标注 (cc-sdd 边界优先)'},
        ],
    },
    'impl': {
        'require': [
            {'check': 'all-tasks-done', 'desc': 'tasks.md 还有 - [ ] 待办未完成'},
            {'check': 'has-progress', 'desc': 'progress.md 没有本 sprint 的记录'},
        ],
    },
    'review': {
        'require': [
            {'check': 'review-report', 'desc': 'reviews/sprint-N.md 不存在'},
            {'check': 'review-has-test', 'desc': '审查报告无测试通过记录'},
            {'check': 'review-has-external', 'desc': 'Feature+ 路径审查报告缺外部审查 (codex/reviewer)'},
            {'check': 'verdict-ok', 'desc': 'VERDICT 不是 PASS 或 CONCERNS'},
        ],
    },
}


def trace(sd, event_dict):
    try:
        line = json.dumps({
            'ts': datetime.now(timezone.utc).isoformat(),
            'hook': 'delivery-gate',
            **event_dict,
        }) + '\n'
        (sd / 'hook-trace.jsonl').open('a').write(line)
    except Exception:
        pass


def safe_read(p):
    try:
        return Path(p).read_text(encoding='utf-8')
    except Exception:
        return None


def check_rule(rule, project, sd):
    sprint = project.get('sprint', 0)
    c = rule['check']
    if c == 'file':
        return (sd / rule['target']).exists()
    if c == 'has-pending-task':
        t = safe_read(sd / 'tasks.md') or ''
        return bool(re.search(r'^- \[ \]', t, flags=re.MULTILINE))
    if c == 'all-tasks-done':
        t = safe_read(sd / 'tasks.md') or ''
        pending = len(re.findall(r'^- \[ \]', t, flags=re.MULTILINE))
        return pending == 0
    if c == 'has-section':
        t = safe_read(sd / rule['target']) or ''
        return bool(re.search(r'^##+\s+' + re.escape(rule['section']), t, flags=re.MULTILINE | re.IGNORECASE))
    if c == 'has-progress':
        t = safe_read(sd / 'progress.md') or ''
        return bool(re.search(rf'sprint/{sprint}|/sprint{sprint}|sprint {sprint}', t, flags=re.IGNORECASE))
    if c == 'tasks-have-boundary':
        t = safe_read(sd / 'tasks.md') or ''
        task_lines = re.findall(r'^- \[[ x]\] Task', t, flags=re.MULTILINE)
        if not task_lines:
            return True
        return bool(re.search(r'_Boundary:_', t, flags=re.IGNORECASE))
    if c == 'review-report':
        return (sd / 'reviews' / f'sprint-{sprint}.md').exists()
    if c == 'review-has-test':
        r = safe_read(sd / 'reviews' / f'sprint-{sprint}.md') or ''
        return bool(re.search(r'test|测试|pass|通过|✅', r, flags=re.IGNORECASE))
    if c == 'review-has-external':
        path_val = project.get('path', '')
        if path_val not in ('Feature', 'Refactor', 'System'):
            return True
        r = safe_read(sd / 'reviews' / f'sprint-{sprint}.md') or ''
        return bool(re.search(
            r'/codex:review|/codex:adversarial|adversarial|ecc-agentshield|reviewer|codex unavailable|review unavailable',
            r, flags=re.IGNORECASE,
        ))
    if c == 'verdict-ok':
        r = safe_read(sd / 'reviews' / f'sprint-{sprint}.md') or ''
        m = re.search(r'VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)', r, flags=re.IGNORECASE)
        if not m:
            return False
        v = m.group(1).upper()
        return v in ('PASS', 'CONCERNS')
    if c == 'scenario-conditional':
        if project.get('scenario') != rule['scenario']:
            return True
        return (sd / rule['target']).exists()
    return True


def describe_rule(rule):
    if 'desc' in rule:
        return rule['desc']
    if rule['check'] == 'file':
        return f"{rule['target']} 不存在"
    return rule['check']


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}

    if event.get('stop_hook_active'):
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

    path_val = p.get('path', '')
    stage = p.get('stage', '')

    if path_val in ('Hotfix', 'Bugfix') or not stage:
        sys.exit(0)

    rules = STAGE_EXIT_RULES.get(stage)
    if not rules:
        sys.exit(0)

    failed = []
    for rule in rules['require']:
        if not check_rule(rule, p, sd):
            failed.append(describe_rule(rule))

    if not failed:
        # review 阶段额外 lessons 提醒
        if stage == 'review':
            lm = safe_read(sd / 'lessons.md') or ''
            compounded = bool(re.search(rf'Sprint {p.get("sprint", 0)}\b', lm))
            if not compounded:
                msg = f"⚠ Sprint {p.get('sprint', 0)} 通过但 lessons.md 无条目, 建议运行 $compound 沉淀经验 (铁律 7)"
                sys.stderr.write(f"[delivery-gate] review->ship soft-warn: {msg}\n")
                trace(sd, {'action': 'soft-warn', 'path': path_val, 'stage': stage,
                          'sprint': p.get('sprint', 0), 'reason': 'no compound'})
                print(json.dumps({'systemMessage': f'VibeCoding: {msg}'}))
                sys.exit(0)
        sys.stderr.write(f"[delivery-gate] {path_val}/{stage} 出口检查通过\n")
        trace(sd, {'action': 'pass', 'path': path_val, 'stage': stage, 'sprint': p.get('sprint', 0)})
        sys.exit(0)

    # 失败 → block
    reason = (
        f"[delivery-gate] {path_val}/{stage} 阶段出口条件未满足:\n"
        + '\n'.join(f'  • {f}' for f in failed)
        + '\n\n请修复以上问题后再交付。如确认本阶段已完成, 检查 .ai_state/ 文件是否齐全。'
    )

    sys.stderr.write(f"[delivery-gate] BLOCK {path_val}/{stage}: {', '.join(failed)}\n")
    trace(sd, {'action': 'block', 'path': path_val, 'stage': stage,
              'sprint': p.get('sprint', 0), 'failed': failed})

    print(json.dumps({
        'continue': False,
        'stopReason': reason,
    }))
    sys.exit(0)


if __name__ == '__main__':
    main()

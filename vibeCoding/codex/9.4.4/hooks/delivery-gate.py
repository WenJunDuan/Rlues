#!/usr/bin/env python3
"""
VibeCoding Stop hook — delivery-gate 质量门。
在 stage=review 且不是 Hotfix 时, 检查:
  - tasks.md 是否全部完成
  - reviews/sprint-N.md 是否存在
  - Feature+ 是否有 /review 或 reviewer 记录
  - 是否有测试通过记录
  - VERDICT 状态 (REWORK/FAIL → 阻断; CONCERNS → 提示; PASS → 检查 lessons)

Codex Stop hook 协议:
- stdout JSON with {"continue": false, "stopReason": "..."} → 阻止 turn 结束, agent 继续
- stdout JSON with {"systemMessage": "..."} → 显示系统消息
- exit 0 = 放行
"""
import json
import os
import re
import sys
from pathlib import Path


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}

    # 官方 Stop hook 支持 stop_hook_active 标志防递归
    if event.get("stop_hook_active"):
        sys.exit(0)

    project_dir = Path(os.environ.get("PWD") or os.getcwd())
    state_dir = project_dir / ".ai_state"
    project_json_path = state_dir / "project.json"

    if not project_json_path.is_file():
        sys.exit(0)

    try:
        p = json.loads(project_json_path.read_text(encoding="utf-8"))
    except Exception:
        sys.exit(0)

    sprint = p.get("sprint")
    stage = p.get("stage")
    path = p.get("path")

    # 只在 review 阶段 + 非 Hotfix + 有 sprint 时检查
    if not sprint or not stage or path == "Hotfix" or stage != "review":
        sys.exit(0)

    issues = []
    needs_ext_review = path in ("Feature", "Refactor", "System")

    # 1. tasks.md 全部完成
    tasks_md = state_dir / "tasks.md"
    if tasks_md.is_file():
        tasks_text = tasks_md.read_text(encoding="utf-8")
        pending_count = len(re.findall(r"^- \[ \]", tasks_text, flags=re.MULTILINE))
        if pending_count > 0:
            issues.append(f"{pending_count} Task 未完成")
    else:
        issues.append("tasks.md 不存在")

    # 2. reviews/sprint-N.md 存在
    review_file = state_dir / "reviews" / f"sprint-{sprint}.md"
    review_content = ""
    if review_file.is_file():
        review_content = review_file.read_text(encoding="utf-8")
    else:
        issues.append("审查报告不存在")

    # 3. Feature+ 必须有外部审查记录
    if needs_ext_review and review_content and not re.search(
        r"/review|reviewer|\[agents\.reviewer\]|adversarial|ecc-agentshield",
        review_content,
        flags=re.IGNORECASE,
    ):
        issues.append("无外部审查记录 (缺 /review 或 reviewer subagent)")

    # 4. 测试通过记录
    if review_content and not re.search(
        r"test|测试|pass|通过|✅", review_content, flags=re.IGNORECASE
    ):
        issues.append("无测试通过记录")

    # 5. VERDICT 检查
    verdict = ""
    if review_content:
        m = re.search(
            r"VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)",
            review_content,
            flags=re.IGNORECASE,
        )
        if m:
            verdict = m.group(1).upper()
            if verdict == "REWORK":
                issues.append("VERDICT=REWORK")
            elif verdict == "FAIL":
                issues.append("VERDICT=FAIL")
            elif verdict == "CONCERNS":
                sys.stderr.write(
                    "[delivery-gate] CONCERNS: 建议修复后重新评分\n"
                )

    # 有阻断问题 → continue=false, 让 agent 继续处理
    if issues:
        issue_list = "\n".join(f"• {i}" for i in issues)
        sys.stderr.write(
            f"[delivery-gate] 阻断 {path}/{stage}: {', '.join(issues)}\n"
        )
        print(json.dumps({
            "continue": False,
            "stopReason": f"[delivery-gate] 阻断:\n{issue_list}\n\n修复后再交付。",
            "systemMessage": f"VibeCoding delivery-gate 阻断了本次交付 ({path}/{stage}):\n{issue_list}",
        }))
        sys.exit(0)

    # VERDICT=PASS → 检查是否沉淀了本 sprint 的 lesson (soft warn, 不阻塞)
    if verdict == "PASS":
        compounded = False
        lessons_md = state_dir / "lessons.md"
        if lessons_md.is_file():
            try:
                lessons_text = lessons_md.read_text(encoding="utf-8")
                compounded = f"Sprint {sprint}" in lessons_text
            except Exception:
                pass
        if not compounded:
            msg = (
                f"⚠ Sprint {sprint} 通过但 lessons.md 未沉淀, "
                f"建议运行 $compound 提炼经验 (铁律 7)"
            )
            sys.stderr.write(
                f"[delivery-gate] PASS {path}/{stage} · {msg}\n"
            )
            # soft warn: 只用 systemMessage, 不 continue=false
            print(json.dumps({"systemMessage": f"VibeCoding: {msg}"}))
        else:
            sys.stderr.write(
                f"[delivery-gate] PASS {path}/{stage} · lessons ✓\n"
            )
    else:
        sys.stderr.write(f"[delivery-gate] 放行 {path}/{stage}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()

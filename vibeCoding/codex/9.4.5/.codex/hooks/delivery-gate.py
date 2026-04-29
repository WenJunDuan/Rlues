#!/usr/bin/env python3
"""
VibeCoding Stop hook (Codex)

stage="review" + 非 Hotfix 时检查质量门:
  - tasks.md 是否全部完成
  - reviews/sprint-N.md 是否存在
  - Feature+ 是否有 /review 或 reviewer 记录
  - 是否有测试通过记录
  - VERDICT 状态

Codex Stop hook 协议:
- exit 0 + JSON {"continue":false, "stopReason":"..."} → 让 Codex 用 reason 作为新 prompt 继续一轮
  (这正好是 VibeCoding 要的"喂修复指令")
- {"systemMessage":"..."} → soft warn
- exit 0 + 无输出 → 放行
- stop_hook_active=true 时立即 exit 防递归
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def trace(sd, event_dict):
    try:
        line = json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "hook": "delivery-gate",
            **event_dict,
        }) + "\n"
        (sd / "hook-trace.jsonl").open("a").write(line)
    except Exception:
        pass


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}

    if event.get("stop_hook_active"):
        sys.exit(0)

    project_dir = Path(os.environ.get("PWD") or os.getcwd())
    sd = project_dir / ".ai_state"
    project_json_path = sd / "project.json"

    if not project_json_path.is_file():
        sys.exit(0)

    try:
        p = json.loads(project_json_path.read_text(encoding="utf-8"))
    except Exception:
        sys.exit(0)

    sprint = p.get("sprint")
    stage = p.get("stage")
    path = p.get("path")

    if not sprint or not stage or path == "Hotfix" or stage != "review":
        sys.exit(0)

    issues = []
    needs_ext_review = path in ("Feature", "Refactor", "System")

    # 1. tasks 全完成
    tasks_md = sd / "tasks.md"
    if tasks_md.is_file():
        t = tasks_md.read_text(encoding="utf-8")
        pending = len(re.findall(r"^- \[ \]", t, flags=re.MULTILINE))
        if pending > 0:
            issues.append(f"{pending} Task 未完成")
    else:
        issues.append("tasks.md 不存在")

    # 2. reviews/sprint-N.md
    review_file = sd / "reviews" / f"sprint-{sprint}.md"
    rc = ""
    if review_file.is_file():
        rc = review_file.read_text(encoding="utf-8")
    else:
        issues.append("审查报告不存在")

    # 3. Feature+ 外部审查
    if needs_ext_review and rc and not re.search(
        r"/review|reviewer|spawn_agent|adversarial|ecc-agentshield|unavailable",
        rc, flags=re.IGNORECASE,
    ):
        issues.append("无外部审查记录 (缺 /review 或 reviewer subagent)")

    # 4. 测试通过记录
    if rc and not re.search(r"test|测试|pass|通过|✅", rc, flags=re.IGNORECASE):
        issues.append("无测试通过记录")

    # 5. VERDICT
    verdict = ""
    if rc:
        m = re.search(r"VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)", rc, flags=re.IGNORECASE)
        if m:
            verdict = m.group(1).upper()
            if verdict == "REWORK":
                issues.append("VERDICT=REWORK")
            elif verdict == "FAIL":
                issues.append("VERDICT=FAIL")
            elif verdict == "CONCERNS":
                sys.stderr.write("[delivery-gate] CONCERNS: 建议修复后重新评分\n")

    if issues:
        issue_list = "\n".join(f"• {i}" for i in issues)
        sys.stderr.write(
            f"[delivery-gate] 要求继续修复 {path}/{stage}: {', '.join(issues)}\n"
        )
        trace(sd, {"action": "block", "path": path, "stage": stage, "sprint": sprint, "issues": issues})
        # Codex Stop: continue:false + stopReason → 让 Codex 用 reason 作为新 prompt 继续
        print(json.dumps({
            "continue": False,
            "stopReason": (
                f"delivery-gate 检查未通过, 继续修复:\n{issue_list}\n\n"
                f"修复完成后重新跑测试和 /review, 然后更新 .ai_state/reviews/sprint-{sprint}.md。"
            ),
            "systemMessage": (
                f"VibeCoding delivery-gate 阻断本次交付 ({path}/{stage}):\n{issue_list}"
            ),
        }))
        sys.exit(0)

    # PASS → 检查 lessons
    if verdict == "PASS":
        compounded = False
        lm = sd / "lessons.md"
        if lm.is_file():
            try:
                compounded = f"Sprint {sprint}" in lm.read_text(encoding="utf-8")
            except Exception:
                pass
        if not compounded:
            msg = f"⚠ Sprint {sprint} 通过但 lessons.md 未沉淀, 建议运行 $compound 提炼经验 (铁律 7)"
            sys.stderr.write(f"[delivery-gate] PASS {path}/{stage} · {msg}\n")
            trace(sd, {"action": "soft-warn", "path": path, "stage": stage, "sprint": sprint, "reason": "no compound"})
            print(json.dumps({"systemMessage": f"VibeCoding: {msg}"}))
        else:
            sys.stderr.write(f"[delivery-gate] PASS {path}/{stage} · lessons ✓\n")
            trace(sd, {"action": "pass", "path": path, "stage": stage, "sprint": sprint})
    else:
        sys.stderr.write(f"[delivery-gate] 放行 {path}/{stage}\n")
        trace(sd, {"action": "pass", "path": path, "stage": stage, "sprint": sprint, "verdict": verdict})

    sys.exit(0)


if __name__ == "__main__":
    main()

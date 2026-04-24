#!/usr/bin/env python3
"""
VibeCoding Stop hook — delivery-gate 质量门。
在 stage=review 且不是 Hotfix 时, 检查:
  - tasks.md 是否全部完成
  - reviews/sprint-N.md 是否存在
  - Feature+ 是否有 /review 或 reviewer 记录
  - 是否有测试通过记录
  - VERDICT 状态 (REWORK/FAIL → 阻断; CONCERNS → 提示; PASS → 检查 lessons)

Codex Stop hook 官方协议 (与 CC 不同):
- exit 0 时 stdout 必须是 JSON (plain text 无效)
- {"decision":"block","reason":"..."} → 让 Codex 用 reason 作为新 prompt 继续一轮
  这**不是拒绝交付**, 而是"自动喂 Codex 修复指令继续干"——契合 VibeCoding 语义
- {"continue":false,"stopReason":"..."} → 标记这次 hook 运行停止 (不是阻止 agent)
- {"systemMessage":"..."} → 作为系统消息显示
- stop_hook_active=true 时立即 exit 防递归
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

    # 防递归: 上一轮 Stop hook 已经让 Codex 继续了, 这次不要再拦
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

    # 有阻断问题 → decision:block, Codex 会用 reason 作为新 prompt 继续一轮
    # 语义: "喂一条修复指令给 Codex 继续干"——正好是 VibeCoding 要的
    if issues:
        issue_list = "\n".join(f"• {i}" for i in issues)
        sys.stderr.write(
            f"[delivery-gate] 要求继续修复 {path}/{stage}: {', '.join(issues)}\n"
        )
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"delivery-gate 检查未通过, 继续修复:\n{issue_list}\n\n"
                f"修复完成后重新跑一次测试和 /review, 然后更新 .ai_state/reviews/sprint-{sprint}.md。"
            ),
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
            # soft warn: systemMessage 显示为警告, 不阻止 Codex 结束 turn
            print(json.dumps({"systemMessage": f"VibeCoding: {msg}"}))
        else:
            sys.stderr.write(
                f"[delivery-gate] PASS {path}/{stage} · lessons ✓\n"
            )
            # exit 0 无输出 = 放行 (Stop hook 可以接受 exit 0 + 无 JSON, 但官方说"plain text invalid"
            # 所以最安全是输出 {} 或不输出; 实测无输出也能 work)
    else:
        sys.stderr.write(f"[delivery-gate] 放行 {path}/{stage}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Stop 阻断熔断器行为矩阵测试 (design §10.1 / AC16).

端到端: 把 delivery-gate.py 当子进程跑, 喂真实 hook payload, 断言 stdout 的 decision:block
与 stderr 的 ESCALATED, 以及 stop-failures.jsonl 的记录形状。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GATE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent / "delivery-gate.py"
RUNNER = ["node", str(GATE)] if GATE.suffix == ".cjs" else [sys.executable, str(GATE)]
print(f"driving: {GATE}")

INDEX_TEMPLATE = """---
version: "9.9.3"
path: "{path}"
stage: "{stage}"
current_sprint_slug: "{slug}"
current_roadmap_slug: ""
skip_polish: false
skip_architecture_check: false
skip_impl_subagent_check: false
skip_runtime_verify: false
plan_critique_max_rounds: 2
plan_critique_min_rounds: 0
plan_critique_disabled: false
---

# index
"""

failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        failures.append(name)


def make_repo(path_type: str = "Refactor", stage: str = "ship", slug: str = "s1") -> Path:
    root = Path(tempfile.mkdtemp(prefix="gate-test-"))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    ai = root / ".ai_state"
    (ai / "sprints" / slug).mkdir(parents=True)
    (ai / "_index.md").write_text(
        INDEX_TEMPLATE.format(path=path_type, stage=stage, slug=slug), encoding="utf-8"
    )
    (root / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    # 让 ship 不被判为 light ship (light ship 走轻门禁, 绕开本测试关心的路径)
    src = root / "src"
    src.mkdir()
    (src / "app.ts").write_text("export const x = 1;\n" + "// pad\n" * 200, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "impl"], cwd=root, check=True)
    return root


def run_gate(root: Path, payload: dict) -> tuple[str, str]:
    proc = subprocess.run(
        RUNNER,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=root,
    )
    return proc.stdout, proc.stderr


def stop_payload(root: Path, session: str = "sess-A") -> dict:
    return {"hook_event_name": "Stop", "cwd": str(root), "session_id": session}


def write_payload(root: Path, session: str = "sess-A") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "cwd": str(root),
        "session_id": session,
        "tool_name": "Write",
        "tool_input": {"file_path": str(root / "src" / "app.ts")},
    }


def ledger(root: Path, slug: str = "s1") -> list[dict]:
    p = root / ".ai_state" / "sprints" / slug / "stop-failures.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def blocked(stdout: str) -> bool:
    return '"decision"' in stdout and '"block"' in stdout


# ---------------------------------------------------------------- AC16a / M3+M4
print("\nAC16a: 前 2 次阻断, 第 3 次起 ESCALATED")
root = make_repo()
results = []
for i in range(4):
    out, err = run_gate(root, stop_payload(root))
    results.append((blocked(out), "ESCALATED" in err))
check("第1次 = block", results[0] == (True, False), str(results[0]))
check("第2次 = block", results[1] == (True, False), str(results[1]))
check("第3次 = ESCALATED 且不发 block", results[2] == (False, True), str(results[2]))
check("第4次 = 继续 ESCALATED (AC16b2: 升级不清零)", results[3] == (False, True), str(results[3]))
rows = ledger(root)
check("ledger 有 2 条 GateBlock", sum(r["event"] == "GateBlock" for r in rows) == 2, str(rows))
check("ledger 有 2 条 GateEscalated", sum(r["event"] == "GateEscalated" for r in rows) == 2)
check(
    "记录字段齐全",
    all({"event", "ts", "session_id", "reason_sha1", "stage", "path", "consecutive"} <= set(r) for r in rows),
)
shutil.rmtree(root)

# ---------------------------------------------------------------- AC16h
print("\nAC16h: 连续 12 次 Stop, block 发射总数 ≤3")
root = make_repo()
block_count = sum(1 for _ in range(12) if blocked(run_gate(root, stop_payload(root))[0]))
check(f"12 次尝试中 block 发射 {block_count} 次 (≤3)", block_count <= 3, f"实际 {block_count}")
shutil.rmtree(root)

# ---------------------------------------------------------------- AC16f
print("\nAC16f: PreToolUse 实现写入永不被熔断放行, 且不推进 Stop 计数")
root = make_repo()
pre = [blocked(run_gate(root, write_payload(root))[0]) for _ in range(5)]
check("5 次实现写入全部被阻断", all(pre), str(pre))
check("PreToolUse 未写 ledger (不推进计数)", ledger(root) == [], str(ledger(root)))
out, err = run_gate(root, stop_payload(root))
check("其后首个 Stop 仍是 block 而非升级", blocked(out) and "ESCALATED" not in err)
shutil.rmtree(root)

# ---------------------------------------------------------------- AC16c 并发
print("\nAC16c: 并发双会话互不污染")
root = make_repo()
run_gate(root, stop_payload(root, "sess-A"))
run_gate(root, stop_payload(root, "sess-A"))
out_b, err_b = run_gate(root, stop_payload(root, "sess-B"))
check("A 已 2 条时 B 的首个 Stop 仍正常阻断", blocked(out_b) and "ESCALATED" not in err_b)
out_a, err_a = run_gate(root, stop_payload(root, "sess-A"))
check("A 的第 3 次仍按自己的链升级 (B 的记录不打断 A)", (not blocked(out_a)) and "ESCALATED" in err_a)
shutil.rmtree(root)

# ---------------------------------------------------------------- AC16e
print("\nAC16e: 解锁动作报根因 (polish 未跑), 补齐后才轮到 manifest")
root = make_repo()
_, err = run_gate(root, stop_payload(root))
check("缺 cleanup-pass.md 时报 polish 未跑", "polish stage 未跑" in err, err.strip()[:120])
check("且给出完整解锁链", "cleanup-pass.md" in err and "review-manifest.yaml" in err)
sprint = root / ".ai_state" / "sprints" / "s1"
(sprint / "cleanup-pass.md").write_text("# cleanup\n空壳, 无结论\n", encoding="utf-8")
_, err = run_gate(root, stop_payload(root, "sess-C"))
check("空壳 cleanup-pass.md 仍判未跑", "polish stage 未跑" in err, err.strip()[:120])
(sprint / "cleanup-pass.md").write_text("# cleanup\nVERDICT: PASS\n", encoding="utf-8")
_, err = run_gate(root, stop_payload(root, "sess-D"))
check("补齐后改报缺 review-manifest (manifest 未被降级)", "review-manifest.yaml" in err, err.strip()[:120])
shutil.rmtree(root)

# ------------------------------------------------- impl 段 spec-gate 也必须接熔断器
# Codex 首版只把熔断接在 ship 段异常处理上, impl 段 spec-gate 失败仍会无限活锁。
print("\n补漏: impl 段 spec-gate 失败同样熔断 (非仅 ship 段)")
root = make_repo(path_type="Feature", stage="impl")
res = [
    (blocked(o), "ESCALATED" in e)
    for o, e in (run_gate(root, stop_payload(root)) for _ in range(4))
]
check("impl spec-gate 前 2 次 block", res[0] == (True, False) and res[1] == (True, False), str(res[:2]))
check("impl spec-gate 第 3/4 次升级", res[2] == (False, True) and res[3] == (False, True), str(res[2:]))
shutil.rmtree(root)

# ------------------------------------------- manifest 不得因 gitignored 文件哈希漂移而死锁
# 2026-07-27 实测: .gitignore 有意排除 evidence.yaml (hook 运行日志), 而 manifest 固定其
# sha256 → 文件被 hook 持续改写, 又不在 git 里无从还原 → 已 ship 的 sprint 永久卡死。
print("\n死锁回归: manifest 里的 gitignored 文件不参与哈希校验")
root = make_repo()
sprint = root / ".ai_state" / "sprints" / "s1"
(root / ".gitignore").write_text(".ai_state/**/evidence.yaml\n", encoding="utf-8")
(sprint / "evidence.yaml").write_text("collected_evidence: [] # 初始\n", encoding="utf-8")
subprocess.run(["git", "add", "-A"], cwd=root, check=True)
subprocess.run(["git", "commit", "-qm", "ignore evidence"], cwd=root, check=True)
tracked = subprocess.run(
    ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
).stdout.split()
check(
    "前提: evidence.yaml 确实未被 git 跟踪",
    ".ai_state/sprints/s1/evidence.yaml" not in tracked,
    str(tracked),
)
# 模拟 hook 追加导致哈希漂移
(sprint / "evidence.yaml").write_text("collected_evidence: [] # 被 hook 改写\n", encoding="utf-8")
_, err = run_gate(root, stop_payload(root, "sess-E"))
check(
    "不得因 evidence.yaml 哈希漂移而阻断",
    "hash mismatch: evidence.yaml" not in err,
    err.strip()[:160],
)
shutil.rmtree(root)

# ---------------------------------------------------------------- 非 Stop 事件不受影响
print("\nM7: 非 Athena 目录 / 其他事件 行为不变")
plain = Path(tempfile.mkdtemp(prefix="plain-"))
out, err = run_gate(plain, {"hook_event_name": "Stop", "cwd": str(plain), "session_id": "x"})
check("非 Athena 目录静默放行", out.strip() == "" and err.strip() == "", repr(out + err))
shutil.rmtree(plain)

print(f"\n{'=' * 50}")
if failures:
    print(f"FAILED {len(failures)}: {failures}")
    sys.exit(1)
print("ALL GREEN")

#!/usr/bin/env python3
"""Release-contract validator for Athena 9.9.8.

Preserves 9.9.3 coverage categories (package parity, fresh install, F-series,
hook/runtime contracts, Codex smoke) and adds 9.9.8 review-packet / tree-hash
fail-closed fixtures. Implementation review: sprints/2026-08-27-athena-9-9-8/reviews/implementation-review.md
"""

from __future__ import annotations

import sys

# The validator imports release hook modules directly. Keep its self-check clean
# when invoked with the user-facing command, so the package-junk assertion does
# not fail on the validator's own transient __pycache__.
sys.dont_write_bytecode = True

if sys.version_info < (3, 11):  # tomllib 是 3.11+ stdlib; 门禁不能在 import 阶段静默崩
    raise SystemExit(
        "validate-athena-9.9.8 需要 Python >= 3.11 (tomllib), 当前 "
        + sys.version.split()[0]
    )

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
import types
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CC = ROOT / "vibeCoding/claude/9.9.8/.claude"
CX = ROOT / "vibeCoding/codex/9.9.8/.codex"
CC_BASE = ROOT / "vibeCoding/claude/9.9.3/.claude"
CX_BASE = ROOT / "vibeCoding/codex/9.9.3/.codex"
CODEX_REQUIRED_VERSION = "0.150.0"
passes: list[str] = []
failures: list[str] = []
skips: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    (passes if condition else failures).append(name if condition or not detail else f"{name}: {detail}")


def skip(name: str, detail: str) -> None:
    skips.append(f"{name}: {detail}")


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"read {path.relative_to(ROOT)}: {exc}")
        return ""


def digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        if is_junk(path):
            continue
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def is_junk(path: Path) -> bool:
    return path.name in {".DS_Store", "__pycache__", "tmp"} or path.suffix == ".pyc"


def managed_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not is_junk(path)
    }


def load_module(path: Path, name: str) -> Any:
    """Load a hook module without writing __pycache__ next to canonical sources."""
    module = types.ModuleType(name)
    module.__file__ = str(path)
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    exec(code, module.__dict__)
    return module


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None, timeout: int = 120, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **(env or {}), "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        command,
        cwd=cwd,
        env=merged,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def check_baseline_and_package_parity() -> None:
    for endpoint, baseline, target in (("CC", CC_BASE, CC), ("CX", CX_BASE, CX)):
        check(f"{endpoint} 9.9.3 baseline exists", baseline.is_dir())
        check(f"{endpoint} 9.9.8 target exists", target.is_dir())
        missing = sorted(managed_files(baseline) - managed_files(target))
        check(f"{endpoint} complete-fork file parity", not missing, repr(missing[:12]))
        junk = _canonical_junk(target)
        check(f"{endpoint} package has no junk", not junk, repr(junk[:8]))

    cc_skills = {path.name for path in (CC / "skills").iterdir() if path.is_dir()}
    cx_skills = {path.name for path in (CX / "skills").iterdir() if path.is_dir()}
    check("CC/CX skill parity", cc_skills == cx_skills, repr(sorted(cc_skills ^ cx_skills)))
    check("26 skills per endpoint", len(cc_skills) == len(cx_skills) == 26, f"cc={len(cc_skills)} cx={len(cx_skills)}")


def check_identity_and_config() -> None:
    try:
        settings = json.loads(read(CC / "settings.json"))
    except json.JSONDecodeError as exc:
        check("CC settings JSON", False, str(exc))
        settings = {}
    try:
        config = tomllib.loads(read(CX / "config.toml"))
    except tomllib.TOMLDecodeError as exc:
        check("CX config TOML", False, str(exc))
        config = {}

    check("CC settings JSON", bool(settings))
    check("CC version marker", settings.get("env", {}).get("VIBECODING_ATHENA_VERSION") == "9.9.8")
    check("CC template keeps default permission mode", settings.get("permissions", {}).get("defaultMode") == "default")
    allowed = set(settings.get("permissions", {}).get("allow", []))
    required_npx = {
        "Bash(npx playwright)",
        "Bash(npx playwright *)",
        "Bash(npx ecc-agentshield)",
        "Bash(npx ecc-agentshield *)",
    }
    check("CC npx rules have command boundaries", required_npx <= allowed, repr(sorted(required_npx - allowed)))
    check("CC unsafe npx prefixes removed", not ({"Bash(npx playwright*)", "Bash(npx ecc-agentshield*)"} & allowed))

    check("CX config TOML", bool(config))
    check("CX built-in provider", config.get("model_provider") == "openai", repr(config.get("model_provider")))
    check("CX model selection", config.get("model") == "gpt-5.6-sol", repr(config.get("model")))
    check("fresh CX omits openai_base_url", "openai_base_url" not in config)
    check("CX version marker", config.get("shell_environment_policy", {}).get("set", {}).get("VIBECODING_VERSION") == "9.9.8")


def check_skills_and_agents() -> None:
    bad_fences: list[str] = []
    bad_frontmatter: list[str] = []
    for endpoint in (CC, CX):
        for path in sorted((endpoint / "skills").glob("*/SKILL.md")):
            body = read(path)
            if body.count("```") % 2:
                bad_fences.append(str(path.relative_to(ROOT)))
            lines = body.splitlines()
            if not lines or lines[0].strip() != "---" or "---" not in [line.strip() for line in lines[1:]]:
                bad_frontmatter.append(str(path.relative_to(ROOT)))
    check("all SKILL.md fences balanced", not bad_fences, repr(bad_fences))
    check("all SKILL.md frontmatter delimited", not bad_frontmatter, repr(bad_frontmatter))

    reviewer = read(CC / "agents/reviewer.md")
    athena_review = read(CC / "skills/athena-review/SKILL.md")
    check("CC generator does not preload pace", "skills: [pace]" not in read(CC / "agents/generator.md"))
    check("CC architect keeps pace skill", "skills: [pace" in read(CC / "agents/architect.md"))
    check("CC critic is a stub", "禁止 live" in read(CC / "agents/critic.md") and "disable-model-invocation" in read(CC / "agents/critic.md"))
    check("CC evaluator is a stub", "禁止 live" in read(CC / "agents/evaluator.md"))
    check("CC spec-compliance is a stub", "禁止 live" in read(CC / "agents/spec-compliance.md"))
    check("CC review is one native request", "一次" in athena_review and "await-review-result" in athena_review)
    check("CC reviewer writes implementation-review", "implementation-review" in reviewer)
    check("CX critic is a stub", "禁止 live" in read(CX / "agents/critic.toml"))
    check("CX evaluator is a stub", "禁止 live" in read(CX / "agents/evaluator.toml"))


def check_hooks() -> None:
    try:
        hooks = json.loads(read(CX / "hooks.json"))["hooks"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        check("CX hooks JSON", False, str(exc))
        return
    pre = hooks.get("PreToolUse", [])
    spawn = [group for group in pre if re.search(r"(?:spawn_agent|Agent)", group.get("matcher", ""))]
    check("CX spawn PreToolUse registered", len(spawn) == 1, f"matches={len(spawn)}")
    command = spawn[0].get("hooks", [{}])[0].get("command", "") if spawn else ""
    check("CX spawn guard command", command.endswith("subagent-worktree-audit.py"), command)
    start_commands = {
        hook.get("command", "")
        for group in hooks.get("SubagentStart", [])
        for hook in group.get("hooks", [])
    }
    check("CX SubagentStart retains worktree audit", any(value.endswith("subagent-worktree-audit.py") for value in start_commands))
    check("CX retry shim not falsely registered", all("subagent-retry.py" not in json.dumps(value) for value in hooks.values()))
    hook_docs = read(CX / "skills/pace/references/hooks.md")
    check("CX hook docs describe spawn guard", "spawn_agent|Agent" in hook_docs and "前置阻断" in hook_docs)
    check("CX hook docs mark retry unregistered", "未注册" in hook_docs and "subagent-retry.py" in hook_docs)
    audit = read(CX / "hooks/subagent-worktree-audit.py")
    gate = read(CX / "hooks/delivery-gate.py")
    check("spawn guard blocks with exit 2", "return 2" in audit and "blocked_before_start" in audit)
    check("ship gate consumes worktree violations", "validate_worktree_violations(sprint_dir)" in gate)

    registered = {
        Path(hook["command"].split()[-1]).name
        for groups in hooks.values()
        for group in groups
        for hook in group.get("hooks", [])
        if hook.get("command")
    }
    documented = set(re.findall(r"[\w.-]+\.py", hook_docs))
    check(
        "CX 每个注册 hook 都在 hooks.md 有记录",
        registered <= documented,
        f"未记录={sorted(registered - documented)}",
    )
    unmarked = sorted(
        name
        for name in documented - registered
        if not re.search(re.escape(name) + r"[^\n]*未注册", hook_docs)
    )
    check("CX 文档提到但未注册的 hook 已显式标注", not unmarked, f"未标注={unmarked}")


def _gate_blocked(result: subprocess.CompletedProcess[str]) -> str:
    text = (result.stdout or "") + (result.stderr or "")
    if '"decision": "block"' in text or '"decision":"block"' in text:
        return text
    return ""


def _write_feature_repo(repo: Path, *, design: str, packet: str, evidence: bool = True, review: str | None = None) -> None:
    sprint = repo / ".ai_state/sprints/test-sprint"
    (sprint / "reviews").mkdir(parents=True)
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src/app.js").write_text("module.exports = 1;\n", encoding="utf-8")
    (repo / ".ai_state/_index.md").write_text(
        "---\n"
        'path: "Feature"\n'
        'stage: "impl"\n'
        'current_sprint_slug: "test-sprint"\n'
        "skip_impl_subagent_check: true\n"
        "---\n",
        encoding="utf-8",
    )
    (sprint / "design.md").write_text(design, encoding="utf-8")
    (sprint / "review-packet.md").write_text(packet, encoding="utf-8")
    if evidence:
        (sprint / "evidence.yaml").write_text(
            "collected_evidence:\n- tool_use_id: t1\n  result: pass\n",
            encoding="utf-8",
        )
    if review is not None:
        (sprint / "reviews/implementation-review.md").write_text(review, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c", "user.email=a@b.c",
            "-c", "user.name=t",
            "-c", "commit.gpgsign=false",
            "commit", "--no-verify", "-m", "init",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _run_cc_gate(repo: Path, payload: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return run(
        ["node", str(CC / "hooks/delivery-gate.cjs")],
        cwd=repo,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdin=json.dumps(payload),
    )


def _run_cx_gate(repo: Path, payload: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return run(
        [sys.executable, str(CX / "hooks/delivery-gate.py")],
        cwd=repo,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        stdin=json.dumps(payload),
    )


def _sha_design(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def check_998_gate_runtime() -> None:
    design = "# d\n\n## 验收标准\n\n- [ ] AC1: foo\n- [ ] AC2: bar\n"
    good_packet = (
        "---\nschema_version: 1\nsource_design_sha256: "
        + _sha_design(design)
        + "\n---\n\n# Review Packet\n\n| ID | Must hold |\n| AC1 | foo |\n| AC2 | bar |\n"
    )
    write_payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": "src/app.js"},
        "cwd": "",
    }
    stop_payload = {"hook_event_name": "Stop", "cwd": ""}

    with tempfile.TemporaryDirectory(prefix="athena-998-stale-") as raw:
        repo = Path(raw)
        stale = good_packet.replace(_sha_design(design), "0" * 64)
        _write_feature_repo(repo, design=design, packet=stale)
        write_payload["cwd"] = str(repo)
        for label, runner in (("CC", _run_cc_gate), ("CX", _run_cx_gate)):
            blocked = _gate_blocked(runner(repo, write_payload))
            check(f"{label} stale design hash fail-closed", "source_design_sha256" in blocked, blocked[-400:])

    with tempfile.TemporaryDirectory(prefix="athena-998-missac-") as raw:
        repo = Path(raw)
        miss = good_packet.replace("| AC2 | bar |", "")
        _write_feature_repo(repo, design=design, packet=miss)
        write_payload["cwd"] = str(repo)
        for label, runner in (("CC", _run_cc_gate), ("CX", _run_cx_gate)):
            blocked = _gate_blocked(runner(repo, write_payload))
            check(f"{label} missing AC fail-closed", "AC set mismatch" in blocked, blocked[-400:])

    with tempfile.TemporaryDirectory(prefix="athena-998-extraac-") as raw:
        repo = Path(raw)
        extra = good_packet + "\n| AC9 | extra |\n"
        _write_feature_repo(repo, design=design, packet=extra)
        write_payload["cwd"] = str(repo)
        for label, runner in (("CC", _run_cc_gate), ("CX", _run_cx_gate)):
            blocked = _gate_blocked(runner(repo, write_payload))
            check(f"{label} extra AC fail-closed", "AC set mismatch" in blocked, blocked[-400:])

    with tempfile.TemporaryDirectory(prefix="athena-998-norev-") as raw:
        repo = Path(raw)
        _write_feature_repo(repo, design=design, packet=good_packet, review=None)
        (repo / ".ai_state/_index.md").write_text(
            "---\npath: \"Feature\"\nstage: \"ship\"\ncurrent_sprint_slug: \"test-sprint\"\nskip_impl_subagent_check: true\n---\n",
            encoding="utf-8",
        )
        stop_payload["cwd"] = str(repo)
        for label, runner in (("CC", _run_cc_gate), ("CX", _run_cx_gate)):
            blocked = _gate_blocked(runner(repo, stop_payload))
            check(f"{label} missing implementation-review fail-closed", "implementation-review.md" in blocked, blocked[-400:])

    with tempfile.TemporaryDirectory(prefix="athena-998-nref-") as raw:
        repo = Path(raw)
        live = ""
        review = (
            "---\nschema_version: 1\nmode: implementation\n"
            "packet_sha256: PLACE\nreviewed_diff_sha256: PLACE\n"
            "review_run_id: r1\nnative_output_ref: reviews/_native/missing.md\n"
            "verdict: PASS\n---\n\nVERDICT: PASS\n"
        )
        _write_feature_repo(repo, design=design, packet=good_packet, review=review)
        (repo / ".ai_state/_index.md").write_text(
            "---\npath: \"Feature\"\nstage: \"ship\"\ncurrent_sprint_slug: \"test-sprint\"\nskip_impl_subagent_check: true\n---\n",
            encoding="utf-8",
        )
        stop_payload["cwd"] = str(repo)
        for label, runner in (("CC", _run_cc_gate), ("CX", _run_cx_gate)):
            blocked = _gate_blocked(runner(repo, stop_payload))
            check(f"{label} missing native_output_ref path fail-closed", "native_output_ref" in blocked, blocked[-400:])

    with tempfile.TemporaryDirectory(prefix="athena-998-dhash-") as raw:
        repo = Path(raw)
        _write_feature_repo(repo, design=design, packet=good_packet, review=None)
        native = repo / ".ai_state/sprints/test-sprint/reviews/_native/r1.md"
        native.parent.mkdir(parents=True, exist_ok=True)
        native.write_text("native\n", encoding="utf-8")
        packet_hash = hashlib.sha256((repo / ".ai_state/sprints/test-sprint/review-packet.md").read_bytes()).hexdigest()
        gate_mod = load_module(CX / "hooks/delivery-gate.py", "athena_998_hash_mod")
        live_hash = gate_mod.source_diff_sha256(repo)
        (repo / ".ai_state/sprints/test-sprint/reviews/implementation-review.md").write_text(
            "---\nschema_version: 1\nmode: implementation\n"
            f"packet_sha256: {packet_hash}\n"
            "reviewed_diff_sha256: deadbeef\n"
            "review_run_id: r1\nnative_output_ref: reviews/_native/r1.md\n"
            "verdict: PASS\n---\n\nVERDICT: PASS\n",
            encoding="utf-8",
        )
        (repo / ".ai_state/_index.md").write_text(
            "---\npath: \"Feature\"\nstage: \"ship\"\ncurrent_sprint_slug: \"test-sprint\"\nskip_impl_subagent_check: true\n---\n",
            encoding="utf-8",
        )
        stop_payload["cwd"] = str(repo)
        for label, runner in (("CC", _run_cc_gate), ("CX", _run_cx_gate)):
            blocked = _gate_blocked(runner(repo, stop_payload))
            check(f"{label} diff hash mismatch fail-closed", "reviewed_diff_sha256" in blocked, blocked[-400:])
        check("tree hash is non-empty", bool(live_hash) and live_hash != "deadbeef", live_hash)

    with tempfile.TemporaryDirectory(prefix="athena-998-parity-") as raw:
        repo = Path(raw)
        _write_feature_repo(repo, design=design, packet=good_packet)
        (repo / "untracked-extra.txt").write_text("secret change\n", encoding="utf-8")
        py_mod = load_module(CX / "hooks/delivery-gate.py", "athena_998_hash_parity")
        py_hash = py_mod.source_diff_sha256(repo)
        node = shutil.which("node")
        if node:
            js = run(
                [node, "-e", "const g=require(process.argv[1]); process.stdout.write(g.sourceDiffSha256(process.argv[2]));", str(CC / "hooks/delivery-gate.cjs"), str(repo)],
                cwd=repo,
            )
            check("CC/CX sourceDiffSha256 parity including untracked", js.stdout == py_hash, f"cc={js.stdout} cx={py_hash} err={js.stderr[-200:]}")
            before = py_hash
            (repo / "untracked-extra.txt").write_text("secret change 2\n", encoding="utf-8")
            after = py_mod.source_diff_sha256(repo)
            check("untracked edit changes tree hash", before != after, f"before={before} after={after}")
        else:
            skip("CC/CX sourceDiffSha256 parity including untracked", "node not found")

    node = shutil.which("node")
    if node:
        js = run(
            [node, "-e", "const g=require(process.argv[1]); const s=g.findSubstitutions(\"rg 'foo$(rm -rf /)bar'\"); process.stdout.write(JSON.stringify(s));", str(CC / "hooks/pre-bash-guard.cjs")],
        )
        check("CC rg single-quoted $( is not substitution", js.stdout == "[]", js.stdout + js.stderr[-200:])
        js2 = run(
            [node, "-e", "const g=require(process.argv[1]); const s=g.findSubstitutions(\"echo $(rm -rf /)\"); process.stdout.write(String(s.length));", str(CC / "hooks/pre-bash-guard.cjs")],
        )
        check("CC unquoted $( still detected", js2.stdout.strip() != "0", js2.stdout + js2.stderr[-200:])
    else:
        skip("CC rg quote fixture", "node not found")


def check_998_review_contract() -> None:
    node = shutil.which("node")
    if node:
        probe = run([node, "--check", str(CC / "hooks/delivery-gate.cjs")])
        check("CC delivery-gate syntax", probe.returncode == 0, probe.stderr[-400:])
        probe = run([node, "--check", str(CC / "hooks/pre-bash-guard.cjs")])
        check("CC pre-bash-guard syntax", probe.returncode == 0, probe.stderr[-400:])
    for label, path in (
        ("CX delivery-gate syntax", CX / "hooks/delivery-gate.py"),
        ("CX pre-bash-guard syntax", CX / "hooks/pre-bash-guard.py"),
    ):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
            check(label, True)
        except (OSError, SyntaxError) as exc:
            check(label, False, str(exc))

    cc_gate = read(CC / "hooks/delivery-gate.cjs")
    check("CC gate drops critic title counts as block", "expected at least ${minimum}" not in cc_gate)
    check("CC gate requires implementation-review.md", "implementation-review.md" in cc_gate)
    check("CC gate requires native_output_ref", "native_output_ref" in cc_gate)
    cx_gate = read(CX / "hooks/delivery-gate.py")
    check("CX gate requires implementation-review.md", "implementation-review.md" in cx_gate)
    check("CX gate requires native_output_ref", "native_output_ref" in cx_gate)

    # rg quote fixture: single-quoted $(...) must not be treated as substitution
    guard_mod = load_module(CX / "hooks/pre-bash-guard.py", "athena_998_pre_bash")
    quoted = guard_mod.find_substitutions("rg 'foo$(rm -rf /)bar'")
    check("CX rg single-quoted $( is not substitution", quoted == [], repr(quoted))
    unquoted = guard_mod.find_substitutions("echo $(rm -rf /)")
    check("CX unquoted $( still detected", any(x is None or x for x in unquoted), repr(unquoted))

    index_cc = read(CC / "hooks/index-updater.cjs")
    check("CC next_action allows await-review-result", "await-review-result" in index_cc)
    check("CX next_action allows await-review-result", "await-review-result" in read(CX / "hooks/index-updater.py"))
    check("CC continuator skips await-review-result", "await-review-result" in read(CC / "hooks/pace-continuator.cjs"))
    check("CX continuator skips await-review-result", "await-review-result" in read(CX / "hooks/pace-continuator.py"))
    check("packet template exists", (CC / "skills/pace/templates/sprints/review-packet.md").is_file())
    check("implementation-review template exists", (CC / "skills/pace/templates/sprints/reviews/implementation-review.md").is_file())
    check("CC REVIEW.md exists", (CC / "REVIEW.md").is_file())


def check_contract_text() -> None:
    combined_release = "\n".join(
        read(path)
        for path in (
            ROOT / "vibeCoding/claude/9.9.8/RELEASE.md",
            ROOT / "vibeCoding/codex/9.9.8/RELEASE.md",
            ROOT / "vibeCoding/codex/9.9.8/CHANGELOG.md",
        )
    )
    check("manual alias documented", "manual` 作为 `default` alias" in combined_release)
    check("obsolete no-manual claim removed", "无 `manual`" not in combined_release)
    check("obsolete no-PreToolUse claim removed", "不派发 PreToolUse" not in combined_release and "不派发 `PreToolUse`" not in combined_release)
    platform = read(CX / "skills/pace/references/platform-contracts.md")
    check("gateway risk scoped to Azure report", "Azure OpenAI" in platform and "not proof that every" in platform)
    check("code_mode_only is dogfood obligation", "code_mode_only" in platform and "dogfood" in platform)
    provenance = read(CX / "standards/iron-law-provenance.md")
    check("CX Standards/.rules law has provenance", "[Standards ≠ Codex .rules]" in provenance)


def check_install_contract() -> None:
    setup_script = CX / "skills/athena-setup/scripts/setup-athena.py"
    setup_body = read(setup_script)
    check("setup has atomic writes", "atomic_write" in setup_body and "os.replace" in setup_body)
    check("setup renders CX config", "render_cx_config" in setup_body and "tomllib.loads" in setup_body)
    with tempfile.TemporaryDirectory(prefix="athena-996-setup-") as raw:
        home = Path(raw)
        env = {**os.environ, "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1"}
        first = run(
            [sys.executable, str(setup_script), "--home", str(home), "--repo-root", str(ROOT), "--only", "both"],
            env=env,
            timeout=120,
        )
        check("fresh setup exits zero", first.returncode == 0, (first.stdout + first.stderr)[-800:])
        installed = home / ".codex/config.toml"
        try:
            cfg = tomllib.loads(installed.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            check("fresh installed CX config parses", False, str(exc))
            return
        check("fresh installed CX config parses", True)
        check("fresh install omits openai_base_url", "openai_base_url" not in cfg)
        before = digest_tree(home)
        second = run(
            [sys.executable, str(setup_script), "--home", str(home), "--repo-root", str(ROOT), "--only", "both"],
            env=env,
            timeout=120,
        )
        check("same-version setup verifies", second.returncode == 0, (second.stdout + second.stderr)[-800:])
        check("same-version setup is non-mutating", before == digest_tree(home))


def check_runtime_contract() -> None:
    audit = CX / "hooks/subagent-worktree-audit.py"
    with tempfile.TemporaryDirectory(prefix="athena-996-hook-") as raw:
        repo = Path(raw) / "repo"
        secondary = Path(raw) / "isolated"
        sprint = repo / ".ai_state/sprints/test-sprint"
        sprint.mkdir(parents=True)
        (repo / ".ai_state/_index.md").write_text(
            '---\npath: "System"\nstage: "impl"\ncurrent_sprint_slug: "test-sprint"\n---\n',
            encoding="utf-8",
        )
        (repo / "seed").write_text("seed\n", encoding="utf-8")
        run(["git", "init", "-q"], cwd=repo)
        run(["git", "add", "seed"], cwd=repo)
        run(["git", "-c", "user.name=Athena", "-c", "user.email=athena@example.invalid", "commit", "-qm", "seed"], cwd=repo)
        add = run(["git", "worktree", "add", "-q", str(secondary), "HEAD"], cwd=repo)
        check("runtime fixture creates isolated worktree", add.returncode == 0, add.stderr)

        base_payload = {
            "hook_event_name": "PreToolUse",
            "cwd": str(repo),
            "tool_name": "spawn_agent",
            "tool_input": {"agent_type": "generator", "message": "write the feature"},
        }
        blocked = run([sys.executable, str(audit)], cwd=repo, stdin=json.dumps(base_payload))
        check("spawn guard blocks missing worktree", blocked.returncode == 2, blocked.stderr)
        allowed_payload = dict(base_payload)
        allowed_payload["tool_input"] = {
            "agent_type": "generator",
            "message": f"worktree={secondary} write the feature",
        }
        allowed = run([sys.executable, str(audit)], cwd=repo, stdin=json.dumps(allowed_payload))
        check("spawn guard allows registered isolated worktree", allowed.returncode == 0, allowed.stderr)

        violation_file = sprint / "worktree-violations.jsonl"
        rows = [json.loads(line) for line in violation_file.read_text(encoding="utf-8").splitlines()]
        check("blocked attempt is recorded as blocked", rows and rows[0].get("blocked_before_start") is True)
        gate = load_module(CX / "hooks/delivery-gate.py", "athena_996_delivery_gate")
        try:
            gate.validate_worktree_violations(sprint)
        except Exception as exc:  # blocked attempts must not poison ship
            check("ship ignores successfully blocked spawn attempts", False, str(exc))
        else:
            check("ship ignores successfully blocked spawn attempts", True)
        violation_file.write_text(
            json.dumps({**rows[0], "event": "SubagentStart", "blocked_before_start": False}) + "\n",
            encoding="utf-8",
        )
        try:
            gate.validate_worktree_violations(sprint)
        except gate.GateError:
            check("ship blocks an actually started red-zone violation", True)
        else:
            check("ship blocks an actually started red-zone violation", False)
        violation_file.write_text(
            json.dumps(
                {
                    **rows[0],
                    "event": "SubagentStart",
                    "blocked_before_start": False,
                    "resolved": True,
                    "resolution": "discarded unauthorized checkout changes",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            gate.validate_worktree_violations(sprint)
        except gate.GateError as exc:
            check("ship accepts remediated violation evidence", False, str(exc))
        else:
            check("ship accepts remediated violation evidence", True)


def check_f_series_regressions() -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    external = re.compile(r"missing quantum-(?:front|backend) pack", re.I)
    for name in (
        "test-scaffold-page-gen.py",
        "test-db-unit-gen.py",
        "test-security-e2e.py",
        "test-biz-delivery-loop.py",
        "test-delivery-gate.py",
        "test-token-usage-collector.py",
    ):
        path = ROOT / "vibeCoding/scripts" / name
        if not path.is_file():
            check(f"F-series {name}", False, "script missing")
            continue
        result = run([sys.executable, str(path)], env=env, timeout=180)
        output = result.stdout + result.stderr
        if result.returncode == 0:
            check(f"F-series {name}", True)
        elif external.search(output):
            skip(f"F-series {name}", "external convention pack unavailable")
        else:
            check(f"F-series {name}", False, output[-500:])


def check_fresh_codex_runtime() -> None:
    codex = shutil.which("codex")
    if not codex:
        skip("exact Codex runtime", "codex binary unavailable")
        return
    version = run([codex, "--version"], timeout=30)
    output = version.stdout + version.stderr
    if CODEX_REQUIRED_VERSION not in output:
        skip("exact Codex runtime", f"requires {CODEX_REQUIRED_VERSION}; found {output.strip()}")
        return
    with tempfile.TemporaryDirectory(prefix="athena-996-codex-") as raw:
        home = Path(raw)
        env = {**os.environ, "HOME": str(home), "CODEX_HOME": str(home / ".codex"), "PYTHONDONTWRITEBYTECODE": "1"}
        setup = run(
            [sys.executable, str(CX / "skills/athena-setup/scripts/setup-athena.py"), "--home", str(home), "--repo-root", str(ROOT), "--only", "cx"],
            env=env,
            timeout=120,
        )
        check("exact Codex fresh setup", setup.returncode == 0, (setup.stdout + setup.stderr)[-800:])
        doctor = run([codex, "--strict-config", "doctor", "--json"], env=env, timeout=90)
        try:
            report = json.loads(doctor.stdout)
        except json.JSONDecodeError:
            check("exact Codex config.load", False, (doctor.stdout + doctor.stderr)[-800:])
            return
        status = report.get("checks", {}).get("config.load", {}).get("status")
        check("exact Codex config.load", status == "ok", repr(status))


def check_998_index_bounds() -> None:
    bounds = load_module(CX / "hooks/_index_bounds.py", "athena_998_index_bounds")
    long_item = "x" * 400
    with tempfile.TemporaryDirectory(prefix="athena-998-bounds-") as raw:
        repo = Path(raw)
        sprint = repo / ".ai_state/sprints/test-sprint"
        sprint.mkdir(parents=True)
        items = [f'"{long_item}-{i}"' for i in range(12)]
        status = "\n".join(f"- {long_item} status {i}" for i in range(12))
        original = (
            "---\n"
            'current_sprint_slug: "test-sprint"\n'
            f"route_history: [{', '.join(items)}]  # re-route ≤10\n"
            "---\n\n"
            f"## 当前状态\n\n{status}\n\n"
            "## 工具调度建议\n\nok\n"
        )
        (repo / ".ai_state/_index.md").write_text(original, encoding="utf-8")
        next_text = bounds.enforce_index_bounds(original, repo / ".ai_state")
        (repo / ".ai_state/_index.md").write_text(next_text, encoding="utf-8")
        overflow = sprint / "index-overflow.md"
        check("index overflow file created", overflow.is_file(), str(overflow))
        check("overflow keeps full item text", long_item in overflow.read_text(encoding="utf-8"))
        rh = re.search(r"^route_history:\s*\[(.*)\]\s*$", next_text, re.M)
        values = bounds.split_quoted_list(rh.group(1)) if rh else []
        check("route_history capped at 10", len(values) <= 10, str(len(values)))
        too_long = [v for v in values if bounds.byte_len(bounds.unquote(v)) > bounds.ITEM_MAX_BYTES]
        check("route_history items ≤160B", not too_long, repr(too_long[:1]))
        body_items = re.findall(r"^\s*-\s+(.*)$", next_text, re.M)
        state = re.search(r"^## 当前状态\s*$([\s\S]*?)(?=^## |\Z)", next_text, re.M)
        state_items = re.findall(r"^\s*-\s+(.*)$", state.group(1) if state else "", re.M)
        check("status list capped at 10", len(state_items) <= 10, str(len(state_items)))
        over = [item for item in state_items if bounds.byte_len(item) > bounds.ITEM_MAX_BYTES]
        check("status items ≤160B", not over, repr(over[:1]))
        check("index file ≤12KiB after overflow", bounds.byte_len(next_text) <= bounds.INDEX_MAX_BYTES, str(bounds.byte_len(next_text)))
        node = shutil.which("node")
        if node:
            js = run(
                [
                    node, "-e",
                    "const b=require(process.argv[1]); const fs=require('fs');"
                    "const t=fs.readFileSync(process.argv[2],'utf8');"
                    "const n=b.enforceIndexBounds(t, process.argv[3]);"
                    "const rh=(n.match(/^route_history:\\s*\\[(.*)\\]\\s*$/m)||[])[1]||'';"
                    "const items=b.splitQuotedList(rh).map(b.unquote);"
                    "process.stdout.write(JSON.stringify({n:items.length,max:Math.max(0,...items.map(b.byteLen))}));",
                    str(CC / "hooks/_index-bounds.cjs"),
                    str(repo / ".ai_state/_index.md"),
                    str(repo / ".ai_state"),
                ]
            )
            try:
                payload = json.loads(js.stdout or "{}")
            except json.JSONDecodeError:
                payload = {}
            check("CC bounds module caps route_history", payload.get("n", 99) <= 10 and payload.get("max", 999) <= 160, js.stdout + js.stderr[-200:])
        else:
            skip("CC index bounds module", "node not found")


def check_998_ac11_baseline() -> None:
    baseline = ROOT / ".ai_state/.runtime/baseline/baseline-9.9.6-tokens.json"
    check("AC11 baseline freeze exists", baseline.is_file())
    if not baseline.is_file():
        return
    try:
        data = json.loads(baseline.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        check("AC11 baseline JSON parses", False, str(exc))
        return
    check("AC11 baseline JSON parses", True)
    files = data.get("files") or []
    check("AC11 baseline lists source files", len(files) >= 3, str(len(files)))
    classified = data.get("classified") or {}
    check("AC11 classified rollup present", "sprints" in classified and "projection_998" in classified, repr(sorted(classified)))
    proj = classified.get("projection_998") or {}
    check("AC11 projection records median drop", "median_control_drop_pct" in proj, repr(proj))
    eval_path = ROOT / ".ai_state/sprints/2026-08-27-athena-9-9-8/eval-ac11.md"
    check("AC11 eval report exists", eval_path.is_file())


def _canonical_junk(target: Path) -> list[str]:
    return sorted(str(path.relative_to(ROOT)) for path in target.rglob("*") if is_junk(path))


def main() -> int:
    check_baseline_and_package_parity()
    check_identity_and_config()
    check_skills_and_agents()
    check_hooks()
    check_998_review_contract()
    check_998_gate_runtime()
    check_998_index_bounds()
    check_998_ac11_baseline()
    check_contract_text()
    check_install_contract()
    check_runtime_contract()
    check_f_series_regressions()
    check_fresh_codex_runtime()
    for endpoint, target in (("CC", CC), ("CX", CX)):
        junk = _canonical_junk(target)
        check(f"{endpoint} package still has no junk after validator", not junk, repr(junk[:8]))
    for name in passes:
        print(f"PASS {name}")
    for entry in skips:
        print(f"SKIP {entry}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"SUMMARY pass={len(passes)} fail={len(failures)} skip={len(skips)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Static/TDD release contract for Athena 9.9.2.

The first run against the untouched 9.9.1 copy is intentionally red. Runtime
fixtures are expanded by the validation sprint; this file keeps the release
identity and drift checks executable throughout implementation.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

try:
    import yaml
except ImportError:  # Keep the release summary available on lean Python installs.
    yaml = None


ROOT = Path(__file__).resolve().parents[2]
CX = ROOT / "vibeCoding/codex/9.9.2/.codex"
CC = ROOT / "vibeCoding/claude/9.9.2/.claude"
# 9.9.2 baseline = the committed 9.9.1 release trees (P1-2: the old constants
# pinned the 9.9.0 tree / a stale commit and compared the wrong history).
CC_991_TREE = "1d05a7e3ac326d69b61e721f0842dcb3e3b2a4bd"
CX_991_TREE = "f48e25330f4f220ef83fb6dda3bc86f04ee2ee0d"
failures: list[str] = []
passes: list[str] = []
skips: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        passes.append(name)
    else:
        failures.append(f"{name}: {detail}" if detail else name)


def skip(name: str, detail: str) -> None:
    skips.append(f"{name}: {detail}")


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"read {path.relative_to(ROOT)}: {exc}")
        return ""


def all_text(root: Path, suffixes: tuple[str, ...]) -> list[tuple[Path, str]]:
    rows: list[tuple[Path, str]] = []
    if not root.is_dir():
        return rows
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in suffixes:
            rows.append((path, text(path)))
    return rows


def check_baseline() -> None:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            "HEAD",
            "--",
            "vibeCoding/codex/9.9.1",
            "vibeCoding/claude/9.9.1",
        ],
        cwd=ROOT,
        check=False,
    )
    check("9.9.1 baseline unchanged in working tree", proc.returncode == 0, f"git diff exit={proc.returncode}")
    for label, spec, expected in (
        ("committed CC 9.9.1 tree object unchanged", "HEAD:vibeCoding/claude/9.9.1/.claude", CC_991_TREE),
        ("committed CX 9.9.1 tree object unchanged", "HEAD:vibeCoding/codex/9.9.1/.codex", CX_991_TREE),
    ):
        tree = subprocess.run(
            ["git", "rev-parse", spec],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        check(
            label,
            tree.returncode == 0 and tree.stdout.strip() == expected,
            tree.stdout.strip() or tree.stderr.strip(),
        )

    release_roots = (ROOT / "vibeCoding/codex/9.9.2", ROOT / "vibeCoding/claude/9.9.2", ROOT / "vibeCoding/scripts")
    junk = [
        path.relative_to(ROOT)
        for release_root in release_roots
        for path in release_root.rglob("*")
        if path.name in {"__pycache__", ".DS_Store", "tmp"} or path.suffix == ".pyc"
    ]
    check("release tree has no junk", not junk, ", ".join(map(str, junk[:8])))

    future_hits: list[str] = []
    text_suffixes = {".md", ".py", ".toml", ".json", ".yaml", ".yml", ".cjs", ".js", ".sh"}
    for release_root in release_roots:
        for path in release_root.rglob("*"):
            if not path.is_file() or path.suffix not in text_suffixes:
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not re.search(r"(?i)Athena|VIBECODING(?:_ATHENA)?_VERSION|\b(?:FROM_|TO_)?VERSION\s*[:=]", line):
                    continue
                versions = re.findall(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)(?![\d.])", line)
                # P1-2: the release target itself is 9.9.2, so the ceiling is
                # 9.9.2 — anything beyond it is an unexplained future marker.
                if any((int(major), int(minor), int(patch)) > (9, 9, 2) for major, minor, patch in versions):
                    future_hits.append(str(path.relative_to(ROOT)))
                    break
    check("release tree has no future version marker", not future_hits, ", ".join(future_hits[:8]))

    diff_check = subprocess.run(
        ["git", "diff", "--check"], cwd=ROOT, check=False, capture_output=True, text=True
    )
    check("git diff --check", diff_check.returncode == 0, f"exit={diff_check.returncode}")


def check_identity_and_config() -> None:
    check("CX package exists", CX.is_dir())
    check("CC package exists", CC.is_dir())
    cfg_path = CX / "config.toml"
    cfg_text = text(cfg_path)
    try:
        cfg = tomllib.loads(cfg_text)
    except tomllib.TOMLDecodeError as exc:
        failures.append(f"CX config TOML: {exc}")
        cfg = {}

    # P0-4/P1-2: the package ships a custom provider; the selected id must equal
    # a registered model_providers.<id> (official Codex config contract).
    check("config model_provider=custom_openai", cfg.get("model_provider") == "custom_openai", repr(cfg.get("model_provider")))
    check(
        "config model_provider registered under model_providers",
        cfg.get("model_provider") in cfg.get("model_providers", {}),
        f"selected={cfg.get('model_provider')!r} registered={sorted(cfg.get('model_providers', {}))}",
    )
    check("config model=gpt-5.6-sol", cfg.get("model") == "gpt-5.6-sol", repr(cfg.get("model")))
    check("config has no manual context", "model_context_window" not in cfg)
    check("config has no manual compact", "model_auto_compact_token_limit" not in cfg)
    check("config has no model availability NUX", "tui" not in cfg or "model_availability_nux" not in cfg.get("tui", {}))
    providers = cfg.get("model_providers", {})
    empty_base = [name for name, value in providers.items() if isinstance(value, dict) and value.get("base_url") == ""]
    check("config has no empty provider endpoint", not empty_base, ",".join(empty_base))
    version = cfg.get("shell_environment_policy", {}).get("set", {}).get("VIBECODING_VERSION")
    check("config version=9.9.2", version == "9.9.2", repr(version))
    skill_paths = [entry.get("path", "") for entry in cfg.get("skills", {}).get("config", [])]
    check("config skills use ~/.agents/skills", bool(skill_paths) and all("/.agents/skills/" in path for path in skill_paths))
    check("AGENTS identity=9.9.2", "v9.9.2" in text(CX / "AGENTS.md"))
    check("CLAUDE identity=9.9.2", "v9.9.2" in text(CC / "CLAUDE.md"))

    settings_path = CC / "settings.json"
    try:
        settings = json.loads(text(settings_path))
    except json.JSONDecodeError as exc:
        failures.append(f"CC settings JSON: {exc}")
        settings = {}
    check("CC model=best", settings.get("model") == "best", repr(settings.get("model")))
    check("CC persisted effort=xhigh", settings.get("effortLevel") == "xhigh", repr(settings.get("effortLevel")))
    check("CC fallback models", settings.get("fallbackModel") == ["opus", "sonnet"], repr(settings.get("fallbackModel")))
    check("CC native worktree baseRef=head", settings.get("worktree", {}).get("baseRef") == "head")
    env = settings.get("env", {})
    check("CC has no global subagent model override", "CLAUDE_CODE_SUBAGENT_MODEL" not in env)
    check("CC has no default model alias pins", not any(key.startswith("ANTHROPIC_DEFAULT_") for key in env))
    hooks = settings.get("hooks", {})
    check("CC has no WorktreeCreate override", "WorktreeCreate" not in hooks)
    check("CC has no WorktreeRemove override", "WorktreeRemove" not in hooks)
    precompact_matchers = [entry.get("matcher") for entry in hooks.get("PreCompact", [])]
    check(
        "CC PreCompact matcher uses official manual|auto trigger values",
        precompact_matchers == ["manual|auto"],
        repr(precompact_matchers),
    )
    private_keys: list[str] = []

    def find_private_keys(value: object, prefix: str = "settings") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).startswith("_comment"):
                    private_keys.append(f"{prefix}.{key}")
                find_private_keys(child, f"{prefix}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                find_private_keys(child, f"{prefix}[{index}]")

    find_private_keys(settings)
    check("CC settings has no private _comment keys", not private_keys, ", ".join(private_keys[:8]))
    allow = settings.get("permissions", {}).get("allow", [])
    check("CC permissions have no broad write allow", "Write(**)" not in allow and "Write" not in allow)
    check("CC permissions do not pre-allow install/push/ssh", not any(
        re.search(r"(?:install|git push|ssh|scp|rsync|curl)", str(rule), re.I) for rule in allow
    ))
    deny = settings.get("permissions", {}).get("deny", [])
    check("CC permissions deny common secret reads", any(".env" in str(rule) for rule in deny) and any(".ssh" in str(rule) for rule in deny))


def check_hooks() -> None:
    evidence = text(CX / "hooks/evidence-collector.py")
    retry = text(CX / "hooks/subagent-retry.py")
    gate = text(CX / "hooks/delivery-gate.py")
    hooks_json = text(CX / "hooks.json")
    check("PostToolUse reads tool_response", "tool_response" in evidence and "tool_response" in retry)
    check("PostToolUse rejects legacy tool_output", "tool_output" not in evidence and "tool_output" not in retry)
    check("gate uses assignment JSONL", "subagent-assignments.jsonl" in gate)
    check("gate uses event JSONL", "subagent-events.jsonl" in gate)
    check("gate validates final PASS", "VERDICT" in gate and "PASS" in gate)
    check("SessionStart includes clear", bool(re.search(r'"matcher"\s*:\s*"[^"]*clear', hooks_json, re.I)))

    cc_evidence = text(CC / "hooks/evidence-collector.cjs")
    cc_retry = text(CC / "hooks/subagent-retry.cjs")
    cc_tracker = text(CC / "hooks/subagent-tracker.cjs")
    cc_gate = text(CC / "hooks/delivery-gate.cjs")
    settings = text(CC / "settings.json")
    check("CC evidence uses hook event success/failure", "PostToolUseFailure" in cc_evidence and "PostToolUse" in cc_evidence)
    check("CC evidence rejects legacy tool_output", "tool_output" not in cc_evidence and "tool_output" not in cc_retry)
    check("CC registers PostToolUseFailure", '"PostToolUseFailure"' in settings)
    check("CC registers SubagentStart and Stop", '"SubagentStart"' in settings and '"SubagentStop"' in settings)
    check("CC tracker writes shared assignment schema", "subagent-assignments.jsonl" in cc_tracker and "task_name" in cc_tracker)
    check("CC tracker writes shared event schema", "subagent-events.jsonl" in cc_tracker and "agent_type" in cc_tracker)
    check("CC gate uses assignment JSONL", "subagent-assignments.jsonl" in cc_gate)
    check("CC gate uses event JSONL", "subagent-events.jsonl" in cc_gate)
    check("CC gate selects latest passN", "pass([1-9]" in cc_gate and "numbered" in cc_gate)
    check("CC gate enforces PASS only", 'verdict !== "PASS"' in cc_gate)
    # design §4.2/§4.4: executable spec gate at impl entry plus ship recheck.
    check("CX gate has impl-entry spec gate", "validate_spec_gate" in gate and '"impl"' in gate)
    check("CX gate maps labeled ACs to evidence", "validate_ac_mapping" in gate)
    check("CC gate has impl-entry spec gate", "validateImplEntry" in cc_gate and "validateSpecGate" in cc_gate)
    check("CC gate maps labeled ACs to evidence", "validateAcMapping" in cc_gate)
    for endpoint, body in (("CX", gate), ("CC", cc_gate)):
        check(f"{endpoint} gate requires review state manifest", "review-manifest.yaml" in body and "Reviewed state manifest sha256" in body)
        check(f"{endpoint} gate requires TDD red-green evidence", "tdd-evidence.yaml" in body and "red_observed_at" in body)
        check(f"{endpoint} gate validates sprint-local user authorization", "user-authorizations/" in body and "authorization_source" in body)
        check(f"{endpoint} gate captures command evidence artifact", "output_artifact" in body and "artifact_sha256" in body and "implementation_commit" in body)
    # P0-3: the acceptance heading matcher must not rely on \b after CJK.
    check("CX gate acceptance heading is CJK-safe", "验收标准)(?=" in gate, "boundary lookahead missing")
    check("CC gate acceptance heading is CJK-safe", "验收标准)(?=" in cc_gate, "boundary lookahead missing")


def check_cc_agents() -> None:
    expected = {
        "critic": ("fable", "xhigh", "plan", False),
        "architect": ("fable", "xhigh", "plan", False),
        "reviewer": ("sonnet", "high", "plan", True),
        "spec-compliance": ("sonnet", "high", "plan", True),
        "evaluator": ("opus", "xhigh", "plan", False),
        "generator": ("sonnet", "high", "default", False),
        "polish-worker": ("sonnet", "high", "default", False),
    }
    found = {path.stem for path in (CC / "agents").glob("*.md")}
    check("CC role agent set 7/7", found == set(expected), f"found={sorted(found)}")
    for name, (model, effort, permission, background) in expected.items():
        body = text(CC / "agents" / f"{name}.md")
        if not body.startswith("---") or body.count("---") < 2:
            check(f"CC agent {name} frontmatter", False, "missing frontmatter")
            continue
        head = body.split("---", 2)[1]
        try:
            meta = yaml.safe_load(head) if yaml is not None else {}
        except Exception as exc:
            check(f"CC agent {name} frontmatter", False, type(exc).__name__)
            continue
        check(f"CC agent {name} model", meta.get("model") == model, repr(meta.get("model")))
        check(f"CC agent {name} effort", meta.get("effort") == effort, repr(meta.get("effort")))
        check(f"CC agent {name} permission", meta.get("permissionMode") == permission, repr(meta.get("permissionMode")))
        check(f"CC agent {name} background", meta.get("background") is background, repr(meta.get("background")))
        check(f"CC agent {name} maxTurns", isinstance(meta.get("maxTurns"), int) and meta["maxTurns"] > 0)
        check(f"CC agent {name} skills", isinstance(meta.get("skills"), list) and bool(meta["skills"]))
        if permission == "plan":
            denied = set(meta.get("disallowedTools", []))
            check(f"CC agent {name} write tools denied", {"Write", "Edit", "Agent"} <= denied, repr(denied))
    generator = yaml.safe_load(text(CC / "agents/generator.md").split("---", 2)[1]) if yaml else {}
    check("CC yellow generator does not force isolation", "isolation" not in generator)
    polish = yaml.safe_load(text(CC / "agents/polish-worker.md").split("---", 2)[1]) if yaml else {}
    check("CC red polish uses native worktree isolation", polish.get("isolation") == "worktree")


def check_contract_text() -> None:
    cx_rows = all_text(CX, (".md", ".toml"))
    forbidden = {
        "spawn_agent --cwd": re.compile(r"spawn_agent\s+--cwd"),
        "assign_task": re.compile(r"\bassign_task\b"),
        "bare wait": re.compile(r"(?m)^\s*(?:[-*]\s*)?wait\s*$"),
    }
    for label, pattern in forbidden.items():
        hits = [str(path.relative_to(ROOT)) for path, body in cx_rows if pattern.search(body)]
        check(f"CX has no {label}", not hits, ", ".join(hits[:8]))

    details_hits = []
    for path, body in all_text(CX, (".md", ".toml", ".py")):
        if "athena-migrate" in path.parts:
            continue
        if ".ai_state/details" in body:
            details_hits.append(str(path.relative_to(ROOT)))
    check("non-migrate details refs removed", not details_hits, ", ".join(details_hits[:8]))

    bad_frontmatter = []
    for skill in sorted((CX / "skills").glob("*/SKILL.md")):
        body = text(skill)
        head = body.split("---", 2)[1] if body.startswith("---") and body.count("---") >= 2 else ""
        if re.search(r"(?m)^(effort|attach_to_stages):", head):
            bad_frontmatter.append(skill.parent.name)
    check("CX skill frontmatter official-only", not bad_frontmatter, ", ".join(bad_frontmatter))

    bad_cc_frontmatter = []
    for skill in sorted((CC / "skills").glob("*/SKILL.md")):
        body = text(skill)
        head = body.split("---", 2)[1] if body.startswith("---") and body.count("---") >= 2 else ""
        if re.search(r"(?m)^attach_to_stages:", head):
            bad_cc_frontmatter.append(skill.parent.name)
    check("CC skill frontmatter has no attach_to_stages", not bad_cc_frontmatter, ", ".join(bad_cc_frontmatter))

    cc_hot_rows = [
        *all_text(CC / "agents", (".md",)),
        *all_text(CC / "skills/pace", (".md",)),
        *all_text(CC / "skills/athena-review", (".md",)),
    ]
    task_tool_hits = [str(path.relative_to(ROOT)) for path, body in cc_hot_rows if re.search(r"\bTask tool\b|\bTask subagent\b", body)]
    check("CC hot path uses Agent terminology", not task_tool_hits, ", ".join(task_tool_hits[:8]))

    # AC8 route-source drift test: athena-dev is the only detailed route source.
    # The normative confidence thresholds must live there and must NOT be
    # duplicated back into pace/SKILL.md.
    threshold = re.compile(r"≥\s*0\.8|0\.5\s*[–-]\s*0\.8")
    for endpoint, root in (("CX", CX), ("CC", CC)):
        dev_body = text(root / "skills/athena-dev/SKILL.md")
        pace_body = text(root / "skills/pace/SKILL.md")
        check(f"{endpoint} athena-dev owns route thresholds", bool(threshold.search(dev_body)))
        check(
            f"{endpoint} pace has no duplicated route thresholds",
            not threshold.search(pace_body),
            "normative threshold block reintroduced into pace/SKILL.md",
        )
        check(f"{endpoint} pace points to athena-dev route source", "athena-dev" in pace_body)

    memory_markers = ("Tier1 working memory", "Tier2 persistent memory", "_index.md retrieval router")
    for endpoint, root in (("CX", CX), ("CC", CC)):
        surfaces = {
            "template": root / "skills/pace/templates/_index.md",
            "init": root / "skills/athena-init/SKILL.md",
            "checkpoint": root / "skills/athena-checkpoint/SKILL.md",
            "status": root / "skills/athena-status/SKILL.md",
            "session-start": root / ("hooks/session-start.py" if endpoint == "CX" else "hooks/session-start.cjs"),
        }
        for surface, path in surfaces.items():
            body = text(path)
            missing = [marker for marker in memory_markers if marker not in body]
            check(f"{endpoint} AC7 {surface} consumer contract", not missing, ", ".join(missing))
        init_body = text(surfaces["init"])
        check(f"{endpoint} init active identity=9.9.2", "v9.9.2" in init_body and "初始化完成" in init_body)
        check(f"{endpoint} init has no removed cx_goal_default_on", "cx_goal_default_on" not in init_body)
        status_body = text(surfaces["status"])
        check(f"{endpoint} status pointer diagnostics", all(marker in status_body for marker in (
            "missing authoritative pointer", "escaping authoritative pointer", "stale authoritative pointer"
        )))
        session_body = text(surfaces["session-start"])
        check(f"{endpoint} SessionStart pointer diagnostics", all(marker in session_body for marker in (
            "missing authoritative pointer", "escaping authoritative pointer", "stale authoritative pointer", "overflow"
        )))

    cx_workflow_files = (
        CX / "skills/pace/references/stages.md",
        CX / "skills/pace/templates/sprints/reviews/pass1.md",
        CX / "skills/polish/SKILL.md",
        CX / "agents/polish_worker.toml",
    )
    conflicting = [
        str(path.relative_to(ROOT))
        for path in cx_workflow_files
        if re.search(r"PASS\s*/\s*CONCERNS|\{PASS,\s*CONCERNS\}", text(path))
    ]
    check("CX active workflow is PASS-only before polish/ship", not conflicting, ", ".join(conflicting))

    for endpoint, release_root in (("CX", CX.parent), ("CC", CC.parent)):
        release = text(release_root / "RELEASE.md")
        changelog_active = text(release_root / "CHANGELOG.md").split("# Athena CHANGELOG — v9.9.1", 1)[0]
        check(f"{endpoint} RELEASE uses current runtime commands", "test-athena-claude-9.9.2-runtime.cjs" in release and "test-athena-9.9.2-runtime.py" in release)
        check(f"{endpoint} RELEASE has no wrong Node Python command", "node vibeCoding/scripts/test-athena-9.9.2-runtime.py" not in release)
        stale = re.search(r"83 PASS|73/0/0|33/33|70 PASS|71/0/2|待 py3\.11|本包留待 review", release + changelog_active)
        check(f"{endpoint} active release docs have no stale result/pending text", stale is None, stale.group(0) if stale else "")

    # AC13 (design §13): active quantum surfaces must not invoke legacy names.
    legacy = re.compile(
        r"project-data-reader|unit-test-gen|playwright-e2e|scaffold-page-gen|scaffold-module-gen|db-schema-gen"
    )
    residue: list[str] = []
    for root in (CX, CC):
        for area in ("skills/quantum-codegen/references", "skills/quantum-data/references"):
            for path in sorted((root / area).rglob("*.md")):
                if legacy.search(text(path)):
                    residue.append(str(path.relative_to(ROOT)))
    check("quantum references have no legacy skill-name residue", not residue, ", ".join(residue[:8]))
    for endpoint, root in (("CX", CX), ("CC", CC)):
        hub_dirs = {p.name for p in (root / "skills").iterdir() if p.is_dir() and p.name.startswith("quantum-")}
        check(f"{endpoint} quantum hubs = exactly 2", hub_dirs == {"quantum-codegen", "quantum-data"}, repr(sorted(hub_dirs)))


def check_release_static() -> None:
    roots = (CX, CC, ROOT / "vibeCoding/scripts")
    python_files = sorted(path for root in roots for path in root.rglob("*.py"))
    compile_errors: list[str] = []
    for path in python_files:
        try:
            compile(path.read_bytes(), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            compile_errors.append(f"{path.relative_to(ROOT)}:{type(exc).__name__}")
    check(f"Python compile no-pycache {len(python_files)}/{len(python_files)}", not compile_errors, ", ".join(compile_errors[:8]))

    for suffixes, label in (({ ".json" }, "JSON"), ({ ".toml" }, "TOML"), ({ ".yaml", ".yml" }, "YAML")):
        files = sorted(path for root in roots for path in root.rglob("*") if path.is_file() and path.suffix in suffixes)
        errors: list[str] = []
        if label == "YAML" and yaml is None:
            errors.append("PyYAML unavailable")
        else:
            for path in files:
                try:
                    if path.suffix == ".json":
                        json.loads(path.read_text(encoding="utf-8"))
                    elif path.suffix == ".toml":
                        tomllib.loads(path.read_text(encoding="utf-8"))
                    else:
                        yaml.safe_load(path.read_text(encoding="utf-8"))
                except Exception as exc:  # parser-specific errors still become a summarized FAIL
                    errors.append(f"{path.relative_to(ROOT)}:{type(exc).__name__}")
        check(f"{label} parse {len(files)}/{len(files)}", not errors, ", ".join(errors[:8]))

    node = shutil.which("node")
    node_files = sorted([*CC.rglob("*.cjs"), *CC.rglob("*.js")])
    node_failures: list[str] = []
    if node:
        for path in node_files:
            run = subprocess.run([node, "--check", str(path)], cwd=ROOT, check=False, capture_output=True, text=True)
            if run.returncode != 0:
                node_failures.append(str(path.relative_to(ROOT)))
    check(
        f"CC Node syntax {len(node_files)}/{len(node_files)}",
        bool(node) and not node_failures,
        "node unavailable" if not node else ", ".join(node_failures[:8]),
    )

    quick_validate = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills/.system/skill-creator/scripts/quick_validate.py"
    skills = [
        *(path for path in sorted((CX / "skills").iterdir()) if path.is_dir()),
        *(path for path in sorted((CC / "skills").iterdir()) if path.is_dir()),
    ]
    skill_failures: list[str] = []
    if quick_validate.is_file():
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for skill in skills:
            run = subprocess.run(
                [sys.executable, str(quick_validate), str(skill)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            if run.returncode != 0:
                skill_failures.append(str(skill.relative_to(ROOT)))
    # P1-2: 26 skills per endpoint after the 7→2 consolidation, so 26 × 2 = 52.
    check(
        f"official quick_validate {len(skills)}/52",
        quick_validate.is_file() and len(skills) == 52 and not skill_failures,
        "official validator unavailable" if not quick_validate.is_file() else f"count={len(skills)}; " + ", ".join(skill_failures[:8]),
    )

    junk_after = [path for root in roots for path in root.rglob("*") if path.name == "__pycache__" or path.suffix == ".pyc"]
    check("static validation leaves no bytecode", not junk_after, ", ".join(str(path.relative_to(ROOT)) for path in junk_after[:8]))


def tree_manifest(root: Path) -> dict[str, tuple[str, int]]:
    return {
        str(path.relative_to(root)): (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode & 0o111)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def check_package_parity() -> None:
    cx_skills = {path.name for path in (CX / "skills").iterdir() if path.is_dir()}
    cc_skills = {path.name for path in (CC / "skills").iterdir() if path.is_dir()}
    def declared_names(root: Path, names: set[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for name in names:
            try:
                body = (root / name / "SKILL.md").read_text(encoding="utf-8")
                frontmatter = body.split("---", 2)[1]
            except (OSError, IndexError):
                frontmatter = ""
            match = re.search(r"(?m)^name:\s*['\"]?([a-z0-9-]+)", frontmatter)
            result[name] = match.group(1) if match else ""
        return result

    cx_declared = declared_names(CX / "skills", cx_skills)
    cc_declared = declared_names(CC / "skills", cc_skills)
    check(
        "shared skill-name parity 26/26",
        cx_skills == cc_skills and len(cx_skills) == 26 and cx_declared == cc_declared,
    )
    for skill_name in ("athena-setup", "athena-migrate"):
        cx_tree = tree_manifest(CX / "skills" / skill_name)
        cc_tree = tree_manifest(CC / "skills" / skill_name)
        check(f"{skill_name} CC/CX parity", cx_tree == cc_tree)


def check_install_contract() -> None:
    setup = text(CX / "skills/athena-setup/SKILL.md")
    migrate = text(CX / "skills/athena-migrate/SKILL.md")
    check("setup installs AGENTS", "AGENTS.md" in setup)
    check("setup finds repo-root CX package", "vibeCoding/codex/9.9.2/.codex" in setup)
    check("setup finds repo-root CC package", "vibeCoding/claude/9.9.2/.claude" in setup)
    for state in ("fresh", "CC-only", "CX-only", "same-version", "old-version"):
        check(f"setup documents {state}", state in setup)
    # 9.9.2 (design §7.2, user decision): migration is AI-guided; scripted
    # migrate/tests are retired. The contract is now: guide present at both
    # package roots, installed with athena-migrate (references/), all four
    # copies identical, red-line invariants documented, legacy 7→2 covered.
    check("migrate is AI-guided to 9.9.2", "AI" in migrate and "9.9.2" in migrate)
    check("migrate references AI-MIGRATION-GUIDE", "AI-MIGRATION-GUIDE" in migrate)
    check("setup routes old endpoints to athena-migrate", "athena-migrate" in setup)
    guide_copies = {
        "CX package root": CX.parent / "AI-MIGRATION-GUIDE.md",
        "CC package root": CC.parent / "AI-MIGRATION-GUIDE.md",
        "CX installed skill copy": CX / "skills/athena-migrate/references/AI-MIGRATION-GUIDE.md",
        "CC installed skill copy": CC / "skills/athena-migrate/references/AI-MIGRATION-GUIDE.md",
    }
    for label, path in guide_copies.items():
        check(f"AI migration guide present ({label})", path.is_file(), str(path.relative_to(ROOT)))
    digests = {
        label: hashlib.sha256(path.read_bytes()).hexdigest()
        for label, path in guide_copies.items()
        if path.is_file()
    }
    check(
        "AI migration guide copies identical",
        len(digests) == 4 and len(set(digests.values())) == 1,
        repr({label: digest[:8] for label, digest in digests.items()}),
    )
    guide_body = text(CX.parent / "AI-MIGRATION-GUIDE.md")
    for marker in ("备份", "preserve", "rollback", "密钥", "quantum-codegen", "quantum-data", "project-data-reader", "9.9.2"):
        check(f"AI migration guide invariant: {marker}", marker in guide_body)
    for marker in (
        "CC runtime assets/config → `~/.claude`",
        "CX config/hooks/agents → `~/.codex`",
        "CX skills → `~/.agents/skills`",
    ):
        check(f"AI migration guide destination: {marker}", marker in guide_body)
    check("AI migration guide has no CX package-to-~/.agents instruction", "复制到 `~/.claude` / `~/.agents`" not in guide_body)

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for label, test_path in (
        ("CX setup behavior suite", CX / "skills/athena-setup/tests/test_setup_991.py"),
        ("CC setup behavior suite", CC / "skills/athena-setup/tests/test_setup_991.py"),
    ):
        run = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        detail = (run.stdout + run.stderr)[-1200:]
        check(label, run.returncode == 0, detail)


def isolated_env(home: Path) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not any(marker in key.upper() for marker in ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))
    }
    env.update(
        {
            "HOME": str(home),
            "CODEX_HOME": str(home / ".codex"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "NO_COLOR": "1",
        }
    )
    return env


def check_fresh_codex_runtime() -> None:
    setup_script = CX / "skills/athena-setup/scripts/setup-athena.py"
    codex = shutil.which("codex")
    if codex is None:
        check("temp HOME Codex doctor", False, "codex unavailable")
        check("temp HOME prompt-input", False, "codex unavailable")
        return
    # ignore_cleanup_errors=True (Python 3.11+, matches this file's tomllib
    # floor): macOS + fast Python releases have shown a benign TOCTOU where
    # a child `codex`/`node` process still holds a just-closed handle under
    # raw_home when the `with` block exits, making rmtree race and raise
    # OSError on an otherwise-successful run. That race is irrelevant to the
    # release contract this check verifies, so cleanup failures are swallowed
    # instead of failing the whole validator on an environment artifact.
    with tempfile.TemporaryDirectory(
        prefix="athena-992-release-", ignore_cleanup_errors=True
    ) as raw_home:
        home = Path(raw_home)
        env = isolated_env(home)
        setup = subprocess.run(
            [sys.executable, str(setup_script), "--home", str(home), "--repo-root", str(ROOT), "--only", "both"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
        installed = setup.returncode == 0
        check("temp HOME fresh setup", installed, f"exit={setup.returncode}")
        if not installed:
            check("temp HOME Codex doctor", False, "setup failed")
            check("temp HOME prompt-input", False, "setup failed")
            return

        try:
            doctor = subprocess.run(
                [codex, "--strict-config", "doctor", "--json"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=90,
                env=env,
            )
            report = json.loads(doctor.stdout)
            checks = report.get("checks", {}) if isinstance(report, dict) else {}
            config_status = checks.get("config.load", {}).get("status")
            provider_status = checks.get("network.provider_reachability", {}).get("status")
            auth_status = checks.get("auth.credentials", {}).get("status", "unknown")
            doctor_ok = config_status == "ok" and provider_status == "ok"
            detail = f"config={config_status} provider={provider_status} auth={auth_status} (auth fail accepted)"
            if provider_status != "ok":
                detail += "; network unavailable or provider endpoint unreachable"
            check("temp HOME Codex doctor redacted JSON", doctor_ok, detail)
        except subprocess.TimeoutExpired:
            check("temp HOME Codex doctor redacted JSON", False, "network unavailable or doctor timed out")
        except (json.JSONDecodeError, OSError, AttributeError) as exc:
            check("temp HOME Codex doctor redacted JSON", False, f"invalid redacted JSON: {type(exc).__name__}")

        try:
            prompt = subprocess.run(
                [codex, "debug", "prompt-input", "release validation"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            prompt_data = json.loads(prompt.stdout)
            rendered = json.dumps(prompt_data, ensure_ascii=False)
            identity = "VibeCoding Athena v9.9.2" in rendered
            pace = "- pace:" in rendered and "/.agents/skills/pace/SKILL.md" in rendered
            agents_skills = "/.agents/skills/" in rendered
            check(
                "temp HOME prompt-input Athena/PACE/.agents",
                prompt.returncode == 0 and identity and pace and agents_skills,
                f"exit={prompt.returncode} identity={identity} pace={pace} agents_skills={agents_skills}",
            )
        except (json.JSONDecodeError, OSError) as exc:
            check("temp HOME prompt-input Athena/PACE/.agents", False, f"invalid JSON: {type(exc).__name__}")


def check_f_series_regressions() -> None:
    """AC13 / design §13.3: the six relocated F-series regressions must execute
    from vibeCoding/scripts with repository-root paths. Three of them require
    external workspace/quantum convention packs; a missing external fixture is
    reported as an explicit SKIP, never silently ignored and never a silent
    pass."""
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    external_marker = re.compile(r"missing quantum-(?:front|backend) pack")
    for name in (
        "test-scaffold-page-gen.py",
        "test-db-unit-gen.py",
        "test-security-e2e.py",
        "test-biz-delivery-loop.py",
        "test-delivery-gate.py",
        "test-token-usage-collector.py",
    ):
        script = ROOT / "vibeCoding/scripts" / name
        if not script.is_file():
            check(f"F-series regression {name}", False, "script missing")
            continue
        run = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )
        output = run.stdout + run.stderr
        if run.returncode == 0:
            check(f"F-series regression {name}", True)
        elif external_marker.search(output):
            skip(f"F-series regression {name}", "external workspace/quantum convention pack unavailable")
        else:
            check(f"F-series regression {name}", False, output[-400:])


def check_runtime_contract() -> None:
    runtime_suite = ROOT / "vibeCoding/scripts/test-athena-9.9.2-runtime.py"
    check("runtime behavior suite exists", runtime_suite.is_file())
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run(
        [sys.executable, str(runtime_suite)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    detail = (run.stdout + run.stderr)[-2000:]
    check("runtime behavior suite", run.returncode == 0, detail)
    cc_runtime_suite = ROOT / "vibeCoding/scripts/test-athena-claude-9.9.2-runtime.cjs"
    check("CC runtime behavior suite exists", cc_runtime_suite.is_file())
    node = shutil.which("node")
    if node is None:
        check("CC runtime behavior suite", False, "node unavailable")
    else:
        cc_run = subprocess.run(
            [node, str(cc_runtime_suite)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        cc_detail = (cc_run.stdout + cc_run.stderr)[-3000:]
        check("CC runtime behavior suite", cc_run.returncode == 0, cc_detail)


def main() -> int:
    check_baseline()
    check_identity_and_config()
    check_hooks()
    check_cc_agents()
    check_contract_text()
    check_release_static()
    check_package_parity()
    check_install_contract()
    check_f_series_regressions()
    check_runtime_contract()
    check_fresh_codex_runtime()
    for name in passes:
        print(f"PASS {name}")
    for entry in skips:
        print(f"SKIP {entry}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"SUMMARY pass={len(passes)} fail={len(failures)} skip={len(skips)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env node
"use strict";

/**
 * Runtime contract tests for the Athena v9.9.3 Claude Code package.
 *
 * The suite invokes the shipped hooks with official-shaped payloads. It uses
 * only temporary projects and never writes into the release package.
 */

const assert = require("assert");
const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "../..");
const CC = path.join(ROOT, "vibeCoding/claude/9.9.3/.claude");
const HOOKS = path.join(CC, "hooks");
const FIXTURES = path.join(ROOT, "vibeCoding/scripts/fixtures/athena-9.9.3/claude");
const GATE = path.join(HOOKS, "delivery-gate.cjs");
const SESSION_START = path.join(HOOKS, "session-start.cjs");
const EVIDENCE = path.join(HOOKS, "evidence-collector.cjs");
const TRACKER = path.join(HOOKS, "subagent-tracker.cjs");
const GUARD = path.join(HOOKS, "pre-bash-guard.cjs");
const CONFIG_AUDIT = path.join(HOOKS, "config-change-audit.cjs");
const STOP_FAILURE = path.join(HOOKS, "stop-failure-recorder.cjs");
const COMPACT_SNAPSHOT = path.join(HOOKS, "compact-snapshot.cjs");
const BREADCRUMB = path.join(HOOKS, "stage-breadcrumb.cjs");
const EVALUATOR = path.join(CC, "agents", "evaluator.md");
const SPRINT = "cc-runtime-contract";
const ROADMAP = "cc-runtime-roadmap";

let passed = 0;
let failed = 0;
let skipped = 0;

function test(name, fn) {
  try {
    fn();
    passed += 1;
    process.stdout.write(`PASS ${name}\n`);
  } catch (error) {
    failed += 1;
    process.stderr.write(`FAIL ${name}: ${error.stack || error.message}\n`);
  }
}

function skip(name, reason) {
  skipped += 1;
  process.stdout.write(`SKIP ${name}: ${reason}\n`);
}

function tempProject() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "athena-cc991-"));
}

function rmProject(project) {
  fs.rmSync(project, { recursive: true, force: true });
}

function digestTree(root) {
  const result = {};
  function walk(current) {
    if (!fs.existsSync(current)) return;
    for (const entry of fs.readdirSync(current, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const absolute = path.join(current, entry.name);
      if (entry.isDirectory()) walk(absolute);
      else if (entry.isFile()) {
        result[path.relative(root, absolute)] = crypto.createHash("sha256").update(fs.readFileSync(absolute)).digest("hex");
      }
    }
  }
  walk(root);
  return result;
}

function runNode(script, payload, cwd, args = []) {
  return spawnSync(process.execPath, [script, ...args], {
    cwd,
    input: JSON.stringify(payload || {}),
    encoding: "utf8",
    timeout: 15000,
    env: { ...process.env, ATHENA_TEST_MODE: "1" },
  });
}

function fixture(name) {
  return JSON.parse(fs.readFileSync(path.join(FIXTURES, name), "utf8"));
}

function runGateNoGit(project) {
  // Strip PATH (and any *_HOME hints) so every `git` invocation the gate
  // shells out to fails with ENOENT, simulating "git is unavailable" rather
  // than "git ran and reported an empty diff".
  const result = spawnSync(process.execPath, [GATE], {
    cwd: project,
    input: JSON.stringify({ hook_event_name: "Stop", cwd: project }),
    encoding: "utf8",
    timeout: 15000,
    env: { ATHENA_TEST_MODE: "1", PATH: "" },
  });
  assert.strictEqual(result.status, 0, result.stderr);
  const lines = result.stdout.split(/\r?\n/).filter(Boolean);
  let response = {};
  if (lines.length) {
    try { response = JSON.parse(lines[lines.length - 1]); } catch (_) {}
  }
  return { blocked: response.decision === "block", reason: response.reason || result.stderr, result };
}

function runGate(project) {
  const result = runNode(GATE, { hook_event_name: "Stop", cwd: project }, project);
  assert.strictEqual(result.status, 0, result.stderr);
  const lines = result.stdout.split(/\r?\n/).filter(Boolean);
  let response = {};
  if (lines.length) {
    try { response = JSON.parse(lines[lines.length - 1]); } catch (_) {}
  }
  return { blocked: response.decision === "block", reason: response.reason || result.stderr, result };
}

function write(pathname, body) {
  fs.mkdirSync(path.dirname(pathname), { recursive: true });
  fs.writeFileSync(pathname, body, "utf8");
}

function gitRun(project, args) {
  const result = spawnSync("git", args, { cwd: project, encoding: "utf8" });
  if (result.status !== 0) throw new Error(`git ${args.join(" ")} failed: ${result.stderr || result.stdout}`);
  return (result.stdout || "").trim();
}

function sha256File(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function bindReview(ctx, reviewPath) {
  const commit = gitRun(ctx.project, ["rev-parse", "HEAD"]);
  const manifestFiles = {
    "design.md": path.join(ctx.sprintDir, "design.md"),
    "checklist.yaml": path.join(ctx.sprintDir, "checklist.yaml"),
    "evidence.yaml": path.join(ctx.sprintDir, "evidence.yaml"),
    "runtime-verify.md": path.join(ctx.sprintDir, "runtime-verify.md"),
    "rework-notes.md": path.join(ctx.sprintDir, "rework-notes.md"),
    "cleanup-pass.md": path.join(ctx.sprintDir, "cleanup-pass.md"),
    "tdd-evidence.yaml": path.join(ctx.sprintDir, "tdd-evidence.yaml"),
    "architecture/ARCHITECTURE.md": path.join(ctx.ai, "architecture/ARCHITECTURE.md"),
    "architecture/athena-9.9.3.md": path.join(ctx.ai, "architecture/athena-9.9.3.md"),
  };
  const manifestLines = [
    "schema_version: 1",
    `implementation_commit: "${commit}"`,
    `index_governance_sha256: "${indexGovernanceSha256(path.join(ctx.ai, "_index.md"))}"`,
    "files:",
  ];
  for (const [name, filePath] of Object.entries(manifestFiles)) manifestLines.push(`  "${name}": "${sha256File(filePath)}"`);
  const manifestPath = path.join(ctx.sprintDir, "review-manifest.yaml");
  write(manifestPath, `${manifestLines.join("\n")}\n`);
  let body = fs.readFileSync(reviewPath, "utf8")
    .replace(/^Reviewed design sha256:.*\r?\n?/gm, "")
    .replace(/^Reviewed implementation commit:.*\r?\n?/gm, "")
    .replace(/^Reviewed state manifest sha256:.*\r?\n?/gm, "").trimEnd();
  body += `\n\nReviewed design sha256: ${sha256File(path.join(ctx.sprintDir, "design.md"))}`;
  body += `\nReviewed implementation commit: ${commit}`;
  body += `\nReviewed state manifest sha256: ${sha256File(manifestPath)}\n`;
  write(reviewPath, body);
}

function indexGovernanceSha256(indexPath) {
  const fm = {};
  for (const raw of fs.readFileSync(indexPath, "utf8").split(/\r?\n/)) {
    const match = raw.match(/^([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$/);
    if (match) fm[match[1]] = match[2].replace(/^['"]|['"]$/g, "");
  }
  const keys = [
    "path", "current_sprint_slug", "skip_polish", "skip_runtime_verify",
    "skip_architecture_check", "skip_impl_subagent_check",
    "plan_critique_disabled", "plan_critique_min_rounds",
  ].sort();
  const protectedFields = {};
  for (const key of keys) protectedFields[key] = fm[key] || "";
  return crypto.createHash("sha256").update(JSON.stringify(protectedFields)).digest("hex");
}

function writeAuthorization(sprintDir, {
  reason,
  authorizedBy = "user:release-owner",
  authorizedAt = "2026-07-13T08:00:00Z",
  expiry = "2099-01-01T00:00:00Z",
} = {}) {
  write(path.join(sprintDir, "user-authorizations/release-owner.yaml"), [
    "schema_version: 1",
    "kind: spec_gate_exception_authorization",
    `sprint_slug: "${SPRINT}"`,
    'path: "Feature"',
    `reason: "${reason}"`,
    "decision: approve",
    "authorization_source: user_prompt",
    `authorized_by: "${authorizedBy}"`,
    `authorized_at: "${authorizedAt}"`,
    `expiry: "${expiry}"`,
    'removal_condition: "acceptance criteria restored"',
    "",
  ].join("\n"));
}

function appendJsonl(pathname, rows) {
  write(pathname, rows.map(row => JSON.stringify(row)).join("\n") + "\n");
}

function timestamp(offsetSeconds) {
  return new Date(Date.parse("2026-07-10T08:00:00Z") + offsetSeconds * 1000).toISOString();
}

function indexBody({
  pathType = "Feature",
  stage = "ship",
  sprint = SPRINT,
  roadmap = ROADMAP,
  designChanged = false,
  skipRuntime = false,
  skipArchitecture = false,
  critiqueMin = 1,
  extras = [],
} = {}) {
  return [
    "---",
    `path: "${pathType}"`,
    `stage: "${stage}"`,
    `current_sprint_slug: "${sprint}"`,
    `current_roadmap_slug: "${roadmap}"`,
    `design_changed_after_impl: ${designChanged}`,
    `skip_runtime_verify: ${skipRuntime}`,
    `skip_architecture_check: ${skipArchitecture}`,
    "skip_impl_subagent_check: false",
    "plan_critique_disabled: false",
    `plan_critique_min_rounds: ${critiqueMin}`,
    ...extras,
    "---",
    "",
  ].join("\n");
}

function assignment(overrides = {}) {
  return {
    schema_version: 1,
    agent_id: "agent-generator-1",
    task_name: "implement CC 9.9.3",
    role: "generator",
    sprint_slug: SPRINT,
    timestamp: timestamp(1),
    ...overrides,
  };
}

function event(eventName, overrides = {}) {
  return {
    schema_version: 1,
    event: eventName,
    agent_id: "agent-generator-1",
    agent_type: "generator",
    sprint_slug: SPRINT,
    timestamp: eventName === "SubagentStart" ? timestamp(0) : timestamp(2),
    ...overrides,
  };
}

function createCompleteProject(options = {}) {
  const project = tempProject();
  const ai = path.join(project, ".ai_state");
  const sprintDir = path.join(ai, "sprints", SPRINT);
  write(path.join(ai, "_index.md"), indexBody(options));
  write(path.join(sprintDir, "design.md"), "# Design\n\n## Acceptance Criteria\n- [ ] AC1: 用户以输入 X 得到可观测输出 Y\n\n## Round 1 · Critic Findings\nPASS\n");
  write(path.join(sprintDir, "checklist.yaml"), [
    `sprint_slug: "${SPRINT}"`,
    "tasks:",
    "  - id: T1",
    "    title: implementation",
    "    status: completed",
    "",
  ].join("\n"));
  write(path.join(sprintDir, "evidence.yaml"), [
    `sprint_slug: "${SPRINT}"`,
    "collected_evidence:",
    "  - tool_use_id: validation-1",
    "    tool: Bash",
    "    ac_id: AC1",
    "    result: pass",
    "    file: src/a.js",
    "    source: command",
    "    command_or_artifact: node test.js",
    "    observed_at: 2026-07-13T08:00:00Z",
    "    summary: runtime contract completed with exit 0",
    "",
  ].join("\n"));
  appendJsonl(path.join(sprintDir, "subagent-assignments.jsonl"), [assignment()]);
  appendJsonl(path.join(sprintDir, "subagent-events.jsonl"), [
    event("SubagentStart"),
    event("SubagentStop"),
  ]);
  write(path.join(sprintDir, "reviews/pass1.md"), [
    "# Review Pass 1",
    "## Spec Compliance",
    "PASS",
    "## Evidence Cross-Check",
    "PASS",
    "VERDICT: PASS",
    "",
  ].join("\n"));
  write(path.join(sprintDir, "reviews/pass2.md"), [
    "# Review Pass 2",
    "## Spec Compliance",
    "PASS",
    "## Evidence Cross-Check",
    "PASS",
    "VERDICT: PASS",
    "",
  ].join("\n"));
  write(path.join(sprintDir, "runtime-verify.md"), "## Test Scenarios\n\nPASS\n");
  write(path.join(sprintDir, "rework-notes.md"), "# Rework\n\nPASS\n");
  write(path.join(sprintDir, "cleanup-pass.md"), "# Cleanup\n\nPASS\n");
  write(path.join(ai, "architecture/ARCHITECTURE.md"), "# Architecture\n");
  write(path.join(ai, "architecture/athena-9.9.3.md"), "# Athena 9.9.3\n");
  write(path.join(project, "implementation.txt"), "reviewed implementation\n");
  write(path.join(ai, "roadmap", ROADMAP, "items.yaml"), [
    `roadmap_slug: "${ROADMAP}"`,
    "total_items: 1",
    "items:",
    "  - slug: release",
    "    status: completed",
    "",
  ].join("\n"));
  gitRun(project, ["init", "-q"]);
  gitRun(project, ["config", "user.email", "athena@example.invalid"]);
  gitRun(project, ["config", "user.name", "Athena Runtime Contract"]);
  gitRun(project, ["add", "."]);
  gitRun(project, ["commit", "-qm", "reviewed implementation"]);
  const implementationCommit = gitRun(project, ["rev-parse", "HEAD"]);
  const outputArtifact = path.join(sprintDir, "evidence/runtime.txt");
  write(outputArtifact, "command: node test.js\nexit_code: 0\nsummary: runtime contract completed with exit 0\n");
  write(path.join(sprintDir, "evidence.yaml"), [
    "collected_evidence:",
    "  - tool_use_id: validation-1",
    "    ac_id: AC1",
    "    result: pass",
    "    source: command",
    "    command_or_artifact: node test.js",
    "    observed_at: 2026-07-13T08:00:00Z",
    "    summary: runtime contract completed with exit 0",
    "    exit_code: 0",
    "    output_artifact: evidence/runtime.txt",
    `    artifact_sha256: ${sha256File(outputArtifact)}`,
    `    implementation_commit: ${implementationCommit}`,
    "",
  ].join("\n"));
  write(path.join(sprintDir, "tdd-evidence.yaml"), [
    "schema_version: 1",
    "records:",
    "  - test_file: vibeCoding/scripts/test-athena-claude-9.9.3-runtime.cjs",
    "    red_command: node vibeCoding/scripts/test-athena-claude-9.9.3-runtime.cjs",
    "    red_summary: fail-open negative cases failed before implementation",
    "    red_observed_at: 2026-07-13T07:00:00Z",
    "    implementation_files: [delivery-gate.cjs]",
    "    implementation_observed_at: 2026-07-13T07:30:00Z",
    "    green_command: node vibeCoding/scripts/test-athena-claude-9.9.3-runtime.cjs",
    "    green_summary: runtime contract passed",
    "    green_observed_at: 2026-07-13T08:00:00Z",
    "",
  ].join("\n"));
  const ctx = { project, ai, sprintDir };
  bindReview(ctx, path.join(sprintDir, "reviews/pass2.md"));
  return ctx;
}

function expectBlocked(name, mutate, expected = "") {
  test(name, () => {
    const ctx = createCompleteProject();
    try {
      mutate(ctx);
      const gate = runGate(ctx.project);
      assert.strictEqual(gate.blocked, true, `gate passed unexpectedly; stderr=${gate.result.stderr}`);
      if (expected) assert.match(gate.reason, new RegExp(expected, "i"));
    } finally {
      rmProject(ctx.project);
    }
  });
}

test("gate accepts a complete Feature chain", () => {
  const ctx = createCompleteProject();
  try { assert.strictEqual(runGate(ctx.project).blocked, false); }
  finally { rmProject(ctx.project); }
});

expectBlocked("gate blocks missing _index", ({ ai }) => fs.rmSync(path.join(ai, "_index.md")), "index");
expectBlocked("gate blocks malformed _index", ({ ai }) => write(path.join(ai, "_index.md"), "not frontmatter\n"), "index");
expectBlocked("gate blocks unknown stage", ({ ai }) => write(path.join(ai, "_index.md"), indexBody({ stage: "banana" })), "stage");
expectBlocked("gate blocks missing assignments", ({ sprintDir }) => fs.rmSync(path.join(sprintDir, "subagent-assignments.jsonl")), "assignment");
expectBlocked("gate blocks malformed assignment JSONL", ({ sprintDir }) => write(path.join(sprintDir, "subagent-assignments.jsonl"), "{bad\n"), "malformed");
expectBlocked("gate blocks assignment schema extras", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-assignments.jsonl"), [assignment({ extra: true })]), "schema");
expectBlocked("gate blocks duplicate assignments", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-assignments.jsonl"), [assignment(), assignment({ timestamp: timestamp(3) })]), "ambiguous|duplicate");
expectBlocked("gate blocks assignment for another sprint", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-assignments.jsonl"), [assignment({ sprint_slug: "other" })]), "sprint");
expectBlocked("gate blocks no generator role", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-assignments.jsonl"), [assignment({ role: "reviewer" })]), "generator");
expectBlocked("gate blocks missing events", ({ sprintDir }) => fs.rmSync(path.join(sprintDir, "subagent-events.jsonl")), "event");
expectBlocked("gate blocks malformed event JSONL", ({ sprintDir }) => write(path.join(sprintDir, "subagent-events.jsonl"), "[]\n{bad\n"), "schema|malformed|object");
expectBlocked("gate blocks orphan stop", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-events.jsonl"), [event("SubagentStop", { agent_id: "orphan" })]), "orphan|assignment");
expectBlocked("gate blocks unbound start", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-events.jsonl"), [event("SubagentStart", { agent_id: "unbound" })]), "unbound|assignment");
expectBlocked("gate blocks duplicate start", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-events.jsonl"), [event("SubagentStart"), event("SubagentStart", { timestamp: timestamp(1) }), event("SubagentStop")]), "start");
expectBlocked("gate blocks duplicate stop", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-events.jsonl"), [event("SubagentStart"), event("SubagentStop"), event("SubagentStop", { timestamp: timestamp(3) })]), "stop");
expectBlocked("gate blocks missing stop", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-events.jsonl"), [event("SubagentStart")]), "stop");
expectBlocked("gate blocks stop before start", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-events.jsonl"), [event("SubagentStart", { timestamp: timestamp(3) }), event("SubagentStop", { timestamp: timestamp(2) })]), "precedes");
expectBlocked("gate blocks stop before assignment", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-assignments.jsonl"), [assignment({ timestamp: timestamp(3) })]), "assignment");
expectBlocked("gate blocks lifecycle type mismatch", ({ sprintDir }) => appendJsonl(path.join(sprintDir, "subagent-events.jsonl"), [event("SubagentStart"), event("SubagentStop", { agent_type: "reviewer" })]), "agent_type");
expectBlocked("gate blocks missing checklist", ({ sprintDir }) => fs.rmSync(path.join(sprintDir, "checklist.yaml")), "checklist");
expectBlocked("gate blocks incomplete checklist", ({ sprintDir }) => write(path.join(sprintDir, "checklist.yaml"), "tasks:\n  - id: T1\n    status: pending\n"), "checklist");
expectBlocked("gate blocks missing evidence", ({ sprintDir }) => fs.rmSync(path.join(sprintDir, "evidence.yaml")), "evidence");
expectBlocked("gate blocks unknown-only evidence", ({ sprintDir }) => write(path.join(sprintDir, "evidence.yaml"), "collected_evidence:\n  - tool_use_id: u1\n    result: unknown\n"), "pass|unknown");
expectBlocked("gate blocks failing evidence", ({ sprintDir }) => write(path.join(sprintDir, "evidence.yaml"), "collected_evidence:\n  - tool_use_id: f1\n    result: fail\n"), "fail");
expectBlocked("gate blocks missing reviews", ({ sprintDir }) => fs.rmSync(path.join(sprintDir, "reviews"), { recursive: true }), "review");
expectBlocked("gate blocks malformed pass filename", ({ sprintDir }) => write(path.join(sprintDir, "reviews/pass-final.md"), "VERDICT: PASS\n"), "malformed");
expectBlocked("gate uses latest passN", ({ sprintDir }) => write(path.join(sprintDir, "reviews/pass3.md"), "# Review\n## Spec Compliance\nVERDICT: REWORK\n"), "pass3|rework");
expectBlocked("gate requires PASS only", ({ sprintDir }) => write(path.join(sprintDir, "reviews/pass2.md"), "# Review\n## Spec Compliance\nVERDICT: CONCERNS\n"), "concerns|pass");
expectBlocked("gate requires spec compliance", ({ sprintDir }) => write(path.join(sprintDir, "reviews/pass2.md"), "# Review\nVERDICT: PASS\n"), "spec");

test("gate accepts evaluator.md's real bold-markdown PASS template", () => {
  const ctx = createCompleteProject();
  try {
    write(path.join(ctx.sprintDir, "reviews/pass2.md"), [
      "# Review Pass 2",
      "## Spec Compliance",
      "PASS",
      "## Evidence Cross-Check",
      "PASS",
      "## VERDICT (evaluator, cc-runtime-contract)",
      "",
      "**判定**: PASS",
      "",
      "总评: 4.8 / 5.0",
      "",
    ].join("\n"));
    bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, `gate incorrectly blocked a real PASS template; reason=${gate.reason}`);
  } finally { rmProject(ctx.project); }
});

expectBlocked(
  "gate blocks evaluator.md's real bold-markdown REWORK template",
  ({ sprintDir }) => write(path.join(sprintDir, "reviews/pass2.md"), [
    "# Review Pass 2",
    "## Spec Compliance",
    "PASS",
    "## VERDICT (evaluator, cc-runtime-contract)",
    "",
    "**判定**: REWORK",
    "",
  ].join("\n")),
  "rework",
);
expectBlocked("gate blocks missing roadmap", ({ ai }) => fs.rmSync(path.join(ai, "roadmap"), { recursive: true }), "roadmap");
expectBlocked("gate blocks incomplete roadmap", ({ ai }) => write(path.join(ai, "roadmap", ROADMAP, "items.yaml"), `roadmap_slug: ${ROADMAP}\ntotal_items: 1\nitems:\n  - slug: release\n    status: pending\n`), "roadmap|pending");
expectBlocked("gate blocks design content changed after review", ({ sprintDir }) => write(path.join(sprintDir, "design.md"), "# Design changed after review\n\n## Acceptance Criteria\n- [ ] AC1: 可观测 X\n\n## Round 1 · Critic Findings\n"), "design");
expectBlocked("gate blocks insufficient critic rounds", ctx => { write(path.join(ctx.ai, "_index.md"), indexBody({ critiqueMin: 2 })); write(path.join(ctx.sprintDir, "design.md"), "# Design\n\n## Acceptance Criteria\n- [ ] AC1: 可观测 X\n\n## Round 1 · Critic Findings\n"); bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md")); }, "critic");
expectBlocked("spec-gate blocks missing acceptance criteria", ({ sprintDir }) => { write(path.join(sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n"); }, "spec-gate");

// --- P0-3: CC must accept its own packaged Chinese template heading ---
test("spec-gate accepts the packaged Chinese acceptance heading", () => {
  const ctx = createCompleteProject();
  try {
    write(path.join(ctx.sprintDir, "design.md"), "# Design\n\n## 验收标准 (acceptance criteria)\n- [ ] AC1: 用户以输入 X 得到可观测输出 Y\n\n## Round 1 · Critic Findings\nPASS\n");
    bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, `Chinese heading rejected: ${gate.reason}`);
  } finally { rmProject(ctx.project); }
});

test("spec-gate accepts a bare Chinese acceptance heading", () => {
  const ctx = createCompleteProject();
  try {
    write(path.join(ctx.sprintDir, "design.md"), "# Design\n\n## 验收标准\n- [ ] AC1: 输入 X 输出 Y\n\n## Round 1 · Critic Findings\nPASS\n");
    bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, `bare Chinese heading rejected: ${gate.reason}`);
  } finally { rmProject(ctx.project); }
});

// --- design §4.3: semantic placeholder rejection (prefix/substring) ---
expectBlocked("spec-gate blocks placeholder criteria semantically", ({ sprintDir }) => {
  write(path.join(sprintDir, "design.md"), "# Design\n\n## Acceptance Criteria\n- [ ] TODO: define later\n- [ ] 登录 works correctly.\n- [ ] 待定\n\n## Round 1 · Critic Findings\nPASS\n");
}, "spec-gate");

// --- design §4.2 primary gate: plan/design → impl without criteria blocks ---
expectBlocked("impl-entry spec-gate blocks Feature without acceptance criteria", ({ ai, sprintDir }) => {
  write(path.join(ai, "_index.md"), indexBody({ stage: "impl" }));
  write(path.join(sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n");
}, "spec-gate");

test("impl-entry passes Feature with machine-recognizable criteria", () => {
  const ctx = createCompleteProject({ stage: "impl" });
  try {
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, `impl entry rejected valid criteria: ${gate.reason}`);
  } finally { rmProject(ctx.project); }
});

test("impl-entry does not force Quick through the Feature+ gate", () => {
  const ctx = createCompleteProject({ stage: "impl", pathType: "Quick" });
  try {
    write(path.join(ctx.sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n");
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, `Quick wrongly gated: ${gate.reason}`);
  } finally { rmProject(ctx.project); }
});

// --- design §4.2/§4.3: requirements fallback must be linked from design ---
expectBlocked("spec-gate rejects unlinked requirements artifacts", ({ ai, sprintDir }) => {
  write(path.join(sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n");
  write(path.join(ai, "requirements", "unrelated.md"), "# Req\n\n## Acceptance Criteria\n- [ ] AC1: observable outcome\n");
}, "spec-gate");

test("spec-gate accepts a requirements artifact linked from design", () => {
  const ctx = createCompleteProject({ stage: "impl" });
  try {
    write(path.join(ctx.sprintDir, "design.md"), "# Design\n\n验收标准见 requirements/linked-req.md\n\n## Round 1 · Critic Findings\nPASS\n");
    write(path.join(ctx.ai, "requirements", "linked-req.md"), "# Req\n\n## Acceptance Criteria\n- [ ] AC1: observable outcome Y\n");
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, `linked requirements rejected: ${gate.reason}`);
  } finally { rmProject(ctx.project); }
});

// --- design §4.5: escape needs reason + user authorization + unexpired expiry ---
expectBlocked("spec-gate exception without authorization fields fails closed", ({ ai, sprintDir }) => {
  write(path.join(ai, "_index.md"), indexBody({ extras: [`spec_gate_exception: "${SPRINT}"`] }));
  write(path.join(sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n");
}, "spec_gate_exception");

expectBlocked("expired spec-gate exception fails closed", ({ ai, sprintDir }) => {
  write(path.join(ai, "_index.md"), indexBody({ extras: [
    `spec_gate_exception: "${SPRINT}"`,
    'spec_gate_exception_reason: "emergency hotfix drill"',
    'spec_gate_exception_path: "Feature"',
    'spec_gate_exception_authorized_by: "user:release-owner"',
    'spec_gate_exception_authorized_at: "2026-07-13T08:00:00Z"',
    'spec_gate_exception_expiry: "2020-01-01T00:00:00Z"',
    'spec_gate_exception_removal_condition: "acceptance criteria restored"',
    'spec_gate_exception_emergency_hotfix: false',
    'spec_gate_exception_authorization_ref: "user-authorizations/release-owner.yaml"',
  ] }));
  writeAuthorization(sprintDir, { reason: "emergency hotfix drill", expiry: "2020-01-01T00:00:00Z" });
  write(path.join(sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n");
}, "过期");

test("fully authorized unexpired spec-gate exception allows impl entry only", () => {
  const ctx = createCompleteProject({ stage: "impl", extras: [
    `spec_gate_exception: "${SPRINT}"`,
    'spec_gate_exception_path: "Feature"',
    'spec_gate_exception_reason: "user-approved dogfood exception"',
    'spec_gate_exception_authorized_by: "user:release-owner"',
    'spec_gate_exception_authorized_at: "2026-07-13T08:00:00Z"',
    'spec_gate_exception_expiry: "2099-01-01T00:00:00Z"',
    'spec_gate_exception_removal_condition: "acceptance criteria restored"',
    'spec_gate_exception_emergency_hotfix: false',
    'spec_gate_exception_authorization_ref: "user-authorizations/release-owner.yaml"',
  ] });
  try {
    writeAuthorization(ctx.sprintDir, { reason: "user-approved dogfood exception" });
    write(path.join(ctx.sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n");
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, `authorized exception rejected: ${gate.reason}`);
  } finally { rmProject(ctx.project); }
});

expectBlocked("spec-gate exception rejects unstructured authorizer", ({ ai, sprintDir }) => {
  write(path.join(ai, "_index.md"), indexBody({ stage: "impl", extras: [
    `spec_gate_exception: "${SPRINT}"`,
    'spec_gate_exception_path: "Feature"',
    'spec_gate_exception_reason: "dogfood exception"',
    'spec_gate_exception_authorized_by: "someone said yes"',
    'spec_gate_exception_authorized_at: "2026-07-13T08:00:00Z"',
    'spec_gate_exception_expiry: "2099-01-01T00:00:00Z"',
    'spec_gate_exception_removal_condition: "acceptance criteria restored"',
    'spec_gate_exception_emergency_hotfix: false',
    'spec_gate_exception_authorization_ref: "user-authorizations/release-owner.yaml"',
  ] }));
  write(path.join(sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n");
}, "authorized_by|用户");

expectBlocked("spec-gate exception must be cleared before ship", ({ ai, sprintDir }) => {
  write(path.join(ai, "_index.md"), indexBody({ extras: [
    `spec_gate_exception: "${SPRINT}"`,
    'spec_gate_exception_path: "Feature"',
    'spec_gate_exception_reason: "temporary impl entry"',
    'spec_gate_exception_authorized_by: "user:release-owner"',
    'spec_gate_exception_authorized_at: "2026-07-13T08:00:00Z"',
    'spec_gate_exception_expiry: "2099-01-01T00:00:00Z"',
    'spec_gate_exception_removal_condition: "acceptance criteria restored"',
    'spec_gate_exception_emergency_hotfix: false',
    'spec_gate_exception_authorization_ref: "user-authorizations/release-owner.yaml"',
  ] }));
  writeAuthorization(sprintDir, { reason: "temporary impl entry" });
  write(path.join(sprintDir, "design.md"), "# Design\n\n## Round 1 · Critic Findings\nPASS\n");
}, "clear|移除|ship");

// --- design §4.4(2): every labeled AC must map to checklist/evidence ---
expectBlocked("ship blocks a labeled acceptance criterion without evidence mapping", ctx => {
  write(path.join(ctx.sprintDir, "design.md"), "# Design\n\n## Acceptance Criteria\n- [ ] AC1: 输出 X 可观测\n- [ ] AC2: 输出 Y 可观测\n\n## Round 1 · Critic Findings\nPASS\n");
  bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
}, "AC2");

expectBlocked("ship blocks unknown evidence for a labeled AC despite unrelated PASS", ctx => {
  write(path.join(ctx.sprintDir, "evidence.yaml"), [
    "collected_evidence:",
    "  - tool_use_id: ac1-unknown",
    "    result: unknown",
    "    criteria: [AC1]",
    "  - tool_use_id: unrelated-pass",
    "    result: pass",
    "    criteria: []",
    "",
  ].join("\n"));
  bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
}, "AC1|evidence");

expectBlocked("ship blocks checklist-only AC mapping", ctx => {
  write(path.join(ctx.sprintDir, "design.md"), "# Design\n\n## Acceptance Criteria\n- [ ] AC1: 输出 X 可观测\n- [ ] AC2: 输出 Y 可观测\n\n## Round 1 · Critic Findings\nPASS\n");
  write(path.join(ctx.sprintDir, "checklist.yaml"), "tasks:\n  - id: T1\n    title: implement AC1 and AC2\n    status: completed\n");
  bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
}, "AC2|evidence");

expectBlocked("ship blocks missing artifact evidence", ctx => {
  write(path.join(ctx.sprintDir, "evidence.yaml"), [
    "collected_evidence:",
    "  - tool_use_id: ac1-missing-artifact",
    "    ac_id: AC1",
    "    result: pass",
    "    source: artifact",
    "    command_or_artifact: missing/runtime-report.md",
    "    observed_at: 2026-07-13T08:00:00Z",
    "    summary: claimed artifact coverage",
    "",
  ].join("\n"));
  bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
}, "artifact|AC1|missing");

expectBlocked("ship blocks stale review evidence", ctx => {
  write(path.join(ctx.sprintDir, "reviews/pass3.md"), "# Review Pass 3\n\n## Spec Compliance\n\n| AC | Result |\n|---|---|\n| AC1 | SATISFIED |\n\n## Evidence Cross-Check\n\nPASS\n\nVERDICT: PASS\n");
  write(path.join(ctx.sprintDir, "evidence.yaml"), [
    "collected_evidence:",
    "  - tool_use_id: ac1-stale-review",
    "    ac_id: AC1",
    "    result: pass",
    "    source: review",
    "    command_or_artifact: reviews/pass2.md",
    "    observed_at: 2026-07-13T08:00:00Z",
    "    summary: stale review reference",
    "",
  ].join("\n"));
  bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass3.md"));
}, "latest|stale|pass2");

test("explicit final review acceptance can cover a labeled AC", () => {
  const ctx = createCompleteProject();
  try {
    write(path.join(ctx.sprintDir, "evidence.yaml"), [
      "collected_evidence:",
      "  - tool_use_id: ac1-review",
      "    ac_id: AC1",
      "    result: pass",
      "    source: review",
      "    command_or_artifact: reviews/pass2.md",
      "    observed_at: 2026-07-13T08:00:00Z",
      "    summary: final review explicitly accepted AC1",
      "",
    ].join("\n"));
    write(path.join(ctx.sprintDir, "reviews/pass2.md"), "# Review\n\n## Spec Compliance\n\n| AC | Result |\n|---|---|\n| AC1 | SATISFIED |\n\n## Evidence Cross-Check\n\nPASS\n\nVERDICT: PASS\n");
    bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, gate.reason);
  } finally { rmProject(ctx.project); }
});

test("review acceptance rejects negative phrases", () => {
  for (const phrase of ["NOT SATISFIED", "MISSING", "DEVIATED", "FAIL", "does not PASS"]) {
    const ctx = createCompleteProject();
    try {
      write(path.join(ctx.sprintDir, "evidence.yaml"), [
        "collected_evidence:",
        "  - tool_use_id: ac1-review",
        "    ac_id: AC1",
        "    result: pass",
        "    source: review",
        "    command_or_artifact: reviews/pass2.md",
        "    observed_at: 2026-07-13T08:00:00Z",
        "    summary: final review result",
        "",
      ].join("\n"));
      write(path.join(ctx.sprintDir, "reviews/pass2.md"), `# Review\n\n## Spec Compliance\n\n| AC | Result |\n|---|---|\n| AC1 | ${phrase} |\n\n## Evidence Cross-Check\n\nPASS\n\nVERDICT: PASS\n`);
      bindReview(ctx, path.join(ctx.sprintDir, "reviews/pass2.md"));
      assert.match(runGate(ctx.project).reason, /AC1/);
    } finally { rmProject(ctx.project); }
  }
});

test("review binding blocks protected index governance mutations", () => {
  for (const [oldText, newText] of [
    ['path: "Feature"', 'path: "Quick"'],
    [`current_sprint_slug: "${SPRINT}"`, 'current_sprint_slug: "other-sprint"'],
    ["skip_runtime_verify: false", "skip_runtime_verify: true"],
    ["skip_architecture_check: false", "skip_architecture_check: true"],
    ["skip_impl_subagent_check: false", "skip_impl_subagent_check: true"],
    ["plan_critique_min_rounds: 1", "plan_critique_min_rounds: 0"],
  ]) {
    const ctx = createCompleteProject();
    try {
      const index = path.join(ctx.ai, "_index.md");
      write(index, fs.readFileSync(index, "utf8").replace(oldText, newText));
      assert.strictEqual(runGate(ctx.project).blocked, true);
    } finally { rmProject(ctx.project); }
  }
});

test("pre-write spec-gate blocks first implementation write", () => {
  const ctx = createCompleteProject({ stage: "design" });
  try {
    write(path.join(ctx.sprintDir, "design.md"), "# Design\n");
    const result = runNode(GATE, {
      hook_event_name: "PreToolUse",
      cwd: ctx.project,
      tool_name: "Write",
      tool_input: { file_path: path.join(ctx.project, "src/app.js") },
    }, ctx.project);
    assert.match(result.stdout + result.stderr, /spec-gate/);
  } finally { rmProject(ctx.project); }
});

test("review binding allows state-only post-review change", () => {
  const ctx = createCompleteProject();
  try {
    write(path.join(ctx.sprintDir, "session-log.md"), "# Session\n");
    assert.strictEqual(runGate(ctx.project).blocked, false);
  } finally { rmProject(ctx.project); }
});

for (const [name, mutate] of [
  ["unstaged", ctx => write(path.join(ctx.project, "implementation.txt"), "changed after review\n")],
  ["staged", ctx => { write(path.join(ctx.project, "staged.txt"), "staged after review\n"); gitRun(ctx.project, ["add", "staged.txt"]); }],
  ["untracked", ctx => write(path.join(ctx.project, "untracked.txt"), "untracked after review\n")],
  ["committed", ctx => { write(path.join(ctx.project, "committed.txt"), "committed after review\n"); gitRun(ctx.project, ["add", "committed.txt"]); gitRun(ctx.project, ["commit", "-qm", "post-review implementation drift"]); }],
]) {
  test(`review binding blocks ${name} implementation drift`, () => {
    const ctx = createCompleteProject();
    try {
      mutate(ctx);
      assert.match(runGate(ctx.project).reason, /unreviewed implementation drift/);
    } finally { rmProject(ctx.project); }
  });
}

function memoryIndex({ latestDesign, latestReview }) {
  return [
    "---",
    'version: "9.9.3"',
    'path: "System"',
    'stage: "review"',
    `current_sprint_slug: "${SPRINT}"`,
    'next_action: "review"',
    "pointers:",
    `  latest_design: "${latestDesign}"`,
    `  latest_review: "${latestReview}"`,
    '  latest_cleanup: ""',
    '  latest_requirement: ""',
    "route_history: []",
    "---",
    "",
  ].join("\n");
}

test("SessionStart routes existing Tier2 pointers", () => {
  const ctx = createCompleteProject({ stage: "review" });
  try {
    write(path.join(ctx.ai, "_index.md"), memoryIndex({
      latestDesign: `sprints/${SPRINT}/design.md`,
      latestReview: `sprints/${SPRINT}/reviews/pass2.md`,
    }));
    const result = runNode(SESSION_START, { hook_event_name: "SessionStart", cwd: ctx.project }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.match(result.stdout, /Tier1 working memory/);
    assert.match(result.stdout, /Tier2 persistent memory/);
    assert.match(result.stdout, /_index\.md retrieval router/);
    assert.match(result.stdout, new RegExp(`sprints/${SPRINT}/design\\.md`));
    assert.doesNotMatch(result.stdout, /missing authoritative pointer/);
  } finally { rmProject(ctx.project); }
});

test("SessionStart warns on a missing authoritative pointer", () => {
  const ctx = createCompleteProject({ stage: "review" });
  try {
    write(path.join(ctx.ai, "_index.md"), memoryIndex({
      latestDesign: `sprints/${SPRINT}/missing-design.md`,
      latestReview: `sprints/${SPRINT}/reviews/pass2.md`,
    }));
    const result = runNode(SESSION_START, { hook_event_name: "SessionStart", cwd: ctx.project }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.match(result.stdout, /missing authoritative pointer/);
  } finally { rmProject(ctx.project); }
});

test("SessionStart warns on a stale latest review pointer", () => {
  const ctx = createCompleteProject({ stage: "review" });
  try {
    write(path.join(ctx.sprintDir, "reviews/pass3.md"), "VERDICT: PASS\n");
    write(path.join(ctx.ai, "_index.md"), memoryIndex({
      latestDesign: `sprints/${SPRINT}/design.md`,
      latestReview: `sprints/${SPRINT}/reviews/pass2.md`,
    }));
    const result = runNode(SESSION_START, { hook_event_name: "SessionStart", cwd: ctx.project }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.match(result.stdout, /stale authoritative pointer/);
  } finally { rmProject(ctx.project); }
});

test("SessionStart warns on escaping pointers and history overflow", () => {
  const ctx = createCompleteProject({ stage: "review" });
  try {
    let body = memoryIndex({ latestDesign: "", latestReview: "../../outside.md" });
    body = body.replace("route_history: []", "route_history: [1,2,3,4,5,6,7,8,9,10,11]");
    write(path.join(ctx.ai, "_index.md"), body);
    const result = runNode(SESSION_START, { hook_event_name: "SessionStart", cwd: ctx.project }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    assert.match(result.stdout, /escaping authoritative pointer/);
    assert.match(result.stdout, /route_history overflow/);
  } finally { rmProject(ctx.project); }
});

test("System gate accepts bound runtime, polish, architecture and evidence cross-check", () => {
  const ctx = createCompleteProject({ pathType: "System", critiqueMin: 1 });
  try {
    const gate = runGate(ctx.project);
    assert.strictEqual(gate.blocked, false, gate.reason);
  } finally { rmProject(ctx.project); }
});

test("System gate fails closed when review freshness Git is unavailable", () => {
  const ctx = createCompleteProject({ pathType: "System", critiqueMin: 1 });
  try {
    const gate = runGateNoGit(ctx.project);
    assert.strictEqual(gate.blocked, true, `gate should fail closed when git is unavailable; reason=${gate.reason}`);
    assert.match(gate.reason, /review freshness|git/i);
  } finally { rmProject(ctx.project); }
});

function readJsonl(pathname) {
  return fs.readFileSync(pathname, "utf8").split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line));
}

test("PostToolUse records explicit success from the event, not legacy exit_code", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    fs.rmSync(path.join(ctx.sprintDir, "evidence.yaml"));
    const payload = { ...fixture("posttool-success.json"), cwd: ctx.project };
    const result = runNode(EVIDENCE, payload, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    const rows = readJsonl(path.join(ctx.sprintDir, "tool-trace.jsonl"));
    assert.strictEqual(rows.at(-1).status, "pass");
    assert.strictEqual(rows.at(-1).exit_code, null);
    assert.match(fs.readFileSync(path.join(ctx.sprintDir, "evidence.yaml"), "utf8"), /result:\s*["']?pass/i);
  } finally { rmProject(ctx.project); }
});

test("env-var prefixed validation command is still recognized as evidence", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    fs.rmSync(path.join(ctx.sprintDir, "evidence.yaml"));
    const payload = {
      hook_event_name: "PostToolUse",
      cwd: ctx.project,
      tool_name: "Bash",
      tool_use_id: "bash-env-prefixed",
      tool_input: { command: "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest" },
      tool_response: { stdout: "ok" },
    };
    const result = runNode(EVIDENCE, payload, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    const evidence = fs.readFileSync(path.join(ctx.sprintDir, "evidence.yaml"), "utf8");
    assert.match(evidence, /tool_use_id:\s*["']?bash-env-prefixed/);
    assert.match(evidence, /result:\s*["']?pass/i);
  } finally { rmProject(ctx.project); }
});

test("PostToolUseFailure records fail, error, interrupt and duration", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    fs.rmSync(path.join(ctx.sprintDir, "evidence.yaml"));
    const payload = { ...fixture("posttool-failure.json"), cwd: ctx.project };
    const result = runNode(EVIDENCE, payload, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    const row = readJsonl(path.join(ctx.sprintDir, "tool-trace.jsonl")).at(-1);
    assert.strictEqual(row.status, "fail");
    assert.strictEqual(row.error, "exit status 7");
    assert.strictEqual(row.is_interrupt, false);
    assert.strictEqual(row.duration_ms, 42);
    assert.match(fs.readFileSync(path.join(ctx.sprintDir, "evidence.yaml"), "utf8"), /result:\s*["']?fail/i);
  } finally { rmProject(ctx.project); }
});

test("unknown hook event never becomes passing evidence", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    fs.rmSync(path.join(ctx.sprintDir, "evidence.yaml"));
    const result = runNode(EVIDENCE, {
      cwd: ctx.project,
      tool_name: "Bash",
      tool_use_id: "unknown",
      tool_input: { command: "python3 -m pytest" },
      tool_output: { exit_code: 0 },
    }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    const row = readJsonl(path.join(ctx.sprintDir, "tool-trace.jsonl")).at(-1);
    assert.strictEqual(row.status, "unknown");
    const body = fs.existsSync(path.join(ctx.sprintDir, "evidence.yaml"))
      ? fs.readFileSync(path.join(ctx.sprintDir, "evidence.yaml"), "utf8") : "";
    assert.doesNotMatch(body, /result:\s*["']?pass/i);
  } finally { rmProject(ctx.project); }
});

test("SubagentStart freezes sprint and Stop returns to that sprint", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    fs.rmSync(path.join(ctx.sprintDir, "subagent-events.jsonl"));
    fs.rmSync(path.join(ctx.sprintDir, "subagent-assignments.jsonl"));
    let result = runNode(TRACKER, { ...fixture("subagent-start.json"), cwd: ctx.project }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    result = runNode(TRACKER, {}, ctx.project, [
      "assign", "--agent-id", "cc-agent-77", "--task-name", "implement hooks", "--role", "generator",
    ]);
    assert.strictEqual(result.status, 0, result.stderr);
    write(path.join(ctx.ai, "_index.md"), indexBody({ stage: "review", sprint: "switched-sprint", roadmap: "" }));
    result = runNode(TRACKER, { ...fixture("subagent-stop.json"), cwd: ctx.project }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    const events = readJsonl(path.join(ctx.sprintDir, "subagent-events.jsonl"));
    assert.deepStrictEqual(events.map(row => row.event), ["SubagentStart", "SubagentStop"]);
    assert(events.every(row => row.sprint_slug === SPRINT));
    const assignments = readJsonl(path.join(ctx.sprintDir, "subagent-assignments.jsonl"));
    assert.strictEqual(assignments[0].task_name, "implement hooks");
    assert.strictEqual(assignments[0].role, "generator");
  } finally { rmProject(ctx.project); }
});

test("concurrent SubagentStart appends complete JSONL records", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    fs.rmSync(path.join(ctx.sprintDir, "subagent-events.jsonl"));
    const children = [];
    for (let i = 0; i < 16; i += 1) {
      children.push(spawnSync(process.execPath, [TRACKER], {
        cwd: ctx.project,
        input: JSON.stringify({ hook_event_name: "SubagentStart", cwd: ctx.project, agent_id: `a-${i}`, agent_type: "reviewer" }),
        encoding: "utf8",
      }));
    }
    assert(children.every(child => child.status === 0));
    const rows = readJsonl(path.join(ctx.sprintDir, "subagent-events.jsonl"));
    assert.strictEqual(rows.length, 16);
    assert.strictEqual(new Set(rows.map(row => row.agent_id)).size, 16);
  } finally { rmProject(ctx.project); }
});

test("ConfigChange audit stores metadata without configuration values", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    const result = runNode(CONFIG_AUDIT, {
      hook_event_name: "ConfigChange",
      cwd: ctx.project,
      source: "user_settings",
      file_path: "/tmp/settings.json",
      secret_value: "must-not-persist",
    }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    const body = fs.readFileSync(path.join(ctx.ai, ".snapshots/config-events.jsonl"), "utf8");
    assert.match(body, /user_settings/);
    assert.match(body, /settings\.json/);
    assert.doesNotMatch(body, /must-not-persist/);
  } finally { rmProject(ctx.project); }
});

test("StopFailure recorder stores only redacted failure metadata", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    const result = runNode(STOP_FAILURE, { ...fixture("stop-failure.json"), cwd: ctx.project }, ctx.project);
    assert.strictEqual(result.status, 0, result.stderr);
    const rows = readJsonl(path.join(ctx.sprintDir, "stop-failures.jsonl"));
    assert.strictEqual(rows[0].event, "StopFailure");
    assert.strictEqual(rows[0].error, "rate_limit");
    assert.doesNotMatch(JSON.stringify(rows[0]), /request could not complete|API Error/);
  } finally { rmProject(ctx.project); }
});

test("official PreCompact trigger=auto payload drives compact-snapshot.cjs to write a snapshot", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    const snapshotsDir = path.join(ctx.ai, ".snapshots");
    const before = fs.existsSync(snapshotsDir) ? new Set(fs.readdirSync(snapshotsDir)) : new Set();
    const result = spawnSync(process.execPath, [COMPACT_SNAPSHOT], {
      cwd: ctx.project,
      input: JSON.stringify({
        hook_event_name: "PreCompact",
        trigger: "auto",
        cwd: ctx.project,
        custom_instructions: "",
      }),
      encoding: "utf8",
      timeout: 15000,
    });
    assert.strictEqual(result.status, 0, result.stderr);
    assert(fs.existsSync(snapshotsDir), "compact-snapshot.cjs did not create .snapshots directory");
    const after = fs.readdirSync(snapshotsDir);
    const created = after.filter(name => !before.has(name) && name.startsWith("pre-compact-"));
    assert(created.length >= 1, `expected a new pre-compact-*.md snapshot; found=${after.join(",")}`);
    const snapshotBody = fs.readFileSync(path.join(snapshotsDir, created[0]), "utf8");
    assert.match(snapshotBody, /stage/);
  } finally { rmProject(ctx.project); }
});

function runGuard(project, command) {
  return runNode(GUARD, { hook_event_name: "PreToolUse", cwd: project, tool_name: "Bash", tool_input: { command } }, project);
}

test("guard ignores quoted git push text", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "printf '%s\\n' 'git push origin main'").status, 0); }
  finally { rmProject(ctx.project); }
});

test("guard blocks actual git push before ship", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "git push origin main").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks git push with global Git options", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "git -C . push origin main").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard ignores quoted destructive text", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "echo 'rm -rf /'").status, 0); }
  finally { rmProject(ctx.project); }
});

test("guard blocks actual destructive command", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "rm -rf /").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks destructive command behind sudo wrapper", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "sudo rm -rf /").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks git push hidden behind command substitution", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "echo $(git push origin main)").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks git push hidden behind backticks", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "echo `git push origin main`").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks command substitution executed inside double quotes", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, 'true && echo "$(rm -rf /)"').status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard ignores command substitution text literal inside single quotes", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "echo '$(git push origin main)'").status, 0); }
  finally { rmProject(ctx.project); }
});

test("guard ignores arithmetic expansion", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "echo $((1+2))").status, 0); }
  finally { rmProject(ctx.project); }
});

test("guard blocks rm -rf /* glob variant", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "rm -rf /*").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks rm -rf // double-slash variant", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "rm -rf //").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks rm -rf /. dot variant", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "rm -rf /.").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks rm -rf $HOME/* glob variant", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "rm -rf $HOME/*").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks xargs forwarding a destructive command", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "xargs rm -rf / < list.txt").status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard blocks eval forwarding a destructive command", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, 'eval "rm -rf /"').status, 2); }
  finally { rmProject(ctx.project); }
});

test("guard treats a real shell comment as inert: push before ship blocks only on the push, not on comment text shaped like rm -rf /", () => {
  const ctx = createCompleteProject({ stage: "review", roadmap: "" });
  try {
    const result = runGuard(ctx.project, "git push origin main # $(rm -rf /)");
    assert.strictEqual(result.status, 2);
    assert.match(result.stderr, /git push requires ship/i);
    assert.doesNotMatch(result.stderr, /recursive force removal/i);
  } finally { rmProject(ctx.project); }
});

test("guard allows the same comment-carried command at ship stage", () => {
  const ctx = createCompleteProject({ stage: "ship", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "git push origin main # $(rm -rf /)").status, 0); }
  finally { rmProject(ctx.project); }
});

test("guard ignores a literal '#' inside single quotes (not a comment start)", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try { assert.strictEqual(runGuard(ctx.project, "echo 'a # b'").status, 0); }
  finally { rmProject(ctx.project); }
});

test("guard does not treat a mid-word '#' as a comment start", () => {
  const ctx = createCompleteProject({ stage: "impl", roadmap: "" });
  try {
    assert.strictEqual(runGuard(ctx.project, "cat file#1").status, 0);
    assert.strictEqual(runGuard(ctx.project, 'echo "a#b"').status, 0);
  } finally { rmProject(ctx.project); }
});

test("native Git worktree contract keeps main checkout unchanged", () => {
  const repo = tempProject();
  const wt = `${repo}-wt`;
  try {
    const git = args => spawnSync("git", args, { cwd: repo, encoding: "utf8" });
    assert.strictEqual(git(["init", "-q"]).status, 0);
    assert.strictEqual(git(["config", "user.email", "athena@example.invalid"]).status, 0);
    assert.strictEqual(git(["config", "user.name", "Athena Contract"]).status, 0);
    write(path.join(repo, "base.txt"), "base\n");
    assert.strictEqual(git(["add", "base.txt"]).status, 0);
    assert.strictEqual(git(["commit", "-qm", "base"]).status, 0);
    write(path.join(repo, "head.txt"), "local head\n");
    assert.strictEqual(git(["add", "head.txt"]).status, 0);
    assert.strictEqual(git(["commit", "-qm", "local head"]).status, 0);
    const head = git(["rev-parse", "HEAD"]).stdout.trim();
    assert.strictEqual(git(["worktree", "add", "--detach", wt, "HEAD"]).status, 0);
    const wtHead = spawnSync("git", ["rev-parse", "HEAD"], { cwd: wt, encoding: "utf8" }).stdout.trim();
    assert.strictEqual(wtHead, head);
    write(path.join(wt, "worktree-only.txt"), "isolated\n");
    assert.strictEqual(fs.existsSync(path.join(repo, "worktree-only.txt")), false);
    assert.strictEqual(git(["worktree", "remove", "--force", wt]).status, 0);
  } finally {
    fs.rmSync(wt, { recursive: true, force: true });
    rmProject(repo);
  }
});

test("AI-guided migration guide documents 9.9.3 upgrade invariants", () => {
  const guide = path.join(CC, "..", "AI-MIGRATION-GUIDE.md");
  assert(fs.existsSync(guide), "AI-MIGRATION-GUIDE.md missing");
  const g = fs.readFileSync(guide, "utf8");
  for (const m of ["9.9.3", "preserve", "quantum-codegen", "spec-gate", "rollback"]) {
    assert(g.includes(m), `AI-MIGRATION-GUIDE.md missing marker: ${m}`);
  }
});

test("CC breadcrumb total context is at most ten lines", () => {
  const root = tempProject();
  const home = path.join(root, "home");
  const project = path.join(root, "project");
  try {
    write(path.join(project, ".ai_state/_index.md"), [
      "---",
      'path: "System"',
      'stage: "ship"',
      'current_sprint_slug: "breadcrumb-contract"',
      'next_action: "release_complete"',
      "---",
      "",
    ].join("\n"));
    write(
      path.join(home, ".claude/skills/pace/references/stages.md"),
      "## ship\n" + Array.from({ length: 14 }, (_, index) => `- obligation ${index + 1}`).join("\n") + "\n"
    );
    const result = spawnSync(process.execPath, [BREADCRUMB], {
      cwd: project,
      input: "{}",
      encoding: "utf8",
      timeout: 15000,
      env: { ...process.env, HOME: home },
    });
    assert.strictEqual(result.status, 0, result.stderr);
    const context = JSON.parse(result.stdout).hookSpecificOutput.additionalContext;
    assert(context.includes("~/.claude/skills/pace/references/stages.md"));
    assert(context.split(/\r?\n/).length <= 10, context);
  } finally {
    rmProject(root);
  }
});

test("CC evaluator caps one or two unresolved over-engineering findings at CONCERNS", () => {
  const body = fs.readFileSync(EVALUATOR, "utf8");
  assert.match(body, /unresolved_over_engineering\s*(?:>=|≥)\s*1/);
  assert.match(body, /(?:1\s*(?:or|\/|或|、|-|–)\s*2|exactly 1 or 2).{0,160}CONCERNS/s);
  assert.match(body, /resolved over-engineering.{0,200}(?:does not|不).{0,80}(?:cap|限制|触发)/s);
});

test("M5 artifacts are distributable package-root documents and not installed skills", () => {
  const packageRoots = [path.join(ROOT, "vibeCoding/claude/9.9.3"), path.join(ROOT, "vibeCoding/codex/9.9.3")];
  for (const packageRoot of packageRoots) {
    const spec = path.join(packageRoot, "build-spec-final.md");
    const harness = path.join(packageRoot, "harness-iteration-v1.1.md");
    assert(fs.existsSync(spec), `${spec} missing`);
    assert(fs.existsSync(harness), `${harness} missing`);
    const body = fs.readFileSync(harness, "utf8");
    assert.match(body, /package-root-only/);
    assert.match(body, /not installed|不安装/);
    assert.strictEqual(fs.existsSync(path.join(packageRoot, packageRoot.includes("claude") ? ".claude" : ".codex", "skills", "harness-iteration")), false);
  }
});

// Live floor/target matrix: attempts a real `npm exec` load of each pinned
// Claude Code release against the shipped settings.json in an isolated temp
// HOME. Network/npm-registry access is required; when unavailable the test
// records an explicit SKIP with the failure reason instead of assuming PASS.
function liveClaudeVersionCheck(pinnedVersion) {
  const home = tempProject();
  try {
    const claudeHome = path.join(home, ".claude");
    fs.mkdirSync(claudeHome, { recursive: true });
    fs.copyFileSync(path.join(CC, "settings.json"), path.join(claudeHome, "settings.json"));
    const run = spawnSync(
      "npm",
      ["exec", "--yes", `--package=@anthropic-ai/claude-code@${pinnedVersion}`, "--", "claude", "--version"],
      { encoding: "utf8", env: { ...process.env, HOME: home }, timeout: 120000 }
    );
    return run;
  } finally {
    rmProject(home);
  }
}

for (const pinnedVersion of process.env.ATHENA_SKIP_LIVE_CLAUDE_MATRIX === "1" ? [] : ["2.1.203", "2.1.206"]) {
  const label = `Claude Code ${pinnedVersion} loads shipped settings.json from a temp HOME`;
  const npmProbe = spawnSync("npm", ["--version"], { encoding: "utf8" });
  if (npmProbe.error) {
    skip(label, `npm unavailable: ${npmProbe.error.message}`);
    continue;
  }
  const result = liveClaudeVersionCheck(pinnedVersion);
  if (result.error) {
    skip(label, `npm exec failed to spawn: ${result.error.message}`);
    continue;
  }
  if (result.status !== 0) {
    skip(label, `npm exec exited ${result.status}; likely no registry access. stderr=${(result.stderr || "").slice(0, 200)}`);
    continue;
  }
  test(label, () => {
    assert.match(result.stdout, new RegExp(`^${pinnedVersion.replace(/\./g, "\\.")} \\(Claude Code\\)`));
  });
}

process.stdout.write(`SUMMARY pass=${passed} fail=${failed} skip=${skipped}\n`);
process.exit(failed === 0 ? 0 : 1);

#!/usr/bin/env node
/**
 * Athena v9.9.6 Claude Code delivery gate.
 *
 * Shared artifacts use the same schema and fail-closed semantics as CX 9.9.6.
 * Platform-specific hook payloads are normalized here; no private reasoning or
 * inferred tool success is used as delivery evidence.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { execFileSync } = require("child_process");

const VALID_PATHS = new Set(["Hotfix", "Bugfix", "Quick", "Feature", "Refactor", "System"]);
const VALID_STAGES = new Set([
  "brainstorm", "roadmap", "plan", "design", "impl",
  "runtime-verify", "review", "polish", "ship",
]);
const GENERATOR_PATHS = new Set(["Feature", "Refactor", "System"]);
const REFACTOR_SYSTEM = new Set(["Refactor", "System"]);
const SAFE_SLUG = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

class GateError extends Error {}

function findAiState(cwd) {
  let current = path.resolve(cwd);
  for (let depth = 0; depth < 8; depth += 1) {
    const candidate = path.join(current, ".ai_state");
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) return candidate;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return null;
}

function parseFrontmatter(content) {
  if (!content.startsWith("---\n") && !content.startsWith("---\r\n")) {
    throw new GateError("_index.md must start with YAML frontmatter");
  }
  const lines = content.split(/\r?\n/);
  const end = lines.indexOf("---", 1);
  if (end < 0) throw new GateError("_index.md frontmatter is not closed");
  const result = {};
  for (const raw of lines.slice(1, end)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const match = line.match(/^([A-Za-z0-9_.-]+)\s*:\s*(.*)$/);
    if (!match) continue;
    let value = match[2].trim();
    const quoted = value.match(/^"([^"]*)"|^'([^']*)'/);
    if (quoted) value = quoted[1] !== undefined ? quoted[1] : quoted[2];
    else if (value.includes(" #")) value = value.split(" #", 1)[0].trim();
    result[match[1]] = value;
  }
  return result;
}

function truthy(value) {
  return String(value || "").trim().toLowerCase() === "true";
}

function requireFile(filePath, label) {
  let content;
  try { content = fs.readFileSync(filePath, "utf8"); }
  catch (error) { throw new GateError(`missing ${label}: ${filePath}`); }
  if (!content.trim()) throw new GateError(`${label} is empty`);
  return content;
}

function parseTimestamp(value, label) {
  const millis = Date.parse(value);
  if (!Number.isFinite(millis)) throw new GateError(`${label}.timestamp must be ISO-8601`);
  return millis;
}

function exactKeys(value, expected, label) {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (JSON.stringify(actual) !== JSON.stringify(wanted)) {
    throw new GateError(`${label} must use schema v1 fields ${wanted.join(",")}`);
  }
}

function nonEmptyString(value, field, label) {
  if (typeof value[field] !== "string" || !value[field].trim()) {
    throw new GateError(`${label}.${field} must be a non-empty string`);
  }
}

function validateAssignment(value, label, sprintSlug) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new GateError(`${label} must be a JSON object`);
  }
  const fields = ["schema_version", "agent_id", "task_name", "role", "sprint_slug", "timestamp"];
  exactKeys(value, fields, label);
  if (value.schema_version !== 1) throw new GateError(`${label}.schema_version must be integer 1`);
  for (const field of fields.slice(1)) nonEmptyString(value, field, label);
  if (value.sprint_slug !== sprintSlug) throw new GateError(`${label}.sprint_slug does not match ${sprintSlug}`);
  return { ...value, parsedTimestamp: parseTimestamp(value.timestamp, label) };
}

function validateEvent(value, label, sprintSlug) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new GateError(`${label} must be a JSON object`);
  }
  const fields = ["schema_version", "event", "agent_id", "agent_type", "sprint_slug", "timestamp"];
  exactKeys(value, fields, label);
  if (value.schema_version !== 1) throw new GateError(`${label}.schema_version must be integer 1`);
  for (const field of fields.slice(1)) nonEmptyString(value, field, label);
  if (!new Set(["SubagentStart", "SubagentStop"]).has(value.event)) {
    throw new GateError(`${label}.event must be SubagentStart or SubagentStop`);
  }
  if (value.sprint_slug !== sprintSlug) throw new GateError(`${label}.sprint_slug does not match ${sprintSlug}`);
  return { ...value, parsedTimestamp: parseTimestamp(value.timestamp, label) };
}

function readJsonl(filePath, label, sprintSlug, validator) {
  const content = requireFile(filePath, label);
  const records = [];
  content.split(/\r?\n/).forEach((raw, index) => {
    if (!raw.trim()) return;
    let value;
    try { value = JSON.parse(raw); }
    catch (error) { throw new GateError(`malformed ${label} line ${index + 1}: ${error.message}`); }
    // lineNumber is the stable tiebreaker for same-timestamp events (see
    // validateGeneratorChain): the events file has 1-second resolution.
    records.push({ ...validator(value, `${label} line ${index + 1}`, sprintSlug), lineNumber: index + 1 });
  });
  if (!records.length) throw new GateError(`${label} contains no records`);
  return records;
}

function lifecycleKey(record) {
  return `${record.agent_id}\u0000${record.sprint_slug}`;
}

function validateGeneratorChain(sprintDir, sprintSlug) {
  const assignments = readJsonl(
    path.join(sprintDir, "subagent-assignments.jsonl"),
    "subagent assignments", sprintSlug, validateAssignment,
  );
  const events = readJsonl(
    path.join(sprintDir, "subagent-events.jsonl"),
    "subagent events", sprintSlug, validateEvent,
  );
  const assignmentMap = new Map();
  for (const row of assignments) {
    const key = lifecycleKey(row);
    if (assignmentMap.has(key)) throw new GateError(`ambiguous duplicate assignment for agent_id=${row.agent_id}`);
    assignmentMap.set(key, row);
  }
  if (![...assignmentMap.values()].some(row => row.role === "generator")) {
    throw new GateError("no role=generator assignment found");
  }
  // generator-chain 只校验 generator 生命周期。events 由 hook 记录全部 subagent 类型, 而
  // agent_type 记的是平台 subagent 类型, 不区分 Athena 角色, 无法据此识别 generator;
  // 唯一可靠判据是 assign 握手写入的 role=generator。critic/reviewer/evaluator/spec-compliance
  // 无握手且多轮 Start/Stop, 不属于本校验范围, 按 role 过滤后跳过, 避免误报 unbound。
  const generatorKeys = new Set(
    [...assignmentMap.values()].filter(row => row.role === "generator").map(lifecycleKey),
  );
  const eventMap = new Map();
  for (const row of events) {
    const key = lifecycleKey(row);
    if (!generatorKeys.has(key)) continue;
    if (!eventMap.has(key)) eventMap.set(key, []);
    eventMap.get(key).push(row);
  }
  for (const [key, assignment] of assignmentMap.entries()) {
    if (assignment.role !== "generator") continue;
    // P2 fix (2026-07-25, .ai_state/proposals.md P2; 台账见 .ai_state/harness-patches.md):
    // "exactly one Start/Stop" made every legitimately resumed generator structurally
    // unshippable — an API blip plus SendMessage continuation appends a second
    // Start/Stop pair to the same agent_id. What this check actually needs to guarantee
    // is that the work *settled*, not that it physically ran once: at least one Start,
    // at least one Stop, and the final lifecycle event is a Stop. A truncated agent
    // (Starts with no Stop, or a Stop only in the middle) still blocks, which is the
    // correct outcome — it really did not finish; releasing that case stays explicit via
    // skip_impl_subagent_check (compound/2026-07-22-decision-e3-4-generator-truncation-
    // subagent-check.md).
    // Sort is stable for equal timestamps: subagent-events.jsonl has 1-second
    // resolution, so a same-second Start/Stop pair must keep file append order,
    // otherwise "which event is last" would be arbitrary.
    const rows = [...(eventMap.get(key) || [])]
      .sort((a, b) => a.parsedTimestamp - b.parsedTimestamp || a.lineNumber - b.lineNumber);
    const starts = rows.filter(row => row.event === "SubagentStart");
    const stops = rows.filter(row => row.event === "SubagentStop");
    if (starts.length < 1) throw new GateError(`agent_id=${assignment.agent_id} requires at least one SubagentStart`);
    if (stops.length < 1) throw new GateError(`agent_id=${assignment.agent_id} requires at least one SubagentStop`);
    if (rows.at(-1).event !== "SubagentStop") {
      throw new GateError(`agent_id=${assignment.agent_id} must end with SubagentStop (work not settled)`);
    }
    // Stronger than the old first-Start-vs-first-Stop comparison and resume-safe: every
    // event recorded for this agent_id must agree on agent_type.
    if (new Set(rows.map(row => row.agent_type)).size !== 1) {
      throw new GateError(`inconsistent agent_type lifecycle for agent_id=${assignment.agent_id}`);
    }
    const firstStart = starts[0];
    const lastStop = stops.at(-1);
    if (assignment.parsedTimestamp < firstStart.parsedTimestamp) {
      throw new GateError(`assignment handshake precedes SubagentStart for agent_id=${assignment.agent_id}`);
    }
    if (lastStop.parsedTimestamp < firstStart.parsedTimestamp) {
      throw new GateError(`SubagentStop precedes SubagentStart for agent_id=${assignment.agent_id}`);
    }
    if (lastStop.parsedTimestamp < assignment.parsedTimestamp) {
      throw new GateError(`SubagentStop precedes assignment handshake for agent_id=${assignment.agent_id}`);
    }
  }
}

function scalar(value) {
  let result = String(value || "").trim();
  if (result.includes(" #")) result = result.split(" #", 1)[0].trim();
  if (result.length >= 2 && result[0] === result.at(-1) && ["'", '"'].includes(result[0])) {
    result = result.slice(1, -1);
  }
  return result.trim();
}

function validateChecklist(filePath) {
  const content = requireFile(filePath, "checklist.yaml");
  const tasks = [...content.matchAll(/^\s*-\s+id\s*:\s*([^#\n]+)/gm)];
  const statuses = [...content.matchAll(/^\s+status\s*:\s*([^#\n]+)/gm)].map(match => scalar(match[1]).toLowerCase());
  if (!tasks.length) throw new GateError("checklist.yaml has no tasks");
  if (statuses.length < tasks.length) throw new GateError("checklist.yaml has tasks without status");
  if (statuses.some(status => status !== "completed")) throw new GateError(`checklist.yaml is incomplete: ${statuses.join(",")}`);
}

function validateEvidence(filePath) {
  const content = requireFile(filePath, "evidence.yaml");
  if (!/^collected_evidence\s*:\s*(?:#.*)?$/m.test(content)) {
    throw new GateError("evidence.yaml lacks collected_evidence list");
  }
  const items = [...content.matchAll(/^\s*-\s+tool_use_id\s*:\s*([^#\n]*)/gm)];
  if (!items.length) throw new GateError("evidence.yaml contains no evidence records");
  const results = [];
  items.forEach((item, index) => {
    const id = scalar(item[1]);
    if (!id || ["[]", "null", "~"].includes(id)) throw new GateError("evidence.yaml contains an empty tool_use_id");
    const end = index + 1 < items.length ? items[index + 1].index : content.length;
    const block = content.slice(item.index + item[0].length, end);
    const matches = [...block.matchAll(/^\s+result\s*:\s*([^#\n]+)/gm)];
    if (matches.length !== 1) throw new GateError(`evidence ${id} must have exactly one result`);
    const result = scalar(matches[0][1]).toLowerCase();
    if (!["pass", "fail", "unknown"].includes(result)) throw new GateError(`evidence ${id} has unsupported result ${result}`);
    results.push(result);
  });
  if (results.includes("fail")) throw new GateError("evidence.yaml contains failing evidence");
  if (!results.includes("pass")) throw new GateError("evidence.yaml has no explicit pass; unknown-only is insufficient");
  return parseEvidenceRecords(filePath);
}

function selectLatestReview(reviewsDir) {
  let names;
  try { names = fs.readdirSync(reviewsDir); }
  catch (_) { throw new GateError(`missing reviews directory: ${reviewsDir}`); }
  const numbered = [];
  for (const name of names) {
    if (!name.startsWith("pass") || !name.endsWith(".md")) continue;
    const match = name.match(/^pass([1-9]\d*)\.md$/);
    if (!match) throw new GateError(`malformed numbered review filename: ${name}`);
    numbered.push([Number(match[1]), path.join(reviewsDir, name)]);
  }
  if (!numbered.length) throw new GateError("reviews directory has no numbered passN.md review");
  numbered.sort((a, b) => a[0] - b[0]);
  return numbered.at(-1)[1];
}

function finalVerdict(content, reviewName) {
  const verdicts = [];
  for (const raw of content.split(/\r?\n/)) {
    // Markdown bold (**判定**: PASS) can place "*" anywhere inline, not just at
    // the line edges — strip every "*" before matching so the evaluator's own
    // template (see agents/evaluator.md) parses the same as plain text.
    const line = raw.trim().replace(/\*/g, "").trim();
    let match = line.match(/^(?:Evaluator\s+)?VERDICT\s*:\s*([A-Za-z][A-Za-z _-]*?)\.?$/i);
    if (!match) match = line.match(/^判定\s*:\s*([A-Za-z][A-Za-z _-]*?)\.?$/i);
    if (match) verdicts.push(match[1].trim().toUpperCase().replace(/\s+/g, " "));
  }
  if (!verdicts.length) throw new GateError(`${reviewName} has no explicit VERDICT line`);
  return verdicts.at(-1);
}

function validateReview(reviewPath, pathType) {
  const content = requireFile(reviewPath, `latest review ${path.basename(reviewPath)}`);
  const verdict = finalVerdict(content, path.basename(reviewPath));
  if (verdict !== "PASS") throw new GateError(`latest review ${path.basename(reviewPath)} VERDICT is ${verdict}; expected PASS`);
  if (!content.includes("## Spec Compliance")) throw new GateError(`latest review ${path.basename(reviewPath)} lacks ## Spec Compliance`);
  // K1 (2026-07-28, 台账 W31): Evidence Cross-Check 段不再由 gate 强制 — evaluator prompt
  // 仍产出该段 (行为不变), 但缺段不 block; 段落存在性检查是文档剧场, 判定由 VERDICT 承载。
  return content;
}

function gitText(cwd, args, label) {
  try {
    return execFileSync("git", args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  } catch (error) {
    const detail = String(error.stderr || error.stdout || error.message || "").trim();
    throw new GateError(`review freshness git check failed (${label}): ${detail}`);
  }
}

/**
 * Resolve the main repository root for `cwd`, or null when it cannot be determined.
 *
 * P3 fix (2026-07-25, .ai_state/proposals.md P3; 台账见 .ai_state/harness-patches.md):
 * inside a linked worktree `--show-toplevel` returns the *worktree* path, so the gate
 * resolved `.ai_state` against a fresh checkout that legitimately lacks the archive and
 * blocked every ship. `--git-common-dir` points at the main repo's .git from anywhere in
 * the repo; `--path-format=absolute` (git >= 2.31) keeps it absolute in the main checkout
 * too, where the bare form prints a relative ".git". Submodules (`.git/modules/<name>`)
 * and bare repos (`repo.git`) yield no ".git" basename, so they fall back to
 * `--show-toplevel` instead of being permanently mis-rooted.
 *
 * Non-throwing by contract: this runs on every PreToolUse, including writes in
 * directories that are not Git repositories at all — any failure returns null and the
 * caller keeps the pre-existing cwd semantics rather than crashing the hook.
 */
function tryRepoRoot(cwd) {
  const run = args => {
    try {
      return execFileSync("git", args, {
        cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: 15000,
      }).trim();
    } catch (_) {
      return "";
    }
  };
  const commonDir = run(["rev-parse", "--path-format=absolute", "--git-common-dir"]);
  if (commonDir && path.basename(commonDir) === ".git") return path.dirname(commonDir);
  return run(["rev-parse", "--show-toplevel"]) || null;
}

// Manifest required-file sets are tiered by path (P8): a Feature sprint has no
// polish/rework artifacts by design, and version-specific architecture notes
// (e.g. architecture/athena-9.9.6.md) belong to individual sprints, not the
// generic schema. Files beyond the required tier are declared-then-verified:
// whatever the manifest lists gets hash-checked, nothing extra is mandated.
// 2026-07-28 gate-descaling (台账 .ai_state/harness-patches.md): 必钉集从"文档存在性"收
// 缩到"行为证据"。checklist.yaml 降为可选 (存在才验), evidence.yaml 是 hook 自动记账
// (P1 教训: 钉住 hook 持续改写的文件 = 结构性哈希漂移), cleanup-pass/architecture 在
// validateShip 有独立存在性检查 — 全部移出必钉集。declared-then-verified 语义不变:
// manifest 里声明了就哈希校验。
const MANIFEST_REQUIRED_CORE = ["design.md"];
const MANIFEST_REQUIRED_REFACTOR_SYSTEM = [
  ...MANIFEST_REQUIRED_CORE, "runtime-verify.md",
];

function parseReviewManifest(filePath, pathType) {
  const content = requireFile(filePath, "review-manifest.yaml");
  let schemaVersion = "";
  let implementationCommit = "";
  let indexGovernanceSha256 = "";
  let inFiles = false;
  const files = {};
  for (const raw of content.split(/\r?\n/)) {
    if (!raw.trim() || raw.trimStart().startsWith("#")) continue;
    if (raw.startsWith("  ")) {
      if (!inFiles) throw new GateError("review-manifest has nested values outside files");
      const match = raw.match(/^\s{2}(["']?)(.+?)\1\s*:\s*(["'])([0-9a-f]{64})\3\s*$/);
      if (!match) throw new GateError(`malformed review-manifest file hash line: ${raw}`);
      if (Object.hasOwn(files, match[2])) throw new GateError(`duplicate review-manifest path: ${match[2]}`);
      files[match[2]] = match[4];
      continue;
    }
    inFiles = false;
    const match = raw.match(/^([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$/);
    if (!match) throw new GateError(`malformed review-manifest line: ${raw}`);
    const value = scalar(match[2]);
    if (match[1] === "schema_version") schemaVersion = value;
    else if (match[1] === "implementation_commit") implementationCommit = value;
    else if (match[1] === "index_governance_sha256") indexGovernanceSha256 = value;
    else if (match[1] === "files" && !value) inFiles = true;
    else throw new GateError(`unsupported review-manifest field: ${match[1]}`);
  }
  const required = REFACTOR_SYSTEM.has(pathType) ? MANIFEST_REQUIRED_REFACTOR_SYSTEM : MANIFEST_REQUIRED_CORE;
  if (schemaVersion !== "1" || !/^[0-9a-f]{40}$/.test(implementationCommit) || !/^[0-9a-f]{64}$/.test(indexGovernanceSha256)) {
    throw new GateError("review-manifest requires schema_version=1, a 40-hex implementation_commit, and a 64-hex index_governance_sha256");
  }
  const missing = required.filter(name => !Object.hasOwn(files, name));
  if (missing.length) {
    throw new GateError(`review-manifest missing required file hashes for ${pathType}: ${missing.join(", ")}`);
  }
  return { implementationCommit, indexGovernanceSha256, files };
}

const INDEX_GOVERNANCE_FIELDS = [
  "path", "current_sprint_slug", "skip_polish", "skip_runtime_verify",
  "skip_architecture_check", "skip_impl_subagent_check",
  "plan_critique_disabled", "plan_critique_min_rounds",
];

function indexGovernanceSha256(fm) {
  const protectedFields = {};
  for (const key of [...INDEX_GOVERNANCE_FIELDS].sort()) protectedFields[key] = String(fm[key] || "");
  return crypto.createHash("sha256").update(JSON.stringify(protectedFields)).digest("hex");
}

function validateIndexGovernance(sprintDir, fm) {
  const manifest = parseReviewManifest(path.join(sprintDir, "review-manifest.yaml"), fm.path);
  if (manifest.indexGovernanceSha256 !== indexGovernanceSha256(fm)) {
    throw new GateError("review-manifest index governance does not match protected _index fields");
  }
}

function validateReviewBinding(reviewContent, reviewPath, sprintDir, aiState, cwd, fm) {
  const designMatches = [...reviewContent.matchAll(/^Reviewed design sha256:\s*([0-9a-f]{64})\s*$/gm)];
  const commitMatches = [...reviewContent.matchAll(/^Reviewed implementation commit:\s*([0-9a-f]{40})\s*$/gm)];
  const manifestMatches = [...reviewContent.matchAll(/^Reviewed state manifest sha256:\s*([0-9a-f]{64})\s*$/gm)];
  if (designMatches.length !== 1 || commitMatches.length !== 1 || manifestMatches.length !== 1) {
    throw new GateError("latest PASS review must contain exactly one design, implementation commit, and state-manifest binding");
  }
  const design = requireFile(path.join(sprintDir, "design.md"), "design.md");
  const digest = crypto.createHash("sha256").update(design, "utf8").digest("hex");
  if (designMatches[0][1] !== digest) {
    throw new GateError("Reviewed design sha256 does not match current authoritative design.md");
  }
  const reviewedCommit = commitMatches[0][1];
  const manifestPath = path.join(sprintDir, "review-manifest.yaml");
  const manifestBuffer = fs.readFileSync(manifestPath);
  if (crypto.createHash("sha256").update(manifestBuffer).digest("hex") !== manifestMatches[0][1]) {
    throw new GateError("Reviewed state manifest sha256 does not match review-manifest.yaml");
  }
  const manifest = parseReviewManifest(manifestPath, fm.path);
  if (manifest.implementationCommit !== reviewedCommit) {
    throw new GateError("review-manifest implementation_commit does not match final review binding");
  }
  if (manifest.indexGovernanceSha256 !== indexGovernanceSha256(fm)) {
    throw new GateError("review-manifest index governance does not match protected _index fields");
  }
  const root = gitText(cwd, ["rev-parse", "--show-toplevel"], "repository root").trim();
  if (!root) throw new GateError("review freshness cannot determine Git repository root");
  // 治理哈希只对**版本化**文件有意义。被 gitignore 的档案 (典型: evidence.yaml ——
  // evidence-collector 每次 PostToolUse 都追加, 消费侧项目因此有意把它排除出 git)
  // 哈希必然漂移, 且不在 git 里就没有任何来源可还原成 manifest 记录的值; 重算 manifest
  // 去迁就它又正是 block 消息自己禁止的绕过。净效果是**一个已 ship 的 sprint 在往后每个
  // 新会话都卡死且无合法出路** (2026-07-27 实测)。故未跟踪文件跳过哈希校验并留声明。
  const tracked = new Set(
    gitText(root, ["ls-files"], "tracked files").split(/\r?\n/).map(line => line.trim()).filter(Boolean),
  );
  for (const [name, expectedHash] of Object.entries(manifest.files)) {
    const target = name.startsWith("architecture/") ? path.join(aiState, name) : path.join(sprintDir, name);
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) throw new GateError(`review-manifest target missing: ${name}`);
    const rel = path.relative(fs.realpathSync(root), fs.realpathSync(target)).split(path.sep).join("/");
    if (!tracked.has(rel)) {
      process.stderr.write(`[delivery-gate] manifest 跳过未跟踪文件的哈希校验: ${name} (gitignored, 无版本化真相源)\n`);
      continue;
    }
    const actual = crypto.createHash("sha256").update(fs.readFileSync(target)).digest("hex");
    if (actual !== expectedHash) throw new GateError(`review-manifest hash mismatch: ${name}`);
  }
  gitText(root, ["cat-file", "-e", `${reviewedCommit}^{commit}`], "reviewed commit exists");
  gitText(root, ["merge-base", "--is-ancestor", reviewedCommit, "HEAD"], "reviewed commit ancestor");
  const changed = new Set();
  for (const [args, label] of [
    [["diff", "--name-only", `${reviewedCommit}..HEAD`], "committed drift"],
    [["diff", "--name-only"], "working drift"],
    [["diff", "--name-only", "--cached"], "staged drift"],
    [["ls-files", "--others", "--exclude-standard"], "untracked drift"],
  ]) {
    for (const line of gitText(root, args, label).split(/\r?\n/)) if (line.trim()) changed.add(line.trim());
  }
  const implementationDrift = [...changed].filter(file => file !== ".ai_state" && !file.startsWith(".ai_state/")).sort();
  if (implementationDrift.length) {
    throw new GateError(`unreviewed implementation drift after Reviewed implementation commit: ${implementationDrift.slice(0, 8).join(", ")}`);
  }
  const sprintRel = path.relative(fs.realpathSync(root), fs.realpathSync(sprintDir)).split(path.sep).join("/");
  const allowedExact = new Set([
    ".ai_state/_index.md",
    ...Object.keys(manifest.files).filter(name => !name.startsWith("architecture/")).map(name => `${sprintRel}/${name}`),
    `${sprintRel}/review-manifest.yaml`, `${sprintRel}/ship-receipt.md`, `${sprintRel}/session-log.md`,
    `${sprintRel}/subagent-assignments.jsonl`, `${sprintRel}/subagent-events.jsonl`, `${sprintRel}/subagent-log.md`,
    // Hook-maintained process bookkeeping, not review subjects: token-usage-collector.cjs
    // writes token-usage.yaml on every Stop (before this gate runs) and stop-failure-
    // recorder.cjs appends stop-failures.jsonl on every block — so a blocked ship could
    // never become unblocked, the recorder's own write was the next drift.
    // token-usage.jsonl kept for back-compat with pre-9.9.3 sprints.
    // 9.9.3 已修 → 9.9.6 升级回归 → 2026-07-25 重修, 台账见 .ai_state/harness-patches.md
    `${sprintRel}/token-usage.jsonl`, `${sprintRel}/token-usage.yaml`,
    `${sprintRel}/stop-failures.jsonl`, `${sprintRel}/tool-trace.jsonl`,
    ".ai_state/architecture/ARCHITECTURE.md", ".ai_state/architecture/athena-9.9.6.md",
    // P13 fix (2026-07-28, .ai_state/proposals.md P13): 过程台账不是被审对象。review 绑定
    // 之后补一笔 harness-patches/proposals (正确行为: 修复轮的安装态改动要登记、block 时要
    // 写提案) 不得变成卡死 ship 的 "unreviewed drift"。light-ship 护栏不受影响 —— diff 含
    // harness-patches.md 依然强制走全契约 (isLightShipFile 分支未动)。
    ".ai_state/harness-patches.md", ".ai_state/proposals.md",
  ]);
  const stateDrift = [...changed].filter(file => file.startsWith(".ai_state/")
    && !allowedExact.has(file)
    && !file.startsWith(`${sprintRel}/reviews/`)
    && !file.startsWith(`${sprintRel}/evidence/`)
    && !file.startsWith(`${sprintRel}/user-authorizations/`)).sort();
  if (stateDrift.length) throw new GateError(`unreviewed .ai_state drift outside post-review allowlist: ${stateDrift.slice(0, 8).join(", ")}`);
  return reviewedCommit;
}

function validateTddEvidence(filePath) {
  const content = requireFile(filePath, "tdd-evidence.yaml");
  const records = [...content.matchAll(/^\s*-\s+test_file\s*:\s*([^#\n]+)/gm)];
  if (!records.length) throw new GateError("tdd-evidence.yaml contains no red-to-green records");
  records.forEach((record, index) => {
    const end = index + 1 < records.length ? records[index + 1].index : content.length;
    const block = content.slice(record.index, end);
    const values = {};
    for (const key of ["red_command", "red_summary", "red_observed_at", "implementation_files", "implementation_observed_at", "green_command", "green_summary", "green_observed_at"]) {
      values[key] = evidenceField(block, key);
    }
    if (Object.values(values).some(value => !value)) throw new GateError("tdd-evidence record is missing red/implementation/green fields");
    const red = parseUtcTimestamp(values.red_observed_at, "tdd red_observed_at");
    const implementation = parseUtcTimestamp(values.implementation_observed_at, "tdd implementation_observed_at");
    const green = parseUtcTimestamp(values.green_observed_at, "tdd green_observed_at");
    if (!(red < implementation && implementation < green)) {
      throw new GateError("tdd-evidence timestamps must satisfy red < implementation < green");
    }
  });
}

function validateRoadmap(aiState, roadmapSlug, sprintSlug) {
  if (!SAFE_SLUG.test(roadmapSlug)) throw new GateError(`invalid current_roadmap_slug ${roadmapSlug}`);
  const filePath = path.join(aiState, "roadmap", roadmapSlug, "items.yaml");
  const content = requireFile(filePath, `roadmap/${roadmapSlug}/items.yaml`);
  // Roadmap slug consistency: the current template declares a top-level `slug:`; the
  // pre-9.6 template used `roadmap_slug:`. Accept either so migrated roadmaps still pass.
  const declared = [...content.matchAll(/^(?:roadmap_slug|slug)\s*:\s*([^#\n]*)/gm)];
  if (declared.length < 1 || scalar(declared[0][1]) !== roadmapSlug) {
    throw new GateError("roadmap slug is missing or mismatched");
  }
  // Parse items. The current template opens each item with `- id:` (slug is a child field);
  // the pre-9.6 template opened with `- slug:`. Try id-first, fall back to slug-first.
  let itemStarts = [...content.matchAll(/^\s*-\s+id\s*:\s*[^#\n]*/gm)];
  if (itemStarts.length === 0) itemStarts = [...content.matchAll(/^\s*-\s+slug\s*:\s*[^#\n]*/gm)];
  if (itemStarts.length < 1) throw new GateError("roadmap items.yaml declares no items");
  // 9.9.6 mid-program fix (see .ai_state/proposals.md P1): shipping ONE sprint only requires
  // the roadmap item it maps to (the item whose slug is a trailing segment of the sprint
  // slug) to be done/completed — sibling items may still be pending. Requiring EVERY item
  // completed made every mid-program sprint ship structurally impossible. An ad-hoc sprint
  // with no matching item is not gated on item status here; its own per-sprint 9.9.6
  // contract (manifest / reviews / tdd-evidence) still applies below.
  let matched = null;
  itemStarts.forEach((item, index) => {
    const end = index + 1 < itemStarts.length ? itemStarts[index + 1].index : content.length;
    const block = content.slice(item.index, end);
    const slugRow = block.match(/^\s+slug\s*:\s*([^#\n]*)/m) || block.match(/-\s+slug\s*:\s*([^#\n]*)/);
    if (!slugRow) return;
    const itemSlug = scalar(slugRow[1]);
    if (!itemSlug || !sprintSlug || !sprintSlug.endsWith(itemSlug)) return;
    const statusRow = block.match(/^\s+status\s*:\s*([^#\n]*)/m);
    matched = { slug: itemSlug, status: statusRow ? scalar(statusRow[1]).toLowerCase() : "" };
  });
  if (matched && matched.status !== "completed" && matched.status !== "done") {
    throw new GateError(`roadmap item ${matched.slug} status is ${matched.status || "(none)"}; ship requires it completed/done`);
  }
}

function gitLines(cwd, args) {
  try {
    return {
      ok: true,
      lines: execFileSync("git", args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: 15000 })
        .split(/\r?\n/).map(line => line.trim()).filter(Boolean),
    };
  } catch (error) {
    process.stderr.write(`[delivery-gate] git ${args.join(" ")} failed: ${error.message}\n`);
    return { ok: false, lines: [] };
  }
}

/**
 * Count files changed for the architecture-doc gate. If every git call fails
 * (e.g. git itself is unavailable), we cannot confirm the diff is really
 * empty — treating that the same as a verified zero-file diff would let a
 * large Refactor/System change silently skip the ARCHITECTURE.md
 * requirement (fail-open). So an all-failed git probe returns Infinity,
 * which always trips the ">= 5" architecture-doc check; a genuinely empty
 * diff (git ran, returned nothing) still counts as its real, possibly small,
 * number of files.
 */
function changedFiles(cwd, evidenceContent) {
  const files = new Set();
  let anyGitSucceeded = false;
  const probes = [
    ["diff", "--name-only", "main...HEAD"],
    ["diff", "--name-only", "master...HEAD"],
    ["diff", "--name-only"],
    ["diff", "--name-only", "--cached"],
    ["ls-files", "--others", "--exclude-standard"],
  ];
  for (const args of probes) {
    const probe = gitLines(cwd, args);
    if (probe.ok) anyGitSucceeded = true;
    for (const file of probe.lines) files.add(file);
  }
  for (const match of evidenceContent.matchAll(/^\s+file\s*:\s*([^#\n]+)/gm)) files.add(scalar(match[1]));
  for (const match of evidenceContent.matchAll(/^\s+files\s*:\s*\[([^\]]*)\]/gm)) {
    for (const file of match[1].split(",").map(scalar).filter(Boolean)) files.add(file);
  }
  if (!anyGitSucceeded) return Infinity;
  return files.size;
}

function validateCriticRounds(sprintDir, fm) {
  if (truthy(fm.plan_critique_disabled)) return;
  const design = requireFile(path.join(sprintDir, "design.md"), "design.md");
  // P10 fix (2026-07-28, .ai_state/proposals.md P10): 全文字面计数会被讨论该契约的正文
  // 污染 (写一句 "Critic Findings" 就虚增一轮)。锚定到 2-3 级标题行, 与 Round N 段头体例
  // 一致; 正文提及不再计数。
  const rounds = (design.match(/^#{2,3}\s.*Critic Findings/gm) || []).length;
  const configured = Number.parseInt(fm.plan_critique_min_rounds || "0", 10);
  if (!Number.isFinite(configured)) throw new GateError("plan_critique_min_rounds must be an integer");
  // 2026-07-28 gate-descaling: 默认最少轮数全路径 1 (原 R/S=2)。多轮审议是 max_rounds 的
  // 事, 下限门禁只保证"至少被独立批过一次"; 要更多轮用 plan_critique_min_rounds 显式调高。
  const minimum = configured > 0 ? configured : 1;
  if (rounds < minimum) throw new GateError(`design.md has ${rounds} Critic Findings rounds; expected at least ${minimum}`);
  // 文书预算警告 (不 block, 防 P 系列死锁复发): design.md 超 300 行提示收敛。
  const designLines = design.split(/\r?\n/).length;
  if (designLines > 300) {
    process.stderr.write(`[delivery-gate] 文书预算警告: design.md ${designLines} 行 (目标 System ≤200 / Feature ≤80); 散文该下沉或删减, 不 block\n`);
  }
}

// P0-3: JS \b never creates a boundary after CJK, so "## 验收标准" was rejected
// while the packaged design template emits exactly that heading. Use an explicit
// boundary lookahead instead; numbered section prefixes ("## 9. Acceptance
// criteria") are also recognized.
const ACCEPTANCE_HEAD = /^#{2,3}\s*\**\s*(?:\d+[.)]\s*)?(?:acceptance criteria|验收标准)(?=$|[\s*:：()（）[\]【】·—-])/i;
const PLACEHOLDER_PREFIXES = ["todo", "tbd", "fixme", "wip", "placeholder", "待定", "待补", "占位", "暂定"];
const PLACEHOLDER_PHRASES = ["works correctly", "works as expected", "功能正常", "正常工作", "n/a"];

// design §4.3: placeholder rejection is semantic (prefix/substring), not an
// exact-string list — "TODO: define later" and "login works correctly." fail.
function isPlaceholderCriterion(text) {
  const t = text.trim().toLowerCase().replace(/[.。!！;；,，]+$/, "").trim();
  if (!t) return true;
  if (PLACEHOLDER_PREFIXES.some(prefix => t.startsWith(prefix))) return true;
  return PLACEHOLDER_PHRASES.some(phrase => t === phrase || t.includes(phrase));
}

function acceptanceCriteria(text) {
  const item = /^\s*(?:[-*]|\d+[.)]|\[[ xX]\])\s+\S/;
  const nextHead = /^#{1,6}\s/;
  const found = [];
  let inSec = false;
  for (const raw of text.split(/\r?\n/)) {
    if (ACCEPTANCE_HEAD.test(raw.trim())) { inSec = true; continue; }
    if (!inSec) continue;
    if (nextHead.test(raw)) { inSec = false; continue; }
    if (item.test(raw)) {
      const t = raw.replace(/^\s*(?:[-*]|\d+[.)])\s+/, "").replace(/^\[[ xX]\]\s+/, "").trim();
      if (t && !isPlaceholderCriterion(t)) found.push(t);
    }
  }
  return found;
}

// design §4.5 escape policy: the exception must name the current sprint AND carry
// reason + user authorization + an unexpired expiry. A partially-declared escape
// fails closed instead of silently widening.
function parseUtcTimestamp(value, label) {
  const millis = Date.parse(value);
  if (!Number.isFinite(millis) || !/(?:Z|\+00:00)$/.test(value)) {
    throw new GateError(`${label} 必须是 UTC ISO-8601`);
  }
  return millis;
}

function parseAuthorizationRecord(filePath) {
  const content = requireFile(filePath, "spec-gate user authorization");
  const result = {};
  for (const raw of content.split(/\r?\n/)) {
    if (!raw.trim() || raw.trimStart().startsWith("#")) continue;
    if (/^\s/.test(raw)) throw new GateError("spec-gate user authorization must be a flat YAML mapping");
    const match = raw.match(/^([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$/);
    if (!match) throw new GateError(`malformed spec-gate user authorization line: ${raw}`);
    if (Object.hasOwn(result, match[1])) throw new GateError(`duplicate spec-gate user authorization field: ${match[1]}`);
    result[match[1]] = scalar(match[2]);
  }
  const expected = [
    "schema_version", "kind", "sprint_slug", "path", "reason", "decision",
    "authorization_source", "authorized_by", "authorized_at", "expiry", "removal_condition",
  ];
  exactKeys(result, expected, "spec-gate user authorization");
  return result;
}

function specGateExceptionActive(fm, sprintSlug, pathType, sprintDir) {
  if (!fm.spec_gate_exception || fm.spec_gate_exception !== sprintSlug) return false;
  const fields = {};
  for (const key of [
    "spec_gate_exception_path", "spec_gate_exception_reason", "spec_gate_exception_authorized_by",
    "spec_gate_exception_authorized_at", "spec_gate_exception_expiry",
    "spec_gate_exception_removal_condition", "spec_gate_exception_emergency_hotfix",
    "spec_gate_exception_authorization_ref",
  ]) fields[key] = String(fm[key] || "").trim();
  if (Object.values(fields).some(value => !value)) {
    throw new GateError("spec_gate_exception requires path/reason/authorized_by/authorized_at/expiry/removal_condition/emergency_hotfix/authorization_ref; missing fields fail closed");
  }
  const reason = fields.spec_gate_exception_reason;
  const removal = fields.spec_gate_exception_removal_condition;
  if (isPlaceholderCriterion(reason) || isPlaceholderCriterion(removal)) {
    throw new GateError("spec_gate_exception reason/removal_condition cannot be placeholders");
  }
  if (!GENERATOR_PATHS.has(pathType) || fields.spec_gate_exception_path !== pathType) {
    throw new GateError("spec_gate_exception_path must exactly match current Feature/Refactor/System path");
  }
  const authorizedBy = fields.spec_gate_exception_authorized_by;
  if (!/^user:[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/.test(authorizedBy)) {
    throw new GateError("spec_gate_exception_authorized_by must be user:<stable-label>; generic user/self fails");
  }
  if (fields.spec_gate_exception_emergency_hotfix.toLowerCase() !== "false") {
    throw new GateError("Feature/Refactor/System spec exception must set emergency_hotfix=false");
  }
  const authorizedAt = parseUtcTimestamp(fields.spec_gate_exception_authorized_at, "spec_gate_exception_authorized_at");
  const expiryMs = parseUtcTimestamp(fields.spec_gate_exception_expiry, "spec_gate_exception_expiry");
  if (authorizedAt > Date.now()) throw new GateError("spec_gate_exception_authorized_at cannot be in the future");
  if (expiryMs <= Date.now()) throw new GateError(`spec_gate_exception 已于 ${fields.spec_gate_exception_expiry} 过期; 移除或重新授权`);
  const ref = fields.spec_gate_exception_authorization_ref;
  if (!/^user-authorizations\/[A-Za-z0-9][A-Za-z0-9._-]*\.yaml$/.test(ref)) {
    throw new GateError("spec_gate_exception_authorization_ref must be user-authorizations/<id>.yaml");
  }
  const authPath = path.resolve(sprintDir, ref);
  if (!authPath.startsWith(`${path.resolve(sprintDir)}${path.sep}`)) {
    throw new GateError("spec_gate_exception_authorization_ref escapes current sprint");
  }
  const record = parseAuthorizationRecord(authPath);
  const expected = {
    schema_version: "1",
    kind: "spec_gate_exception_authorization",
    sprint_slug: sprintSlug,
    path: pathType,
    reason,
    decision: "approve",
    authorization_source: "user_prompt",
    authorized_by: authorizedBy,
    authorized_at: fields.spec_gate_exception_authorized_at,
    expiry: fields.spec_gate_exception_expiry,
    removal_condition: removal,
  };
  if (Object.keys(expected).some(key => record[key] !== expected[key])) {
    throw new GateError("spec-gate user authorization record does not exactly match frontmatter");
  }
  return true;
}

// design §4.2/§4.3: criteria must come from the sprint's own design.md, or from a
// requirements artifact explicitly linked in that design — not any random file
// under .ai_state/requirements/.
function resolveAcceptanceCriteria(sprintDir, aiState) {
  const designPath = path.join(sprintDir, "design.md");
  if (!fs.existsSync(designPath)) return [];
  const designText = fs.readFileSync(designPath, "utf8");
  const own = acceptanceCriteria(designText);
  if (own.length) return own;
  for (const match of designText.matchAll(/requirements\/([A-Za-z0-9][A-Za-z0-9._-]*\.md)/g)) {
    const linked = path.join(aiState, "requirements", match[1]);
    if (!fs.existsSync(linked)) continue;
    const fromLinked = acceptanceCriteria(fs.readFileSync(linked, "utf8"));
    if (fromLinked.length) return fromLinked;
  }
  return [];
}

// spec-gate 主门禁在 impl 入口 (design §4.2); ship 处复核 (design §4.4).
function validateSpecGate(sprintDir, aiState, fm, sprintSlug, { allowException }) {
  if (specGateExceptionActive(fm, sprintSlug, fm.path, sprintDir)) {
    if (allowException) return [];
    throw new GateError("active Feature+ spec_gate_exception must be removed before ship");
  }
  const criteria = resolveAcceptanceCriteria(sprintDir, aiState);
  if (!criteria.length) {
    throw new GateError("spec-gate: design.md (或其显式链接的 requirements 档) 缺机器可识别的验收标准段 (## Acceptance Criteria / ## 验收标准 + ≥1 条可观测 checkbox/编号/列表项); 占位符/TODO/泛化陈述不算");
  }
  return criteria;
}

// design §4.4(2): labeled criteria (ACn) must each map to checklist/evidence;
// a single unrelated evidence row no longer satisfies the whole spec.
function evidenceField(block, key) {
  const matches = [...block.matchAll(new RegExp(`^\\s+${key}\\s*:\\s*([^#\\n]+)`, "gm"))];
  if (matches.length > 1) throw new GateError(`evidence record has duplicate ${key}`);
  return matches.length ? scalar(matches[0][1]) : "";
}

function parseEvidenceRecords(filePath) {
  const content = requireFile(filePath, "evidence.yaml");
  const items = [...content.matchAll(/^\s*-\s+tool_use_id\s*:\s*([^#\n]*)/gm)];
  return items.map((item, index) => {
    const end = index + 1 < items.length ? items[index + 1].index : content.length;
    const block = content.slice(item.index, end);
    const coversRaw = evidenceField(block, "covers");
    let covers = [];
    if (coversRaw) {
      if (!coversRaw.startsWith("[") || !coversRaw.endsWith("]")) throw new GateError("evidence covers must be an inline AC list");
      covers = coversRaw.slice(1, -1).split(",").map(value => scalar(value).toUpperCase()).filter(Boolean);
      if (covers.some(label => !/^AC\d+$/.test(label))) throw new GateError("evidence covers contains an invalid AC label");
    }
    return {
      tool_use_id: scalar(item[1]),
      ac_id: evidenceField(block, "ac_id").toUpperCase(),
      covers,
      result: evidenceField(block, "result").toLowerCase(),
      source: evidenceField(block, "source").toLowerCase(),
      command_or_artifact: evidenceField(block, "command_or_artifact"),
      // B1 (2026-07-28, 台账 W23): evidence-collector 自动记录的字段, lite-admissible 用
      command: evidenceField(block, "command"),
      timestamp: evidenceField(block, "timestamp"),
      observed_at: evidenceField(block, "observed_at"),
      summary: evidenceField(block, "summary"),
      exit_code: evidenceField(block, "exit_code"),
      output_artifact: evidenceField(block, "output_artifact"),
      artifact_sha256: evidenceField(block, "artifact_sha256"),
      implementation_commit: evidenceField(block, "implementation_commit"),
    };
  });
}

function reviewExplicitlyAccepts(reviewContent, label) {
  const negative = /\b(?:NOT\s+SATISFIED|MISSING|DEVIATED|FAIL(?:ED)?|REWORK|DOES\s+NOT\s+PASS|NOT\s+PASS)\b/i;
  const positive = new RegExp(`(?:^|\\|)\\s*${label}\\s*(?:\\||:|[-—])\\s*(?:SATISFIED|PASS)\\s*(?:\\||$)`, "i");
  return reviewContent.split(/\r?\n/).some(line => !negative.test(line) && positive.test(line));
}

function validateAcMapping(sprintDir, criteria, records, reviewPath, reviewContent, reviewedCommit) {
  const labels = new Set();
  for (const criterion of criteria) {
    for (const match of criterion.matchAll(/(?:^|[^A-Za-z0-9])(AC\d+)(?![0-9])/g)) labels.add(match[1].toUpperCase());
  }
  if (!labels.size) return;
  // hotfix2 AC5 (2026-07-29, W38): 保留标号 AC11/12 静默豁免移除 (compound learning
  // reserved-ac-labels-silent-exemption 教训) — 全部 AC 统一走 admissible 证据 (W23 lite 已够廉价)。
  const missing = [...labels].sort().filter(label => !records.some(record => {
    const mapped = record.ac_id === label || record.covers.includes(label);
    if (!mapped || record.result !== "pass") return false;
    // B1 lite-admissible (2026-07-28, 台账 W23): hook 自动落的验证记录 (command/timestamp/
    // result, evidence-collector 从真实 Bash 验证命令写入) + agent 补一行 ac_id/covers 映射
    // 即 admissible。十字段手写 artifact 契约是文书税的机器根源, 且 sha256/artifact 同为
    // agent 手造、无更强防伪性。带 source 的严格记录仍走下方原路径。
    if (!record.source && record.command && record.timestamp) {
      try { parseUtcTimestamp(record.timestamp, `evidence ${record.tool_use_id} timestamp`); return true; }
      catch (_) { return false; }
    }
    if (![record.source, record.command_or_artifact, record.observed_at, record.summary].every(Boolean)) return false;
    try { parseUtcTimestamp(record.observed_at, `evidence ${record.tool_use_id} observed_at`); }
    catch (_) { return false; }
    if (record.source === "command") {
      const output = path.resolve(sprintDir, record.output_artifact || "");
      if (!output.startsWith(`${path.resolve(sprintDir)}${path.sep}`)
          || record.exit_code !== "0"
          || !/^[0-9a-f]{64}$/.test(record.artifact_sha256)
          || record.implementation_commit !== reviewedCommit
          || !fs.existsSync(output)
          || !fs.statSync(output).isFile()) return false;
      const outputBuffer = fs.readFileSync(output);
      const outputText = outputBuffer.toString("utf8");
      return crypto.createHash("sha256").update(outputBuffer).digest("hex") === record.artifact_sha256
        && outputText.includes(record.command_or_artifact)
        && /^exit_code:\s*0\s*$/im.test(outputText)
        && outputText.includes(record.summary);
    }
    if (record.source === "artifact") {
      const artifact = path.resolve(sprintDir, record.command_or_artifact);
      return artifact.startsWith(`${path.resolve(sprintDir)}${path.sep}`) && fs.existsSync(artifact) && fs.statSync(artifact).isFile();
    }
    if (record.source === "review") {
      return path.resolve(sprintDir, record.command_or_artifact) === path.resolve(reviewPath)
        && reviewContent.includes("## Spec Compliance")
        && reviewContent.includes("## Evidence Cross-Check")
        && finalVerdict(reviewContent, path.basename(reviewPath)) === "PASS"
        && reviewExplicitlyAccepts(reviewContent, label);
    }
    return false;
  }));
  if (missing.length) {
    throw new GateError(`spec-gate ship 复核: 验收标准 ${missing.join(", ")} 缺 admissible per-AC PASS evidence (unknown/checklist-only/missing artifact/stale review do not count)`);
  }
}

// hotfix2 AC5/W38: validateMetaAcceptance (AC11/12 元受理) 已删 — 统一 per-AC 证据。

// design §4.2 主门禁: Feature/Refactor/System 处于 impl 时必须已有机器可识别验收
// 标准; 缺标准的 Stop 立即 block. ship 段复核是纵深防御, 不是替代 (design §4.4).
function validateImplEntry(aiState, fm) {
  if (!GENERATOR_PATHS.has(fm.path)) return;
  const sprintSlug = fm.current_sprint_slug;
  if (!SAFE_SLUG.test(sprintSlug || "")) throw new GateError(`invalid current_sprint_slug ${sprintSlug || ""}`);
  validateSpecGate(path.join(aiState, "sprints", sprintSlug), aiState, fm, sprintSlug, { allowException: true });
}

// 9.9.6 P2: a ship whose net diff vs the tracked upstream stays within this many changed
// lines AND touches only docs/config/deps/state/tests (no source logic, no harness/hooks)
// is a "light" ship — no TDD red/green story — and takes the light gate in validateShip.
const SHIP_LIGHT_MAX_LINES = 60;

function isLightShipFile(file) {
  // Harness/hook/gate files and harness config are high-risk — never light.
  if (/(^|\/)hooks\//.test(file)) return false;
  // Patches to the installed harness live outside every project repo (~/.claude,
  // ~/.codex), so the hooks/ guard above cannot see them — the ledger entry is their only
  // in-repo trace. Touching it means this sprint changed the gate: run the full contract.
  if (/(^|\/)harness-patches\.md$/.test(file)) return false;
  if (/(^|\/)settings(\.local)?\.json$/.test(file)) return false;
  // Source logic (non-test code) needs review even when small — never light.
  const isTest = /(^|\/)(tests?|__tests__|specs?)\//.test(file) || /\.(test|spec)\.[A-Za-z]+$/.test(file);
  const isCode = /\.(py|ts|tsx|js|jsx|mjs|cjs|go|rs|java|rb|php|c|cc|cpp|h|hpp|swift|kt|scala|sh|bash|zsh|sql)$/.test(file);
  if (isCode && !isTest) return false;
  // Docs / config / deps-lockfiles / .ai_state / tests / prompts are light-eligible.
  return true;
}

// Classify the shipped change = local commits ahead of the tracked upstream (fallback
// origin/<branch>). Light iff net diff <= SHIP_LIGHT_MAX_LINES and every changed file is
// light-eligible. Fail-closed: if the range/diff cannot be determined, return false.
function shipChangeIsLight(cwd) {
  let base = null;
  const up = gitLines(cwd, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]);
  if (up.ok && up.lines[0] && up.lines[0] !== "@{upstream}") base = up.lines[0];
  if (!base) {
    const branch = gitLines(cwd, ["rev-parse", "--abbrev-ref", "HEAD"]);
    if (branch.ok && branch.lines[0] && branch.lines[0] !== "HEAD") {
      const remote = gitLines(cwd, ["rev-parse", "--verify", "--quiet", `origin/${branch.lines[0]}`]);
      if (remote.ok && remote.lines[0]) base = `origin/${branch.lines[0]}`;
    }
  }
  if (!base) return false;
  const stat = gitLines(cwd, ["diff", "--numstat", `${base}..HEAD`]);
  if (!stat.ok) return false;
  let totalLines = 0;
  const files = [];
  for (const row of stat.lines) {
    const cols = row.split("\t");
    if (cols.length < 3) continue;
    const file = cols[2];
    files.push(file);
    // .ai_state/ is auto-maintained state (token-usage churn, logs, pointers) and does not
    // count toward the line budget — only toward file eligibility below.
    if (/(^|\/)\.ai_state\//.test(file)) continue;
    const added = cols[0] === "-" ? 0 : Number(cols[0]) || 0;
    const deleted = cols[1] === "-" ? 0 : Number(cols[1]) || 0;
    totalLines += added + deleted;
  }
  if (files.length === 0) return false;
  if (totalLines > SHIP_LIGHT_MAX_LINES) return false;
  return files.every(isLightShipFile);
}

function validateShip(aiState, fm, cwd) {
  const sprintSlug = fm.current_sprint_slug;
  if (!SAFE_SLUG.test(sprintSlug || "")) throw new GateError(`invalid current_sprint_slug ${sprintSlug || ""}`);
  const sprintDir = path.join(aiState, "sprints", sprintSlug);
  // 9.9.6 P2 fix (see .ai_state/proposals.md): a light ship — small net diff vs upstream,
  // touching only docs/config/deps/state/tests (no source logic, no harness/hooks) — has no
  // TDD red/green story and takes the light gate: roadmap consistency only, skipping the
  // review-manifest / tdd-evidence / review-artifact contract mechanical changes cannot
  // honestly produce. Substantive, harness-touching, or over-budget ships run the full
  // contract below (fail-closed: an unclassifiable diff is treated as full).
  if (shipChangeIsLight(cwd)) {
    const lightRoadmap = fm.current_roadmap_slug || "";
    if (lightRoadmap) validateRoadmap(aiState, lightRoadmap, sprintSlug);
    return;
  }
  // P8: the 9.9.6 review-manifest contract is opt-in per sprint (declared by the
  // manifest file's presence) except for Refactor/System, where it is mandatory.
  // Sprints shipped under the pre-9.9.6 contract have no manifest and must not be
  // retroactively blocked — they are still held to the full 9.9.1 check set below.
  // 解锁动作正确化 (design §10.1): 先判 polish 产物再判 manifest。缺 polish 时报缺
  // review-manifest 是**误导** —— manifest 是 review 的下游产物, polish 角色造不出来,
  // 给出的解锁动作物理不可执行, 正是 290 次活锁的起因。manifest 仍为必需项, 只是后报。
  if (REFACTOR_SYSTEM.has(fm.path)) {
    let cleanup = "";
    try {
      cleanup = requireFile(path.join(sprintDir, "cleanup-pass.md"), "cleanup-pass.md");
    } catch (_) { /* 缺失与空壳走同一分支 */ }
    // 复用 validateMetaAcceptance 的既有判据, 不新造机制 (R1-F5a)。
    if (!/\bPASS\b|completed|完成/i.test(cleanup)) {
      throw new GateError(
        "Refactor/System polish stage 未跑; 解锁链: 跑 polish → 产出 cleanup-pass.md 即可 (review-manifest 全路径 opt-in, 仅已声明时才补)",
      );
    }
  }
  const hasManifest = fs.existsSync(path.join(sprintDir, "review-manifest.yaml"));
  // K1 (2026-07-28, 台账 W31): R/S 的 review-manifest 契约从强制降为 opt-in (与 Feature 同构)。
  // 实测 (quantum-cowork sensory-retirement): 强制 manifest→binding→tdd-evidence 链在 ship
  // 同因 block×4 直到熔断, 期间产出全是文档不是修复。声明即验语义不变: manifest 存在则全链
  // fail-closed 照验。R/S 行为证据底线改由 runtime-verify + cleanup-pass + PASS 承载。
  if (hasManifest) validateIndexGovernance(sprintDir, fm);
  const roadmapSlug = fm.current_roadmap_slug || "";
  if (roadmapSlug) validateRoadmap(aiState, roadmapSlug, sprintSlug);
  if (fm.path === "Bugfix") requireFile(path.join(sprintDir, "fix-note.md"), "fix-note.md");
  if (GENERATOR_PATHS.has(fm.path)) {
    if (!truthy(fm.skip_impl_subagent_check)) validateGeneratorChain(sprintDir, sprintSlug);
    // 2026-07-28 gate-descaling: checklist.yaml 可选 — done_contract 已并入 design.md
    // (spec-gate 验 AC), 双写清单只在超大 sprint 才立; 存在则照旧必须全绿。
    if (fs.existsSync(path.join(sprintDir, "checklist.yaml"))) {
      validateChecklist(path.join(sprintDir, "checklist.yaml"));
    }
    const evidencePath = path.join(sprintDir, "evidence.yaml");
    const evidenceRecords = validateEvidence(evidencePath);
    const reviewPath = selectLatestReview(path.join(sprintDir, "reviews"));
    const reviewContent = validateReview(reviewPath, fm.path);
    if (hasManifest) {
      const specCriteria = validateSpecGate(sprintDir, aiState, fm, sprintSlug, { allowException: false });
      validateTddEvidence(path.join(sprintDir, "tdd-evidence.yaml"));
      const reviewedCommit = validateReviewBinding(reviewContent, reviewPath, sprintDir, aiState, cwd, fm);
      validateAcMapping(sprintDir, specCriteria, evidenceRecords, reviewPath, reviewContent, reviewedCommit);
    }
    validateCriticRounds(sprintDir, fm);

    if (REFACTOR_SYSTEM.has(fm.path)) {
      if (!truthy(fm.skip_runtime_verify)) {
        const runtime = requireFile(path.join(sprintDir, "runtime-verify.md"), "runtime-verify.md");
        if (!runtime.includes("## 测试场景") && !runtime.includes("## Test Scenarios")) {
          throw new GateError("runtime-verify.md lacks an executed test-scenarios section");
        }
      }
      requireFile(path.join(sprintDir, "cleanup-pass.md"), "cleanup-pass.md");
      if (!truthy(fm.skip_architecture_check)) {
        const evidence = requireFile(evidencePath, "evidence.yaml");
        if (changedFiles(cwd, evidence) >= 5) {
          requireFile(path.join(aiState, "architecture", "ARCHITECTURE.md"), "architecture/ARCHITECTURE.md");
        }
      }
    }
  }
}

function isImplementationWrite(payload) {
  if (payload.hook_event_name !== "PreToolUse") return false;
  const tool = String(payload.tool_name || "").toLowerCase();
  if (!["edit", "write", "multiedit", "apply_patch"].includes(tool)) return false;
  const input = payload.tool_input && typeof payload.tool_input === "object" ? payload.tool_input : {};
  const candidates = [input.file_path, input.path, input.patch].filter(Boolean).map(String);
  if (!candidates.length) return true;
  const joined = candidates.join("\n");
  const paths = [...joined.matchAll(/(?:\*\*\* (?:Update|Add) File:|^)([^\n]+)/gm)].map(match => match[1]);
  return (paths.length ? paths : candidates).some(file => !file.replace(/\\/g, "/").includes(".ai_state/"));
}

function block(reason) {
  const message = `[delivery-gate] ${reason}\n解锁动作: 修复上述档案或流程后重试 Stop；不得用旧 PASS 或未知证据绕过。`;
  process.stderr.write(`${message}\n`);
  process.stdout.write(`${JSON.stringify({ decision: "block", reason: message })}\n`);
}

// ---------------------------------------------------------------------------
// Stop 阻断活锁熔断器 (design §10.1 / AC16)。
// 起因: 同一条阻断在一个会话里重复 290 次 / 42 分钟, 零进展 —— 门禁的判定没错, 但它
// 要求的产物当前角色**造不出来** (polish 造不出 review-manifest), 解锁动作物理不可执行。
// 熔断只停止无意义重试并交还人类, 不放行任何东西: PreToolUse 的实现写入门禁完全不变。
// ---------------------------------------------------------------------------
const GATE_LEDGER_WINDOW_MS = 30 * 60 * 1000;
const GATE_EVENTS = new Set(["GateBlock", "GateEscalated", "GatePass"]);
const GATE_ESCALATE_AT = 3;

function gateLedgerPath(ctx) {
  return path.join(ctx.sprintDir, "stop-failures.jsonl");
}

/** 只读取本熔断器写的记录; stop-failure-recorder 的 StopFailure 行原样跳过。 */
function parseGateLedger(filePath) {
  let raw;
  try {
    raw = fs.readFileSync(filePath, "utf8");
  } catch (_) {
    return [];
  }
  const rows = [];
  for (const line of raw.split(/\r?\n/)) {
    if (!line.trim()) continue;
    try {
      const row = JSON.parse(line);
      if (row && typeof row === "object" && GATE_EVENTS.has(row.event)) rows.push(row);
    } catch (_) { /* 半截行或他人写的行, 跳过 */ }
  }
  return rows;
}

function gateRowIsRecent(row, now) {
  const ts = Date.parse(String(row.ts || ""));
  if (!Number.isFinite(ts)) return false;
  const age = now - ts;
  return age >= 0 && age <= GATE_LEDGER_WINDOW_MS;
}

/** session_id 缺失时退化为仅按 reason 匹配 (兜底, 不报错)。 */
function gateRowMatchesSession(row, sessionId) {
  return sessionId ? row.session_id === sessionId : true;
}

/**
 * 尾部连续、同会话、同 reason 且在窗口内的记录数。
 * 其他会话的记录用 continue 跳过而非 break —— 红区强制并行 worktree, 多会话共写同一
 * ledger, 若 break 则交替 reason 会打断彼此链条, 熔断在并行场景永不触发 (R1-F2)。
 */
function gateChainCount(filePath, sessionId, reasonSha1) {
  const now = Date.now();
  const rows = parseGateLedger(filePath);
  let count = 0;
  for (let i = rows.length - 1; i >= 0; i -= 1) {
    const row = rows[i];
    if (!gateRowMatchesSession(row, sessionId)) continue;
    if (!gateRowIsRecent(row, now)) break;
    if (row.reason_sha1 !== reasonSha1 || row.event === "GatePass") break;
    count += 1;
  }
  return count;
}

function latestGateRecord(filePath, sessionId) {
  const now = Date.now();
  const rows = parseGateLedger(filePath);
  for (let i = rows.length - 1; i >= 0; i -= 1) {
    if (gateRowMatchesSession(rows[i], sessionId) && gateRowIsRecent(rows[i], now)) return rows[i];
  }
  return null;
}

function appendGateRecord(filePath, record) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  // O_APPEND 单次 write: 并发 worktree 会同时追加同一文件。
  fs.appendFileSync(filePath, `${JSON.stringify(record)}\n`, { encoding: "utf8", mode: 0o600 });
}

/**
 * Stop 路径专用。**必须只在 Stop 事件生效** —— 若把熔断塞进共用的 block(),
 * 同因重试的 PreToolUse 实现写入第 3 次就会被放行执行, 那是 P0 越权。
 */
function stopFailure(payload, reason, ctx) {
  if (payload.hook_event_name !== "Stop" || !ctx) return block(reason);
  const sessionId = typeof payload.session_id === "string" ? payload.session_id.trim() : "";
  const reasonSha1 = crypto.createHash("sha1").update(reason, "utf8").digest("hex");
  const ledger = gateLedgerPath(ctx);
  const consecutive = gateChainCount(ledger, sessionId, reasonSha1) + 1;
  const record = {
    event: consecutive >= GATE_ESCALATE_AT ? "GateEscalated" : "GateBlock",
    ts: new Date().toISOString(),
    session_id: sessionId,
    reason_sha1: reasonSha1,
    stage: ctx.stage,
    path: ctx.pathType,
    consecutive,
  };
  appendGateRecord(ledger, record);
  if (record.event === "GateEscalated") {
    // 不发 decision:block —— 停止空转, 让 turn 正常结束并交还人类。判定本身没有改变:
    // 状态真实变化 (reason 变) 或窗口过期后, 阻断照常恢复。
    process.stderr.write(`[delivery-gate] ESCALATED: ${reason}\n`);
    return;
  }
  block(reason);
}

/**
 * 清零 = 一次**通过全部校验**的 Stop, 不是"未发 block"的 Stop ——
 * escalated 的 Stop 本身就不发 block, 若按后者清零会退化成 3 block + 1 escalate 的
 * 无限循环, 活锁只降 25% (R1-F1)。仅在有链可断时写哨兵, 无链时零成本。
 */
function appendGatePass(payload, ctx) {
  if (payload.hook_event_name !== "Stop" || !ctx) return;
  const sessionId = typeof payload.session_id === "string" ? payload.session_id.trim() : "";
  const ledger = gateLedgerPath(ctx);
  const latest = latestGateRecord(ledger, sessionId);
  if (!latest || !["GateBlock", "GateEscalated"].includes(latest.event)) return;
  if (typeof latest.reason_sha1 !== "string" || !latest.reason_sha1) return;
  appendGateRecord(ledger, {
    event: "GatePass",
    ts: new Date().toISOString(),
    session_id: sessionId,
    reason_sha1: latest.reason_sha1,
    stage: ctx.stage,
    path: ctx.pathType,
    consecutive: 0,
  });
}

function main() {
  let payload = {};
  try {
    const input = fs.readFileSync(0, "utf8");
    if (input.trim()) payload = JSON.parse(input);
  } catch (_) {}
  const cwd = path.resolve(payload.cwd || process.cwd());
  // Fast quiet exit for non-Athena directories stays *before* any git call: this hook
  // fires on every PreToolUse, and a write to /tmp must neither pay for a subprocess nor
  // be able to crash (design Round 3 F12).
  const aiStateLocal = findAiState(cwd);
  if (!aiStateLocal) return;
  // 熔断器上下文: 需要 sprintDir 才能写 ledger。_index 尚未解析出 slug 时为 null,
  // 此时 stopFailure 退化为普通 block (已知局限, 见 gate-breaker-evidence.md §5)。
  let breakerCtx = null;
  try {
    // P3: root and .ai_state must be resolved from the same checkout. Taking root from
    // the main repo while reading .ai_state from a worktree cwd made `sprintRel` come out
    // as "../wt-x/..." and mis-framed every drift comparison (design Round 3 F17), so the
    // main-repo root is the single source both here and inside validateShip.
    const root = tryRepoRoot(cwd);
    const aiState = (root && findAiState(root)) || aiStateLocal;
    const index = requireFile(path.join(aiState, "_index.md"), "_index.md");
    const fm = parseFrontmatter(index);
    // P8: idle state (no sprint in flight) is legal — path/stage/current_sprint_slug
    // all empty means a closed-out project between sprints; nothing to validate.
    // Without this, a shipped sprint can never be released from the ship gate
    // except by immediately opening the next sprint.
    if (!(fm.path || "") && !(fm.stage || "") && !(fm.current_sprint_slug || "")) return;
    if (fm.current_sprint_slug) {
      breakerCtx = {
        sprintDir: path.join(aiState, "sprints", fm.current_sprint_slug),
        stage: fm.stage || "",
        pathType: fm.path || "",
      };
    }
    if (!VALID_PATHS.has(fm.path || "")) throw new GateError(`unknown or missing path ${fm.path || ""}`);
    if (!VALID_STAGES.has(fm.stage || "")) throw new GateError(`unknown or missing stage ${fm.stage || ""}`);
    if (isImplementationWrite(payload) && ["design", "impl"].includes(fm.stage)) validateImplEntry(aiState, fm);
    // P8 deadlock fix: during ship, .ai_state maintenance writes (state pointer
    // moves, archive backfills) must not be blocked by ship validation — otherwise
    // a failing check can never be resolved (fixing state requires a write, and
    // every write re-runs the failing check). Implementation writes and the Stop
    // final gate still validate in full.
    const shipMustValidate = payload.hook_event_name !== "PreToolUse" || isImplementationWrite(payload);
    if (fm.stage === "ship" && shipMustValidate) validateShip(aiState, fm, root || cwd);
    else if (fm.stage === "impl") validateImplEntry(aiState, fm);
    appendGatePass(payload, breakerCtx);
  } catch (error) {
    stopFailure(payload, error instanceof GateError ? error.message : `internal fail-closed error: ${error.message}`, breakerCtx);
  }
}

main();

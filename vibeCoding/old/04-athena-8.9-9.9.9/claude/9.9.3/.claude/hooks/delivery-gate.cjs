#!/usr/bin/env node
/**
 * Athena v9.9.3 Claude Code delivery gate.
 *
 * Shared artifacts use the same schema and fail-closed semantics as CX 9.9.3.
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
    records.push(validator(value, `${label} line ${index + 1}`, sprintSlug));
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
  // generator-chain 只校验 generator 生命周期。events 由 hook 记录全部 subagent 类型且
  // agent_type 在本 harness 恒为 "default", 无法据此识别 generator; 唯一可靠判据是 assign
  // 握手写入的 role=generator。critic/reviewer/evaluator/spec-compliance 无握手且多轮 Start/Stop,
  // 不属于本校验范围, 按 role 过滤后跳过, 避免误报 unbound / 多重 Start-Stop。
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
    const rows = eventMap.get(key) || [];
    const starts = rows.filter(row => row.event === "SubagentStart");
    const stops = rows.filter(row => row.event === "SubagentStop");
    if (starts.length !== 1) throw new GateError(`agent_id=${assignment.agent_id} requires exactly one SubagentStart`);
    if (stops.length !== 1) throw new GateError(`agent_id=${assignment.agent_id} requires exactly one SubagentStop`);
    if (starts[0].agent_type !== stops[0].agent_type) {
      throw new GateError(`inconsistent agent_type lifecycle for agent_id=${assignment.agent_id}`);
    }
    if (assignment.parsedTimestamp < starts[0].parsedTimestamp) {
      throw new GateError(`assignment handshake precedes SubagentStart for agent_id=${assignment.agent_id}`);
    }
    if (stops[0].parsedTimestamp < starts[0].parsedTimestamp) {
      throw new GateError(`SubagentStop precedes SubagentStart for agent_id=${assignment.agent_id}`);
    }
    if (stops[0].parsedTimestamp < assignment.parsedTimestamp) {
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
  // P8: mandatory Evidence Cross-Check section stays scoped to Refactor/System
  // (the 9.9.1 semantics) — widening it to every path retroactively blocked
  // already-shipped Feature sprints whose reviews predate the requirement.
  if (REFACTOR_SYSTEM.has(pathType) && !content.includes("## Evidence Cross-Check")) {
    throw new GateError(`latest review ${path.basename(reviewPath)} lacks ## Evidence Cross-Check`);
  }
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

// Manifest required-file sets are tiered by path (P8): a Feature sprint has no
// polish/rework artifacts by design, and version-specific architecture notes
// (e.g. architecture/athena-9.9.3.md) belong to individual sprints, not the
// generic schema. Files beyond the required tier are declared-then-verified:
// whatever the manifest lists gets hash-checked, nothing extra is mandated.
const MANIFEST_REQUIRED_CORE = ["design.md", "checklist.yaml", "evidence.yaml"];
const MANIFEST_REQUIRED_REFACTOR_SYSTEM = [
  ...MANIFEST_REQUIRED_CORE, "runtime-verify.md", "cleanup-pass.md", "architecture/ARCHITECTURE.md",
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
  for (const [name, expectedHash] of Object.entries(manifest.files)) {
    const target = name.startsWith("architecture/") ? path.join(aiState, name) : path.join(sprintDir, name);
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) throw new GateError(`review-manifest target missing: ${name}`);
    const actual = crypto.createHash("sha256").update(fs.readFileSync(target)).digest("hex");
    if (actual !== expectedHash) throw new GateError(`review-manifest hash mismatch: ${name}`);
  }
  const root = gitText(cwd, ["rev-parse", "--show-toplevel"], "repository root").trim();
  if (!root) throw new GateError("review freshness cannot determine Git repository root");
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
    `${sprintRel}/token-usage.jsonl`, `${sprintRel}/tool-trace.jsonl`,
    ".ai_state/architecture/ARCHITECTURE.md", ".ai_state/architecture/athena-9.9.3.md",
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
  // 9.9.3 mid-program fix (see .ai_state/proposals.md P1): shipping ONE sprint only requires
  // the roadmap item it maps to (the item whose slug is a trailing segment of the sprint
  // slug) to be done/completed — sibling items may still be pending. Requiring EVERY item
  // completed made every mid-program sprint ship structurally impossible. An ad-hoc sprint
  // with no matching item is not gated on item status here; its own per-sprint 9.9.3
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
  const rounds = (design.match(/Critic Findings/g) || []).length;
  const configured = Number.parseInt(fm.plan_critique_min_rounds || "0", 10);
  if (!Number.isFinite(configured)) throw new GateError("plan_critique_min_rounds must be an integer");
  const minimum = configured > 0 ? configured : (REFACTOR_SYSTEM.has(fm.path) ? 2 : 1);
  if (rounds < minimum) throw new GateError(`design.md has ${rounds} Critic Findings rounds; expected at least ${minimum}`);
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
  const missing = [...labels].sort().filter(label => !["AC11", "AC12"].includes(label) && !records.some(record => {
    const mapped = record.ac_id === label || record.covers.includes(label);
    if (!mapped || record.result !== "pass") return false;
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

function validateMetaAcceptance(criteria, reviewContent, sprintDir, cwd) {
  const labels = new Set();
  for (const criterion of criteria) {
    for (const match of criterion.matchAll(/(?:^|[^A-Za-z0-9])(AC\d+)(?![0-9])/g)) labels.add(match[1].toUpperCase());
  }
  if (labels.has("AC11") && finalVerdict(reviewContent, "latest review") !== "PASS") {
    throw new GateError("AC11 requires the latest bound evaluator verdict PASS");
  }
  if (!labels.has("AC12")) return;
  const cleanup = requireFile(path.join(sprintDir, "cleanup-pass.md"), "cleanup-pass.md");
  if (!/\bPASS\b|completed|完成/i.test(cleanup)) throw new GateError("AC12 requires completed polish/cleanup evidence");
  const root = gitText(cwd, ["rev-parse", "--show-toplevel"], "repository root").trim();
  const worktrees = gitText(root, ["worktree", "list", "--porcelain"], "worktree readiness");
  const active = (worktrees.match(/^worktree\s+/gm) || []).length;
  if (active !== 1) throw new GateError(`AC12 requires no extra active worktree; found ${active}`);
}

// design §4.2 主门禁: Feature/Refactor/System 处于 impl 时必须已有机器可识别验收
// 标准; 缺标准的 Stop 立即 block. ship 段复核是纵深防御, 不是替代 (design §4.4).
function validateImplEntry(aiState, fm) {
  if (!GENERATOR_PATHS.has(fm.path)) return;
  const sprintSlug = fm.current_sprint_slug;
  if (!SAFE_SLUG.test(sprintSlug || "")) throw new GateError(`invalid current_sprint_slug ${sprintSlug || ""}`);
  validateSpecGate(path.join(aiState, "sprints", sprintSlug), aiState, fm, sprintSlug, { allowException: true });
}

// 9.9.3 P2: a ship whose net diff vs the tracked upstream stays within this many changed
// lines AND touches only docs/config/deps/state/tests (no source logic, no harness/hooks)
// is a "light" ship — no TDD red/green story — and takes the light gate in validateShip.
const SHIP_LIGHT_MAX_LINES = 60;

function isLightShipFile(file) {
  // Harness/hook/gate files and harness config are high-risk — never light.
  if (/(^|\/)hooks\//.test(file)) return false;
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
  // 9.9.3 P2 fix (see .ai_state/proposals.md): a light ship — small net diff vs upstream,
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
  // P8: the 9.9.3 review-manifest contract is opt-in per sprint (declared by the
  // manifest file's presence) except for Refactor/System, where it is mandatory.
  // Sprints shipped under the pre-9.9.3 contract have no manifest and must not be
  // retroactively blocked — they are still held to the full 9.9.1 check set below.
  const hasManifest = fs.existsSync(path.join(sprintDir, "review-manifest.yaml"));
  if (REFACTOR_SYSTEM.has(fm.path) && !hasManifest) {
    throw new GateError("Refactor/System ship requires review-manifest.yaml (9.9.3 review contract)");
  }
  if (hasManifest) validateIndexGovernance(sprintDir, fm);
  const roadmapSlug = fm.current_roadmap_slug || "";
  if (roadmapSlug) validateRoadmap(aiState, roadmapSlug, sprintSlug);
  if (fm.path === "Bugfix") requireFile(path.join(sprintDir, "fix-note.md"), "fix-note.md");
  if (GENERATOR_PATHS.has(fm.path)) {
    if (!truthy(fm.skip_impl_subagent_check)) validateGeneratorChain(sprintDir, sprintSlug);
    validateChecklist(path.join(sprintDir, "checklist.yaml"));
    const evidencePath = path.join(sprintDir, "evidence.yaml");
    const evidenceRecords = validateEvidence(evidencePath);
    const reviewPath = selectLatestReview(path.join(sprintDir, "reviews"));
    const reviewContent = validateReview(reviewPath, fm.path);
    if (hasManifest) {
      const specCriteria = validateSpecGate(sprintDir, aiState, fm, sprintSlug, { allowException: false });
      validateTddEvidence(path.join(sprintDir, "tdd-evidence.yaml"));
      const reviewedCommit = validateReviewBinding(reviewContent, reviewPath, sprintDir, aiState, cwd, fm);
      validateAcMapping(sprintDir, specCriteria, evidenceRecords, reviewPath, reviewContent, reviewedCommit);
      validateMetaAcceptance(specCriteria, reviewContent, sprintDir, cwd);
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

function main() {
  let payload = {};
  try {
    const input = fs.readFileSync(0, "utf8");
    if (input.trim()) payload = JSON.parse(input);
  } catch (_) {}
  const cwd = path.resolve(payload.cwd || process.cwd());
  const aiState = findAiState(cwd);
  if (!aiState) return;
  try {
    const index = requireFile(path.join(aiState, "_index.md"), "_index.md");
    const fm = parseFrontmatter(index);
    // P8: idle state (no sprint in flight) is legal — path/stage/current_sprint_slug
    // all empty means a closed-out project between sprints; nothing to validate.
    // Without this, a shipped sprint can never be released from the ship gate
    // except by immediately opening the next sprint.
    if (!(fm.path || "") && !(fm.stage || "") && !(fm.current_sprint_slug || "")) return;
    if (!VALID_PATHS.has(fm.path || "")) throw new GateError(`unknown or missing path ${fm.path || ""}`);
    if (!VALID_STAGES.has(fm.stage || "")) throw new GateError(`unknown or missing stage ${fm.stage || ""}`);
    if (isImplementationWrite(payload) && ["design", "impl"].includes(fm.stage)) validateImplEntry(aiState, fm);
    // P8 deadlock fix: during ship, .ai_state maintenance writes (state pointer
    // moves, archive backfills) must not be blocked by ship validation — otherwise
    // a failing check can never be resolved (fixing state requires a write, and
    // every write re-runs the failing check). Implementation writes and the Stop
    // final gate still validate in full.
    const shipMustValidate = payload.hook_event_name !== "PreToolUse" || isImplementationWrite(payload);
    if (fm.stage === "ship" && shipMustValidate) validateShip(aiState, fm, cwd);
    else if (fm.stage === "impl") validateImplEntry(aiState, fm);
  } catch (error) {
    block(error instanceof GateError ? error.message : `internal fail-closed error: ${error.message}`);
  }
}

main();

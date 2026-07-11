#!/usr/bin/env node
/**
 * Athena v9.9.1 Claude Code delivery gate.
 *
 * Shared artifacts use the same schema and fail-closed semantics as CX 9.9.1.
 * Platform-specific hook payloads are normalized here; no private reasoning or
 * inferred tool success is used as delivery evidence.
 */
"use strict";

const fs = require("fs");
const path = require("path");
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
  const eventMap = new Map();
  for (const row of events) {
    const key = lifecycleKey(row);
    if (!assignmentMap.has(key)) {
      const kind = row.event === "SubagentStop" ? "orphan SubagentStop" : "unbound SubagentStart";
      throw new GateError(`${kind}: agent_id=${row.agent_id}`);
    }
    if (!eventMap.has(key)) eventMap.set(key, []);
    eventMap.get(key).push(row);
  }
  for (const [key, assignment] of assignmentMap.entries()) {
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
  if (REFACTOR_SYSTEM.has(pathType) && !content.includes("## Evidence Cross-Check")) {
    throw new GateError(`latest review ${path.basename(reviewPath)} lacks ## Evidence Cross-Check`);
  }
  return content;
}

function validateRoadmap(aiState, roadmapSlug) {
  if (!SAFE_SLUG.test(roadmapSlug)) throw new GateError(`invalid current_roadmap_slug ${roadmapSlug}`);
  const filePath = path.join(aiState, "roadmap", roadmapSlug, "items.yaml");
  const content = requireFile(filePath, `roadmap/${roadmapSlug}/items.yaml`);
  const declared = [...content.matchAll(/^roadmap_slug\s*:\s*([^#\n]*)/gm)];
  if (declared.length !== 1 || scalar(declared[0][1]) !== roadmapSlug) throw new GateError("roadmap slug is missing or mismatched");
  const totalRows = [...content.matchAll(/^total_items\s*:\s*([^#\n]*)/gm)];
  if (totalRows.length !== 1 || !/^\d+$/.test(scalar(totalRows[0][1]))) throw new GateError("roadmap total_items must be one integer");
  const total = Number(scalar(totalRows[0][1]));
  const items = [...content.matchAll(/^\s*-\s+slug\s*:\s*([^#\n]*)/gm)];
  if (total < 1 || items.length !== total) throw new GateError(`roadmap total_items=${total} but parsed ${items.length}`);
  const seen = new Set();
  items.forEach((item, index) => {
    const slug = scalar(item[1]);
    if (!slug || seen.has(slug)) throw new GateError(`roadmap contains empty or duplicate item slug ${slug}`);
    seen.add(slug);
    const end = index + 1 < items.length ? items[index + 1].index : content.length;
    const block = content.slice(item.index + item[0].length, end);
    const statuses = [...block.matchAll(/^\s+status\s*:\s*([^#\n]*)/gm)];
    if (statuses.length !== 1) throw new GateError(`roadmap item ${slug} must have exactly one status`);
    const status = scalar(statuses[0][1]).toLowerCase();
    if (status !== "completed") throw new GateError(`roadmap item ${slug} status is ${status}; ship requires completed`);
  });
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

function validateShip(aiState, fm, cwd) {
  const sprintSlug = fm.current_sprint_slug;
  if (!SAFE_SLUG.test(sprintSlug || "")) throw new GateError(`invalid current_sprint_slug ${sprintSlug || ""}`);
  const sprintDir = path.join(aiState, "sprints", sprintSlug);
  const roadmapSlug = fm.current_roadmap_slug || "";
  if (roadmapSlug) validateRoadmap(aiState, roadmapSlug);
  if (truthy(fm.design_changed_after_impl)) throw new GateError("design_changed_after_impl=true; repeat review before ship");

  if (fm.path === "Bugfix") requireFile(path.join(sprintDir, "fix-note.md"), "fix-note.md");
  if (GENERATOR_PATHS.has(fm.path)) {
    if (!truthy(fm.skip_impl_subagent_check)) validateGeneratorChain(sprintDir, sprintSlug);
    validateChecklist(path.join(sprintDir, "checklist.yaml"));
    const evidencePath = path.join(sprintDir, "evidence.yaml");
    validateEvidence(evidencePath);
    const reviewPath = selectLatestReview(path.join(sprintDir, "reviews"));
    validateReview(reviewPath, fm.path);
    const designPath = path.join(sprintDir, "design.md");
    if (fs.existsSync(designPath) && fs.statSync(designPath).mtimeMs > fs.statSync(reviewPath).mtimeMs + 2000) {
      throw new GateError(`design.md is newer than latest review ${path.basename(reviewPath)}; repeat review`);
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
    if (!VALID_PATHS.has(fm.path || "")) throw new GateError(`unknown or missing path ${fm.path || ""}`);
    if (!VALID_STAGES.has(fm.stage || "")) throw new GateError(`unknown or missing stage ${fm.stage || ""}`);
    if (fm.stage === "ship") validateShip(aiState, fm, cwd);
  } catch (error) {
    block(error instanceof GateError ? error.message : `internal fail-closed error: ${error.message}`);
  }
}

main();

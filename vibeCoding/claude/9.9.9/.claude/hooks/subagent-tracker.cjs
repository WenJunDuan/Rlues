#!/usr/bin/env node
/** Athena v9.9.6 SubagentStart/Stop ledger and assignment handshake. */
"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const SAFE_SLUG = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

function findAiState(cwd) {
  let current = path.resolve(cwd);
  for (let depth = 0; depth < 8; depth += 1) {
    const candidate = path.join(current, ".ai_state");
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) return candidate;
    // 2026-09-07 fix: stop at git repo boundary — do not inherit a parent project's .ai_state
    if (fs.existsSync(path.join(current, ".git"))) return null;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return null;
}

function redirectToMainRepo(aiState, cwd) {
  try {
    const options = { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] };
    const gitDir = path.resolve(cwd, execFileSync("git", ["rev-parse", "--git-dir"], options).trim());
    const commonDir = path.resolve(cwd, execFileSync("git", ["rev-parse", "--git-common-dir"], options).trim());
    if (gitDir === commonDir) return { aiState, failed: false };
    const main = path.join(path.dirname(commonDir), ".ai_state");
    if (fs.existsSync(main) && fs.statSync(main).isDirectory()) return { aiState: main, failed: false };
    return { aiState, failed: false };
  } catch (_) {
    return { aiState, failed: true };
  }
}

function hitGitBoundary(cwd) {
  let current = path.resolve(cwd);
  for (let depth = 0; depth < 8; depth += 1) {
    const candidate = path.join(current, ".ai_state");
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) return false;
    if (fs.existsSync(path.join(current, ".git"))) return true;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return false;
}

function worktreeSlug(cwd, mainAiState) {
  try {
    const options = { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] };
    const gitDir = path.resolve(cwd, execFileSync("git", ["rev-parse", "--git-dir"], options).trim());
    const commonDir = path.resolve(cwd, execFileSync("git", ["rev-parse", "--git-common-dir"], options).trim());
    if (gitDir === commonDir) return "";
  } catch (_) {
    return "";
  }
  const local = findAiState(cwd);
  if (!local) return "";
  const slug = currentSprint(local);
  if (!slug) return "";
  const sprintDir = path.join(mainAiState, "sprints", slug);
  if (fs.existsSync(sprintDir) && fs.statSync(sprintDir).isDirectory()) return slug;
  return "";
}

function assignmentSprint(mainAiState, agentId, candidates) {
  const hits = [];
  for (const slug of candidates) {
    if (!slug) continue;
    const rows = readJsonl(path.join(mainAiState, "sprints", slug, "subagent-assignments.jsonl"));
    if (rows.some(row => row && row.agent_id === agentId)) hits.push(slug);
  }
  const unique = [...new Set(hits)];
  return unique.length === 1 ? unique[0] : "";
}

function resolveStartSprint(cwd, mainAiState) {
  const wt = worktreeSlug(cwd, mainAiState);
  if (wt) return { slug: wt, source: "worktree-index" };
  return { slug: currentSprint(mainAiState), source: "main-index" };
}

function resolveStopSprint(cwd, mainAiState, agentId) {
  const mainSlug = currentSprint(mainAiState);
  const wt = worktreeSlug(cwd, mainAiState);
  const assigned = assignmentSprint(mainAiState, agentId, [mainSlug, wt]);
  if (assigned) return { slug: assigned, source: "assignment" };
  const locations = startLocations(mainAiState, agentId);
  if (locations.length === 1) {
    const slug = locations[0];
    return { slug, source: slug === wt ? "worktree-index" : "main-index" };
  }
  return resolveStartSprint(cwd, mainAiState);
}

function currentSprint(aiState) {
  try {
    const content = fs.readFileSync(path.join(aiState, "_index.md"), "utf8");
    const match = content.match(/^current_sprint_slug\s*:\s*["']?([^"'\n#]+)/m);
    const slug = match ? match[1].trim() : "";
    return SAFE_SLUG.test(slug) ? slug : "";
  } catch (_) { return ""; }
}

function readJsonl(filePath) {
  try {
    return fs.readFileSync(filePath, "utf8").split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line));
  } catch (_) { return []; }
}

function startLocations(aiState, agentId) {
  const sprints = path.join(aiState, "sprints");
  let names = [];
  try { names = fs.readdirSync(sprints, { withFileTypes: true }).filter(row => row.isDirectory()).map(row => row.name); }
  catch (_) { return []; }
  const locations = [];
  for (const slug of names) {
    if (!SAFE_SLUG.test(slug)) continue;
    const rows = readJsonl(path.join(sprints, slug, "subagent-events.jsonl"));
    if (rows.some(row => row && row.event === "SubagentStart" && row.agent_id === agentId && row.sprint_slug === slug)) {
      locations.push(slug);
    }
  }
  return [...new Set(locations)];
}

function appendJsonl(filePath, row) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.appendFileSync(filePath, `${JSON.stringify(row)}\n`, "utf8");
}

function appendHumanLog(aiState, sprintSlug, eventName, agentId, agentType, lastMessage) {
  const filePath = path.join(aiState, "sprints", sprintSlug, "subagent-log.md");
  if (!fs.existsSync(filePath)) fs.writeFileSync(filePath, `# Subagent Log — ${sprintSlug}\n\n`, "utf8");
  const summary = String(lastMessage || "").replace(/\s+/g, " ").slice(0, 200);
  const entry = [
    `## ${new Date().toISOString()} · ${agentType}`,
    `- Event: ${eventName}`,
    `- Agent ID: ${agentId}`,
    ...(summary ? [`- Last message: ${summary}`] : []),
    "",
    "",
  ].join("\n");
  fs.appendFileSync(filePath, entry, "utf8");
}

function parseArgs(args) {
  const result = {};
  for (let i = 0; i < args.length; i += 1) {
    if (!args[i].startsWith("--") || i + 1 >= args.length) continue;
    result[args[i].slice(2)] = args[i + 1];
    i += 1;
  }
  return result;
}

function assign(args) {
  const values = parseArgs(args);
  const cwd = path.resolve(values.cwd || process.cwd());
  let aiState = findAiState(cwd);
  if (!aiState) throw new Error("Athena .ai_state not found");
  aiState = redirectToMainRepo(aiState, cwd).aiState;
  const agentId = String(values["agent-id"] || "").trim();
  const taskName = String(values["task-name"] || "").trim();
  const role = String(values.role || "").trim();
  if (!agentId || !taskName || !role) throw new Error("assign requires --agent-id, --task-name and --role");
  const locations = startLocations(aiState, agentId);
  if (locations.length !== 1) throw new Error(`assignment requires exactly one new SubagentStart; found ${locations.length}`);
  const sprintSlug = locations[0];
  const filePath = path.join(aiState, "sprints", sprintSlug, "subagent-assignments.jsonl");
  if (readJsonl(filePath).some(row => row && row.agent_id === agentId && row.sprint_slug === sprintSlug)) {
    throw new Error(`duplicate assignment for agent_id=${agentId}`);
  }
  appendJsonl(filePath, {
    schema_version: 1,
    agent_id: agentId,
    task_name: taskName,
    role,
    sprint_slug: sprintSlug,
    timestamp: new Date().toISOString(),
  });
}

function hook() {
  let payload = {};
  try {
    const input = fs.readFileSync(0, "utf8");
    if (input.trim()) payload = JSON.parse(input);
  } catch (_) {}
  const eventName = String(payload.hook_event_name || "");
  if (!["SubagentStart", "SubagentStop"].includes(eventName)) return;
  const cwd = path.resolve(payload.cwd || process.cwd());
  let aiState = findAiState(cwd);
  if (!aiState) {
    if (hitGitBoundary(cwd)) {
      process.stderr.write("[subagent-tracker] .git boundary; event not recorded\n");
    }
    return;
  }
  const redirected = redirectToMainRepo(aiState, cwd);
  aiState = redirected.aiState;
  const agentId = String(payload.agent_id || "").trim();
  const agentType = String(payload.agent_type || "").trim();
  if (!agentId || !agentType) {
    process.stderr.write("[subagent-tracker] missing official agent_id or agent_type; event not recorded\n");
    return;
  }
  const resolved = eventName === "SubagentStop"
    ? resolveStopSprint(cwd, aiState, agentId)
    : resolveStartSprint(cwd, aiState);
  const sprintSlug = resolved.slug;
  if (!sprintSlug) {
    process.stderr.write("[subagent-tracker] no safe sprint slug; event not recorded\n");
    return;
  }
  const row = {
    schema_version: 1,
    event: eventName,
    agent_id: agentId,
    agent_type: agentType,
    sprint_slug: sprintSlug,
    timestamp: new Date().toISOString(),
    sprint_source: resolved.source,
  };
  if (redirected.failed) {
    process.stderr.write("[subagent-tracker] redirect failed\n");
    row.redirect = "failed";
  }
  appendJsonl(path.join(aiState, "sprints", sprintSlug, "subagent-events.jsonl"), row);
  appendHumanLog(aiState, sprintSlug, eventName, agentId, agentType, payload.last_assistant_message);
}

try {
  if (process.argv[2] === "assign") assign(process.argv.slice(3));
  else hook();
} catch (error) {
  process.stderr.write(`[subagent-tracker] ${error.message}\n`);
  process.exitCode = 2;
}

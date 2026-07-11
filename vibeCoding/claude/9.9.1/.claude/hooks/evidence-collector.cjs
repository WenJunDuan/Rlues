#!/usr/bin/env node
/** Athena v9.9.1 PostToolUse/PostToolUseFailure evidence collector. */
"use strict";

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

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

function redirectToMainRepo(aiState, cwd) {
  try {
    const options = { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] };
    const gitDir = path.resolve(cwd, execFileSync("git", ["rev-parse", "--git-dir"], options).trim());
    const commonDir = path.resolve(cwd, execFileSync("git", ["rev-parse", "--git-common-dir"], options).trim());
    if (gitDir === commonDir) return aiState;
    const main = path.join(path.dirname(commonDir), ".ai_state");
    if (fs.existsSync(main) && fs.statSync(main).isDirectory()) return main;
  } catch (_) {}
  return aiState;
}

function currentSprint(aiState) {
  try {
    const content = fs.readFileSync(path.join(aiState, "_index.md"), "utf8");
    const match = content.match(/^current_sprint_slug\s*:\s*["']?([^"'\n#]+)/m);
    return match ? match[1].trim() : "";
  } catch (_) { return ""; }
}

function redact(value) {
  return String(value || "")
    .replace(/\b(sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,})\b/g, "[REDACTED]")
    .replace(/((?:api[_-]?key|token|password|secret)\s*[=:]\s*)[^\s,;]+/gi, "$1[REDACTED]")
    .slice(0, 500);
}

function classifyEvent(eventName) {
  if (eventName === "PostToolUse") return "pass";
  if (eventName === "PostToolUseFailure") return "fail";
  return "unknown";
}

function isValidationCommand(command) {
  const normalized = String(command || "").trim().toLowerCase();
  // Real validation commands are frequently run with a leading KEY=VAL env
  // prefix (e.g. "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest", the exact form
  // runtime-verify.md records); tolerate any number of such prefixes at the
  // start of the command or right after a shell separator.
  const envPrefix = "(?:[a-z_][a-z0-9_]*=\\S+\\s+)*";
  return new RegExp(
    `(^|[;&|]\\s*)${envPrefix}(?:python3?\\s+-m\\s+(?:pytest|unittest)|pytest|npm\\s+(?:test|run\\s+(?:test|build|lint|typecheck|check))|pnpm\\s+(?:test|run\\s+(?:test|build|lint|typecheck|check))|yarn\\s+(?:test|run\\s+(?:test|build|lint|typecheck|check))|bun\\s+(?:test|run\\s+(?:test|build|lint|typecheck|check))|cargo\\s+(?:test|build|check|clippy)|go\\s+(?:test|build|vet)|mvn\\s+(?:test|verify|compile)|\\.\\/gradlew\\s+(?:test|build)|node\\s+--check|git\\s+diff\\s+--check)\\b`,
  ).test(normalized);
}

function yamlString(value) {
  return JSON.stringify(String(value || ""));
}

function appendEvidence(filePath, sprintSlug, row) {
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, `sprint_slug: ${yamlString(sprintSlug)}\ncollected_evidence:\n`, "utf8");
  }
  const entry = [
    `  - tool_use_id: ${yamlString(row.tool_use_id)}`,
    `    tool: ${yamlString(row.tool)}`,
    `    result: ${row.result}`,
    `    command: ${yamlString(row.command)}`,
    `    timestamp: ${yamlString(row.timestamp)}`,
    "",
  ].join("\n");
  fs.appendFileSync(filePath, entry, "utf8");
}

function main() {
  try {
    let payload = {};
    try {
      const input = fs.readFileSync(0, "utf8");
      if (input.trim()) payload = JSON.parse(input);
    } catch (_) {}
    const cwd = path.resolve(payload.cwd || process.cwd());
    let aiState = findAiState(cwd);
    if (!aiState) return;
    aiState = redirectToMainRepo(aiState, cwd);
    const sprintSlug = currentSprint(aiState);
    if (!sprintSlug) return;

    const eventName = String(payload.hook_event_name || "");
    const status = classifyEvent(eventName);
    const tool = String(payload.tool_name || "");
    const toolUseId = String(payload.tool_use_id || "");
    const toolInput = payload.tool_input && typeof payload.tool_input === "object" ? payload.tool_input : {};
    const command = tool === "Bash" ? String(toolInput.command || "").slice(0, 500) : "";
    const timestamp = new Date().toISOString();
    const trace = {
      schema_version: 1,
      timestamp,
      event: eventName || "unknown",
      tool,
      tool_use_id: toolUseId,
      status,
      exit_code: null,
    };
    if (["Edit", "Write", "MultiEdit"].includes(tool)) {
      trace.file = String(toolInput.file_path || toolInput.path || "");
    }
    if (tool === "Bash") trace.command = command;
    if (eventName === "PostToolUseFailure") {
      trace.error = redact(payload.error);
      trace.is_interrupt = payload.is_interrupt === true;
      trace.duration_ms = Number.isFinite(payload.duration_ms) ? payload.duration_ms : null;
    }
    const sprintDir = path.join(aiState, "sprints", sprintSlug);
    fs.mkdirSync(sprintDir, { recursive: true });
    fs.appendFileSync(path.join(sprintDir, "tool-trace.jsonl"), `${JSON.stringify(trace)}\n`, "utf8");

    // A successful file write is useful trace data, but it is not validation.
    if (tool === "Bash" && toolUseId && isValidationCommand(command)) {
      appendEvidence(path.join(sprintDir, "evidence.yaml"), sprintSlug, {
        tool_use_id: toolUseId,
        tool,
        result: status,
        command,
        timestamp,
      });
    }
  } catch (error) {
    process.stderr.write(`[evidence-collector] non-blocking: ${error.message}\n`);
  }
}

main();

#!/usr/bin/env node
/** Record StopFailure metadata without persisting prompts, responses or secrets. */
"use strict";

const fs = require("fs");
const path = require("path");

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

function sprint(aiState) {
  try {
    const match = fs.readFileSync(path.join(aiState, "_index.md"), "utf8")
      .match(/^current_sprint_slug\s*:\s*["']?([^"'\n#]+)/m);
    return match ? match[1].trim() : "";
  } catch (_) { return ""; }
}

function redact(value) {
  return String(value || "")
    .replace(/((?:api[_-]?key|token|password|secret)\s*[=:]\s*)[^\s,;]+/gi, "$1[REDACTED]")
    .slice(0, 500);
}

try {
  let payload = {};
  try {
    const input = fs.readFileSync(0, "utf8");
    if (input.trim()) payload = JSON.parse(input);
  } catch (_) {}
  const aiState = findAiState(payload.cwd || process.cwd());
  if (!aiState) process.exit(0);
  const slug = sprint(aiState);
  if (!slug) process.exit(0);
  const filePath = path.join(aiState, "sprints", slug, "stop-failures.jsonl");
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.appendFileSync(filePath, `${JSON.stringify({
    schema_version: 1,
    event: "StopFailure",
    error: redact(payload.error || payload.message),
    is_interrupt: payload.is_interrupt === true,
    duration_ms: Number.isFinite(payload.duration_ms) ? payload.duration_ms : null,
    timestamp: new Date().toISOString(),
  })}\n`, "utf8");
} catch (error) {
  process.stderr.write(`[stop-failure-recorder] non-blocking: ${error.message}\n`);
}

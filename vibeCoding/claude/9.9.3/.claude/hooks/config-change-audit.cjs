#!/usr/bin/env node
/** Record configuration/instruction drift without copying configuration values. */
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

try {
  let payload = {};
  try {
    const input = fs.readFileSync(0, "utf8");
    if (input.trim()) payload = JSON.parse(input);
  } catch (_) {}
  const aiState = findAiState(payload.cwd || process.cwd());
  if (!aiState) process.exit(0);
  const event = {
    schema_version: 1,
    event: String(payload.hook_event_name || "unknown"),
    source: String(payload.source || payload.config_source || "unknown").slice(0, 80),
    file_name: path.basename(String(payload.file_path || payload.path || "")),
    timestamp: new Date().toISOString(),
  };
  const directory = path.join(aiState, ".snapshots");
  fs.mkdirSync(directory, { recursive: true });
  fs.appendFileSync(path.join(directory, "config-events.jsonl"), `${JSON.stringify(event)}\n`, "utf8");
} catch (error) {
  process.stderr.write(`[config-change-audit] non-blocking: ${error.message}\n`);
}

#!/usr/bin/env node
/** Athena v9.9.6 PostToolUse/PostToolUseFailure evidence collector. */
"use strict";

const fs = require("fs");
const path = require("path");
const binding = require('./_input-binding.cjs');
const io = require('./_index-io.cjs');

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

function currentSprint(aiState) {
  try {
    const content = fs.readFileSync(path.join(aiState, "_index.md"), "utf8");
    const match = content.match(/^current_sprint_slug\s*:\s*["']?([^"'\n#]+)/m);
    return match ? match[1].trim() : "";
  } catch (_) { return ""; }
}

function redact(value) {
  const redacted = String(value || "")
    .replace(/\b(sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,})\b/g, "[REDACTED]")
    .replace(/(authorization\s*:\s*bearer\s+)[^\s,;]+/gi, "$1[REDACTED]")
    .replace(/((?:api[_-]?key|token|password|secret|private[_-]?key|client[_-]?secret|aws[_-](?:secret[_-]?access[_-]?key|access[_-]?key[_-]?id)|database[_-]?url)\s*[=:]\s*)[^\s,;]+/gi, "$1[REDACTED]")
    .replace(/(--(?:password|token|api[-_]?key|secret)(?:=|\s+))[^\s,;]+/gi, "$1[REDACTED]")
    .replace(/(\b(?:https?|postgres(?:ql)?|mysql):\/\/)[^\s/@:]+:[^\s/@]+@/gi, "$1[REDACTED]@");
  const characters = [...redacted];
  if (characters.length <= 1500) return redacted;
  return `${characters.slice(0, 300).join("")}\n…[truncated ${characters.length - 1500} chars]…\n${characters.slice(-1200).join("")}`;
}

function resultStatus(payload) {
  const response = payload.tool_response && typeof payload.tool_response === "object" ? payload.tool_response : {};
  const code = response.exit_code;
  if (Number.isInteger(code)) return code === 0 ? "pass" : "fail";
  if (payload.hook_event_name === "PostToolUseFailure") return "fail";
  // 2026-09-14 harness-patches.md H1: Claude Code Bash tool_response carries no exit_code
  // ({stdout, stderr, interrupted, ...}); a non-zero exit surfaces as a tool failure via
  // PostToolUseFailure above, so a non-interrupted PostToolUse for Bash is exit 0.
  if (payload.hook_event_name === "PostToolUse" && String(payload.tool_name || "").toLowerCase() === "bash"
      && response.interrupted === false && typeof response.stdout === "string") return "pass";
  return "unknown";
}

function yamlString(value) {
  return JSON.stringify(String(value || ""));
}

function appendEvidence(filePath, sprintSlug, row) {
  if (!io.acquire(filePath)) return;
  try {
  const prior = fs.existsSync(filePath) ? fs.readFileSync(filePath,'utf8') : `sprint_slug: ${yamlString(sprintSlug)}\ncollected_evidence:\n`;
  const entry = [
    `  - tool_use_id: ${yamlString(row.tool_use_id)}`,
    `    tool: ${yamlString(row.tool)}`,
    `    result: ${row.result}`,
    ...(row.result_reason ? [`    result_reason: ${yamlString(row.result_reason)}`] : []),
    `    command: ${yamlString(row.command)}`,
    `    timestamp: ${yamlString(row.timestamp)}`,
    ...Object.entries(row.binding).map(([key,value])=>'    '+key+': '+yamlString(value)),
    "",
  ].join("\n");
  io.writeAtomic(filePath, prior + entry);
  } finally { io.release(filePath); }
}

function main() {
  try {
    let payload = {};
    try {
      const input = fs.readFileSync(0, "utf8");
      if (input.trim()) payload = JSON.parse(input);
    } catch (_) {}
    const cwd = path.resolve(payload.tool_input?.workdir || payload.cwd || process.cwd());
    let aiState = findAiState(cwd);
    if (!aiState) return;
    // Evidence belongs to the tested worktree, never a different checkout.
    const sprintSlug = currentSprint(aiState);
    if (!sprintSlug) return;

    const status = resultStatus(payload);
    const tool = String(payload.tool_name || "");
    const toolUseId = String(payload.tool_use_id || "");
    const toolInput = payload.tool_input && typeof payload.tool_input === "object" ? payload.tool_input : {};
    // Classification and the status policy must see the whole command: truncating
    // first can cut a trailing `| tail -8` off and turn a masked pipeline into a
    // provable one. Only the persisted copy is bounded.
    const command = tool === "Bash" ? String(toolInput.command || "") : "";
    const timestamp = new Date().toISOString();
    // hotfix2 (2026-07-29, 台账 W35/AC3): tool-trace.jsonl 默认零遥测 —
    // 普通 Bash/Edit/MCP 不再逐行记账 (写放大主源, 无核心 gate 消费者);
    // re-route 文件数已改由 index-updater 用 git 现场变更集计算 (W36)。
    // A successful file write is useful trace data, but it is not validation.
    if (tool === "Bash" && toolUseId && binding.classifyValidation(command)) {
      const sprintDir = path.join(aiState, "sprints", sprintSlug);
      fs.mkdirSync(sprintDir, { recursive: true });
      // A nominal pass only proves the shell line exited 0; downgrade it when the
      // validation command's own status could not reach that exit code.
      const policy = binding.validationStatusPolicy(command);
      const downgraded = status === "pass" && policy.provable === false;
      // F3 (2026-07-29, W35): command 必须脱敏后落盘 — redact 原只盖 error 字段,
      // 凭据/敏感参数经 command 原文进入版本化 evidence 是 P0 泄露面。
      appendEvidence(path.join(sprintDir, "evidence.yaml"), sprintSlug, {
        tool_use_id: toolUseId,
        tool,
        result: downgraded ? "unknown" : status,
        result_reason: downgraded ? policy.reason : "",
        command: redact(command).slice(0, 500),
        timestamp,
        binding: binding.finish(payload, redact(JSON.stringify(payload.tool_response || payload.tool_result || {}))),
      });
    }
  } catch (error) {
    process.stderr.write(`[evidence-collector] non-blocking: ${error.message}\n`);
  }
}

main();

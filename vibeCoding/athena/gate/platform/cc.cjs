'use strict';
// Claude Code adapter: hook payload → AthenaEvent; decision → stdout/stderr/exit code.
// Block: PreToolUse = exit 2 + stderr; Stop = stdout {"decision":"block","reason"}.
// Context: hookSpecificOutput.additionalContext (SessionStart / UserPromptSubmit / PostToolUse).
const fs = require('fs');
const os = require('os');
const path = require('path');
const frontmatter = require('../lib/frontmatter.cjs');

const EVENTS = {
  SessionStart: 'session_start', UserPromptSubmit: 'prompt', PreToolUse: 'pre_tool',
  PostToolUse: 'post_tool', PostToolUseFailure: 'post_tool_fail', SubagentStart: 'subagent_start',
  SubagentStop: 'subagent_stop', Stop: 'stop', PreCompact: 'compact', PostCompact: 'compact',
  InstructionsLoaded: 'config', ConfigChange: 'config',
};
const CONTEXT_EVENTS = new Set(['SessionStart', 'UserPromptSubmit', 'PostToolUse']);
const WRITE_TOOLS = new Set(['edit', 'write', 'multiedit', 'notebookedit']);

const obj = (value) => (value && typeof value === 'object' && !Array.isArray(value) ? value : {});

function toolKind(name) {
  const tool = String(name || '').toLowerCase();
  if (WRITE_TOOLS.has(tool)) return 'write';
  if (tool === 'bash') return 'bash';
  if (tool === 'agent' || tool === 'task') return 'agent';
  if (tool.startsWith('mcp__') || tool === 'mcp') return 'mcp';
  return 'other';
}

function agentDef(dir, type) {
  if (!type || !/^[A-Za-z0-9._-]+$/.test(type)) return null;
  try { return frontmatter.parse(fs.readFileSync(path.join(dir, `${type}.md`), 'utf8')); } catch (_) { return null; }
}

/** CC Bash tool_response carries no exit_code: a non-interrupted PostToolUse is exit 0 (9.9.9 H1). */
function exitCode(payload, event) {
  const response = obj(payload.tool_response);
  if (Number.isInteger(response.exit_code)) return response.exit_code;
  if (Number.isInteger(response.exitCode)) return response.exitCode;
  if (event === 'post_tool_fail') return 1;
  if (event === 'post_tool' && response.interrupted === false && typeof response.stdout === 'string') return 0;
  return null;
}

/**
 * The session cwd decides which project governs the event; a model-chosen `workdir` never does
 * (review S2 P1). It only resolves relative paths and acts as a leading `cd` for pushes.
 */
function base(payload, argEvent, platform) {
  const raw = String(payload.hook_event_name || argEvent || '');
  const input = obj(payload.tool_input);
  const cwd = path.resolve(String(payload.cwd || process.cwd()));
  const workdir = typeof input.workdir === 'string' && input.workdir ? path.resolve(cwd, input.workdir) : null;
  return { platform, raw_event: raw, event: EVENTS[raw] || 'other', input, cwd, workdir, session_id: payload.session_id ? String(payload.session_id) : '' };
}

function normalize(payload, argEvent) {
  const b = base(obj(payload), argEvent, 'cc');
  const ev = { platform: 'cc', event: b.event, raw_event: b.raw_event, cwd: b.cwd, workdir: b.workdir, session_id: b.session_id };
  ev.tool = toolKind(payload.tool_name);
  const input = b.input;
  if (ev.tool === 'write') ev.paths = [input.file_path, input.notebook_path, input.path].filter(Boolean).map(p => path.resolve(b.workdir || b.cwd, String(p)));
  if (ev.tool === 'bash') ev.command = String(input.command || '');
  if (ev.tool === 'agent') {
    const type = String(input.subagent_type || input.agent_type || '');
    ev.agent = { type, isolation: input.isolation, task: String(input.prompt || input.description || ''), write_set: input.write_set,
      def: agentDef(path.join(os.homedir(), '.claude', 'agents'), type) };
  }
  if (ev.event === 'subagent_start' || ev.event === 'subagent_stop') ev.agent = { type: String(payload.agent_type || ''), id: String(payload.agent_id || '') };
  if (ev.event === 'post_tool' || ev.event === 'post_tool_fail') ev.exit_code = exitCode(payload, ev.event);
  return ev;
}

function warningText(result) {
  return (result.warnings || []).map(w => `[athena] advisory ${w.rule}: ${w.message}\n`).join('');
}

/** Decision → {stdout, stderr, code}. Shared by cx (same protocol). */
function render(result, ev) {
  const out = { stdout: '', stderr: warningText(result), code: 0 };
  if (result.decision === 'block') {
    const reason = `[athena ${result.rule}] ${result.reason}`;
    if (ev.event === 'stop') {
      out.stdout = `${JSON.stringify({ decision: 'block', reason })}\n`;
      out.stderr += `${reason}\n`;
    } else if (ev.event === 'pre_tool') {
      out.stderr += `${reason}\n`;
      out.code = 2;
    } else out.stderr += `${reason}\n`;
    return out;
  }
  if (result.context && CONTEXT_EVENTS.has(ev.raw_event)) {
    out.stdout = `${JSON.stringify({ hookSpecificOutput: { hookEventName: ev.raw_event, additionalContext: result.context } })}\n`;
  }
  return out;
}

module.exports = { normalize, render, base, toolKind, exitCode, agentDef, obj, EVENTS };

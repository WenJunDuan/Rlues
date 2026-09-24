'use strict';
// Pi adapter: the extension calls run('pi', {type, toolName, input, cwd, …}) in-process.
// tool_call → pre_tool; tool_result → post_tool; agent_end / agent_before_settle → stop;
// before_agent_start → prompt; session_start; session_compact → compact.
// Render returns a plain object the extension acts on: {block, reason} | {stop, reason} | {context}.
const path = require('path');

const EVENTS = {
  tool_call: 'pre_tool', tool_result: 'post_tool', agent_end: 'stop', agent_before_settle: 'stop',
  before_agent_start: 'prompt', session_start: 'session_start', session_compact: 'compact',
};
const WRITE_TOOLS = new Set(['edit', 'write', 'multiedit', 'apply_patch']);

function toolKind(name) {
  const tool = String(name || '').toLowerCase();
  if (WRITE_TOOLS.has(tool)) return 'write';
  if (tool === 'bash') return 'bash';
  return 'other';
}

function normalize(payload, argEvent) {
  const p = payload && typeof payload === 'object' ? payload : {};
  const raw = String(p.type || argEvent || '');
  const input = p.input && typeof p.input === 'object' ? p.input : {};
  const cwd = path.resolve(String(p.cwd || process.cwd()));
  const ev = { platform: 'pi', event: EVENTS[raw] || 'other', raw_event: raw, cwd, session_id: String(p.session_id || '') };
  ev.tool = toolKind(p.toolName);
  if (ev.tool === 'write') {
    const files = [input.path, input.file_path].filter(Boolean).map(String);
    if (!files.length && typeof input.patch === 'string') files.push(...require('./cx.cjs').patchPaths(input));
    ev.paths = files.map(f => path.resolve(cwd, f));
  }
  if (ev.tool === 'bash') ev.command = String(input.command || '');
  if (ev.event === 'post_tool') {
    ev.exit_code = Number.isInteger(p.exitCode) ? p.exitCode : (p.isError === true ? 1 : (p.isError === false ? 0 : null));
  }
  return ev;
}

function render(result, ev) {
  const warnings = (result.warnings || []).map(w => `advisory ${w.rule}: ${w.message}`);
  if (result.decision === 'block') {
    const reason = `[athena ${result.rule}] ${result.reason}`;
    return ev.event === 'stop' ? { stop: true, reason, warnings } : { block: true, reason, warnings };
  }
  return result.context ? { context: result.context, warnings } : { warnings };
}

module.exports = { normalize, render, EVENTS };

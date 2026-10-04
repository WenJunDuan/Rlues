'use strict';
// Pi adapter: the extension calls run('pi', {type, toolName, input, cwd, …}) in-process.
// tool_call → pre_tool; tool_result → post_tool; before_agent_start → prompt; session_start;
// session_compact → compact. Stop is evaluated at exactly ONE boundary per settlement, so each
// settlement counts once toward the core circuit breaker (lib/ledger.cjs: same block 3 times → release):
//   agent_before_settle (Pi >= 0.87, outcome "completed") → stop, hard: a block renders the continue form
//   agent_end → stop, soft (followUp): the legacy boundary. On hosts that have agent_before_settle the
//       extension passes hardStop:true, which makes agent_end a no-op here (no evaluation, no ledger row).
// Render returns a plain object the extension acts on:
//   {block, reason} | {stop, reason} | {stop, continue: true, reason, entries: [draft]} | {context}.
//
// Checked against the Pi 1.0.2 sources (packages/coding-agent):
//   src/core/extensions/types.ts   BoundaryResult {entries?, continue?}, CustomMessageEntryDraft,
//                                  AgentActivityOutcome, ToolCallEventResult {block, reason}
//   src/core/messages.ts           a custom message reaches the model as a user message, so the draft
//                                  below makes the context runnable (canContinue) on its own
//   src/core/tools/{write,edit,bash}.ts   tool names, `path` / `command` keys
//   src/extensions/codemode/tool.ts       toolName "codemode", input {code}
const path = require('path');

const EVENTS = {
  tool_call: 'pre_tool', tool_result: 'post_tool', agent_end: 'stop', agent_before_settle: 'stop',
  before_agent_start: 'prompt', session_start: 'session_start', session_compact: 'compact',
};
// Pi 1.0 built-in write tools are `write` and `edit`, both keyed by `path`; the other names cover
// third-party tool packages. `codemode` (JS source in input.code) is deliberately neither a write nor
// a bash: each built-in tool its script calls emits its own tool_call (with parentToolCallId) and is
// judged there.
const WRITE_TOOLS = new Set(['edit', 'write', 'multiedit', 'apply_patch']);
const MIN_HARD_STOP = [0, 87, 0];
const STOP_ENTRY_TYPE = 'athena-stop';

function toolKind(name) {
  const tool = String(name || '').toLowerCase();
  if (WRITE_TOOLS.has(tool)) return 'write';
  if (tool === 'bash') return 'bash';
  return 'other';
}

/** Does this host version have the actionable agent_before_settle boundary (added in 0.87.0)? Unknown → no. */
function supportsHardStop(version) {
  const m = /^(\d+)\.(\d+)\.(\d+)/.exec(String(version || ''));
  if (!m) return false;
  for (let i = 0; i < 3; i += 1) {
    const n = Number(m[i + 1]);
    if (n !== MIN_HARD_STOP[i]) return n > MIN_HARD_STOP[i];
  }
  return true;
}

function stopEvent(p, raw) {
  if (raw === 'agent_end') return p.hardStop === true ? 'other' : 'stop';
  // An aborted or failed run is not a delivery claim: never force a continuation on it, never count it.
  return p.outcome === undefined || p.outcome === 'completed' ? 'stop' : 'other';
}

function normalize(payload, argEvent) {
  const p = payload && typeof payload === 'object' ? payload : {};
  const raw = String(p.type || argEvent || '');
  const input = p.input && typeof p.input === 'object' ? p.input : {};
  const cwd = path.resolve(String(p.cwd || process.cwd()));
  let event = EVENTS[raw] || 'other';
  if (event === 'stop') event = stopEvent(p, raw);
  const ev = { platform: 'pi', event, raw_event: raw, cwd, session_id: String(p.session_id || '') };
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
    if (ev.event !== 'stop') return { block: true, reason, warnings };
    if (ev.raw_event !== 'agent_before_settle') return { stop: true, reason, warnings };
    // Hard stop: the extension returns {entries: [...event.entries, ...entries], continue: true}.
    const entries = [{ type: 'custom_message', customType: STOP_ENTRY_TYPE, content: `[athena · ship 纠偏] ${reason}`, display: true }];
    return { stop: true, continue: true, reason, entries, warnings };
  }
  return result.context ? { context: result.context, warnings } : { warnings };
}

module.exports = { normalize, render, EVENTS, toolKind, supportsHardStop };

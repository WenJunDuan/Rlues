'use strict';
// Codex adapter (D2: Codex hooks call the same JS core through node). Output protocol is
// Claude Code's; differences are tool names, apply_patch targets, array commands and agents.
const fs = require('fs');
const os = require('os');
const path = require('path');
const cc = require('./cc.cjs');

const AGENT_KEYS = ['agent_type', 'subagent_type', 'agent', 'name', 'role'];
const TASK_KEYS = ['task', 'prompt', 'instructions', 'input', 'message'];
const SHELL_TOOLS = new Set(['bash', 'shell', 'exec_command', 'local_shell', 'container.exec', 'unified_exec']);
const PATCH_HEAD = /^\*\*\* (?:Add File|Update File|Delete File|Move to):\s*(.+?)\s*$/gm;

function toolKind(name) {
  const tool = String(name || '').toLowerCase();
  if (tool === 'apply_patch' || tool === 'edit' || tool === 'write') return 'write';
  if (SHELL_TOOLS.has(tool)) return 'bash';
  if (tool === 'spawn_agent' || tool === 'agent') return 'agent';
  if (tool.startsWith('mcp__') || tool === 'mcp') return 'mcp';
  return 'other';
}

/** Every file an apply_patch payload touches (Add/Update/Delete and Move targets). */
function patchPaths(input) {
  const command = Array.isArray(input.command) ? input.command.map(String).join('\n') : input.command;
  const text = [input.patch, input.input, typeof command === 'string' ? command : '']
    .filter(v => typeof v === 'string' && v.includes('*** ')).join('\n');
  return [...text.matchAll(PATCH_HEAD)].map(m => m[1]);
}

/** POSIX single-quote an argv word when it is not plain. */
const quote = (w) => (/^[A-Za-z0-9_@%+=:,./-]+$/.test(w) ? w : `'${w.replace(/'/g, "'\\''")}'`);

/** Codex may send argv arrays: ["bash","-lc","…"] → the script; otherwise the quoted argv. */
function commandText(value) {
  if (Array.isArray(value)) {
    const words = value.map(String);
    const shell = /(^|\/)(?:ba|z|da|k)?sh$/.test(words[0] || '');
    const c = shell ? words.findIndex((v, i) => i > 0 && /^-[A-Za-z]*c[A-Za-z]*$/.test(v)) : -1;
    return c >= 0 && words[c + 1] !== undefined ? words[c + 1] : words.map(quote).join(' ');
  }
  return String(value || '');
}

/** apply_patch invoked through the shell tool (argv or heredoc) is a write, not a command. */
function shellPatch(input) {
  const command = input.command !== undefined ? input.command : input.cmd;
  const script = commandText(command);
  const invoked = /(^|\/)apply_patch$/.test(Array.isArray(command) ? String(command[0] || '') : '')
    || /(?:^|[;&|\n(]\s*|&&\s*)(?:\S*\/)?apply_patch\b/.test(script);
  return invoked && patchPaths({ command: [script, ...(Array.isArray(command) ? command : [])] }).length > 0;
}

function pick(source, keys) {
  for (const key of keys) if (typeof source[key] === 'string' && source[key]) return source[key];
  return '';
}

function agentDef(type) {
  if (!type || !/^[A-Za-z0-9._-]+$/.test(type)) return null;
  let text;
  try { text = fs.readFileSync(path.join(os.homedir(), '.codex', 'agents', `${type}.toml`), 'utf8'); } catch (_) { return null; }
  const m = text.match(/^\s*sandbox_mode\s*=\s*["']([^"']+)["']/m);
  return { sandbox: m ? m[1] : 'workspace-write' };
}

function exitCode(payload, event) {
  const response = payload.tool_response;
  if (response && typeof response === 'object') {
    for (const key of ['exit_code', 'exitCode', 'status']) if (Number.isInteger(response[key])) return response[key];
    const text = typeof response.output === 'string' ? response.output : '';
    const m = text.match(/exit(?:ed with)? code:?\s*(-?\d+)/i);
    if (m) return Number(m[1]);
  }
  if (typeof response === 'string') {
    const m = response.match(/exit(?:ed with)? code:?\s*(-?\d+)/i);
    if (m) return Number(m[1]);
  }
  return cc.exitCode(cc.obj(payload), event);
}

function normalize(payload, argEvent) {
  const p = cc.obj(payload);
  const b = cc.base(p, argEvent, 'cx');
  const ev = { platform: 'cx', event: b.event, raw_event: b.raw_event, cwd: b.cwd, workdir: b.workdir, session_id: b.session_id };
  ev.tool = toolKind(p.tool_name);
  const input = b.input;
  if (ev.tool === 'bash' && shellPatch(input)) ev.tool = 'write';
  if (ev.tool === 'write') {
    const explicit = [input.file_path, input.path].filter(v => typeof v === 'string' && v);
    ev.paths = [...new Set([...explicit, ...patchPaths(input)])].map(f => path.resolve(b.workdir || b.cwd, f));
  }
  if (ev.tool === 'bash') ev.command = commandText(input.command !== undefined ? input.command : input.cmd);
  if (ev.tool === 'agent') {
    // Codex has no verified isolation field (design §5.3): only a declared worktree counts.
    const type = pick(input, AGENT_KEYS) || pick(p, AGENT_KEYS);
    ev.agent = { type, task: pick(input, TASK_KEYS) || pick(p, TASK_KEYS), write_set: input.write_set, def: agentDef(type) };
  }
  if (ev.event === 'subagent_start' || ev.event === 'subagent_stop') ev.agent = { type: pick(p, AGENT_KEYS), id: String(p.agent_id || '') };
  if (ev.event === 'post_tool' || ev.event === 'post_tool_fail') ev.exit_code = exitCode(p, ev.event);
  return ev;
}

module.exports = { normalize, render: cc.render, patchPaths, commandText, toolKind, shellPatch };

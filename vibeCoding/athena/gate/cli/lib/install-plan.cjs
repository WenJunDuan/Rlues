'use strict';
// Install plan for `athena install` (design §11.1): which dist file lands where, how config files
// merge, which 9.9.9 files retire. Pure: reads the dist and the target home, writes nothing.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const LEGACY = require('./legacy-999.cjs');

const REQUIRED_CORE = ['hook.cjs', 'core.cjs', 'cli.cjs', 'lib/context.cjs', 'lib/shell-lex.cjs', 'lib/shell-words.cjs',
  'lib/tree-sha.cjs', 'lib/evidence.cjs', 'platform/cc.cjs', 'platform/cx.cjs', 'platform/pi.cjs', 'templates/_index.md'];
const DIST_DIR = { core: 'athena', cc: 'claude', cx: 'codex', pi: 'pi' };
const sha = (buf) => crypto.createHash('sha256').update(buf).digest('hex');
const MANAGED_HOOK = /(?:~|\$HOME|\/)\.athena\/current\/hook\.cjs/;
const LEGACY_HOOK_NAMES = new Set(LEGACY.filter(p => /^\.(claude|codex)\/hooks\//.test(p)).map(p => path.basename(p)));

class InstallError extends Error {}

/** The dist root holding athena/<ver>/manifest.json (running from source or from an installed dist). */
function distRoot(explicit) {
  const candidates = explicit ? [path.resolve(explicit)]
    : [path.resolve(__dirname, '../../../..'), path.resolve(__dirname, '../../../../dist')];
  for (const root of candidates) {
    let versions = [];
    try { versions = fs.readdirSync(path.join(root, 'athena')).filter(v => fs.existsSync(path.join(root, 'athena', v, 'manifest.json'))); } catch (_) { continue; }
    if (versions.length === 1) return { root, release: versions[0] };
    if (versions.length > 1) throw new InstallError(`several releases under ${root}/athena; pass --dist <root> with one`);
  }
  throw new InstallError('no built dist found (node vibeCoding/athena/build.mjs, or pass --dist <dist root>)');
}

/** Files of one dist tree, verified against its manifest (AC4: a missing or altered asset fails the install). */
function readTree(dist, kind) {
  const dir = path.join(dist.root, DIST_DIR[kind], dist.release);
  let manifest;
  try { manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8')); }
  catch (error) { throw new InstallError(`${DIST_DIR[kind]}/${dist.release}/manifest.json unreadable: ${error.message}`); }
  const files = [];
  for (const entry of manifest.files) {
    if (typeof entry.path !== 'string' || path.isAbsolute(entry.path) || entry.path.split('/').includes('..')) {
      throw new InstallError(`manifest path rejected: ${entry.path}`);
    }
    const abs = path.join(dir, entry.path);
    if (!fs.existsSync(abs)) throw new InstallError(`dist asset missing: ${DIST_DIR[kind]}/${dist.release}/${entry.path}`);
    const content = fs.readFileSync(abs);
    if (sha(content) !== entry.sha256) throw new InstallError(`dist asset altered: ${DIST_DIR[kind]}/${dist.release}/${entry.path}`);
    files.push({ rel: entry.path, content, mode: parseInt(entry.mode, 8) });
  }
  return { version: manifest.version, files };
}

/** Hook groups with Athena entries (10.1 core or 9.9.9 hook files) removed, empty groups dropped. */
function userHooks(hooks) {
  const out = {};
  for (const [event, groups] of Object.entries(hooks || {})) {
    const kept = [];
    for (const group of Array.isArray(groups) ? groups : []) {
      const entries = (group.hooks || []).filter(h => {
        const cmd = String(h.command || '');
        // 9.9.9 entries are recognised only inside ~/.claude/hooks or ~/.codex/hooks (review S6 P2)
        return !MANAGED_HOOK.test(cmd) && ![...LEGACY_HOOK_NAMES].some(name => new RegExp(`(?:~|\\$HOME|/)\\.(?:claude|codex)/hooks/${name.replace(/\./g, '\\.')}\\b`).test(cmd));
      });
      if (entries.length) kept.push({ ...group, hooks: entries });
    }
    if (kept.length) out[event] = kept;
  }
  return out;
}

/** User hooks first, then Athena's groups (replacing every earlier Athena entry). */
function mergeHooks(current, proposed) {
  const merged = userHooks(current);
  for (const [event, groups] of Object.entries(proposed || {})) merged[event] = [...(merged[event] || []), ...groups];
  return merged;
}

function parseJson(text, label) {
  try { return JSON.parse(text); } catch (error) { throw new InstallError(`${label} is not valid JSON (${error.message}); fix or move it, then install again`); }
}

function mergeSettings(currentText, proposedText, version) {
  const current = currentText ? parseJson(currentText, '~/.claude/settings.json') : {};
  if (!current || typeof current !== 'object' || Array.isArray(current)) throw new InstallError('~/.claude/settings.json is not a JSON object');
  const proposed = JSON.parse(proposedText);
  const out = { ...current };
  for (const [key, value] of Object.entries(proposed)) if (!(key in out) && key !== 'hooks') out[key] = value;
  out.env = { ...(current.env || {}), VIBECODING_ATHENA_VERSION: version };
  out.hooks = mergeHooks(current.hooks, proposed.hooks);
  const deny = new Set([...((current.permissions && current.permissions.deny) || []), ...((proposed.permissions && proposed.permissions.deny) || [])]);
  if (deny.size) out.permissions = { ...(current.permissions || {}), deny: [...deny] };
  if (proposed.enabledPlugins) out.enabledPlugins = { ...proposed.enabledPlugins, ...(current.enabledPlugins || {}) };
  return `${JSON.stringify(out, null, 2)}\n`;
}

function mergeHooksFile(currentText, proposedText) {
  const current = currentText ? parseJson(currentText, '~/.codex/hooks.json') : {};
  const proposed = JSON.parse(proposedText);
  return `${JSON.stringify({ ...current, hooks: mergeHooks(current.hooks, proposed.hooks) }, null, 2)}\n`;
}

/**
 * config.toml: keep the user's file; only (re)write VIBECODING_VERSION in [shell_environment_policy.set].
 * Only the plain header form is edited; any other spelling of that table (dotted keys, inline table,
 * quoted header) leaves the file untouched and reports it — a second table would break Codex (review S6 P1).
 * Returns {text, note}.
 */
function mergeToml(currentText, proposedText, home, version) {
  const line = `VIBECODING_VERSION = "${version}"`;
  let text = currentText;
  if (!text) text = proposedText.replace(/<USER_HOME>/g, home).split(`${home}/.codex/skills/`).join(`${home}/.agents/skills/`);
  const eol = text.includes('\r\n') ? '\r\n' : '\n';
  const lines = text.split(/\r?\n/);
  const header = (l) => /^\s*\[\s*shell_environment_policy\s*\.\s*set\s*\]\s*(#.*)?$/.test(l);
  // another table header is harmless unless (unquoted) it names shell_environment_policy.set itself or below it
  const otherHeader = (l) => {
    const m = l.match(/^\s*\[\[?([^\]]*)\]/);
    if (!m || header(l)) return false;
    const key = m[1].replace(/["'\s]/g, '');
    return !(key === 'shell_environment_policy.set' || key.startsWith('shell_environment_policy.set.'));
  };
  const heads = lines.map((l, i) => (header(l) ? i : -1)).filter(i => i >= 0);
  // non-standard spellings: quoted/inline forms, or `set…` keys inside a plain [shell_environment_policy] table
  const parent = (l) => /^\s*\[\s*shell_environment_policy\s*\]\s*(#.*)?$/.test(l);
  const mentions = lines.filter(l => /shell_environment_policy/.test(l) && !header(l) && !parent(l) && !otherHeader(l) && !/^\s*#/.test(l));
  lines.forEach((l, i) => {
    if (!parent(l)) return;
    for (let k = i + 1; k < lines.length && !/^\s*\[/.test(lines[k]); k += 1) if (/^\s*["']?set["']?\s*[.=]/.test(lines[k])) mentions.push(lines[k]);
  });
  if (heads.length > 1 || mentions.length) {
    return { text: currentText || text, note: 'config.toml: shell_environment_policy.set is written in a form the installer does not edit; VIBECODING_VERSION not updated (add it by hand)' };
  }
  if (!heads.length) return { text: `${text.replace(/\s*$/, '')}${eol}${eol}[shell_environment_policy.set]${eol}${line}${eol}`, note: null };
  let end = heads[0] + 1;
  while (end < lines.length && !/^\s*\[/.test(lines[end])) end += 1;
  const at = lines.slice(heads[0] + 1, end).findIndex(l => /^\s*["']?VIBECODING_VERSION["']?\s*=/.test(l));
  if (at >= 0) lines[heads[0] + 1 + at] = line; else lines.splice(heads[0] + 1, 0, line);
  return { text: lines.join(eol), note: null };
}

/** Where a dist file of a platform lands (home-relative), or null when it is not installed. */
function target(kind, rel, release) {
  if (kind === 'core') return `.athena/${release}/${rel}`;
  if (kind === 'pi') return /^(plugin|config)\//.test(rel) ? `.athena/${release}/pi/${rel}` : null;
  const top = kind === 'cc' ? '.claude/' : '.codex/';
  if (['manifest.json', 'GENERATED.md', 'contracts.json'].includes(rel)) return null;
  if (!rel.startsWith(top)) return `.athena/${release}/docs/${DIST_DIR[kind]}/${rel}`;
  if (rel === '.claude/settings.proxy.json') return null;
  if (kind === 'cx' && rel.startsWith('.codex/skills/')) return `.agents/skills/${rel.slice('.codex/skills/'.length)}`;
  return rel;
}

/** Full plan: [{kind, action: write|merge|retire, dest (home-relative), content?, mode?}]. */
function plan(home, platforms, dist) {
  const core = readTree(dist, 'core');
  for (const need of REQUIRED_CORE) {
    if (!core.files.some(f => f.rel === need)) throw new InstallError(`dist core is missing a required asset: ${need}`);
  }
  const version = core.version;
  const notes = [];
  const actions = core.files.filter(f => target('core', f.rel, dist.release)).map(f => ({ kind: 'core', action: 'write', dest: target('core', f.rel, dist.release), content: f.content, mode: f.mode }));
  for (const kind of platforms) {
    for (const f of readTree(dist, kind).files) {
      const dest = target(kind, f.rel, dist.release);
      if (!dest) continue;
      const read = () => { try { return fs.readFileSync(path.join(home, dest), 'utf8'); } catch (_) { return ''; } };
      if (dest === '.claude/settings.json') actions.push({ kind, action: 'merge', dest, content: Buffer.from(mergeSettings(read(), f.content.toString('utf8'), version)), mode: 0o600 });
      else if (dest === '.codex/hooks.json') actions.push({ kind, action: 'merge', dest, content: Buffer.from(mergeHooksFile(read(), f.content.toString('utf8'))), mode: 0o644 });
      else if (dest === '.codex/config.toml') {
        const merged = mergeToml(read(), f.content.toString('utf8'), home, version);
        if (merged.note) notes.push(merged.note);
        actions.push({ kind, action: 'merge', dest, content: Buffer.from(merged.text), mode: 0o600 });
      }
      else actions.push({ kind, action: 'write', dest, content: f.content, mode: f.mode });
    }
  }
  // Pre-flight: every destination must stay inside HOME and be writable as a file (no file where a
  // directory is needed, no directory where a file goes) — refuse before anything is written.
  for (const a of actions) {
    const abs = path.resolve(home, a.dest);
    if (!abs.startsWith(home + path.sep)) throw new InstallError(`refusing destination outside HOME: ${a.dest}`);
    for (let d = path.dirname(abs); d.length > home.length; d = path.dirname(d)) {
      let st = null;
      try { st = fs.statSync(d); } catch (_) { continue; }
      if (!st.isDirectory()) throw new InstallError(`${path.relative(home, d)} exists and is not a directory (needed for ${a.dest}); move it aside first`);
    }
    try { if (fs.statSync(abs).isDirectory()) throw new InstallError(`${a.dest} exists as a directory; move it aside first`); } catch (error) { if (error instanceof InstallError) throw error; }
  }
  const hooks = {};
  for (const a of actions.filter(x => x.action === 'merge' && /\.json$/.test(x.dest))) {
    const data = JSON.parse(a.content.toString('utf8'));
    hooks[a.dest] = Object.values(data.hooks || {}).flat().flatMap(g => g.hooks || []).map(h => h.command).filter(c => MANAGED_HOOK.test(String(c)));
  }
  const installing = new Set(actions.map(a => a.dest));
  for (const rel of LEGACY) {
    const owner = rel.startsWith('.claude/') ? 'cc' : 'cx';
    if (platforms.includes(owner) && !installing.has(rel) && fs.existsSync(path.join(home, rel))) actions.push({ kind: owner, action: 'retire', dest: rel });
  }
  return { version, release: dist.release, actions, notes, hooks };
}

module.exports = { plan, distRoot, readTree, mergeSettings, mergeHooksFile, mergeToml, userHooks, target, InstallError, REQUIRED_CORE, sha };

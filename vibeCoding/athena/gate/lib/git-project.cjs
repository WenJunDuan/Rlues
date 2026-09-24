'use strict';
// Which repository a `git push` targets, and whether it is the current project
// (ported from 9.9.9 pre-bash-guard.cjs incl. the S0 fixes, Q12 #29).
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const words = require('./shell-words.cjs');

// Any GIT_DIR-family variable anywhere redirects the repository behind -C's back.
const REPO_REDIRECT_ENV = /\bGIT_(?:DIR|WORK_TREE|COMMON_DIR|OBJECT_DIRECTORY|ALTERNATE_OBJECT_DIRECTORIES|NAMESPACE)\b/;

/** A directory named on the command line, resolved without the shell; null if it needs expansion or is missing. */
function resolveDir(raw, base) {
  if (typeof raw !== 'string' || !raw || raw === '-' || /[$`]/.test(raw)) return null;
  let value = raw;
  if (value === '~' || value.startsWith('~/')) value = path.join(os.homedir(), value.slice(1));
  else if (value.startsWith('~')) return null;
  const resolved = path.resolve(base, value);
  try {
    if (!fs.statSync(resolved).isDirectory()) return null;
    fs.accessSync(resolved, fs.constants.X_OK); // a cd that would fail leaves the push in the project
    return resolved;
  } catch (_) { return null; }
}

/** The repository argument of `git push`: undefined = none named, null = unreadable ($VAR, `…`). */
function pushDestination(args) {
  const withValue = new Set(['-o', '--push-option', '--receive-pack', '--exec', '--repo']);
  for (let i = 0; i < args.length; i += 1) {
    const value = args[i];
    let dest;
    if (value.startsWith('--repo=')) dest = value.slice(7);
    else if (value === '--repo') dest = args[i + 1];
    else if (withValue.has(value)) { i += 1; continue; }
    else if (value.startsWith('-')) continue;
    else dest = value;
    return dest === undefined || /[$`]/.test(dest) ? null : dest;
  }
  return undefined;
}

/**
 * {dir, dest} of the push in `active` (comments stripped, quoted heredoc body masked), starting
 * at `start` (a Codex workdir acts as a leading cd): the last top-level cd joined by && or ;,
 * then the push's own -C options. Anything the guard cannot resolve keeps the strict answer:
 * the session cwd.
 */
function pushTarget(active, cwd, start = cwd) {
  const strict = { dir: cwd, dest: undefined };
  if (REPO_REDIRECT_ENV.test(active)) return strict;
  let base = start;
  let leading = true; // only a run of leading cd's can move the target; a cd after any other command may not run
  for (const item of words.parse(active)) {
    const values = item.args.map(token => token.value);
    // A cd that may not run, or runs in another scope, must not move a later push (review r2/r3):
    // subshell parens, `||`, and control words (if/then/while/do/!/{ …) → strict.
    if ([item.segment.before, item.segment.after].some(op => op === '(' || op === ')' || op === '||')) return strict;
    const first = item.segment.words.find(w => !/^[A-Za-z_][A-Za-z0-9_]*=/.test(w.value));
    if (first && words.CONTROL.has(first.value)) return strict;
    if (item.name === 'cd') {
      // Only the shell builtin moves the directory: `nohup cd`, `timeout 5 cd`, `env cd` … run a
      // child (or fail) and leave the push in the project (review r4 P1).
      const raw = item.segment.words.map(w => w.value).filter(v => !/^[A-Za-z_][A-Za-z0-9_]*=/.test(v));
      const builtin = raw[0] === 'cd' || (['builtin', 'command'].includes(raw[0]) && raw[1] === 'cd');
      if (!leading || !builtin) return strict;
      const next = values.length ? resolveDir(values[0], base) : os.homedir();
      if (!next || !['&&', ';'].includes(item.segment.after)) return strict;
      base = next;
      continue;
    }
    if (item.name === 'git' && words.gitSubcommand(item.args) === 'push') {
      leading = false;
      let dir = base;
      let i = 0;
      for (; i < values.length; i += 1) {
        const value = values[i];
        if (value === '-C') {
          dir = resolveDir(values[i + 1], dir);
          if (!dir) return strict;
          i += 1;
          continue;
        }
        if (/^--(?:git-dir|work-tree)(?:=|$)/.test(value)) return strict;
        if (['-c', '--namespace', '--config-env'].includes(value)) { i += 1; continue; }
        if (!value.startsWith('-')) break;
      }
      return { dir, dest: pushDestination(values.slice(i + 1)) };
    }
    leading = false;
  }
  return strict;
}

function gitOut(dir, args) {
  try {
    return execFileSync('git', ['-C', dir, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 10000 })
      .split('\n').map(line => line.trim()).filter(Boolean);
  } catch (_) { return []; }
}

/** Every remote URL, as written and as rewritten by insteadOf / pushInsteadOf. */
function remoteUrls(dir) {
  const urls = new Set(gitOut(dir, ['config', '--get-regexp', '^remote\\..*\\.(url|pushurl)$'])
    .map(line => line.split(/\s+/).slice(1).join(' ')));
  for (const name of gitOut(dir, ['remote'])) {
    for (const url of gitOut(dir, ['remote', 'get-url', '--all', name])) urls.add(url);
    for (const url of gitOut(dir, ['remote', 'get-url', '--push', '--all', name])) urls.add(url);
  }
  return [...urls];
}

/** base/value without collapsing "..": the OS resolves ".." against a symlink's target. */
function unresolvedJoin(base, value) {
  return path.isAbsolute(value) ? value : `${base}${path.sep}${value}`;
}

/** host/path for network remotes (any scheme, scp-like); a real absolute path for local ones. */
function normalizeRemote(url, base) {
  const raw = String(url).trim().replace(/\/+$/, '');
  const trimmed = raw.replace(/\.git$/, '');
  const local = (value) => {
    let head = unresolvedJoin(base, value);
    const tail = [];
    for (;;) {
      try { return path.join(fs.realpathSync.native(head), ...tail).replace(/\.git$/, ''); } catch (_) { /* climb */ }
      const parent = path.dirname(head);
      if (parent === head) return path.resolve(base, value).replace(/\.git$/, '');
      tail.unshift(path.basename(head));
      head = parent;
    }
  };
  if (/^file:\/\//i.test(raw)) return local(raw.replace(/^file:\/\//i, ''));
  let match = trimmed.match(/^[a-z][a-z0-9+.-]*:\/\/(?:[^@/]+@)?([^/:]+)(?::\d+)?\/?(.*)$/i);
  if (match) return `${match[1]}/${match[2]}`.toLowerCase();
  match = trimmed.match(/^(?:[^@/\s]+@)?([^:/\s]+):(?!\/\/)(.*)$/);
  if (match && match[1].length > 1) return `${match[1]}/${match[2].replace(/^\/+/, '')}`.toLowerCase();
  return local(raw);
}

/** Same repository = same realpath of `git rev-parse --git-common-dir`; any failure = not proven. */
function sameRepository(a, b) {
  const common = (dir) => {
    const out = gitOut(dir, ['rev-parse', '--git-common-dir'])[0];
    if (!out) return null;
    try { return fs.realpathSync(path.resolve(dir, out)); } catch (_) { return null; }
  };
  const left = common(a);
  return left !== null && left === common(b);
}

/**
 * Another checkout of the same project stays under the project's stage: a worktree or
 * subdirectory, a clone sharing any remote, a clone of the project itself, or a push whose
 * destination is one of the project's remotes. Only a repository proven unrelated escapes.
 */
function sameProject(target, cwd, dest) {
  if (sameRepository(target, cwd)) return true;
  if (dest === null) return true;
  const own = new Set(remoteUrls(cwd).map(url => normalizeRemote(url, cwd)));
  const theirs = remoteUrls(target);
  if (typeof dest === 'string') theirs.push(dest, ...gitOut(target, ['ls-remote', '--get-url', dest]));
  for (const raw of theirs) {
    if (own.has(normalizeRemote(raw, target))) return true;
    const local = unresolvedJoin(target, raw);
    try { if (fs.statSync(local).isDirectory() && sameRepository(local, cwd)) return true; } catch (_) { /* not local */ }
  }
  return false;
}

module.exports = { pushTarget, pushDestination, resolveDir, sameProject, sameRepository, normalizeRemote, REPO_REDIRECT_ENV };

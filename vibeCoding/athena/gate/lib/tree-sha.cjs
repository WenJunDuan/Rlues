'use strict';
// Source-tree sha (design §5.3, D4): the git tree of the working tree's current content —
// tracked + untracked-not-ignored — with .ai_state/ and the sprint's review_ignore globs
// excluded. Computed through a throwaway index so the user's index is never touched; the
// copied index lets git re-hash only files whose stat changed.
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

function run(root, args, env) {
  return execFileSync('git', ['-C', root, ...args], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 30000, maxBuffer: 256 * 1024 * 1024, env,
  }).trim();
}

/**
 * A usable review_ignore glob names something: not match-all ("**", "*", "**\/*"), not absolute,
 * no "..". Others are dropped, so the tree stays strict (review S2 P2).
 */
function usableGlob(glob) {
  if (typeof glob !== 'string') return false;
  const g = glob.trim();
  return Boolean(g) && !g.startsWith('/') && !g.split('/').includes('..') && /[^*?/[\]{}!.,\s]/.test(g);
}

/** Tree sha of root's working tree, or null when root is not a git work tree. */
function treeSha(root, ignore = []) {
  const clean = { ...process.env };
  delete clean.GIT_INDEX_FILE;
  let indexPath;
  try { indexPath = path.resolve(root, run(root, ['rev-parse', '--git-path', 'index'], clean)); }
  catch (_) { return null; }
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'athena-tree-'));
  const env = { ...clean, GIT_INDEX_FILE: path.join(tmp, 'index') };
  try {
    try {
      fs.copyFileSync(indexPath, env.GIT_INDEX_FILE);
      // keep the index mtime: git's racy-clean check compares entry mtimes against it, and a fresh
      // copy would make a same-size edit within the same second look clean
      const st = fs.statSync(indexPath);
      fs.utimesSync(env.GIT_INDEX_FILE, st.atime, st.mtime);
    } catch (_) { /* unborn repo: start empty */ }
    // assume-unchanged / skip-worktree entries would hide edits from `git add` (review S2 P2).
    const hidden = run(root, ['ls-files', '-v', '-z'], env).split('\0').filter(l => /^[a-zS]/.test(l)).map(l => l.slice(2));
    // Paths go on argv (git ignores --no-skip-worktree with --stdin), one flag per call (combined
    // flags drop one on git 2.34), in chunks.
    for (const flag of ['--no-assume-unchanged', '--no-skip-worktree']) {
      for (let i = 0; i < hidden.length; i += 200) run(root, ['update-index', flag, '--', ...hidden.slice(i, i + 200)], env);
    }
    const globs = ignore.filter(usableGlob).map(g => g.trim());
    const excluded = ['.ai_state', ...globs.map(g => `:(glob)${g}`)];
    run(root, ['add', '-A', '--', '.', ...excluded.map(p => (p.startsWith(':(') ? `:(exclude,${p.slice(2)}` : `:(exclude)${p}`))], env);
    run(root, ['rm', '-r', '-q', '-f', '--cached', '--ignore-unmatch', '--', ...excluded], env); // temp index only
    return run(root, ['write-tree'], env);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

/** Per-file blob shas of a tree (for review rejection messages, S3). */
function treeFiles(root, tree) {
  const out = {};
  const listing = execFileSync('git', ['-C', root, 'ls-tree', '-r', '-z', tree], { encoding: 'utf8', timeout: 60000 });
  for (const entry of listing.split('\0').filter(Boolean)) {
    const tab = entry.indexOf('\t');
    out[entry.slice(tab + 1)] = entry.slice(0, tab).split(' ')[2];
  }
  return out;
}

module.exports = { treeSha, treeFiles, usableGlob };

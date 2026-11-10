'use strict';
// Review packet Changes (design §6): base → current tree, without commits another sprint made while
// this one was paused (G-006/G-021/G-024/G-033).
const fs = require('fs');
const path = require('path');
const attribution = require('../../lib/attribution.cjs');
const { git } = require('../../lib/context.cjs');
const { pathspec } = require('../../lib/tree-sha.cjs');

// The current tree omits .ai_state and review_ignore; diff the base through the same pathspec
// or every tracked .ai_state file reads as deleted (G-003).
function changed(ctx, base, tree, ignore) {
  if (!base) return { stat: '(design.md has no base_commit)', names: [] };
  const baseTree = git(ctx.root, ['rev-parse', `${base}^{tree}`]);
  if (!baseTree) return { stat: `(base_commit ${base} not found)`, names: [] };
  const spec = ['--', ...pathspec(ignore)];
  return {
    stat: git(ctx.root, ['diff-tree', '-r', '--stat=120', baseTree, tree, ...spec]) || '(no changes)',
    names: (git(ctx.root, ['diff-tree', '-r', '--name-status', baseTree, tree, ...spec]) || '').split('\n').filter(Boolean),
  };
}

/** Hot sprints whose slug (or slug without its date prefix) is a whole token of `text`. */
function sprintsNamed(slugs, text) {
  return slugs.filter(slug => [slug, slug.replace(/^\d{4}-\d{2}-\d{2}-/, '')].some(key => attribution.token(text, key)));
}

// Sprints owning a paused-interval commit: named by its message, a merged branch (by name or via
// sprintForWorktree) or the merged side's messages, or the only sprint whose state it touches.
function commitOwners(ctx, commit, slugs) {
  const owners = new Set(sprintsNamed(slugs, git(ctx.root, ['log', '-1', '--format=%B', commit]) || ''));
  const parents = (git(ctx.root, ['rev-list', '--parents', '-n', '1', commit]) || '').split(' ').slice(1);
  if (parents.length > 1) {
    for (const s of sprintsNamed(slugs, git(ctx.root, ['log', '--format=%B', `${parents[0]}..${parents[1]}`]) || '')) owners.add(s);
    const branch = ((git(ctx.root, ['log', '-1', '--format=%s', commit]) || '').match(/^Merge (?:remote-tracking )?branch '([^']+)'/) || [])[1];
    const mapped = branch && attribution.sprintForWorktree(ctx, '', branch);
    if (mapped) owners.add(mapped);
  } else if (!owners.size) {
    const files = (git(ctx.root, ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]) || '').split('\n').filter(Boolean);
    const dirs = new Set(files.map(f => (f.match(/^\.ai_state\/sprints\/([^/]+)\//) || [])[1]));
    if (files.length && dirs.size === 1 && slugs.includes([...dirs][0])) owners.add([...dirs][0]);
  }
  return owners;
}

// Commits made while this sprint is paused that belong to another sprint: anything naming this sprint
// stays; anything naming only others goes; unknown ownership stays (G-021/G-024) — except while the
// sprint had nothing of its own yet (nothing kept in base..pause head), where only commits naming it
// stay (G-033: a sprint paused right after start listed the whole interval's foreign work). Legacy
// logs without HEAD boundaries keep the inclusive diff; excluded commits are listed in the packet.
function excludedCommits(ctx, base) {
  let log = '';
  try { log = fs.readFileSync(path.join(ctx.sprintDir, 'log.md'), 'utf8'); } catch (_) { return []; }
  const range = new Set((git(ctx.root, ['rev-list', `${base}..HEAD`]) || '').split('\n').filter(Boolean));
  const excluded = new Set();
  const slugs = attribution.hotSprints(ctx).concat(ctx.sprint).filter((s, i, a) => s && a.indexOf(s) === i);
  let paused = null;
  for (const line of log.split('\n')) {
    const m = line.match(/ (paused|resumed) at .*?\(head ([0-9a-f]{40,64})\)/);
    if (!m) continue;
    if (m[1] === 'paused') paused = m[2];
    else if (paused) {
      const fresh = (git(ctx.root, ['rev-list', `${base}..${paused}`]) || '').split('\n').every(c => !c || excluded.has(c));
      const commits = git(ctx.root, ['rev-list', `${paused}..${m[2]}`]);
      for (const commit of (commits || '').split('\n')) {
        if (!range.has(commit)) continue;
        const owners = commitOwners(ctx, commit, slugs);
        if (!owners.has(ctx.sprint) && (owners.size > 0 || fresh)) excluded.add(commit);
      }
      paused = null;
    }
  }
  return [...excluded];
}

function sprintChanges(ctx, base, tree, ignore, excluded) {
  if (!excluded.length) return changed(ctx, base, tree, ignore);
  const omit = new Set(excluded);
  const commits = (git(ctx.root, ['rev-list', '--reverse', '--first-parent', `${base}..HEAD`]) || '').split('\n').filter(c => c && !omit.has(c));
  const spec = ['--', ...pathspec(ignore)];
  const stats = [], names = new Set();
  // Per-commit patches retain this sprint's edits even when another slice touched the same file.
  const pairs = commits.map(c => [c + '^', c]);
  pairs.push(['HEAD', tree]); // staged, unstaged and untracked source are still reviewed
  for (const [from, to] of pairs) {
    const stat = git(ctx.root, ['diff-tree', '-r', '--stat=120', from, to, ...spec]);
    if (stat) stats.push(`${from} → ${to}\n${stat}`);
    for (const name of (git(ctx.root, ['diff-tree', '-r', '--name-status', from, to, ...spec]) || '').split('\n')) if (name) names.add(name);
  }
  return { stat: stats.join('\n') || '(no changes)', names: [...names] };
}

module.exports = { excludedCommits, sprintChanges };

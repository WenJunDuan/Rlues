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

const undated = slug => slug.replace(/^\d{4}-\d{2}-\d{2}-/, '');

/** Sprints whose slug (or slug without its date prefix) is a whole token of `text`. */
function sprintsNamed(slugs, text) {
  return slugs.filter(slug => [slug, undated(slug)].some(key => attribution.token(text, key)));
}

// Archived slugs number in the thousands and include short words (tts, x, boundaries), so prose
// mentions are not ownership: only a conventional-commit scope `type(slug):` names an archived sprint.
function archivedNamed(archived, text) {
  const scopes = new Set([...text.matchAll(/^[a-z]+\(([^)\s]+)\)!?:/gm)].map(m => m[1]));
  return archived.filter(slug => scopes.has(slug) || scopes.has(undated(slug)));
}

/** Owners named in `text`: hot sprints by any whole-token mention, archived ones by commit scope. */
function ownersNamed(slugs, text) {
  return [...sprintsNamed(slugs.hot, text), ...archivedNamed(slugs.archived, text)];
}

function revList(root, ...args) {
  return (git(root, ['rev-list', ...args]) || '').split('\n').filter(Boolean);
}

// The redirect table still names shipped sprints after their directories have been packed.
function archivedSlugs(ctx) {
  let redirects;
  try { redirects = fs.readFileSync(path.join(ctx.aiState, 'archive', 'README.md'), 'utf8'); } catch (_) { return []; }
  return [...redirects.matchAll(/^\| sprints\/([A-Za-z0-9][A-Za-z0-9._-]*)\/? \| archive\/sprints\/\d{4}-\d{2}\/\1\/? \|$/gm)].map(m => m[1]);
}

function commitOwners(ctx, commit, slugs) {
  const named = ownersNamed(slugs, git(ctx.root, ['log', '-1', '--format=%B', commit]) || '');
  if (named.length) return named;
  const files = (git(ctx.root, ['diff-tree', '--no-commit-id', '--name-only', '-r', commit]) || '').split('\n').filter(Boolean);
  const dirs = new Set(files.map(f => (f.match(/^\.ai_state\/sprints\/([^/]+)\//) || [])[1]));
  return dirs.size === 1 && slugs.hot.includes([...dirs][0]) ? [...dirs] : [];
}

function mergeOwners(ctx, commit, parents, slugs, dispatches) {
  const message = git(ctx.root, ['log', '-1', '--format=%B', commit]) || '';
  const sideMessages = git(ctx.root, ['log', '--format=%B', ...sideRange(parents)]) || '';
  const owners = new Set(ownersNamed(slugs, `${message}\n${sideMessages}`));
  const branch = (message.match(/^Merge (?:remote-tracking )?branch '([^']+)'/) || [])[1];
  const mapped = branch && attribution.sprintForWorktree(ctx, '', branch);
  if (mapped) owners.add(mapped);
  const mergedParents = parents.slice(1);
  if (dispatches.some(rec => branch ? rec.branch === branch : mergedParents.includes(rec.head))) owners.add(ctx.sprint);
  if (!branch && !owners.has(ctx.sprint)) {
    // An edited merge subject may omit the branch name. A ref at the merged tip can keep its work.
    for (const parent of mergedParents) {
      const refs = git(ctx.root, ['for-each-ref', `--points-at=${parent}`, '--format=%(refname:lstrip=2)', 'refs/heads', 'refs/remotes']) || '';
      if (sprintsNamed([ctx.sprint], refs).length || dispatches.some(rec => refs.split('\n').includes(rec.branch))) owners.add(ctx.sprint);
    }
  }
  return owners;
}

function pausedCommits(ctx, base, log) {
  const candidates = new Set();
  let keep = null;
  let paused = null;
  for (const line of log.split('\n')) {
    const m = line.match(/ (paused|resumed) at .*?\(head ([0-9a-f]{40,64})\)/);
    if (!m) continue;
    if (m[1] === 'paused') {
      paused = m[2];
      // A later pause can be recorded on a different branch with an older head.
      keep ??= new Set(revList(ctx.root, `${base}..${paused}`));
    } else if (paused) {
      for (const commit of revList(ctx.root, `${paused}..${m[2]}`)) if (!keep.has(commit)) candidates.add(commit);
      paused = null;
    }
  }
  return { keep, candidates };
}

// The first parent already contains mainline changes brought into a writer branch by an earlier sync.
const sideRange = ([first, ...side]) => [...side, `^${first}`];

function attributeMerges(ctx, range, slugs, candidates, keep) {
  const foreign = new Set();
  const dispatches = attribution.writerDispatches(ctx);
  for (const row of revList(ctx.root, '--first-parent', '--merges', '--parents', range)) {
    const [commit, ...parents] = row.split(' ');
    const owners = mergeOwners(ctx, commit, parents, slugs, dispatches);
    const group = owners.has(ctx.sprint) ? keep : candidates.has(commit) && owners.size ? foreign : null;
    if (group) for (const sha of [commit, ...revList(ctx.root, ...sideRange(parents))]) group.add(sha);
  }
  return foreign;
}

// Keep unknown ownership. Legacy logs without HEAD boundaries retain the inclusive diff.
function excludedCommits(ctx, base) {
  if (!base) return [];
  let log;
  try { log = fs.readFileSync(path.join(ctx.sprintDir, 'log.md'), 'utf8'); } catch (_) { return []; }
  const { keep, candidates } = pausedCommits(ctx, base, log);
  if (!candidates.size) return [];
  const headRange = `${base}..HEAD`;
  const reachable = new Set(revList(ctx.root, headRange));
  const hot = [...new Set([...attribution.hotSprints(ctx), ctx.sprint])];
  const slugs = { hot, archived: archivedSlugs(ctx).filter(slug => !hot.includes(slug)) };
  const foreign = attributeMerges(ctx, headRange, slugs, candidates, keep);
  return [...candidates].filter(commit => {
    if (keep.has(commit) || !reachable.has(commit)) return false;
    const owners = commitOwners(ctx, commit, slugs);
    return !owners.includes(ctx.sprint) && (owners.length > 0 || foreign.has(commit));
  });
}

function commitDiffs(root, base, omit, spec) {
  const covered = new Set(omit);
  const pairs = [];
  for (const row of revList(root, '--topo-order', '--parents', `${base}..HEAD`)) {
    const [commit, ...parents] = row.split(' ');
    if (covered.has(commit)) continue;
    let paths = spec;
    if (parents.length > 1) {
      const side = revList(root, ...sideRange(parents));
      if (side.some(sha => omit.has(sha))) {
        // Review the kept side commits separately, plus paths changed relative to every parent.
        const names = (git(root, ['diff-tree', '-r', '-c', '--name-only', '-z', commit, ...spec]) || '').split('\0').slice(1, -1);
        if (!names.length) continue;
        paths = ['--', ...names.map(name => `:(top,literal)${name}`)];
      } else {
        for (const sha of side) covered.add(sha);
      }
    }
    pairs.push([`${commit}^`, commit, paths]);
  }
  return pairs.reverse();
}

function sprintChanges(ctx, base, tree, ignore, excluded) {
  if (!excluded.length) return changed(ctx, base, tree, ignore);
  const spec = ['--', ...pathspec(ignore)];
  const stats = [], names = new Set();
  // Per-commit patches retain this sprint's edits even when another slice touched the same file.
  const pairs = commitDiffs(ctx.root, base, new Set(excluded), spec);
  pairs.push(['HEAD', tree, spec]); // staged, unstaged and untracked source are still reviewed
  for (const [from, to, paths] of pairs) {
    const stat = git(ctx.root, ['diff-tree', '-r', '--stat=120', from, to, ...paths]);
    if (stat) stats.push(`${from} → ${to}\n${stat}`);
    for (const name of (git(ctx.root, ['diff-tree', '-r', '--name-status', from, to, ...paths]) || '').split('\n')) if (name) names.add(name);
  }
  return { stat: stats.join('\n') || '(no changes)', names: [...names] };
}

module.exports = { excludedCommits, sprintChanges };

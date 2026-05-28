#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.4 · CC WorktreeCreate + WorktreeRemove hook
 * 
 * 职责:
 *   1. WorktreeCreate: 写 worktrees.yaml + 更新 _index.active_worktrees
 *   2. WorktreeRemove: 更新 worktrees.yaml.status + 移除 _index.active_worktrees
 * 
 * 输入: hook payload (含 worktree_name, worktree_path, branch, event_name)
 * 源: https://code.claude.com/docs/en/worktrees
 */
'use strict';

const fs = require('fs');
const path = require('path');

function findAiState(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(current, '.ai_state');
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) return candidate;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;
}

function getCurrentSprintSlug(aiState) {
  const idxPath = path.join(aiState, '_index.md');
  if (!fs.existsSync(idxPath)) return null;
  const content = fs.readFileSync(idxPath, 'utf-8');
  const m = content.match(/current_sprint_slug:\s*["']?([^"\n]+)["']?/);
  return m ? m[1].trim() : null;
}

function updateActiveWorktrees(aiState, worktreeName, action) {
  // action = 'add' | 'remove'
  const idxPath = path.join(aiState, '_index.md');
  const content = fs.readFileSync(idxPath, 'utf-8');
  const m = content.match(/^(active_worktrees:\s*)(\[.*?\])/m);
  let current = [];
  if (m) {
    try {
      const raw = m[2];
      if (raw !== '[]') {
        current = raw.replace(/[\[\]"]/g, '').split(',').map(s => s.trim()).filter(Boolean);
      }
    } catch (_) {}
  }

  if (action === 'add' && !current.includes(worktreeName)) current.push(worktreeName);
  if (action === 'remove') current = current.filter(w => w !== worktreeName);

  const newLine = `active_worktrees: [${current.map(w => `"${w}"`).join(', ')}]`;
  if (m) {
    fs.writeFileSync(idxPath, content.replace(/^active_worktrees:.*$/m, newLine), 'utf-8');
  } else {
    // 不存在该字段, 在 frontmatter 末尾添加
    const updated = content.replace(/^---\n([\s\S]*?)\n---/, (_, fmBody) => {
      return `---\n${fmBody}\n${newLine}\n---`;
    });
    fs.writeFileSync(idxPath, updated, 'utf-8');
  }
}

function appendToWorktreesYaml(aiState, sprintSlug, payload, ts, eventName) {
  const ytPath = path.join(aiState, 'sprints', sprintSlug, 'worktrees.yaml');
  fs.mkdirSync(path.dirname(ytPath), { recursive: true });

  const worktreeName = payload?.worktree_name || payload?.name || 'unknown';
  const worktreePath = payload?.worktree_path || payload?.path || '';
  const branch = payload?.branch || '';

  if (eventName === 'WorktreeCreate') {
    if (!fs.existsSync(ytPath)) {
      const header = `sprint_slug: ${sprintSlug}\nworktrees:\n`;
      fs.writeFileSync(ytPath, header, 'utf-8');
    }
    const entry = `  - name: "${worktreeName}"\n` +
                  `    path: "${worktreePath}"\n` +
                  `    branch: "${branch}"\n` +
                  `    created_at: "${ts}"\n` +
                  `    status: active\n`;
    fs.appendFileSync(ytPath, entry);
  } else if (eventName === 'WorktreeRemove') {
    if (!fs.existsSync(ytPath)) { return; }
    let content = fs.readFileSync(ytPath, 'utf-8');
    // 找到匹配 name 的 worktree 块, 把 status: active 改为 removed + 加 removed_at
    const re = new RegExp(`(- name: "${worktreeName}"[\\s\\S]*?status:)\\s*active`);
    if (re.test(content)) {
      content = content.replace(re, `$1 removed`);
      // 在 status: removed 后追加 removed_at (找到对应位置)
      const re2 = new RegExp(`(- name: "${worktreeName}"[\\s\\S]*?status:\\s*removed)\\n`);
      content = content.replace(re2, `$1\n    removed_at: "${ts}"\n`);
      fs.writeFileSync(ytPath, content, 'utf-8');
    }
  }
}

function main() {
  try {
    let data = '';
    try { data = fs.readFileSync(0, 'utf-8'); } catch (_) {}
    const payload = data ? JSON.parse(data) : {};

    const eventName = payload?.hook_event_name || payload?.event || '';
    // 兼容 WorktreeCreate / WorktreeRemove
    if (!['WorktreeCreate', 'WorktreeRemove'].includes(eventName)) {
      process.exit(0);
    }

    const aiState = findAiState(process.cwd());
    if (!aiState) { process.exit(0); }

    const sprintSlug = getCurrentSprintSlug(aiState);
    if (!sprintSlug) { process.exit(0); }

    const ts = new Date().toISOString();
    const worktreeName = payload?.worktree_name || payload?.name || 'unknown';

    appendToWorktreesYaml(aiState, sprintSlug, payload, ts, eventName);

    if (eventName === 'WorktreeCreate') {
      updateActiveWorktrees(aiState, worktreeName, 'add');
    } else {
      updateActiveWorktrees(aiState, worktreeName, 'remove');
    }

    process.exit(0);
  } catch (e) {
    process.stderr.write(`[worktree-tracker] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}

main();

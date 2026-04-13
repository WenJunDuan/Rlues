#!/usr/bin/env node
'use strict';

// pre-compact-save.cjs — PreCompact hook
// compaction 前保存状态快照到 .ai_state/compact-snapshot.json
// PostCompact hook 可以读这个快照恢复上下文

const fs = require('fs');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const stateDir = path.join(projectDir, '.ai_state');

if (!fs.existsSync(stateDir)) {
  process.exit(0);
}

const snapshot = {
  timestamp: new Date().toISOString(),
  project: null,
  tasksSummary: null
};

// 读 project.json
try {
  snapshot.project = JSON.parse(fs.readFileSync(path.join(stateDir, 'project.json'), 'utf8'));
} catch (e) { /* skip */ }

// 读 tasks.md 摘要
try {
  const tasks = fs.readFileSync(path.join(stateDir, 'tasks.md'), 'utf8');
  snapshot.tasksSummary = {
    pending: (tasks.match(/^- \[ \]/gm) || []).length,
    done: (tasks.match(/^- \[x\]/gm) || []).length
  };
} catch (e) { /* skip */ }

// 写快照
try {
  fs.writeFileSync(
    path.join(stateDir, 'compact-snapshot.json'),
    JSON.stringify(snapshot, null, 2)
  );
} catch (e) { /* 写失败不阻断 compaction */ }

process.exit(0);

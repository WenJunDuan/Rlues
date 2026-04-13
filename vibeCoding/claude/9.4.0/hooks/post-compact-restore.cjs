#!/usr/bin/env node
'use strict';

// post-compact-restore.cjs — PostCompact hook
// compaction 后自动注入: 铁律 + 当前状态 + 待办任务 + Gotchas
// 解决: "compaction preserved the code but lost the rules"

const fs = require('fs');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const stateDir = path.join(projectDir, '.ai_state');
const essentialsPath = path.join(projectDir, '.claude', 'skills', 'riper-pace', 'context-essentials.md');

const lines = [];

// ── 1. 注入 context-essentials (铁律 + 身份) ──
try {
  const essentials = fs.readFileSync(essentialsPath, 'utf8').trim();
  if (essentials) lines.push(essentials);
} catch (e) {
  // 无 context-essentials → 注入最小铁律
  lines.push('[VibeCoding] TDD强制 | Review强制 | Sisyphus完整性 | 设计先行');
}

// ── 2. 注入当前 PACE 状态 ──
try {
  const project = JSON.parse(fs.readFileSync(path.join(stateDir, 'project.json'), 'utf8'));
  if (project.path && project.stage) {
    lines.push(`\n[PACE 状态] Path: ${project.path} | Stage: ${project.stage} | Sprint: ${project.sprint || 0}`);
  }
  if (project.gotchas && project.gotchas.length > 0) {
    lines.push(`[Gotchas] ${project.gotchas.join(' | ')}`);
  }
  if (project.conventions && project.conventions.length > 0) {
    lines.push(`[规范] ${project.conventions.join(' | ')}`);
  }
} catch (e) { /* 无状态文件 = 新项目 */ }

// ── 3. 注入待办任务摘要 ──
try {
  const tasks = fs.readFileSync(path.join(stateDir, 'tasks.md'), 'utf8');
  const pending = (tasks.match(/^- \[ \].*/gm) || []);
  const done = (tasks.match(/^- \[x\].*/gm) || []);
  if (pending.length > 0 || done.length > 0) {
    lines.push(`\n[任务进度] ${done.length} 完成, ${pending.length} 待办`);
    if (pending.length > 0 && pending.length <= 5) {
      lines.push('[待办]');
      pending.forEach(t => lines.push(`  ${t}`));
    } else if (pending.length > 5) {
      lines.push(`[待办] ${pending.length} 个 Task (详见 .ai_state/tasks.md)`);
    }
  }
} catch (e) { /* 无 tasks.md */ }

// ── 4. 注入最近的审查结果 (如有) ──
try {
  const project = JSON.parse(fs.readFileSync(path.join(stateDir, 'project.json'), 'utf8'));
  const sprint = project.sprint || 1;
  const reviewPath = path.join(stateDir, 'reviews', `sprint-${sprint}.md`);
  const review = fs.readFileSync(reviewPath, 'utf8');
  const verdictMatch = review.match(/VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)/i);
  if (verdictMatch) {
    lines.push(`[上次审查] VERDICT: ${verdictMatch[1]}`);
  }
} catch (e) { /* 无审查报告 */ }

// ── 输出 ──
if (lines.length > 0) {
  const output = {
    hookSpecificOutput: {
      hookEventName: 'PostCompact',
      additionalContext: lines.join('\n')
    }
  };
  process.stdout.write(JSON.stringify(output));
}

process.exit(0);

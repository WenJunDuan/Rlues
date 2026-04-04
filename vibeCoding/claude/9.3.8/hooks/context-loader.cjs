#!/usr/bin/env node
// VibeCoding Kernel v9.3.8 — SessionStart: 恢复 .ai_state/ 上下文
// 输出: additionalContext 注入到 agent 提示词
'use strict';

const fs = require('fs');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const stateDir = path.join(projectDir, '.ai_state');

// 无 .ai_state/ → 全新项目, 静默退出
if (!fs.existsSync(stateDir)) {
  process.exit(0);
}

const lines = [];

// ── state.json: 会话状态 ──
try {
  const state = JSON.parse(fs.readFileSync(path.join(stateDir, 'state.json'), 'utf8'));
  if (state.path && state.stage) {
    lines.push(`[VibeCoding 状态恢复] Path: ${state.path} | Stage: ${state.stage} | Sprint: ${state.sprint || 0}`);
  }
} catch {}

// ── feature_list.json: Sprint 进度 ──
try {
  const features = JSON.parse(fs.readFileSync(path.join(stateDir, 'feature_list.json'), 'utf8'));
  if (Array.isArray(features) && features.length > 0) {
    const done = features.filter(f => f.status === 'done').length;
    const total = features.length;
    const doing = features.filter(f => f.status === 'doing');
    lines.push(`[Sprint 进度] ${done}/${total} 完成`);
    if (doing.length > 0) {
      lines.push(`[当前进行中] ${doing.map(f => f.id + ': ' + (f.description || '').slice(0, 40)).join('; ')}`);
    }
    const pending = features.filter(f => f.status === 'pending');
    if (pending.length > 0) {
      lines.push(`[待完成] ${pending.map(f => f.id).join(', ')}`);
    }
  }
} catch {}

// ── quality.json: 上次评审结果 ──
try {
  const quality = JSON.parse(fs.readFileSync(path.join(stateDir, 'quality.json'), 'utf8'));
  if (quality.verdict && quality.average > 0) {
    lines.push(`[上次评审] VERDICT: ${quality.verdict} (均分: ${quality.average})`);
    if (quality.issues && quality.issues.length > 0) {
      lines.push(`[待修复] ${quality.issues.slice(0, 3).join('; ')}`);
    }
  }
} catch {}

// ── conventions.md: Gotchas 段 ──
try {
  const conv = fs.readFileSync(path.join(stateDir, 'conventions.md'), 'utf8');
  const gotchasMatch = conv.match(/## Gotchas[\s\S]*?(?=\n## |$)/);
  if (gotchasMatch) {
    const gotchasLines = gotchasMatch[0].split('\n').filter(l => l.startsWith('- '));
    if (gotchasLines.length > 0) {
      lines.push(`[项目 Gotchas] ${gotchasLines.slice(0, 5).join(' | ')}`);
    }
  }
} catch {}

// ── lessons.md: 最近教训 ──
try {
  const lessons = fs.readFileSync(path.join(stateDir, 'lessons.md'), 'utf8');
  const lessonLines = lessons.split('\n').filter(l => l.startsWith('- ')).slice(-3);
  if (lessonLines.length > 0) {
    lines.push(`[近期教训] ${lessonLines.join(' | ')}`);
  }
} catch {}

// 有内容才输出
if (lines.length > 0) {
  process.stdout.write(JSON.stringify({
    additionalContext: lines.join('\n')
  }));
}
process.exit(0);

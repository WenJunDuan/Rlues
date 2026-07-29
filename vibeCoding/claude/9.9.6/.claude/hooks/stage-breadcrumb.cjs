#!/usr/bin/env node
/**
 * VibeCoding Athena v9.9.6 · CC UserPromptSubmit hook (stage-breadcrumb)
 *
 * 职责: 每轮注入当前 stage 义务面包屑 (≤10 行), 替代 "pace SKILL 每 sprint 必读" 固定税.
 * 设计: parser-only — 文案唯一真相在 skills/pace/references/stages.md 对应 `## {stage}` 段,
 *       本 hook 只切段, 不持有任何副本 (对齐 9.9.2 反双写纪律; 借 Trellis workflow-state).
 * Fail-open: 任何解析失败 → 零注入零报错, 不影响门禁 (delivery-gate 仍兜底).
 * 开关: _index.breadcrumb: "off" 关闭 (默认开).
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const MAX_LINES = 10;
const FRAME_LINES = 2;
const SECTION_LINES = MAX_LINES - FRAME_LINES;

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

function parseFrontmatter(filePath) {
  if (!fs.existsSync(filePath)) return {};
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.startsWith('---')) return {};
    const parts = content.split('---', 3);
    if (parts.length < 3) return {};
    const fm = {};
    for (const line of parts[1].split('\n')) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const m = t.match(/^([\w\-_.]+)\s*:\s*(.*)$/);
      if (m) {
        let v = m[2].trim();
        const q = v.match(/^"([^"]*)"|^'([^']*)'/);
        if (q) v = q[1] !== undefined ? q[1] : q[2];
        else {
          const hashIdx = v.indexOf(' #');
          if (hashIdx >= 0) v = v.slice(0, hashIdx).trim();
        }
        fm[m[1]] = v;
      }
    }
    return fm;
  } catch (e) {
    return {};
  }
}

function extractStageSection(stage) {
  const stagesPath = path.join(os.homedir(), '.claude', 'skills', 'pace', 'references', 'stages.md');
  if (!fs.existsSync(stagesPath)) return null;
  const content = fs.readFileSync(stagesPath, 'utf-8');
  const lines = content.split('\n');
  const headRe = new RegExp('^## ' + stage.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b');
  let start = -1;
  for (let i = 0; i < lines.length; i++) {
    if (headRe.test(lines[i])) { start = i; break; }
  }
  if (start < 0) return null;
  const picked = [];
  for (let i = start + 1; i < lines.length && picked.length < SECTION_LINES; i++) {
    if (/^## /.test(lines[i])) break;
    if (lines[i].trim() === '') continue;
    picked.push(lines[i]);
  }
  return picked.length ? picked.join('\n') : null;
}

function main() {
  try {
    const aiState = findAiState(process.cwd());
    if (!aiState) return process.exit(0);
    const fm = parseFrontmatter(path.join(aiState, '_index.md'));
    if ((fm.breadcrumb || 'on') === 'off') return process.exit(0);
    const stage = (fm.stage || '').trim();
    if (!stage) return process.exit(0);
    const section = extractStageSection(stage);
    if (!section) return process.exit(0);

    const head = `[PACE] stage=${stage}` +
      (fm.path ? ` · path=${fm.path}` : '') +
      (fm.current_sprint_slug ? ` · sprint=${fm.current_sprint_slug}` : '');
    // hotfix2 AC6 (2026-07-29, W37): next_action 不再注入 breadcrumb — 它挤掉 stage 义务;
    // 机器信号走 SessionStart 告警与 gate, 进度散文本就该禁。
    const tail = '(全文/前后 stage: Read ~/.claude/skills/pace/references/stages.md · 关闭: _index.breadcrumb: "off")';
    let additionalContext = `${head}\n${section}\n${tail}`;
    // hotfix2 AC6: 每轮常驻预算 <=240 B; 超出按行裁剪, 完整义务留在 stages.md
    if (Buffer.byteLength(additionalContext, 'utf8') > 240) {
      const kept = []; let used = 0;
      for (const line of additionalContext.split('\n')) {
        const n = Buffer.byteLength(line, 'utf8') + 1;
        if (used + n > 220) break;
        kept.push(line); used += n;
      }
      additionalContext = kept.join('\n') + '\n… 完整义务见 stages.md';
    }

    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext: additionalContext,
      },
    }));
    process.exit(0);
  } catch (e) {
    process.exit(0); // fail-open: 面包屑坏了不能挡路, 门禁另有兜底
  }
}

main();

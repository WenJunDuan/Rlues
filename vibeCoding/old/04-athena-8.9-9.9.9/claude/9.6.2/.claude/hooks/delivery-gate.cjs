#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.2 · CC Stop hook (delivery-gate)
 *
 * 触发: 主 agent stop 前
 * 职责:
 * 1. (v9.6.2 新) Refactor/System + stage=ship → 强制检查 cleanup-pass-{sprint}.md
 * 2. PACE 状态机基本合规检查
 *
 * Stop hook 输出协议 (v9.6.1 hotfix2 起):
 * - 用 top-level `decision: "block"`, 不是 `hookSpecificOutput.stopDecision`
 * - 源: https://docs.anthropic.com/en/docs/claude-code/hooks#stop
 */
'use strict';

const fs = require('fs');
const path = require('path');

const EXIT_SUCCESS = 0;
const EXIT_BLOCK = 2;

const REFACTOR_SYSTEM = new Set(['Refactor', 'System']);

function findAiState(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(current, '.ai_state');
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      return candidate;
    }
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;
}

function parseFrontmatter(content) {
  if (!content.startsWith('---')) return {};
  const parts = content.split('---', 3);
  if (parts.length < 3) return {};
  const fm = {};
  for (const line of parts[1].split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const m = trimmed.match(/^([\w\-_.]+)\s*:\s*(.*)$/);
    if (m) {
      let v = m[2].trim();
      if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
      fm[m[1]] = v;
    }
  }
  return fm;
}

function blockResponse(reason) {
  const output = { decision: 'block', reason };
  process.stderr.write(reason + '\n');
  console.log(JSON.stringify(output));
  return EXIT_BLOCK;
}

function main() {
  try {
    const cwd = process.cwd();
    const aiState = findAiState(cwd);
    if (!aiState) return EXIT_SUCCESS;

    const idx = path.join(aiState, '_index.md');
    if (!fs.existsSync(idx)) return EXIT_SUCCESS;

    const content = fs.readFileSync(idx, 'utf-8');
    const fm = parseFrontmatter(content);

    const pathType = fm.path || '';
    const stage = fm.stage || '';
    const sprint = fm.current_sprint || '1';

    // === v9.6.2 新增: polish 强制检查 ===
    if (REFACTOR_SYSTEM.has(pathType) && stage === 'ship') {
      const cleanupFile = path.join(aiState, 'details', `cleanup-pass-${sprint}.md`);
      if (!fs.existsSync(cleanupFile)) {
        return blockResponse(
          `[delivery-gate] Refactor/System 路径必须先完成 polish stage.\n` +
          `运行 /polish 生成 ${path.relative(cwd, cleanupFile)}\n` +
          `然后再 ship.\n`
        );
      }
    }

    // === 原有: pace 状态机基本合规 ===
    const validStages = new Set(['plan', 'design', 'impl', 'review', 'polish', 'ship']);
    if (stage && !validStages.has(stage)) {
      process.stderr.write(
        `[delivery-gate] warning: 未知 stage '${stage}', 期望 ${[...validStages].join('|')}\n`
      );
    }

    return EXIT_SUCCESS;
  } catch (e) {
    if (e.code !== 'MODULE_NOT_FOUND') {
      process.stderr.write(`[delivery-gate] warning (non-blocking): ${e.message}\n`);
    }
    return EXIT_SUCCESS;
  }
}

process.exit(main());

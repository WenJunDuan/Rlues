#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.4 · CC PostToolUse(Edit|Write|MultiEdit) hook
 *
 * 职责: 检测 design.md 在 impl/review/polish 阶段被修改 → 标记 design_changed_after_impl
 * 主 agent 下次 SessionStart 或 Stop hook 会读到该标记, 提示需重新 review.
 *
 * matcher: Edit|Write|MultiEdit (与 evidence-collector 同事件但职责不同)
 * 不冲突: 同 PostToolUse 事件可挂多个 hook (settings.json 数组)
 */
'use strict';

const fs = require('fs');
const path = require('path');
const idxio = require('./_index-io.cjs');

function findAiState(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(current, '.ai_state');
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) return candidate;
    // 2026-09-07 fix: stop at git repo boundary — do not inherit a parent project's .ai_state
    if (fs.existsSync(path.join(current, '.git'))) return null;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;
}

/**
 * athena-10-1 S0 (Q12 #30): a design that did not exist at HEAD is being written for the
 * first time (a Quick that designs and implements in one round), not changed after impl.
 * Any git failure answers "not at baseline" — this hook is a fail-open process rail.
 */
function existedAtBaseline(filePath, cwd) {
  const { execFileSync } = require('child_process');
  try {
    const abs = fs.realpathSync(path.resolve(cwd, filePath));
    const root = execFileSync('git', ['-C', path.dirname(abs), 'rev-parse', '--show-toplevel'],
      { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    const rel = path.relative(fs.realpathSync(root), abs).split(path.sep).join('/');
    execFileSync('git', ['-C', root, 'cat-file', '-e', `HEAD:${rel}`], { stdio: 'ignore' });
    return true;
  } catch (_) {
    return false;
  }
}

function readField(idxPath, field) {
  const content = fs.readFileSync(idxPath, 'utf-8');
  const re = new RegExp(`^${field}:\\s*["']?([^"\\n]*)["']?`, 'm');
  const m = content.match(re);
  return m ? m[1].trim() : '';
}

function updateField(idxPath, field, value) {
  // v9.9.6: 读-改-写全程持锁 + 原子替换, 防同事件并发 hook 丢更新
  const re = new RegExp(`^(${field}:\\s*).*$`, 'm');
  const newLine = `${field}: ${typeof value === 'boolean' ? value : `"${value}"`}`;
  idxio.update(idxPath, (content) => (re.test(content) ? content.replace(re, newLine) : null));
}

function main() {
  try {
    let data = '';
    try { data = fs.readFileSync(0, 'utf-8'); } catch (_) {}
    const payload = data ? JSON.parse(data) : {};

    const toolName = payload?.tool_name || '';
    if (!['Edit', 'Write', 'MultiEdit'].includes(toolName)) {
      process.exit(0);
    }

    const filePath = payload?.tool_input?.file_path || payload?.tool_input?.path || '';
    if (!filePath) { process.exit(0); }

    // 检查是否是 design.md 改动
    if (!filePath.includes('/sprints/') || !filePath.endsWith('/design.md')) {
      process.exit(0);
    }

    const aiState = findAiState(process.cwd());
    if (!aiState) { process.exit(0); }

    const idxPath = path.join(aiState, '_index.md');
    if (!fs.existsSync(idxPath)) { process.exit(0); }

    const stage = readField(idxPath, 'stage');

    // 仅 stage ∈ {impl, review, polish} 时标记 (plan/design 改动是正常的, 不需要 re-review)
    if (['impl', 'review', 'polish'].includes(stage) && existedAtBaseline(filePath, path.resolve(payload?.cwd || process.cwd()))) {
      updateField(idxPath, 'design_changed_after_impl', true);
      process.stderr.write(
        `[design-change-detector] 检测到 design.md 在 ${stage} stage 被修改\n` +
        `已标记 design_changed_after_impl=true, ship 前需重新 review (delivery-gate 会强制)\n`
      );
    }

    process.exit(0);
  } catch (e) {
    process.stderr.write(`[design-change-detector] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}

main();

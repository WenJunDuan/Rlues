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

function readField(idxPath, field) {
  const content = fs.readFileSync(idxPath, 'utf-8');
  const re = new RegExp(`^${field}:\\s*["']?([^"\\n]*)["']?`, 'm');
  const m = content.match(re);
  return m ? m[1].trim() : '';
}

function updateField(idxPath, field, value) {
  const content = fs.readFileSync(idxPath, 'utf-8');
  const re = new RegExp(`^(${field}:\\s*).*$`, 'm');
  const newLine = `${field}: ${typeof value === 'boolean' ? value : `"${value}"`}`;
  if (re.test(content)) {
    fs.writeFileSync(idxPath, content.replace(re, newLine), 'utf-8');
  }
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
    if (['impl', 'review', 'polish'].includes(stage)) {
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

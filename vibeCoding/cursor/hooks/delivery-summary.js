#!/usr/bin/env node
// VibeCoding v1.0-cursor — stop: 会话结束摘要
// 位置: ~/.cursor/hooks/delivery-summary.js
// 注意: stop hook 是观察型，不能阻断完成

const fs = require('fs');
const path = require('path');

try {
  const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
  const status = input?.status || 'unknown';
  const roots = input?.workspace_roots || [];
  const projectRoot = roots[0] || process.cwd();
  const stateDir = path.join(projectRoot, '.ai_state');

  // 如果有 .ai_state 目录，输出进度摘要
  if (fs.existsSync(stateDir)) {
    const parts = [];

    // 读 state.json
    const stateFile = path.join(stateDir, 'state.json');
    if (fs.existsSync(stateFile)) {
      try {
        const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
        if (state.phase) parts.push(`阶段: ${state.phase}`);
        if (state.path) parts.push(`路径: ${state.path}`);
      } catch (_) {}
    }

    // 读 progress.json
    const progressFile = path.join(stateDir, 'progress.json');
    if (fs.existsSync(progressFile)) {
      try {
        const prog = JSON.parse(fs.readFileSync(progressFile, 'utf8'));
        if (prog.percent != null) parts.push(`进度: ${prog.percent}%`);
      } catch (_) {}
    }

    // 读 quality.json
    const qualityFile = path.join(stateDir, 'quality.json');
    if (fs.existsSync(qualityFile)) {
      try {
        const q = JSON.parse(fs.readFileSync(qualityFile, 'utf8'));
        if (q.verdict) parts.push(`质量: ${q.verdict}`);
      } catch (_) {}
    }

    if (parts.length > 0) {
      process.stderr.write(`[VibeCoding] 会话结束 (${status}) — ${parts.join(' | ')}\n`);
    }
  }

  // 如果是非正常结束，提醒
  if (status === 'error' || status === 'aborted') {
    process.stderr.write(`[VibeCoding] ⚠️ 会话非正常结束: ${status}。检查 .ai_state/ 状态文件可恢复进度。\n`);
  }

  process.exit(0);
} catch (e) {
  process.exit(0);
}

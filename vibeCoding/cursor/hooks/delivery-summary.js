#!/usr/bin/env node
// VibeCoding v3.0-cursor — stop: 会话摘要 + 状态保存兜底
// 位置: ~/.cursor/hooks/delivery-summary.js
//
// Cursor stop 协议:
//   stdin:  { status, conversation_id, workspace_roots, ... }
//   此 hook 为观察型，不能阻断

const fs = require('fs');
const path = require('path');

try {
  const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
  const status = input?.status || 'unknown';
  const roots = input?.workspace_roots || [];
  const projectRoot = roots[0] || process.cwd();
  const stateDir = path.join(projectRoot, '.ai_state');

  if (!fs.existsSync(stateDir)) {
    process.exit(0);
  }

  const parts = [];

  // 读 + 更新 state.json（添加 lastSession 时间戳）
  const stateFile = path.join(stateDir, 'state.json');
  if (fs.existsSync(stateFile)) {
    try {
      const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
      if (state.phase) parts.push(`阶段: ${state.phase}`);
      if (state.path) parts.push(`路径: ${state.path}`);
      
      // 兜底写入：更新时间戳和会话状态
      state.lastSession = new Date().toISOString();
      state.sessionStatus = status;
      fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
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

  if (status === 'error' || status === 'aborted') {
    process.stderr.write(`[VibeCoding] ⚠️ 非正常结束。检查 .ai_state/ 恢复进度。\n`);
  }

  process.exit(0);
} catch (e) {
  process.exit(0);
}

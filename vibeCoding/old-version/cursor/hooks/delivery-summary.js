#!/usr/bin/env node
// VibeCoding v3.0-cursor — stop: 状态保存 + 有条件摘要
// 位置: ~/.cursor/hooks/delivery-summary.js
//
// Cursor stop 协议:
//   stdin:  { status: "completed"|"aborted"|"error", conversation_id, workspace_roots }
//   此 hook 为观察型，不能阻断
//
// 设计原则:
//   - 静默保存状态（不产生噪音）
//   - 只在有实质进度时输出摘要
//   - aborted 是正常操作（用户点停止/切话题），不是错误
//   - 只有 error 才是真异常

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

  let phase = '';
  let hasProgress = false;

  // 静默更新 state.json 时间戳（总是做，不输出）
  const stateFile = path.join(stateDir, 'state.json');
  if (fs.existsSync(stateFile)) {
    try {
      const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
      phase = state.phase || '';
      state.lastSession = new Date().toISOString();
      state.sessionStatus = status;
      fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
    } catch (_) {}
  }

  // 读进度
  let percent = 0;
  const progressFile = path.join(stateDir, 'progress.json');
  if (fs.existsSync(progressFile)) {
    try {
      const prog = JSON.parse(fs.readFileSync(progressFile, 'utf8'));
      percent = prog.percent || 0;
    } catch (_) {}
  }

  // 判断是否有实质进度值得汇报
  // phase != idle 且 phase != '' 说明有在进行的工作
  // percent > 0 说明 E 阶段已开始执行任务
  hasProgress = (phase && phase !== 'idle' && percent > 0);

  // 只在有实质进度时输出摘要
  if (hasProgress) {
    const parts = [`阶段: ${phase}`, `进度: ${percent}%`];

    // 读质量判定
    const qualityFile = path.join(stateDir, 'quality.json');
    if (fs.existsSync(qualityFile)) {
      try {
        const q = JSON.parse(fs.readFileSync(qualityFile, 'utf8'));
        if (q.verdict) parts.push(`质量: ${q.verdict}`);
      } catch (_) {}
    }

    process.stderr.write(`[VibeCoding] ${parts.join(' | ')}\n`);
  }

  // 只有 error 才警告。aborted 是用户主动停止，完全正常。
  if (status === 'error') {
    process.stderr.write(`[VibeCoding] 会话异常终止。.ai_state/ 已保存，可恢复。\n`);
  }

  process.exit(0);
} catch (e) {
  process.exit(0);
}

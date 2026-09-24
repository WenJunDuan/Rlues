// VibeCoding v9.3.1 — Codex Delivery Gate
// 注意: Codex 的 hooks 通过 plugin SDK 注册, 不是 config.toml [hooks] 段。
// 本文件供 plugin 开发时使用, 或手动执行: node .codex/hooks/delivery-gate.cjs
'use strict';
const fs = require('fs');
const path = require('path');

const STATE_DIR = path.join(process.cwd(), '.ai_state');
const severity = { fail: [], rework: [], concerns: [] };

try {
  if (!fs.existsSync(STATE_DIR)) { process.exit(0); }

  const planFile = path.join(STATE_DIR, 'plan.md');
  const qualityFile = path.join(STATE_DIR, 'quality.md');

  if (fs.existsSync(planFile)) {
    const plan = fs.readFileSync(planFile, 'utf8');
    const unchecked = (plan.match(/^- \[ \]/gm) || []).length;
    if (unchecked > 0) severity.fail.push(`plan.md 有 ${unchecked} 个未完成任务`);
  }
  if (fs.existsSync(planFile) && !fs.existsSync(qualityFile)) {
    severity.fail.push('缺少 quality.md');
  }
} catch (e) { process.exit(0); }

if (severity.fail.length > 0) {
  process.stderr.write(`[delivery-gate] FAIL:\n${severity.fail.map(i => `  ✗ ${i}`).join('\n')}\n`);
  process.exit(2);
}
process.exit(0);

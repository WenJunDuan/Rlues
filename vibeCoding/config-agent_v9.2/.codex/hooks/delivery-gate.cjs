// VibeCoding v9.1.7 — Stop: 交付质量门控 (含TDD检查)
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const STATE_DIR = path.join(process.cwd(), '.ai_state');
const issues = [];

try {
  const planFile = path.join(STATE_DIR, 'plan.md');
  if (fs.existsSync(planFile)) {
    const plan = fs.readFileSync(planFile, 'utf8');
    const unchecked = (plan.match(/- \[ \]/g) || []).length;
    if (unchecked > 0) issues.push(`plan.md 有 ${unchecked} 个未完成任务`);
  }

  try {
    const diff = execSync('git diff --cached --name-only 2>/dev/null || git diff --name-only 2>/dev/null', { encoding: 'utf8' });
    const srcFiles = diff.split('\n').filter(f => f.match(/^src\//) && !f.match(/\.test\.|\.spec\./));
    const testFiles = diff.split('\n').filter(f => f.match(/\.test\.|\.spec\./));
    if (srcFiles.length > 0 && testFiles.length === 0) {
      issues.push(`${srcFiles.length} 个源码文件修改但无测试`);
    }
  } catch (e) {}

  const qualityFile = path.join(STATE_DIR, 'quality.md');
  if (fs.existsSync(planFile) && !fs.existsSync(qualityFile)) {
    issues.push('缺少 quality.md — T 阶段验证未执行');
  }
} catch (e) {
  process.exit(0);
}

if (issues.length > 0) {
  process.stderr.write(`[delivery-gate] 交付阻断:\n${issues.map(i => `  ✗ ${i}`).join('\n')}\n`);
  process.exit(2);
}
process.exit(0);

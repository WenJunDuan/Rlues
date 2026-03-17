// VibeCoding v9.1.7 — Stop: 交付质量门控 (含TDD检查)
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const STATE_DIR = path.join(process.cwd(), '.ai_state');
const issues = [];

try {
  // 1. plan.md 未完成任务检查
  const planFile = path.join(STATE_DIR, 'plan.md');
  if (fs.existsSync(planFile)) {
    const plan = fs.readFileSync(planFile, 'utf8');
    const unchecked = (plan.match(/- \[ \]/g) || []).length;
    if (unchecked > 0) {
      issues.push(`plan.md 有 ${unchecked} 个未完成任务`);
    }
  }

  // 2. TDD检查: git diff 源码 vs 测试文件对应
  try {
    const diff = execSync('git diff --cached --name-only 2>/dev/null || git diff --name-only 2>/dev/null', { encoding: 'utf8' });
    const srcFiles = diff.split('\n').filter(f => 
      f.match(/^src\//) && !f.match(/\.test\.|\.spec\.|__test__|__spec__/)
    );
    const testFiles = diff.split('\n').filter(f => 
      f.match(/\.test\.|\.spec\.|__test__|__spec__/)
    );
    if (srcFiles.length > 0 && testFiles.length === 0) {
      issues.push(`${srcFiles.length} 个源码文件修改但无对应测试文件`);
    }
  } catch (e) { /* 非 git 仓库，跳过 */ }

  // 3. 检查 quality.md 存在 (T阶段产出)
  const qualityFile = path.join(STATE_DIR, 'quality.md');
  if (fs.existsSync(planFile) && !fs.existsSync(qualityFile)) {
    issues.push('缺少 quality.md — T 阶段验证未执行');
  }

  // 4. 硬编码密钥检查
  try {
    const secrets = execSync(
      'git diff --cached -U0 2>/dev/null | grep -iE "(password|secret|api_key|token)\\s*[:=]\\s*[\"\\x27][^\"\\x27]{8,}" || true',
      { encoding: 'utf8' }
    );
    if (secrets.trim()) {
      issues.push('疑似硬编码密钥');
    }
  } catch (e) { /* 跳过 */ }

} catch (e) {
  // .ai_state 不存在 = Path A 简单任务，允许通过
  process.exit(0);
}

if (issues.length > 0) {
  process.stderr.write(`[delivery-gate] 交付阻断:\n${issues.map(i => `  ✗ ${i}`).join('\n')}\n`);
  process.exit(2);
}
process.exit(0);

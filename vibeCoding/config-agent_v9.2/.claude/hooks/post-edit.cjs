// VibeCoding v9.1.7 — PostToolUse(Write|Edit|MultiEdit): 格式化
const { execSync } = require('child_process');
const input = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
const file = input?.tool_input?.file_path || input?.tool_input?.path || '';

try {
  if (file.match(/\.(ts|tsx|js|jsx)$/)) {
    execSync(`npx prettier --write "${file}" 2>/dev/null`, { timeout: 3000 });
  } else if (file.match(/\.(py)$/)) {
    execSync(`python3 -m black "${file}" --quiet 2>/dev/null`, { timeout: 3000 });
  }
} catch (e) { /* 格式化工具不存在时静默跳过 */ }
process.exit(0);

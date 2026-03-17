// VibeCoding v9.1.7 — PostCompact: compact后保存状态
const fs = require('fs');
const path = require('path');
const STATE_DIR = path.join(process.cwd(), '.ai_state');

try {
  if (fs.existsSync(STATE_DIR)) {
    const statusFile = path.join(STATE_DIR, 'status.md');
    if (fs.existsSync(statusFile)) {
      const content = fs.readFileSync(statusFile, 'utf8');
      // 追加 compact 时间戳
      const timestamp = new Date().toISOString();
      const updated = content.replace(
        /## 最后更新.*$/m,
        `## 最后更新\n${timestamp} (compact后自动保存)`
      );
      if (updated !== content) {
        fs.writeFileSync(statusFile, updated);
      }
    }
    console.log('[VibeCoding] compact完成, 状态已保存。读 .ai_state/status.md 恢复上下文。');
  }
} catch (e) { /* 静默 */ }

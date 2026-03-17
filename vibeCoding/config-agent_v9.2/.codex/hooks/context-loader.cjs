// VibeCoding v9.1.7 — SessionStart: 断点恢复
const fs = require('fs');
const path = require('path');
const STATE_DIR = path.join(process.cwd(), '.ai_state');

try {
  if (fs.existsSync(STATE_DIR)) {
    const status = path.join(STATE_DIR, 'status.md');
    if (fs.existsSync(status)) {
      const content = fs.readFileSync(status, 'utf8');
      if (content.includes('## 当前阶段')) {
        console.log(`[VibeCoding] 检测到未完成会话，读 .ai_state/status.md 恢复进度。`);
      }
    }
  } else {
    console.log(`[VibeCoding v9.1.7] 新项目。描述你的需求开始开发。`);
  }
} catch (e) {}

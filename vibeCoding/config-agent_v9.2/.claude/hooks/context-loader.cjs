// VibeCoding v9.1.7 — SessionStart: 断点恢复 + 上下文加载
const fs = require('fs');
const path = require('path');
const STATE_DIR = path.join(process.cwd(), '.ai_state');

try {
  if (fs.existsSync(STATE_DIR)) {
    const status = path.join(STATE_DIR, 'status.md');
    if (fs.existsSync(status)) {
      const content = fs.readFileSync(status, 'utf8');
      if (content.includes('## 当前阶段')) {
        console.log(`[VibeCoding] 检测到未完成会话，断点恢复中...`);
        console.log(`读 .ai_state/status.md 获取当前进度，然后继续执行。`);
      }
    }
  } else {
    console.log(`[VibeCoding v9.1.7] 新项目。执行 /vibe-init 初始化，或直接描述需求开始。`);
  }
} catch (e) {
  // 静默失败，不阻断会话
}

#!/usr/bin/env node
/**
 * VibeCoding Athena v9.9.2 · CC Notification hook (notification-router)
 *
 * 背景: CC 2.1.198 起后台 agent 需要输入/完成时触发 Notification hook,
 * payload 区分 agent_needs_input / agent_completed.
 * 职责: agent_completed → additionalContext 软提醒主 agent 消费 _index.next_action
 * (Loop Engineering: 事件驱动接续, 替代纯靠 Stop 轮询).
 *
 * Fail-open 设计:
 * - settings matcher 只注册 agent_needs_input|agent_completed
 * - 脚本只读取官方 notification_type/type, 不扫描任意文本
 * - agent_needs_input 不处理 (UI 已通知用户, hook 无增量价值)
 */
'use strict';
const fs = require('fs');
const path = require('path');

function findAiState(cwd) {
  for (let i = 0, c = cwd; i < 5; i++) {
    const cand = path.join(c, '.ai_state');
    if (fs.existsSync(cand) && fs.statSync(cand).isDirectory()) return cand;
    const p = path.dirname(c);
    if (p === c) return null;
    c = p;
  }
  return null;
}

function main() {
  try {
    let payload = {};
    try {
      const d = fs.readFileSync(0, 'utf-8');
      payload = d ? JSON.parse(d) : {};
    } catch (_) { process.exit(0); }

    const notificationType = payload?.notification_type || payload?.type || '';
    if (notificationType !== 'agent_completed') { process.exit(0); }

    const aiState = findAiState(payload?.cwd || process.cwd());
    if (!aiState) { process.exit(0); }
    const idx = path.join(aiState, '_index.md');
    if (!fs.existsSync(idx)) { process.exit(0); }
    const nextAction = ((fs.readFileSync(idx, 'utf-8').match(/^next_action:\s*"?([^"\n]*)"?/m) || [])[1] || '').trim();

    const hints = ['[notification-router] 后台 agent 完成 — 检查 sprints/{slug}/subagent-log.md 新条目.'];
    if (nextAction) hints.push(`next_action="${nextAction}" 待消费, 按 athena-dev 的 next_action 表处理.`);
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'Notification',
        additionalContext: hints.join('\n').slice(0, 9000),
      },
    }));
    process.exit(0);
  } catch (e) {
    process.stderr.write(`[notification-router] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}
main();

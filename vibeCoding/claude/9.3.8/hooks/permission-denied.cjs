#!/usr/bin/env node
// VibeCoding Kernel v9.3.8 — PermissionDenied: auto mode 降级策略
// 当 auto mode classifier 拒绝某操作时, 决定是否重试
'use strict';

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const tool = data.tool_name || '';
    const reason = data.denial_reason || '';

    // 安全类拒绝 (文件访问、网络) → 不重试, 换策略
    if (reason.includes('security') || reason.includes('permission')) {
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PermissionDenied',
          retry: false
        }
      }));
      process.stderr.write(`[permission-denied] ${tool} 被安全策略拒绝, 请换策略。原因: ${reason}`);
      return process.exit(0);
    }

    // 其他拒绝 → 允许重试 (可能是 classifier 误判)
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PermissionDenied',
        retry: true
      }
    }));
    process.exit(0);
  } catch {
    // 解析失败 → 不重试
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PermissionDenied',
        retry: false
      }
    }));
    process.exit(0);
  }
});

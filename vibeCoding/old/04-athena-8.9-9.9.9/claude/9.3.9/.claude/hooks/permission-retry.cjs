#!/usr/bin/env node
'use strict';

// permission-retry.cjs — PermissionDenied hook
// 安全相关的拒绝不重试; 其他可建议替代方案

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  let data = {};
  try { data = JSON.parse(input); } catch (e) { process.exit(0); return; }

  const reason = data.denial_reason || '';
  const tool = data.tool_name || '';

  // 安全拒绝: 不建议重试
  if (/security|forbidden|denied|block/i.test(reason)) {
    const output = {
      hookSpecificOutput: {
        hookEventName: 'PermissionDenied',
        retryDecision: 'no_retry',
        message: `安全策略拒绝 ${tool}: ${reason}。不要重试, 寻找替代方案。`
      }
    };
    process.stdout.write(JSON.stringify(output));
    process.exit(0);
    return;
  }

  // 其他拒绝: 可建议用户授权
  const output = {
    hookSpecificOutput: {
      hookEventName: 'PermissionDenied',
      retryDecision: 'suggest_permission',
      message: `${tool} 被拒绝: ${reason}。可以请求用户授权或使用替代工具。`
    }
  };
  process.stdout.write(JSON.stringify(output));
  process.exit(0);
});

#!/usr/bin/env node
'use strict';

// pre-bash-guard.cjs — PreToolUse hook: 危险命令拦截
// 拦截: rm -rf 危险路径, 管道执行远程脚本, 强制 push 等

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  let cmd = '';
  try {
    const data = JSON.parse(input);
    cmd = (data.tool_input && data.tool_input.command) || '';
  } catch (e) {
    process.exit(0);
    return;
  }

  if (!cmd) { process.exit(0); return; }

  const deny = (reason) => {
    const output = {
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: reason
      }
    };
    process.stdout.write(JSON.stringify(output));
    process.exit(0);
  };

  // 1. rm -rf 危险路径
  if (/rm\s+-[rR]f\s+[\/~]/.test(cmd)) {
    deny(`禁止删除系统/用户根目录: ${cmd}`);
    return;
  }

  // 2. 管道执行远程脚本
  if (/curl\s+.*\|\s*(bash|sh|zsh)/.test(cmd) || /wget\s+.*\|\s*(bash|sh|zsh)/.test(cmd)) {
    deny(`禁止管道执行远程脚本: ${cmd}。请先下载审查后再执行。`);
    return;
  }

  // 3. 强制 push
  if (/git\s+push\s+.*--force/.test(cmd)) {
    deny(`禁止强制 push: ${cmd}。如确需, 请用户手动执行。`);
    return;
  }

  // 4. push 到 main/master
  if (/git\s+push\s+origin\s+(main|master)\b/.test(cmd)) {
    deny(`禁止直接 push 到 ${cmd.includes('main') ? 'main' : 'master'}。请使用 PR。`);
    return;
  }

  // 放行
  process.exit(0);
});

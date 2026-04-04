#!/usr/bin/env node
// VibeCoding Kernel v9.3.8 — PreToolUse Bash: 危险命令拦截
// 触发条件: settings.json 中 if: "Bash(rm *)" 和 "Bash(git push *)" 已预过滤
// 本脚本做细粒度检查, 减少误拦截
'use strict';

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const cmd = (data.tool_input && data.tool_input.command) || '';

    // ── 危险 rm 模式 ──
    const dangerousRm = [
      /rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?[/~]/, // rm -rf / 或 rm -rf ~
      /rm\s+-[a-zA-Z]*r[a-zA-Z]*\s+-[a-zA-Z]*f/, // rm -r -f
      /rm\s+--no-preserve-root/,
    ];
    for (const pattern of dangerousRm) {
      if (pattern.test(cmd)) {
        process.stdout.write(JSON.stringify({
          hookSpecificOutput: {
            hookEventName: 'PreToolUse',
            permissionDecision: 'deny',
            permissionDecisionReason: `危险命令已拦截: ${cmd.slice(0, 80)}。请使用更安全的替代方案 (如 trash-cli 或指定具体路径)。`
          }
        }));
        return process.exit(0);
      }
    }

    // ── 保护分支 push ──
    const protectedPush = /git\s+push\s+(origin\s+)?(main|master)\b/;
    const forcePush = /git\s+push\s+.*--force/;
    if (protectedPush.test(cmd) || forcePush.test(cmd)) {
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: `禁止直接 push 到保护分支或 force push: ${cmd.slice(0, 80)}。请使用 feature branch + PR 流程。`
        }
      }));
      return process.exit(0);
    }

    // ── 管道注入 ──
    const pipeInjection = /curl\s+.*\|\s*(ba)?sh|wget\s+.*\|\s*(ba)?sh/;
    if (pipeInjection.test(cmd)) {
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason: `禁止管道执行远程脚本: ${cmd.slice(0, 80)}。请先下载审查后再执行。`
        }
      }));
      return process.exit(0);
    }

    // 安全 → 放行
    process.exit(0);

  } catch (e) {
    // 解析失败 → 放行 (不阻断正常工作)
    process.exit(0);
  }
});

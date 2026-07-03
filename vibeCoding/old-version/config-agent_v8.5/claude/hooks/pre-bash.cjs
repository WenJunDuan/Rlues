#!/usr/bin/env node
// VibeCoding v8.5 — PreToolUse Hook (Bash)
// 安全守卫: 阻断危险命令, 保护敏感文件
// 扩展名 .cjs 强制 CommonJS

"use strict";

process.on("uncaughtException", function () { process.exit(0); });
if (process.env.VIBECODING_HOOKS_DISABLED === "1") { process.exit(0); }

var inputData = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", function (chunk) { inputData += chunk; });
process.stdin.on("end", function () {
  try {
    var input = JSON.parse(inputData);
    var cmd = (input.tool_input && input.tool_input.command) || "";
    if (!cmd) { process.exit(0); }

    // === 危险命令黑名单 ===
    var dangerous = [
      { pattern: /rm\s+(-rf?|--recursive)\s+\/($|\s)/, reason: "rm -rf / 会删除整个文件系统" },
      { pattern: /sudo\s/, reason: "禁止 sudo 提权" },
      { pattern: /chmod\s+777/, reason: "chmod 777 安全风险" },
      { pattern: /curl\s.*\|\s*(bash|sh|zsh)/, reason: "禁止 pipe to shell (远程代码执行)" },
      { pattern: /(^|[;&|]\s*)\beval\s/, reason: "禁止 eval (代码注入)" },
      { pattern: />\s*\/etc\//, reason: "禁止写入系统配置" },
      { pattern: /mkfs/, reason: "禁止格式化磁盘" },
      { pattern: /dd\s+if=/, reason: "禁止 dd 磁盘操作" },
    ];

    for (var i = 0; i < dangerous.length; i++) {
      if (dangerous[i].pattern.test(cmd)) {
        var output = JSON.stringify({
          hookSpecificOutput: {
            hookEventName: "PreToolUse",
            permissionDecision: "deny",
            permissionDecisionReason: "[VibeCoding Security] " + dangerous[i].reason + ": " + cmd
          }
        });
        process.stdout.write(output);
        process.exit(2);
      }
    }

    // === 敏感文件保护 ===
    var sensitivePatterns = [
      /cat\s+.*\.env/, /cat\s+.*\.pem($|\s)/, /cat\s+.*private.*key/i,
      /cat\s+.*id_rsa/, /cat\s+.*\.secret/
    ];
    for (var j = 0; j < sensitivePatterns.length; j++) {
      if (sensitivePatterns[j].test(cmd)) {
        var warn = JSON.stringify({
          hookSpecificOutput: {
            hookEventName: "PreToolUse",
            additionalContext: "[VibeCoding] ⚠ 访问敏感文件, 确保不要在输出中泄露 secrets"
          }
        });
        process.stdout.write(warn);
        process.exit(0); // 警告但不阻断
      }
    }

  } catch (e) { /* JSON 解析失败, 放行 */ }
  process.exit(0);
});

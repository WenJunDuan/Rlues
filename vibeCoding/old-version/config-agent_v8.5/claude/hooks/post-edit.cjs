#!/usr/bin/env node
// VibeCoding v8.5 — PostToolUse Hook (Write|Edit)
// 非阻塞: 自动格式化 + 增量类型检查
// Block-at-Write 会干扰 agent 计划, 所以这里只做 cleanup, 不阻断
// 扩展名 .cjs 强制 CommonJS

"use strict";
var fs = require("fs");
var child_process = require("child_process");

process.on("uncaughtException", function () { process.exit(0); });
if (process.env.VIBECODING_HOOKS_DISABLED === "1") { process.exit(0); }

// === 从 stdin 读取 hook input JSON ===
var inputData = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", function (chunk) { inputData += chunk; });
process.stdin.on("end", function () {
  try {
    var input = JSON.parse(inputData);
    var filePath = (input.tool_input && input.tool_input.file_path) || "";
    if (!filePath || !fs.existsSync(filePath)) { process.exit(0); }

    // === Auto-format: Prettier ===
    var hasPrettier = fs.existsSync("node_modules/.bin/prettier");
    if (hasPrettier) {
      try {
        child_process.execSync(
          "npx prettier --write " + JSON.stringify(filePath),
          { timeout: 15000, stdio: "pipe" }
        );
      } catch (e) { /* 格式化失败不阻断 */ }
    }

    // === 增量类型检查: 只检查 TS/TSX 文件 ===
    var isTs = /\.(ts|tsx)$/.test(filePath);
    var hasTsConfig = fs.existsSync("tsconfig.json");
    if (isTs && hasTsConfig) {
      try {
        child_process.execSync(
          "npx tsc --noEmit --pretty false 2>&1 | head -20",
          { timeout: 30000, stdio: "pipe" }
        );
      } catch (e) {
        // 输出类型错误摘要供 agent 参考, 但不阻断
        var stderr = (e.stderr || "").toString().trim();
        if (stderr) {
          process.stderr.write("[VibeCoding] tsc warnings on " + filePath + ":\n");
          process.stderr.write(stderr.split("\n").slice(0, 5).join("\n") + "\n");
        }
      }
    }
  } catch (e) { /* JSON 解析失败, 静默退出 */ }
  process.exit(0);
});

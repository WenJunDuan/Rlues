#!/usr/bin/env node
// VibeCoding v8.3.5 — Stop Hook (delivery gate, cross-platform)
// 作用: AI 尝试停止前检查测试和类型, 失败则阻止 (exit 2)
// 关闭: VIBECODING_HOOKS_DISABLED=1
// 注意: exit 2 = 阻止 Stop + 发送 followup message (Claude Code)

"use strict";

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// 开关检查
if (process.env.VIBECODING_HOOKS_DISABLED === "1") {
  process.exit(0);
}

// 只在有 package.json 的项目中运行
if (!fs.existsSync("package.json")) {
  process.exit(0);
}

const failures = [];

/**
 * 静默执行命令, 返回是否成功
 * @param {string} cmd
 * @returns {boolean}
 */
function runQuiet(cmd) {
  try {
    execSync(cmd, { stdio: "pipe", timeout: 120_000 });
    return true;
  } catch {
    return false;
  }
}

/**
 * 检查 package.json 是否有指定 script
 * @param {string} scriptName
 * @returns {boolean}
 */
function hasScript(scriptName) {
  try {
    const pkg = JSON.parse(fs.readFileSync("package.json", "utf-8"));
    return !!(pkg.scripts && pkg.scripts[scriptName]);
  } catch {
    return false;
  }
}

// === 检查 1: npm test ===
if (hasScript("test")) {
  if (!runQuiet("npm test --silent")) {
    failures.push("npm test 失败");
  }
}

// === 检查 2: TypeScript 类型检查 ===
if (fs.existsSync("tsconfig.json")) {
  if (!runQuiet("npx tsc --noEmit")) {
    failures.push("tsc --noEmit 类型检查失败");
  }
}

// === 检查 3: doing.md 有未完成任务 ===
const doingPath = path.resolve(".ai_state", "doing.md");
if (fs.existsSync(doingPath)) {
  try {
    const content = fs.readFileSync(doingPath, "utf-8");
    // 匹配 ☐ 或 - [ ] (未勾选)
    const unchecked = (content.match(/☐|^- \[ \]/gm) || []).length;
    if (unchecked > 0) {
      failures.push(`doing.md 有 ${unchecked} 个未完成任务`);
    }
  } catch {
    // 读取失败不阻止
  }
}

// === 结果 ===
if (failures.length > 0) {
  console.log("=== VibeCoding Delivery Gate: BLOCKED ===");
  console.log("原因:");
  failures.forEach((f) => console.log(`  - ${f}`));
  console.log();
  console.log("请修复以上问题后再完成。");
  console.log("强制跳过: VIBECODING_HOOKS_DISABLED=1");
  process.exit(2); // exit 2 = 阻止 Stop
}

console.log("[VibeCoding] Delivery gate: PASSED ✓");
process.exit(0);

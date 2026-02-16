#!/usr/bin/env node
// VibeCoding v8.5 — Stop Hook (Delivery Gate)
// Block-at-Commit 策略: 不中断写入, 在交付时统一验证
// 扩展名 .cjs 强制 CommonJS, 不受项目 "type":"module" 影响

"use strict";
var fs = require("fs");
var path = require("path");
var child_process = require("child_process");

process.on("uncaughtException", function (err) {
  process.stderr.write("[VibeCoding] delivery-gate error: " + err.message + "\n");
  process.exit(0);
});

if (process.env.VIBECODING_HOOKS_DISABLED === "1") { process.exit(0); }
if (!fs.existsSync("package.json")) { process.exit(0); }

// === 工具 ===
function runQuiet(cmd, timeoutMs) {
  try {
    child_process.execSync(cmd, {
      timeout: timeoutMs || 120000,
      stdio: "pipe",
      env: Object.assign({}, process.env, { FORCE_COLOR: "0", NO_COLOR: "1" })
    });
    return true;
  } catch (e) { return false; }
}

// === 获取 Path ===
var currentPath = "B"; // 默认 Path B
try {
  var sessionPath = path.join(".ai_state", "session.md");
  if (fs.existsSync(sessionPath)) {
    var content = fs.readFileSync(sessionPath, "utf8");
    var match = content.match(/Path[:\s]+([ABCD])/i);
    if (match) { currentPath = match[1].toUpperCase(); }
  }
} catch (e) { /* 用默认 B */ }

var failures = [];

// === 检查 1: npm test (所有 Path) ===
try {
  var pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
  var testScript = (pkg.scripts && pkg.scripts.test) || "";
  // 跳过默认 "no test specified" 占位
  var isDefaultTest = testScript.indexOf("no test specified") !== -1;
  if (testScript && !isDefaultTest) {
    if (!runQuiet("npm test", 180000)) {
      failures.push("npm test 失败");
    }
  }
} catch (e) { /* 无 package.json 或解析失败, 跳过 */ }

// === 检查 2: TypeScript (Path B+) ===
if (currentPath !== "A") {
  var hasTsConfig = fs.existsSync("tsconfig.json");
  if (hasTsConfig) {
    if (!runQuiet("npx tsc --noEmit", 120000)) {
      failures.push("tsc --noEmit 类型检查失败 (Path " + currentPath + "+)");
    }
  }
}

// === 检查 3: ESLint (Path C+) ===
var isStrictPath = currentPath === "C" || currentPath === "D";
var hasEslintConfig = (
  fs.existsSync(".eslintrc") ||
  fs.existsSync(".eslintrc.js") ||
  fs.existsSync(".eslintrc.json") ||
  fs.existsSync(".eslintrc.cjs") ||
  fs.existsSync("eslint.config.js") ||
  fs.existsSync("eslint.config.mjs") ||
  fs.existsSync("eslint.config.cjs")
);
if (isStrictPath && hasEslintConfig) {
  if (!runQuiet("npx eslint . --max-warnings=0", 120000)) {
    failures.push("eslint 检查有 warning 或 error (Path " + currentPath + " 要求 clean)");
  }
}

// === 检查 4: doing.md 未完成任务 (所有 Path) ===
try {
  var doingPath = path.join(".ai_state", "doing.md");
  if (fs.existsSync(doingPath)) {
    var doingContent = fs.readFileSync(doingPath, "utf8");
    var unchecked = (doingContent.match(/- \[ \]/g) || []).length;
    if (unchecked > 0) {
      failures.push("doing.md 有 " + unchecked + " 个未完成任务");
    }
  }
} catch (e) { /* 继续 */ }

// === 结果 ===
if (failures.length > 0) {
  console.log("=== VibeCoding Delivery Gate: BLOCKED (Path " + currentPath + ") ===");
  console.log("原因:");
  failures.forEach(function (f) { console.log("  - " + f); });
  console.log("");
  console.log("修复后重试。强制跳过: VIBECODING_HOOKS_DISABLED=1");
  process.exit(2);
} else {
  console.log("[VibeCoding] Delivery gate PASSED (Path " + currentPath + ") ✓");
  process.exit(0);
}

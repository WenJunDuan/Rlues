#!/usr/bin/env node
// VibeCoding v8.3.5 — Stop Hook (delivery gate, cross-platform)
// 扩展名 .cjs 强制 CommonJS, 不受项目 package.json "type":"module" 影响
// exit 2 = 阻止 Claude Code Stop + 发送 followup message
// 关闭: VIBECODING_HOOKS_DISABLED=1

"use strict";

var fs = require("fs");
var path = require("path");
var childProcess = require("child_process");

// === 全局异常兜底 ===
process.on("uncaughtException", function (err) {
  console.error("[VibeCoding] delivery-gate 异常:", err.message);
  process.exit(0); // hook 自身出错不阻塞交付
});

// === 开关 ===
if (process.env.VIBECODING_HOOKS_DISABLED === "1") {
  process.exit(0);
}

// === 只在有 package.json 的项目中运行 ===
if (!fs.existsSync("package.json")) {
  process.exit(0);
}

var failures = [];

// === 工具函数 ===
function runQuiet(cmd, timeoutMs) {
  try {
    childProcess.execSync(cmd, {
      stdio: "pipe",
      timeout: timeoutMs || 120000,
      env: Object.assign({}, process.env, {
        // 保证 npm 子进程颜色不干扰解析
        FORCE_COLOR: "0",
        NO_COLOR: "1"
      })
    });
    return true;
  } catch (e) {
    return false;
  }
}

function readPkg() {
  try {
    return JSON.parse(fs.readFileSync("package.json", "utf-8"));
  } catch (e) {
    return {};
  }
}

function hasScript(pkg, name) {
  return !!(pkg.scripts && pkg.scripts[name]);
}

function readFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) return null;
    return fs.readFileSync(filePath, "utf-8");
  } catch (e) {
    return null;
  }
}

// === 读取 Path 级别 (决定检查严格度) ===
function detectPath() {
  var session = readFile(path.resolve(".ai_state", "session.md"));
  if (!session) return "B"; // 默认 B
  var match = session.match(/Path:\s*([ABCD])/i);
  return match ? match[1].toUpperCase() : "B";
}

var pkg = readPkg();
var currentPath = detectPath();

// === 检查 1: npm test (所有 Path) ===
if (hasScript(pkg, "test")) {
  // 跳过 test script 是 "echo \"Error: no test specified\" && exit 1" 这种默认值
  var testScript = pkg.scripts.test;
  var isDefault = testScript.indexOf("no test specified") !== -1;
  if (!isDefault && !runQuiet("npm test", 180000)) {
    failures.push("npm test 失败");
  }
}

// === 检查 2: TypeScript 类型检查 (Path B+) ===
if (currentPath !== "A" && fs.existsSync("tsconfig.json")) {
  if (!runQuiet("npx tsc --noEmit", 120000)) {
    failures.push("tsc --noEmit 类型检查失败");
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
var doingContent = readFile(path.resolve(".ai_state", "doing.md"));
if (doingContent) {
  // 匹配: ☐, - [ ], * [ ] (未勾选 checkbox)
  var uncheckedRe = /☐|- \[ \]|\* \[ \]/g;
  var matches = doingContent.match(uncheckedRe);
  if (matches && matches.length > 0) {
    failures.push("doing.md 有 " + matches.length + " 个未完成任务");
  }
}

// === 结果 ===
if (failures.length > 0) {
  console.log("=== VibeCoding Delivery Gate: BLOCKED (Path " + currentPath + ") ===");
  console.log("原因:");
  for (var i = 0; i < failures.length; i++) {
    console.log("  - " + failures[i]);
  }
  console.log("");
  console.log("修复后重试。强制跳过: VIBECODING_HOOKS_DISABLED=1");
  process.exit(2); // 阻止 Stop
}

console.log("[VibeCoding] Delivery gate PASSED (Path " + currentPath + ") \u2713");
process.exit(0);

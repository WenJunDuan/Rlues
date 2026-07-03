#!/usr/bin/env node
// VibeCoding v8.5 — SessionStart Hook
// .cjs 强制 CommonJS, 兼容 ESM 项目

"use strict";
var fs = require("fs");
var path = require("path");

process.on("uncaughtException", function (err) {
  process.stderr.write("[VibeCoding] session-start error: " + err.message + "\n");
  process.exit(0);
});
if (process.env.VIBECODING_HOOKS_DISABLED === "1") { process.exit(0); }

function readHead(fp, n) {
  try {
    if (!fs.existsSync(fp)) { return null; }
    var c = fs.readFileSync(fp, "utf8").trim();
    return c ? c.split("\n").slice(0, n).join("\n") : null;
  } catch (e) { return null; }
}

function countDir(dp) {
  try {
    if (!fs.existsSync(dp)) { return 0; }
    return fs.readdirSync(dp).filter(function (f) { return !f.startsWith("."); }).length;
  } catch (e) { return 0; }
}

// 向上搜索 .ai_state
var aiState = null;
var dir = process.cwd();
for (var i = 0; i < 5; i++) {
  var c = path.join(dir, ".ai_state");
  if (fs.existsSync(c)) { aiState = c; break; }
  var p = path.dirname(dir);
  if (p === dir) { break; }
  dir = p;
}

if (!aiState) {
  console.log("[VibeCoding] .ai_state 未找到 — /vibe-init 初始化");
  process.exit(0);
}

// 只加载必要内容, 不浪费 context window
var out = ["=== VibeCoding v8.5 ==="];

// 1. doing.md (核心: 知道干到哪了)
var doing = readHead(path.join(aiState, "doing.md"), 30);
if (doing) { out.push("", "--- doing.md ---", doing); }

// 2. session.md (核心: 知道需求和 Path)
var session = readHead(path.join(aiState, "session.md"), 15);
if (session) { out.push("", "--- session.md ---", session); }

// 3. pitfalls.md (核心: 避免重蹈覆辙)
var pitfalls = readHead(path.join(aiState, "pitfalls.md"), 15);
if (pitfalls) { out.push("", "--- ⚠ pitfalls.md ---", pitfalls); }

// 4. 资源感知 (只报数量, 不注入内容)
var reqN = countDir(path.join(aiState, "requirements"));
var assetN = countDir(path.join(aiState, "assets"));
if (reqN > 0) { out.push("📋 requirements/: " + reqN + " 文件"); }
if (assetN > 0) { out.push("🎨 assets/: " + assetN + " 文件"); }

// 5. 阶段推断
var phase = "未知";
if (fs.existsSync(path.join(aiState, "review.md"))) { phase = "Rev"; }
else if (fs.existsSync(path.join(aiState, "verified.md"))) { phase = "V→Rev"; }
else if (doing && /- \[ \]|\* \[ \]/.test(doing)) { phase = "E (有未完成任务)"; }
else if (doing) { phase = "V (待验证)"; }
else if (fs.existsSync(path.join(aiState, "plan.md"))) { phase = "P→E"; }
else if (fs.existsSync(path.join(aiState, "design.md"))) { phase = "D→P"; }
else if (fs.existsSync(path.join(aiState, "session.md"))) { phase = "R→D"; }
out.push("", "阶段: " + phase);
out.push("=== /vibe-resume 继续 · /vibe-status 查看 ===");

console.log(out.join("\n"));

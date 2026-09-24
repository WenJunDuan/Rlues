#!/usr/bin/env node
// VibeCoding v8.3.5 — SessionStart Hook (cross-platform)
// 作用: 启动时自动注入 .ai_state 上下文到 AI context
// 关闭: VIBECODING_HOOKS_DISABLED=1

"use strict";

const fs = require("fs");
const path = require("path");

// 开关检查
if (process.env.VIBECODING_HOOKS_DISABLED === "1") {
  process.exit(0);
}

const AI_STATE = path.resolve(".ai_state");

if (!fs.existsSync(AI_STATE)) {
  console.log("[VibeCoding] 未初始化 — 使用 /vibe-init 或 /vibe-dev 开始");
  process.exit(0);
}

/**
 * 安全读取文件前 N 行
 * @param {string} filePath
 * @param {number} maxLines
 * @returns {string|null}
 */
function readHead(filePath, maxLines) {
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    const lines = content.split("\n").slice(0, maxLines);
    return lines.join("\n").trim();
  } catch {
    return null;
  }
}

// === 输出注入 ===

console.log("=== VibeCoding v8.3.5 Context Restore ===\n");

// 优先级 1: doing.md — 当前正在做什么
const doing = readHead(path.join(AI_STATE, "doing.md"), 30);
if (doing) {
  console.log("--- 当前任务 (doing.md) ---");
  console.log(doing);
  console.log();
}

// 优先级 2: session.md — 需求和 Path
const session = readHead(path.join(AI_STATE, "session.md"), 20);
if (session) {
  console.log("--- 会话上下文 (session.md) ---");
  console.log(session);
  console.log();
}

// 优先级 3: conventions.md — 项目规范
const conventions = readHead(path.join(AI_STATE, "conventions.md"), 15);
if (conventions) {
  console.log("--- 项目规范 (conventions.md) ---");
  console.log(conventions);
  console.log();
}

console.log("=== /vibe-resume 从断点继续 · /vibe-status 查看状态 ===");

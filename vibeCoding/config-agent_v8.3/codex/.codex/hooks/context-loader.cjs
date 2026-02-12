#!/usr/bin/env node
// VibeCoding v8.3.5 — SessionStart Hook (cross-platform)
// 扩展名 .cjs 强制 CommonJS, 不受项目 package.json "type":"module" 影响
// 关闭: VIBECODING_HOOKS_DISABLED=1

"use strict";

const fs = require("fs");
const path = require("path");

// === 全局异常兜底 ===
process.on("uncaughtException", function (err) {
  console.error("[VibeCoding] context-loader 异常:", err.message);
  process.exit(0); // hook 出错不阻塞启动
});

// === 开关 ===
if (process.env.VIBECODING_HOOKS_DISABLED === "1") {
  process.exit(0);
}

// === 查找 .ai_state 目录 (向上查找, 兼容 monorepo) ===
function findAiState(startDir) {
  var dir = startDir;
  for (var i = 0; i < 5; i++) {
    var candidate = path.join(dir, ".ai_state");
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      return candidate;
    }
    var parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

var aiState = findAiState(process.cwd());

if (!aiState) {
  console.log("[VibeCoding] .ai_state 未找到 — /vibe-init 初始化");
  process.exit(0);
}

// === 安全读文件前 N 行 ===
function readHead(filePath, maxLines) {
  try {
    if (!fs.existsSync(filePath)) return null;
    var content = fs.readFileSync(filePath, "utf-8");
    if (!content.trim()) return null;
    return content.split("\n").slice(0, maxLines).join("\n").trim();
  } catch (e) {
    return null;
  }
}

// === 输出注入 (优先级排序: 紧急 → 背景) ===
var output = [];
output.push("=== VibeCoding v8.3.5 Context Restore ===");

// 1. doing.md — 当前正在做什么 (最关键)
var doing = readHead(path.join(aiState, "doing.md"), 40);
if (doing) {
  output.push("");
  output.push("--- 当前任务 (doing.md) ---");
  output.push(doing);
}

// 2. session.md — 需求 + Path
var session = readHead(path.join(aiState, "session.md"), 25);
if (session) {
  output.push("");
  output.push("--- 会话上下文 (session.md) ---");
  output.push(session);
}

// 3. design.md — 设计决策 (中断恢复时很关键)
var design = readHead(path.join(aiState, "design.md"), 20);
if (design) {
  output.push("");
  output.push("--- 设计决策 (design.md) ---");
  output.push(design);
}

// 4. plan.md — 任务全景 (知道做到哪了)
var plan = readHead(path.join(aiState, "plan.md"), 20);
if (plan) {
  output.push("");
  output.push("--- 实施计划 (plan.md) ---");
  output.push(plan);
}

// 5. conventions.md — 项目规范
var conventions = readHead(path.join(aiState, "conventions.md"), 15);
if (conventions) {
  output.push("");
  output.push("--- 项目规范 (conventions.md) ---");
  output.push(conventions);
}

// 6. .knowledge/pitfalls.md — 踩坑记录 (跨会话核心价值)
var knowledgeDir = path.resolve(path.dirname(aiState), ".knowledge");
var pitfalls = readHead(path.join(knowledgeDir, "pitfalls.md"), 20);
if (pitfalls) {
  output.push("");
  output.push("--- 历史踩坑 (.knowledge/pitfalls.md) ---");
  output.push(pitfalls);
}

// 7. 阶段推断 — 帮 AI 快速定位中断点
var phase = "未知";
if (fs.existsSync(path.join(aiState, "review.md"))) {
  phase = "Rev (Review) 或已完成";
} else if (fs.existsSync(path.join(aiState, "verified.md"))) {
  phase = "V→Rev (验证已完成, 待审查)";
} else if (doing) {
  // 检查 doing.md 里有没有未完成任务
  var hasUnchecked = /☐|- \[ \]|\* \[ \]/.test(doing);
  phase = hasUnchecked ? "E (Execute, 有未完成任务)" : "V (待验证)";
} else if (fs.existsSync(path.join(aiState, "plan.md"))) {
  phase = "P→E (计划已就绪)";
} else if (fs.existsSync(path.join(aiState, "design.md"))) {
  phase = "D→P (设计已就绪)";
} else if (fs.existsSync(path.join(aiState, "session.md"))) {
  phase = "R→D (研究中)";
}
output.push("");
output.push("--- 推断阶段: " + phase + " ---");

output.push("");
output.push("=== /vibe-resume 继续 · /vibe-status 查看 ===");

console.log(output.join("\n"));

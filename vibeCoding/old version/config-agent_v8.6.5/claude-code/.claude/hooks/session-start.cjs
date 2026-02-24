#!/usr/bin/env node
"use strict";
var fs = require("fs");
// Non-critical hook: log errors but don't block session start
process.on("uncaughtException", function(e) {
  process.stderr.write("[session-start] Warning: " + e.message + "\n");
  process.exit(0);
});
if (process.env.VIBECODING_HOOKS_DISABLED === "1") { process.exit(0); }

var ver = process.env.VIBECODING_VERSION || "8.6.5";

function readHead(p, n) {
  try { if (!fs.existsSync(p)) return null;
    var c = fs.readFileSync(p, "utf8").trim();
    return c ? c.split("\n").slice(0, n).join("\n") : null;
  } catch(e) { return null; }
}

var state = ".ai_state";
var parts = [];

// What am I doing?
var doing = readHead(state + "/doing.md", 30);
if (doing) parts.push("## 当前任务\n" + doing);

// Session context
var session = readHead(state + "/session.md", 20);
if (session) parts.push("## 需求上下文\n" + session);

// Knowledge: pitfalls + lessons (from unified knowledge.md)
var knowledge = readHead(state + "/knowledge.md", 25);
if (knowledge) parts.push("## 项目知识 (陷阱+教训)\n" + knowledge);

// Conventions
var conv = readHead(state + "/conventions.md", 10);
if (conv) parts.push("## 项目规范\n" + conv);

if (parts.length > 0) {
  var msg = "# VibeCoding v" + ver + " — 项目状态\n\n" + parts.join("\n\n");
  process.stdout.write(JSON.stringify({ additionalContext: msg }));
}

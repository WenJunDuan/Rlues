#!/usr/bin/env node
"use strict";
var fs = require("fs");
process.on("uncaughtException", function(e) { process.exit(0); });
if (process.env.VIBECODING_HOOKS_DISABLED === "1") { process.exit(0); }

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

// Pitfalls (avoid repeating mistakes)
var pitfalls = readHead(state + "/pitfalls.md", 15);
if (pitfalls) parts.push("## 已知坑 (避免重蹈覆辙)\n" + pitfalls);

// Conventions
var conv = readHead(state + "/conventions.md", 10);
if (conv) parts.push("## 项目规范\n" + conv);

if (parts.length > 0) {
  var msg = "# VibeCoding v8.6 — 项目状态\n\n" + parts.join("\n\n");
  process.stdout.write(JSON.stringify({ additionalContext: msg }));
}

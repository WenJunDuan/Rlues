#!/usr/bin/env node
"use strict";
// VibeCoding 9.1.5 — PostToolUse Hook (Post-Edit)
var d = "";
process.on("uncaughtException", function() { process.exit(0); });
process.stdin.on("data", function(c) { d += c; });
process.stdin.on("end", function() {
  try {
    var input = JSON.parse(d);
    var p = input.tool_input && input.tool_input.file_path || "";
    if (/\.(md|txt)$/.test(p)
      && !/(README|CLAUDE|AGENTS|CONTRIBUTING|CHANGELOG|LICENSE|API|ARCHITECTURE|SECURITY|MIGRATION)\.md$/.test(p)
      && !/\.claude\//.test(p)
      && !/\.ai_state\//.test(p)
      && !/docs?\//.test(p)
      && !/src\//.test(p)
      && !/plans?\//.test(p)) {
      console.error("[Hook] BLOCKED: 不必要的文档文件: " + p);
      process.exit(2);
    }
  } catch {}
  console.log(d);
});

#!/usr/bin/env node
"use strict";
// VibeCoding 9.1.5 — PreToolUse Hook (Bash Safety Guard)
var d = "";
process.on("uncaughtException", function() { process.exit(0); });
process.stdin.on("data", function(c) { d += c; });
process.stdin.on("end", function() {
  try {
    var input = JSON.parse(d);
    var cmd = (input.tool_input && input.tool_input.command) || "";
    if (/\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive)/.test(cmd) && /\s\/(\s|$)/.test(cmd)) {
      process.stderr.write("[SECURITY] Blocked: rm -rf /\n");
      process.exit(2);
    }
    if (/\bsudo\b/.test(cmd)) {
      process.stderr.write("[SECURITY] Blocked: sudo\n");
      process.exit(2);
    }
    if (/(^|[;&|])\s*eval\b/.test(cmd)) {
      process.stderr.write("[SECURITY] Blocked: eval\n");
      process.exit(2);
    }
    if (/\bcurl\b.*\|\s*(ba)?sh/.test(cmd) || /\bwget\b.*\|\s*(ba)?sh/.test(cmd)) {
      process.stderr.write("[SECURITY] Blocked: curl|bash\n");
      process.exit(2);
    }
    if (/\.(env|pem|key|cert|p12|pfx|jks)\b/.test(cmd)
      && !/\.gitignore/.test(cmd) && !/grep/.test(cmd)) {
      process.stderr.write("[SECURITY] WARNING: sensitive file access\n");
    }
  } catch {}
  console.log(d);
});

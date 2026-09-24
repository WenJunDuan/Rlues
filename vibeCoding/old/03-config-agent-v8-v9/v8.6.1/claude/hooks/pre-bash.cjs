#!/usr/bin/env node
"use strict";
var d = "";
process.stdin.on("data", function(c) { d += c; });
process.stdin.on("end", function() {
  try {
    var input = JSON.parse(d);
    var cmd = input.tool_input && input.tool_input.command || "";

    // Block dangerous commands
    if (/(^|[;&|]\s*)\beval\s/.test(cmd)) {
      process.stderr.write("[SECURITY] Blocked: eval command\n");
      process.exit(2);
    }
    if (/\brm\s+(-rf?|--recursive)\s+\/(?!\w)/.test(cmd)) {
      process.stderr.write("[SECURITY] Blocked: rm -rf /\n");
      process.exit(2);
    }
    if (/\bsudo\b/.test(cmd)) {
      process.stderr.write("[SECURITY] Blocked: sudo\n");
      process.exit(2);
    }

    // Block sensitive file access
    if (/\.(env|pem|key|cert|p12|pfx|jks)(\b|$)/.test(cmd) &&
        !/\.gitignore/.test(cmd) && !/grep/.test(cmd)) {
      process.stderr.write("[SECURITY] Blocked: sensitive file access — " + cmd.slice(0, 80) + "\n");
      process.exit(2);
    }
  } catch(e) {}
  console.log(d);
});

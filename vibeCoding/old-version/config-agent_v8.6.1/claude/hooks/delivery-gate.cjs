#!/usr/bin/env node
"use strict";
var fs = require("fs");
process.on("uncaughtException", function(e) { process.exit(0); });
if (process.env.VIBECODING_HOOKS_DISABLED === "1") { process.exit(0); }

var state = ".ai_state";
var errors = [];

// Check doing.md has no uncompleted items
try {
  if (fs.existsSync(state + "/doing.md")) {
    var doing = fs.readFileSync(state + "/doing.md", "utf8");
    var unchecked = (doing.match(/^- \[ \]/gm) || []).length;
    if (unchecked > 0) errors.push("[GATE] " + unchecked + " uncompleted items in doing.md");
  }
} catch(e) {}

// Check session.md exists (context not lost)
if (!fs.existsSync(state + "/session.md")) {
  errors.push("[GATE] session.md missing — context may be lost");
}

if (errors.length > 0) {
  process.stderr.write(errors.join("\n") + "\n");
  process.stderr.write("[GATE] Complete all items before delivery.\n");
  process.exit(2);
}

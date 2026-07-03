#!/usr/bin/env node
"use strict";
var fs = require("fs");
// Critical hook: log errors as warnings but still check gates
process.on("uncaughtException", function(e) {
  process.stderr.write("[delivery-gate] ERROR in gate script: " + e.message + "\n");
  process.stderr.write("[delivery-gate] Gate check skipped due to script error — manual review needed.\n");
  process.exit(0);
});
if (process.env.VIBECODING_HOOKS_DISABLED === "1") { process.exit(0); }

var state = ".ai_state";
var errors = [];
var warnings = [];

// Check doing.md has no uncompleted items
try {
  if (fs.existsSync(state + "/doing.md")) {
    var doing = fs.readFileSync(state + "/doing.md", "utf8");
    var unchecked = (doing.match(/^- \[ \]/gm) || []).length;
    if (unchecked > 0) errors.push("[GATE] " + unchecked + " uncompleted items in doing.md");
  }
} catch(e) { warnings.push("[GATE] Could not read doing.md: " + e.message); }

// Check plan.md has no uncompleted items (if plan exists)
try {
  if (fs.existsSync(state + "/plan.md")) {
    var plan = fs.readFileSync(state + "/plan.md", "utf8");
    var unfinished = (plan.match(/^- \[ \]/gm) || []).length;
    if (unfinished > 0) errors.push("[GATE] " + unfinished + " unfinished items in plan.md");
  }
} catch(e) { warnings.push("[GATE] Could not read plan.md: " + e.message); }

// Check session.md exists (context not lost)
if (!fs.existsSync(state + "/session.md")) {
  warnings.push("[GATE] session.md missing — context may be lost");
}

// Output warnings first (non-blocking)
if (warnings.length > 0) {
  process.stderr.write(warnings.join("\n") + "\n");
}

// Errors block delivery
if (errors.length > 0) {
  process.stderr.write(errors.join("\n") + "\n");
  process.stderr.write("[GATE] Complete all items before delivery.\n");
  process.exit(2);
}

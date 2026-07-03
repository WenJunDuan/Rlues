#!/usr/bin/env node
"use strict";
var fs = require("fs");
process.on("uncaughtException", function(e) {
  process.stderr.write("[TeammateIdle] Warning: " + e.message + "\n");
  process.exit(0);
});

try {
  var plan = ".ai_state/plan.md";
  if (fs.existsSync(plan)) {
    var content = fs.readFileSync(plan, "utf8");
    var unassigned = (content.match(/^- \[ \]/gm) || []).length;
    if (unassigned > 0) {
      process.stderr.write("[TeammateIdle] " + unassigned + " unassigned tasks remain in plan.md. Pick up next task.\n");
      process.exit(2);
    }
  }
} catch(e) {}
process.exit(0);

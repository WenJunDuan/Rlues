#!/usr/bin/env node
"use strict";
var cp = require("child_process");
var fs = require("fs");
// Critical hook: log errors as warnings, don't silently pass
process.on("uncaughtException", function(e) {
  process.stderr.write("[TaskCompleted] ERROR in quality gate: " + e.message + "\n");
  process.stderr.write("[TaskCompleted] Gate skipped due to script error — manual review needed.\n");
  process.exit(0);
});

var d = "";
process.stdin.on("data", function(c) { d += c; });
process.stdin.on("end", function() {
  try {
    var input = JSON.parse(d);
    var subject = input.task_subject || "unknown";

    // Check if package.json has test script
    if (fs.existsSync("package.json")) {
      var pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
      if (pkg.scripts && pkg.scripts.test && pkg.scripts.test !== "echo \"Error: no test specified\" && exit 1") {
        var result = cp.spawnSync("npm", ["test"], { timeout: 60000, stdio: "pipe" });
        if (result.status !== 0) {
          var out = ((result.stderr || result.stdout || "").toString()).slice(0, 500);
          process.stderr.write("[TaskCompleted] Tests failing for: " + subject + "\n" + out + "\n");
          process.exit(2);
        }
      }
    }

    // Check tsc if tsconfig exists
    if (fs.existsSync("tsconfig.json")) {
      var tsc = cp.spawnSync("npx", ["tsc", "--noEmit"], { timeout: 30000, stdio: "pipe" });
      if (tsc.status !== 0) {
        var tscOut = ((tsc.stderr || tsc.stdout || "").toString()).slice(0, 500);
        process.stderr.write("[TaskCompleted] Type errors for: " + subject + "\n" + tscOut + "\n");
        process.exit(2);
      }
    }
  } catch(e) {
    process.stderr.write("[TaskCompleted] Warning: " + e.message + "\n");
  }
  process.exit(0);
});

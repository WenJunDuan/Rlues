#!/usr/bin/env node
"use strict";
// VibeCoding 9.1.5 — Stop Hook (Delivery Gate)
// 阻止未完成任务/未测试代码的交付
var fs = require("fs");
var child_process = require("child_process");

process.on("uncaughtException", function() { process.exit(0); });
if (process.env.VIBECODING_HOOKS_DISABLED === "1") process.exit(0);

function exists(f) { try { return fs.existsSync(f); } catch { return false; } }
function runQuiet(cmd, timeout) {
  try {
    child_process.execSync(cmd, { timeout: timeout || 60000, stdio: "pipe" });
    return true;
  } catch { return false; }
}
function hasScript(name) {
  try {
    var pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
    return !!(pkg.scripts && pkg.scripts[name]);
  } catch { return false; }
}

var d = "";
process.stdin.on("data", function(c) { d += c; });
process.stdin.on("end", function() {
  try {
    // 1. plan.md 未完成任务
    if (exists(".ai_state/plan.md")) {
      var plan = fs.readFileSync(".ai_state/plan.md", "utf8");
      var unchecked = (plan.match(/^- \[ \]/gm) || []).length;
      if (unchecked > 0) {
        process.stderr.write("[DeliveryGate] BLOCKED: " + unchecked + " unchecked tasks in plan.md\n");
        process.exit(2);
      }
    }

    // 2. Path B+: 运行测试
    var isStrictPath = exists(".ai_state/design.md") || exists(".ai_state/plan.md");
    if (isStrictPath) {
      var testCmd = null;
      if (hasScript("test")) testCmd = "npm test";
      else if (exists("pytest.ini") || exists("pyproject.toml")) testCmd = "pytest --tb=short -q";
      else if (exists("Cargo.toml")) testCmd = "cargo test";
      else if (exists("go.mod")) testCmd = "go test ./...";
      if (testCmd) {
        var passed = runQuiet(testCmd, 120000);
        if (!passed) {
          process.stderr.write("[DeliveryGate] BLOCKED: tests failed (" + testCmd + ")\n");
          process.exit(2);
        }
      }
    }

    // 3. doing.md 进行中警告
    if (exists(".ai_state/doing.md")) {
      var doing = fs.readFileSync(".ai_state/doing.md", "utf8");
      var inProgress = (doing.match(/DOING|进行中/g) || []).length;
      if (inProgress > 0) {
        process.stderr.write("[DeliveryGate] WARNING: " + inProgress + " tasks still in progress\n");
      }
    }
  } catch(e) {}
  console.log(d);
});

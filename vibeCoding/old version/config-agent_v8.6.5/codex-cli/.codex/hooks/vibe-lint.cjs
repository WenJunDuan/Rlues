#!/usr/bin/env node
"use strict";
// VibeCoding Configuration Health Check
// Usage: node .claude/hooks/vibe-lint.cjs  (CC)
//        node .codex/hooks/vibe-lint.cjs   (Codex)
var fs = require("fs");
var path = require("path");

var errors = [];
var warnings = [];
var passed = 0;

function check(label, fn) {
  try {
    var result = fn();
    if (result === true) {
      passed++;
    } else if (typeof result === "string") {
      warnings.push("[WARN] " + label + ": " + result);
    } else {
      errors.push("[FAIL] " + label);
    }
  } catch (e) {
    errors.push("[FAIL] " + label + ": " + e.message);
  }
}

// Detect platform
var isCC = fs.existsSync(".claude/CLAUDE.md");
var isCodex = fs.existsSync("AGENTS.md") || fs.existsSync(".codex/config.toml");
var configDir = isCC ? ".claude" : ".codex";

console.log("# VibeCoding Configuration Health Check");
console.log(
  "Platform: " + (isCC ? "Claude Code" : isCodex ? "Codex CLI" : "UNKNOWN"),
);
console.log("");

// 1. Core config files exist
check("Main config file", function () {
  return isCC ? fs.existsSync(".claude/CLAUDE.md") : fs.existsSync("AGENTS.md");
});
check("Workflow: pace.md", function () {
  return fs.existsSync(configDir + "/workflows/pace.md");
});
check("Workflow: riper-7.md", function () {
  return fs.existsSync(configDir + "/workflows/riper-7.md");
});
check("Gate policy", function () {
  return fs.existsSync(configDir + "/rules/gate-policy.md");
});

// 2. All skills referenced in workflows exist
var workflows = [];
try {
  var wfDir = configDir + "/workflows";
  if (fs.existsSync(wfDir)) {
    fs.readdirSync(wfDir).forEach(function (f) {
      workflows.push(fs.readFileSync(wfDir + "/" + f, "utf8"));
    });
  }
} catch (e) {}

var skillRefs = [];
workflows
  .join("\n")
  .replace(/skills\/([a-z-]+)\/SKILL\.md/g, function (m, name) {
    if (skillRefs.indexOf(name) < 0) skillRefs.push(name);
  });
skillRefs.forEach(function (name) {
  check("Skill exists: " + name, function () {
    return fs.existsSync(configDir + "/skills/" + name + "/SKILL.md");
  });
});

// 3. ai_state templates exist
var requiredTemplates = [
  "session.md",
  "plan.md",
  "doing.md",
  "knowledge.md",
  "conventions.md",
];
requiredTemplates.forEach(function (t) {
  check("Template: " + t, function () {
    return fs.existsSync(configDir + "/templates/ai-state/" + t);
  });
});

// 4. Hooks are executable (CC only)
if (isCC) {
  var hooksDir = configDir + "/hooks";
  if (fs.existsSync(hooksDir)) {
    fs.readdirSync(hooksDir).forEach(function (f) {
      if (f.endsWith(".cjs")) {
        check("Hook parseable: " + f, function () {
          var cp = require("child_process");
          var r = cp.spawnSync("node", ["--check", path.resolve(hooksDir, f)], {
            timeout: 5000,
          });
          return r.status === 0;
        });
      }
    });
  }
}

// 5. CC-specific: agents don't reference dead skills
if (isCC) {
  var agentsDir = configDir + "/agents";
  if (fs.existsSync(agentsDir)) {
    fs.readdirSync(agentsDir).forEach(function (f) {
      var content = fs.readFileSync(agentsDir + "/" + f, "utf8");
      var inSkills = false;
      content.split("\n").forEach(function (line) {
        if (/^skills:/.test(line)) {
          inSkills = true;
          return;
        }
        if (inSkills && /^  - /.test(line)) {
          var skill = line.replace(/^  - /, "").trim();
          // Only check skill names, not tool names
          if (
            !/^(Read|Write|Edit|MultiEdit|Bash|Glob|Grep|Task|WebSearch|WebFetch)/.test(
              skill,
            )
          ) {
            check("Agent " + f + " skill: " + skill, function () {
              return fs.existsSync(
                configDir + "/skills/" + skill + "/SKILL.md",
              );
            });
          }
        } else if (inSkills && !/^  /.test(line)) {
          inSkills = false;
        }
      });
    });
  }
}

// 6. ai_state references in all files match templates
var allContent = "";
try {
  var walk = function (dir) {
    if (!fs.existsSync(dir)) return;
    fs.readdirSync(dir).forEach(function (f) {
      var fp = dir + "/" + f;
      if (fs.statSync(fp).isDirectory()) {
        walk(fp);
      } else if (f.endsWith(".md") || f.endsWith(".cjs")) {
        allContent += fs.readFileSync(fp, "utf8") + "\n";
      }
    });
  };
  walk(configDir);
  if (isCodex) walk("AGENTS.md"); // Also check root AGENTS.md
} catch (e) {}

var stateRefs = {};
allContent.replace(/\.ai_state\/([a-z_-]+\.md)/g, function (m, name) {
  stateRefs[name] = true;
});
Object.keys(stateRefs).forEach(function (name) {
  if (name === "archive") return; // directory, not file
  check("ai_state ref has template: " + name, function () {
    return fs.existsSync(configDir + "/templates/ai-state/" + name);
  });
});

// 7. Version consistency
check("Version in env", function () {
  if (isCC) {
    var settings = JSON.parse(fs.readFileSync(".claude/settings.json", "utf8"));
    return settings.env && settings.env.VIBECODING_VERSION ? true : false;
  } else {
    var toml = fs.readFileSync(".codex/config.toml", "utf8");
    return /VIBECODING_VERSION/.test(toml);
  }
});

// Summary
console.log("## Results");
console.log("Passed: " + passed);
if (warnings.length > 0) {
  console.log("\nWarnings (" + warnings.length + "):");
  warnings.forEach(function (w) {
    console.log("  " + w);
  });
}
if (errors.length > 0) {
  console.log("\nErrors (" + errors.length + "):");
  errors.forEach(function (e) {
    console.log("  " + e);
  });
  process.exit(1);
} else {
  console.log(
    "\n✓ All checks passed" + (warnings.length > 0 ? " (with warnings)" : ""),
  );
}

#!/usr/bin/env node
"use strict";
var fs = require("fs");
process.on("uncaughtException", function(e) { process.exit(0); });

var d = "";
process.stdin.on("data", function(c) { d += c; });
process.stdin.on("end", function() {
  try {
    var input = JSON.parse(d);
    var p = input.tool_input && (input.tool_input.file_path || input.tool_input.path) || "";

    // Update .ai_state/doing.md timestamp
    var state = ".ai_state/doing.md";
    if (fs.existsSync(state)) {
      var content = fs.readFileSync(state, "utf8");
      var ts = new Date().toISOString().slice(0, 16);
      if (content.indexOf("最后编辑:") >= 0) {
        content = content.replace(/最后编辑:.*/, "最后编辑: " + ts + " — " + p);
      } else {
        content = "最后编辑: " + ts + " — " + p + "\n" + content;
      }
      fs.writeFileSync(state, content);
    }
  } catch(e) {}
});

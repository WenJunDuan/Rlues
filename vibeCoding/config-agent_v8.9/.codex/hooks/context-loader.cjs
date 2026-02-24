// VibeCoding v8.9 — Codex SessionStart Hook
const fs = require("fs");
const path = require("path");

function readHead(file, lines) {
  try { return fs.readFileSync(file, "utf8").split("\n").slice(0, lines).join("\n"); }
  catch { return ""; }
}
function exists(f) { try { return fs.existsSync(f); } catch { return false; } }

let ctx = [];

if (exists(".ai_state/conventions.md"))
  ctx.push("📋 conventions:\n" + readHead(".ai_state/conventions.md", 30));

for (const f of ["patterns.md", "pitfalls.md", "decisions.md", "tools.md"]) {
  const p = path.join(".knowledge", f);
  if (exists(p)) { const h = readHead(p, 15); if (h.trim()) ctx.push(`📚 ${f}:\n${h}`); }
}

if (exists(".ai_state/session.md")) {
  ctx.push("🔄 session:\n" + fs.readFileSync(".ai_state/session.md", "utf8"));
  if (exists(".ai_state/review.md")) ctx.push("⚠️ 断点: V(验收) 阶段");
  else if (exists(".ai_state/verified.md")) ctx.push("⚠️ 断点: T(测试) 阶段");
  else if (exists(".ai_state/doing.md")) ctx.push("📝 doing:\n" + readHead(".ai_state/doing.md", 20));
}
if (exists(".ai_state/plan.md")) ctx.push("📐 plan:\n" + readHead(".ai_state/plan.md", 25));
if (exists(".ai_state/design.md")) {
  ctx.push("🎨 design:\n" + readHead(".ai_state/design.md", 15));
  if (!exists(".ai_state/session.md")) {
    ctx.push("⚠️ design.md 存在但 session.md 缺失, 可能异常中断。建议重新开始或恢复。");
  }
}

if (ctx.length > 0) process.stdout.write(ctx.join("\n---\n"));

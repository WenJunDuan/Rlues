// VibeCoding v8.9 — Codex Stop Hook (Delivery Gate)
const fs = require("fs");
const { execSync } = require("child_process");

function exists(f) { try { return fs.existsSync(f); } catch { return false; } }
function runQuiet(cmd, t) { try { execSync(cmd, { timeout: t||60000, stdio: "pipe" }); return true; } catch { return false; } }
function hasScript(n) { try { const p = JSON.parse(fs.readFileSync("package.json","utf8")); return !!(p.scripts&&p.scripts[n]); } catch { return false; } }

let currentPath = "A";
try { const s = fs.readFileSync(".ai_state/session.md","utf8"); const m = s.match(/path:\s*([ABCD])/i); if (m) currentPath = m[1].toUpperCase(); } catch {}

let errors = [];

if (currentPath !== "A" && exists(".ai_state/plan.md")) {
  try { const p = fs.readFileSync(".ai_state/plan.md","utf8"); const t = (p.match(/- \[[ x]\]/g)||[]).length; const d = (p.match(/- \[x\]/gi)||[]).length;
    if (t > 0 && d < t) errors.push(`plan.md: ${d}/${t}, ${t-d} 未完成`); } catch {}
}
if (currentPath !== "A" && hasScript("test")) { if (!runQuiet("npm test",90000)) errors.push("npm test 失败"); }

const isStrict = currentPath === "C" || currentPath === "D";
const hasLint = exists(".eslintrc") || exists(".eslintrc.js") || exists(".eslintrc.json") || exists(".eslintrc.cjs") || exists("eslint.config.js") || exists("eslint.config.mjs") || exists("eslint.config.cjs");
if (isStrict && hasLint) { if (!runQuiet("npx eslint . --max-warnings 0",60000)) errors.push("ESLint 未通过"); }

if (currentPath !== "A" && exists("tsconfig.json")) { if (!runQuiet("npx tsc --noEmit",60000)) errors.push("TypeScript 类型检查失败"); }

if (errors.length > 0) { process.stderr.write("🚫 Delivery Gate:\n" + errors.map(e => "  ❌ "+e).join("\n")); process.exit(2); }
else { process.stdout.write("✅ Pass (Path "+currentPath+")"); }

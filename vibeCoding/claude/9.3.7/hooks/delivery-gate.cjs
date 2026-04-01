// VibeCoding v9.3.7 — Stop: 读 JSON 程序化门禁
const fs = require('fs');
const path = require('path');
let input = ''; try { input = fs.readFileSync('/dev/stdin', 'utf8'); } catch (e) {}
let hc = {}; try { hc = JSON.parse(input); } catch (e) {}
if (hc.stop_hook_active) process.exit(0); // 防循环

const ai = path.join(process.cwd(), '.ai_state');
let level = 'PASS', issues = [], curPath = 'A';

try { curPath = JSON.parse(fs.readFileSync(path.join(ai, 'state.json'), 'utf8')).path || 'A'; } catch (e) {}

if (curPath !== 'A') {
  // feature_list.json
  try {
    const f = JSON.parse(fs.readFileSync(path.join(ai, 'feature_list.json'), 'utf8'));
    // 跳过模板占位符 (description 以 [ 开头 = 未生成真实数据)
    const realFeatures = f.filter(x => x.description && !x.description.startsWith('['));
    if (realFeatures.length > 0) {
      const st = JSON.parse(fs.readFileSync(path.join(ai, 'state.json'), 'utf8'));
      const sprint = st.current_sprint || 1;
      const failing = realFeatures.filter(x => x.sprint <= sprint && !x.passes);
      if (failing.length > 0) {
        issues.push(`${failing.length} features 未通过: ${failing.map(x=>x.id).join(',')}`);
        level = 'FAIL';
      }
    }
  } catch (e) { /* feature_list.json 缺失或无法解析 — 不阻断, R₀/R/D 阶段可能还没生成 */ }

  // quality.json
  try {
    const q = JSON.parse(fs.readFileSync(path.join(ai, 'quality.json'), 'utf8'));
    // 跳过模板 (sprint=0 表示 Evaluator 还没跑过)
    if (q.sprint > 0) {
      if (q.verdict === 'FAIL') { issues.push(`verdict=FAIL`); level = 'FAIL'; }
      else if (q.verdict === 'REWORK') { issues.push(`verdict=REWORK`); if (level==='PASS') level = 'REWORK'; }
      else if (q.verdict === 'CONCERNS') { issues.push('CONCERNS'); if (level==='PASS') level = 'CONCERNS'; }
      for (const [d,s] of Object.entries(q.scores||{})) {
        if (typeof s === 'number' && s > 0 && s < 2) { issues.push(`${d}=${s}`); level = 'REWORK'; }
      }
    }
  } catch (e) { /* quality.json 缺失 — 不阻断, T 阶段之前不需要 */ }
}

// 硬编码密钥 (所有 Path)
const src = path.join(process.cwd(), 'src');
if (fs.existsSync(src)) {
  try {
    const { execFileSync } = require('child_process');
    const r = execFileSync('grep', ['-rl','--include=*.ts','--include=*.js','--include=*.tsx','--include=*.jsx',
      '-E','(password|secret|api_key|apikey|token)\\s*[:=]\\s*["\'][^"\']{8,}', src], {encoding:'utf8'}).trim();
    if (r) { issues.push(`硬编码密钥: ${r.split('\n').length}文件`); level = 'FAIL'; }
  } catch (e) {}
}

if (level === 'PASS') process.exit(0);
if (level === 'CONCERNS') {
  // 放行, 详情已在 quality.json 中, Agent 可读取
  process.exit(0);
}
// REWORK/FAIL: exit 2 阻断, stderr 反馈给 Claude
process.stderr.write(`[delivery-gate] ${level}: ${issues.join('; ')}. 请修复后重试。`);
process.exit(2);

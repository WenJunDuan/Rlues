// VibeCoding v9.3.7 — PostToolUse(Write): 保护 JSON 文件
const fs = require('fs');
const path = require('path');
let input = ''; try { input = fs.readFileSync('/dev/stdin', 'utf8'); } catch (e) {}
let hi = {}; try { hi = JSON.parse(input); } catch (e) {}
const fp = hi.tool_input?.file_path || '';
const bn = path.basename(fp);

if (bn === 'feature_list.json') {
  try {
    const d = JSON.parse(fs.readFileSync(fp, 'utf8'));
    if (!Array.isArray(d)) {
      process.stderr.write('[post-edit] feature_list.json 必须是数组');
    } else {
      for (const it of d) {
        if (!it.id || !it.description || typeof it.passes !== 'boolean')
          process.stderr.write(`[post-edit] ${it.id||'?'} 结构不完整`);
      }
    }
  } catch (e) { process.stderr.write(`[post-edit] feature_list.json 非法JSON: ${e.message}`); }
}
if (bn === 'quality.json') {
  try {
    const q = JSON.parse(fs.readFileSync(fp, 'utf8'));
    for (const k of ['scores','weighted_average','verdict'])
      if (!(k in q)) process.stderr.write(`[post-edit] quality.json 缺 ${k}`);
    for (const [d,s] of Object.entries(q.scores||{}))
      // 0 = 未评分 (模板), 允许; 1-5 合法; 其他不合法
      if (typeof s==='number' && s !== 0 && (s < 1 || s > 5))
        process.stderr.write(`[post-edit] ${d}=${s} 超出1-5范围`);
  } catch (e) { process.stderr.write(`[post-edit] quality.json 非法JSON`); }
}
const ext = path.extname(fp).toLowerCase();
if (['.ts','.js','.tsx','.jsx'].includes(ext)) {
  try {
    const c = fs.readFileSync(fp, 'utf8');
    if (c.includes('execSync(') && !c.includes('execFileSync('))
      process.stderr.write(`[post-edit] ${bn}: execSync→execFileSync`);
  } catch (e) {}
}
process.exit(0);

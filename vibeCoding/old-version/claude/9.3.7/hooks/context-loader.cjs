// VibeCoding v9.3.7 — SessionStart: 读 JSON 注入恢复上下文
// 只有 state.json.path 非空 (项目已经过 PACE 路由) 才注入
const fs = require('fs');
const path = require('path');
const ai = path.join(process.cwd(), '.ai_state');

// 先检查 state.json — path 为空说明项目未初始化, 不注入
let state = null;
try {
  state = JSON.parse(fs.readFileSync(path.join(ai, 'state.json'), 'utf8'));
} catch (e) { process.exit(0); } // 无 state.json → 跳过

if (!state.path) process.exit(0); // 未经 PACE → 跳过

const ctx = {};
ctx.path = state.path;
if (state.current_phase) ctx.phase = state.current_phase;
if (state.total_sprints > 0) ctx.sprint = `${state.current_sprint}/${state.total_sprints}`;
if (state.features_total > 0) ctx.features = `${state.features_passing}/${state.features_total}`;
if (state.last_verdict) ctx.verdict = state.last_verdict;

// progress.json
try {
  const p = JSON.parse(fs.readFileSync(path.join(ai, 'progress.json'), 'utf8'));
  const last = (p.sessions || []).slice(-1)[0];
  if (last) {
    if (last.next_steps) ctx.next = last.next_steps;
    if (last.known_issues) ctx.issues = last.known_issues;
  }
} catch (e) {}

// feature_list.json
try {
  const f = JSON.parse(fs.readFileSync(path.join(ai, 'feature_list.json'), 'utf8'));
  // 只统计真实 features (非模板占位符)
  const real = f.filter(x => x.description && !x.description.startsWith('['));
  if (real.length > 0) {
    const pass = real.filter(x => x.passes).length;
    ctx.fstats = `${pass}/${real.length} passing`;
    const fail = real.find(x => !x.passes);
    if (fail) ctx.nextF = `${fail.id}: ${fail.description}`;
  }
} catch (e) {}

const lines = ['[VibeCoding 恢复]',
  `Path: ${ctx.path}`,
  ctx.phase && `阶段: ${ctx.phase}`,
  ctx.sprint && `Sprint: ${ctx.sprint}`,
  ctx.fstats && `Features: ${ctx.fstats}`,
  ctx.verdict && `评分: ${ctx.verdict}`,
  ctx.next && `下一步: ${ctx.next}`,
  ctx.nextF && `待实现: ${ctx.nextF}`,
  ctx.issues && `问题: ${ctx.issues}`
].filter(Boolean).join('\n');

process.stdout.write(JSON.stringify({
  hookSpecificOutput: { hookEventName: "SessionStart", additionalContext: lines }
}));
process.exit(0);

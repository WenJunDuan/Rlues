#!/usr/bin/env node
/**
 * VibeCoding Athena v9.9.6 · CC SessionStart hook
 *
 * 触发: session 启动 / resume
 * 职责:
 * 1. 注入 .ai_state/_index.md frontmatter 摘要
 * 2. 注入 ~/.claude/rules/_index.md 摘要
 * 3. (v9.9.6) stage 操作提示移交 stage-breadcrumb.cjs 每轮注入 (单一真相: pace/references/stages.md)
 * 4. 若 design_changed_after_impl=true → 强提示需 re-review
 * 5. 若 next_action="next_roadmap_item:..." → 提示自动推进
 *
 * 输出协议: { hookSpecificOutput: { hookEventName, additionalContext } }
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const POINTER_KEYS = ['latest_design', 'latest_review', 'latest_cleanup', 'latest_requirement'];

// v9.9.6: SessionStart 只注入路由必需字段, 不再整段注入 _index frontmatter.
const INDEX_CORE = ['version','path','stage','current_sprint_slug','current_roadmap_slug','next_action','plan_model','platforms_enabled'];
const INDEX_SKIP_FLAGS = ['skip_polish','skip_architecture_check','skip_runtime_verify'];
// latest_design/review/cleanup/requirement 由下方 memory router 注入, 此处不重复
const INDEX_POINTERS = ['latest_decisions','latest_lessons'];

function renderIndexWhitelist(fm) {
  const lines = [];
  for (const k of INDEX_CORE) { const v = String(fm[k] || '').trim(); if (v) lines.push(k + ': ' + v); }
  for (const k of INDEX_SKIP_FLAGS) { if (String(fm[k] || '').trim() === 'true') lines.push(k + ': true'); }
  const ptr = [];
  for (const k of INDEX_POINTERS) {
    const raw = String(fm[k] || '').trim();
    if (!raw) continue;
    const items = raw.replace(/^\[|\]$/g, '').split(',').map((s) => s.trim().replace(/^"|"$/g, '')).filter(Boolean);
    if (!items.length) continue;
    ptr.push(k + ': ' + items[0] + (items.length > 1 ? ` (+${items.length - 1} more, 见 _index)` : ''));
  }
  if (ptr.length) { lines.push('# pointers'); lines.push(...ptr); }
  if (!lines.length) return '';
  return lines.join('\n') + '\n\n其余字段按需 Read .ai_state/_index.md (历史/统计/能力探测不自动注入).';
}

function findAiState(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(current, '.ai_state');
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      return candidate;
    }
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;
}

function readFrontmatterSummary(filePath) {
  if (!fs.existsSync(filePath)) return '';
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.startsWith('---')) return '';
    const parts = content.split('---', 3);
    if (parts.length < 3) return '';
    return parts[1].trim();
  } catch (e) {
    return '';
  }
}

function parseFrontmatter(filePath) {
  if (!fs.existsSync(filePath)) return {};
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    if (!content.startsWith('---')) return {};
    const parts = content.split('---', 3);
    if (parts.length < 3) return {};
    const fm = {};
    for (const line of parts[1].split('\n')) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const m = t.match(/^([\w\-_.]+)\s*:\s*(.*)$/);
      if (m) {
        let v = m[2].trim();
        // v9.9.2 fix: 取首对引号内的值 (而非剥首尾字符), 防止行尾注释被并入值
        // 例: current_sprint_slug: "xxx"  # 注释 "示例" — 旧逻辑会把注释当值的一部分
        const q = v.match(/^"([^"]*)"|^'([^']*)'/);
        if (q) {
          v = q[1] !== undefined ? q[1] : q[2];
        } else {
          const hashIdx = v.indexOf(" #");
          if (hashIdx >= 0) v = v.slice(0, hashIdx).trim();
        }
        fm[m[1]] = v;
      }
    }
    return fm;
  } catch (e) {
    return {};
  }
}

function readRulesSummary() {
  const home = os.homedir();
  const userRules = path.join(home, '.claude', 'rules', '_index.md');
  if (fs.existsSync(userRules)) {
    let content = fs.readFileSync(userRules, 'utf-8');
    // v9.9.6: 按字节截断 — 中文 1 字 3 字节
    if (Buffer.byteLength(content, 'utf8') > 600) {
      content = Buffer.from(content, 'utf8').slice(0, 600).toString('utf8').replace(/\uFFFD+$/, '')
        + '\n... (see ~/.claude/rules/ for full)';
    }
    return content;
  }
  return '';
}

function specialAlerts(fm, aiState) {
  const alerts = [];

  // 1. design_changed_after_impl
  if (fm.design_changed_after_impl === 'true') {
    alerts.push('🚨 **design 改后未重新 review**: `design.md` 在 impl/review/polish 阶段被修改, ship 前必须重新 spawn 3 个 review subagent. delivery-gate 会 block.');
  }

  // 2. next_action (roadmap 自动推进)
  const nextAction = fm.next_action || '';
  if (nextAction.startsWith('next_roadmap_item:')) {
    const itemSlug = nextAction.split(':')[1];
    alerts.push(`🎯 **roadmap 推进**: 上 sprint 完成, 自动进入下一个 item "${itemSlug}". 主 agent 应进 plan stage 处理新 item.`);
  } else if (nextAction === 'roadmap_complete') {
    alerts.push('🎉 **roadmap 完成**: 所有 items 已 ship, 提示用户庆祝 + 触发 `/compound add learning` 沉淀经验.');
  }

  // 3. active worktrees (hint only; truth is live `git worktree list`)
  const activeWts = fm.active_worktrees || '[]';
  if (activeWts !== '[]') {
    alerts.push(`🌿 **worktree 提示**: _index 记录 ${activeWts}; 先运行 git worktree list 现场核对. 默认 hook 不替代原生 Git 创建/清理.`);
  }

  // 4. 未消解的 delivery-gate 熔断升级 (design §10.1 AC16i)
  // 熔断"不是放水"的承重腿: escalation 不发 block, 若无人告警就等于静默吞掉失败。
  // 尤其外包 exec 会话的 stderr 不回喂编排者, 编排侧只会看到一次干净的 Stop。
  const escalation = pendingEscalation(aiState, fm.current_sprint_slug || '');
  if (escalation) {
    alerts.push(`🛑 **门禁升级未消解**: 上次 Stop 连续 ${escalation.consecutive} 次同因阻断后已熔断 (ESCALATED, ${escalation.ts}). 阻断本身**未解除**, 只是停止了空转. 查 \`.ai_state/sprints/${fm.current_sprint_slug}/stop-failures.jsonl\`, 修掉根因再继续; 不得当作已通过.`);
  }

  return alerts;
}

/** 尾部是 GateEscalated 且其后无 GatePass = 升级尚未消解。读取有界, 失败即静默 (fail-open)。 */
function pendingEscalation(aiState, sprintSlug) {
  if (!sprintSlug) return null;
  try {
    const file = path.join(aiState, 'sprints', sprintSlug, 'stop-failures.jsonl');
    const raw = fs.readFileSync(file, 'utf8');
    const rows = [];
    for (const line of raw.split(/\r?\n/)) {
      if (!line.trim()) continue;
      try {
        const row = JSON.parse(line);
        if (row && ['GateBlock', 'GateEscalated', 'GatePass'].includes(row.event)) rows.push(row);
      } catch (_) { /* 跳过非本类记录 */ }
    }
    const last = rows[rows.length - 1];
    return last && last.event === 'GateEscalated' ? last : null;
  } catch (_) {
    return null;
  }
}

function memoryRouterContext(aiState, idxPath, fm) {
  const lines = [
    'Tier1 working memory is non-authoritative conversation/tool context.',
    'Tier2 persistent memory is the versioned .ai_state project truth.',
    '_index.md retrieval router is bounded routing metadata, not a second database.',
  ];
  const currentSprint = fm.current_sprint_slug || '';
  for (const key of POINTER_KEYS) {
    if (!Object.hasOwn(fm, key)) {
      lines.push(`⚠ malformed router: missing required pointer key ${key}`);
      continue;
    }
    const value = String(fm[key] || '').trim();
    if (!value) continue;
    const target = path.resolve(aiState, value);
    if (!target.startsWith(`${path.resolve(aiState)}${path.sep}`)) {
      lines.push(`⚠ escaping authoritative pointer ${key}: ${value}`);
      continue;
    }
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
      lines.push(`⚠ missing authoritative pointer ${key}: ${value}`);
      continue;
    }
    lines.push(`✓ routed ${key}: ${value}`);
    if (key === 'latest_review' && currentSprint) {
      const reviews = path.join(aiState, 'sprints', currentSprint, 'reviews');
      const numbered = fs.existsSync(reviews) ? fs.readdirSync(reviews).map(name => {
        const match = name.match(/^pass([1-9]\d*)\.md$/);
        return match ? [Number(match[1]), path.resolve(reviews, name)] : null;
      }).filter(Boolean) : [];
      if (numbered.length) {
        numbered.sort((a, b) => a[0] - b[0]);
        if (target !== numbered.at(-1)[1]) lines.push(`⚠ stale authoritative pointer ${key}: ${value}`);
      }
    }
  }
  const routeHistory = String(fm.route_history || '[]').trim();
  if (!routeHistory.startsWith('[') || !routeHistory.endsWith(']')) {
    lines.push('⚠ malformed route_history: expected inline list capped at 10');
  } else {
    const inner = routeHistory.slice(1, -1).trim();
    const count = inlineListCount(inner);
    if (count > 10) lines.push(`⚠ route_history overflow: ${count} entries (max 10)`);
  }
  const content = fs.readFileSync(idxPath, 'utf8');
  const state = content.match(/^## 当前状态\s*$\n([\s\S]*?)(?=^##\s|(?![\s\S]))/m);
  if (state) {
    const entries = state[1].split(/\r?\n/).filter(line => /^###\s+|^\s*-\s+/.test(line)).length;
    if (entries > 10) lines.push(`⚠ current-state log overflow: ${entries} entries (max 10)`);
  }
  return lines.join('\n');
}

function inlineListCount(inner) {
  if (!inner) return 0;
  let count = 1;
  let quote = '';
  let escaped = false;
  for (const char of inner) {
    if (escaped) escaped = false;
    else if (char === '\\' && quote === '"') escaped = true;
    else if (quote) { if (char === quote) quote = ''; }
    else if (char === '"' || char === "'") quote = char;
    else if (char === ',') count += 1;
  }
  return count;
}

function main() {
  try {
    const cwd = process.cwd();
    const aiState = findAiState(cwd);

    const contextParts = [];

    if (aiState) {
      const idxPath = path.join(aiState, '_index.md');
      const fm = parseFrontmatter(idxPath);
      const indexSummary = renderIndexWhitelist(fm);
      if (indexSummary) {
        contextParts.push(`## Athena 项目状态 (.ai_state/_index.md)\n\n${indexSummary}`);
      }

      contextParts.push(`## Two-tier memory retrieval\n\n${memoryRouterContext(aiState, idxPath, fm)}`);

      const alerts = specialAlerts(fm, aiState);
      if (alerts.length > 0) {
        contextParts.push(`## 🚨 重要提醒\n\n${alerts.join('\n\n')}`);
      }

      // Tier1 is never elevated over Tier2; checkpoint writes durable state.
      contextParts.push('## 💾 会话记忆 (v9.9.6)\n\n长任务收尾 / context 快满 / 关键决策后, 跑 `/athena-checkpoint` 把进展固化进 .ai_state (免每次手动描述). 与 PreCompact 兜底互补.');
    }

    const rulesSummary = readRulesSummary();
    if (rulesSummary) {
      contextParts.push(`## 项目规范摘要 (~/.claude/rules/_index.md)\n\n${rulesSummary}\n\n详细规则按 stage 触发自动加载.`);
    }

    if (contextParts.length > 0) {
      const additionalContext = contextParts.join('\n\n---\n\n');
      const output = {
        hookSpecificOutput: {
          hookEventName: 'SessionStart',
          additionalContext: additionalContext,
        },
      };
      console.log(JSON.stringify(output));
    }

    process.exit(0);
  } catch (e) {
    if (e.code !== 'MODULE_NOT_FOUND') {
      process.stderr.write(`[session-start] warning (non-blocking): ${e.message}\n`);
    }
    process.exit(0);
  }
}

main();

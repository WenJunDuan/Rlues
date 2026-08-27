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
// B3 (2026-07-28 W28): 白名单渲染/frontmatter 解析/告警 下沉共享模块, compact-restore 复用
const render = require('./_index-render.cjs');
const { parseFrontmatter, renderIndexWhitelist, specialAlerts } = render;
const POINTER_KEYS = ['latest_design', 'latest_review', 'latest_cleanup', 'latest_requirement'];

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

#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.4 · CC SessionStart hook
 *
 * 触发: session 启动 / resume
 * 职责:
 * 1. 注入 .ai_state/_index.md frontmatter 摘要
 * 2. 注入 ~/.claude/rules/_index.md 摘要
 * 3. v9.6.4 新: 注入 stage-specific 操作提示 (ultrathink / critic / spec-compliance / 等)
 * 4. v9.6.4 新: 若 design_changed_after_impl=true → 强提示需 re-review
 * 5. v9.6.4 新: 若 next_action="next_roadmap_item:..." → 提示自动推进
 *
 * 源:
 * - https://code.claude.com/docs/en/hooks-guide#session-start
 * Stop hook 输出协议: { hookSpecificOutput: { hookEventName, additionalContext } }
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

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
        if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
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
    if (content.length > 600) {
      content = content.substring(0, 600) + '\n... (see ~/.claude/rules/ for full)';
    }
    return content;
  }
  return '';
}

function stageHints(fm) {
  // v9.6.4: stage-specific 操作提示
  const stage = fm.stage || '';
  const hints = [];

  if (stage === 'plan' || stage === 'design') {
    hints.push('🧠 **plan/design stage**: 在你的第一条 message 加 "ultrathink" 触发最大 thinking budget (~32K).');
    hints.push('🔍 完成 design.md `## Round N` 后, 用 Task tool 调用 `critic` subagent 评估.');
    const maxRounds = fm.plan_critique_max_rounds || '4';
    const lastRound = fm.last_critic_round || '0';
    hints.push(`📊 critic 多轮限制: max=${maxRounds}, 已跑=${lastRound}.`);
  }

  if (stage === 'impl') {
    hints.push('🔧 **impl stage**: 写代码必须用 Task `generator` subagent (铁律 12).');
    const pathType = fm.path || '';
    if (['Refactor', 'System'].includes(pathType)) {
      hints.push(`⚠️ path=${pathType}: generator 必须 isolation: worktree (大功能强制隔离).`);
    }
  }

  if (stage === 'review') {
    hints.push('🔎 **review stage**: 并行 spawn 3 个 subagent:');
    hints.push('   - `reviewer` (代码层 findings)');
    hints.push('   - `spec-compliance` (design ↔ git diff 一致性, MISSING/EXTRA/DEVIATED)');
    hints.push('   - `evaluator` (综合 VERDICT, 写 _index.next_action)');
  }

  if (stage === 'polish') {
    hints.push('✨ **polish stage**: 强制 (Refactor/System 路径).');
    hints.push('   - spawn `polish_worker` subagent');
    hints.push('   - 5 检查项 + finishing-a-development-branch (worktree 清理)');
  }

  return hints;
}

function specialAlerts(fm, aiState) {
  // v9.6.4 强提示
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

  // 3. active worktrees
  const activeWts = fm.active_worktrees || '[]';
  if (activeWts !== '[]') {
    alerts.push(`🌿 **活着的 worktree**: ${activeWts} (跨 session 可能需要清理, 检查 sprints/{current_sprint}/worktrees.yaml)`);
  }

  return alerts;
}

function main() {
  try {
    const cwd = process.cwd();
    const aiState = findAiState(cwd);

    const contextParts = [];

    if (aiState) {
      const idxPath = path.join(aiState, '_index.md');
      const indexSummary = readFrontmatterSummary(idxPath);
      if (indexSummary) {
        contextParts.push(`## Athena 项目状态 (.ai_state/_index.md)\n\n${indexSummary}`);
      }

      // v9.6.4: 解析 frontmatter 加 stage hints + special alerts
      const fm = parseFrontmatter(idxPath);

      const alerts = specialAlerts(fm, aiState);
      if (alerts.length > 0) {
        contextParts.push(`## 🚨 重要提醒\n\n${alerts.join('\n\n')}`);
      }

      const hints = stageHints(fm);
      if (hints.length > 0) {
        contextParts.push(`## 当前 stage 操作提示 (stage: ${fm.stage || 'unknown'})\n\n${hints.join('\n')}`);
      }
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

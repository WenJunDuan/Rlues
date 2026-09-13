'use strict';
/**
 * VibeCoding Athena · _index.md 注入渲染共享模块 (B3, 2026-07-28 台账 W28)
 * 单一真相: session-start 与 compact-restore 共用白名单渲染 + 告警,
 * 消除 compact-restore 全量 frontmatter 注入 (v9.6.2 遗留) 与双写漂移。
 */
const fs = require('fs');
const path = require('path');

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


module.exports = { INDEX_CORE, INDEX_SKIP_FLAGS, INDEX_POINTERS, renderIndexWhitelist, parseFrontmatter, specialAlerts, pendingEscalation };

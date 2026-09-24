#!/usr/bin/env node
/**
 * VibeCoding Athena v9.7.0 · CC PreToolUse(Task) hook
 *
 * 职责: 强制铁律[零写入] — 红区 (Refactor/System) 与并行场景 worktree 强制
 * 注: 绿区 (主 agent 直接做) 不经过 Task tool, 天然不触发本 hook; 黄区单写者放行.
 *
 * 检查规则:
 * 1. path ∈ {Refactor, System} + subagent 写文件 (tools 含 Write/Edit) → 必须有 isolation: worktree
 * 2. active_worktrees 已有 ≥ 1 个 → 第二个并行 subagent 也必须 isolation: worktree
 *
 * 输入: PreToolUse JSON payload (含 tool_input.subagent_type)
 * 输出: exit 2 + stderr 提示修复; 或 exit 0 通过
 */
'use strict';

const fs = require('fs');
const path = require('path');

function findAiState(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(current, '.ai_state');
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) return candidate;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;
}

function parseFrontmatter(content) {
  if (!content.startsWith('---')) return { fm: {}, body: content };
  const parts = content.split('---', 3);
  if (parts.length < 3) return { fm: {}, body: content };
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
  return { fm, body: parts[2] };
}

function getActiveWorktrees(fm) {
  const raw = fm.active_worktrees || '[]';
  if (raw === '[]' || raw === '') return [];
  return raw.replace(/[\[\]]/g, '').split(',').map(s => s.trim()).filter(Boolean);
}

function subagentWritesFiles(agentFm) {
  const tools = (agentFm.tools || '').toLowerCase();
  return tools.includes('write') || tools.includes('edit');
}

function main() {
  try {
    let data = '';
    try { data = fs.readFileSync(0, 'utf-8'); } catch (_) {}
    const payload = data ? JSON.parse(data) : {};

    const subagentType = payload?.tool_input?.subagent_type || '';
    if (!subagentType) {
      process.exit(0);
    }

    const aiState = findAiState(process.cwd());
    if (!aiState) {
      process.exit(0);
    }

    const idxPath = path.join(aiState, '_index.md');
    if (!fs.existsSync(idxPath)) {
      process.exit(0);
    }

    const { fm: idxFm } = parseFrontmatter(fs.readFileSync(idxPath, 'utf-8'));
    const pathType = idxFm.path || '';

    const agentFile = path.join(process.env.HOME || '', '.claude/agents', `${subagentType}.md`);
    if (!fs.existsSync(agentFile)) {
      process.exit(0);
    }

    const { fm: agentFm } = parseFrontmatter(fs.readFileSync(agentFile, 'utf-8'));
    const hasWorktreeIsolation = agentFm.isolation === 'worktree';
    const writesFiles = subagentWritesFiles(agentFm);

    // 规则 1: 红区 (Refactor/System) + 写文件 subagent → 必须 isolation: worktree
    if (['Refactor', 'System'].includes(pathType) && writesFiles && !hasWorktreeIsolation) {
      process.stderr.write(
        `[subagent-worktree-check] BLOCKED: 铁律[零写入] 红区\n` +
        `当前 path=${pathType}, subagent "${subagentType}" 会写文件但缺 isolation: worktree.\n` +
        `修复方案 (二选一):\n` +
        `  1. 在 ~/.claude/agents/${subagentType}.md frontmatter 加 'isolation: worktree'\n` +
        `  2. 改用其他已 worktree 的 subagent (e.g. generator)\n`
      );
      process.exit(2);
    }

    // 规则 2: 已有 active worktree + 这个 subagent 写文件 + 没 worktree 隔离 → 强制
    const activeWorktrees = getActiveWorktrees(idxFm);
    if (activeWorktrees.length >= 1 && writesFiles && !hasWorktreeIsolation) {
      process.stderr.write(
        `[subagent-worktree-check] BLOCKED: 铁律[零写入] (并行场景)\n` +
        `已有 ${activeWorktrees.length} 个活着的 worktree (${activeWorktrees.join(', ')})\n` +
        `并行调度 subagent "${subagentType}" (会写文件) 必须 isolation: worktree 防文件冲突.\n` +
        `修复: 在 ~/.claude/agents/${subagentType}.md 加 'isolation: worktree'.\n`
      );
      process.exit(2);
    }

    process.exit(0);
  } catch (e) {
    process.stderr.write(`[subagent-worktree-check] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}

main();

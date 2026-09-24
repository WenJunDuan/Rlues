#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.4 · CC PostToolUse hook
 *
 * 职责:
 *   1. 收集 tool_use_id, 文件路径, 时间戳
 *   2. 追加到 sprints/{current_slug}/tool-trace.jsonl (每行一个 JSON)
 *   3. 解析 evidence: 若 Edit/Write 写的文件在 design.md 的 File Structure Plan 中提到 → 写 evidence.yaml
 *   4. v9.9.2: subagent 在隔离 worktree 写文件时, 证据重定向到主仓库 (防随 worktree 清理丢失,
 *      否则 delivery-gate 的 changedFiles 计数与 U3 Evidence Cross-Check 失真)
 *
 * matcher: Edit|Write|MultiEdit|Bash (在 settings.json 中配置)
 * 源: https://code.claude.com/docs/en/hooks-guide
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

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

// 缺陷1 修复 (v9.9.2): PostToolUse 在隔离 worktree 内触发时 (generator 写代码),
// findAiState 命中 worktree 副本 → evidence.yaml/tool-trace.jsonl 随 worktree 清理丢失,
// 致 delivery-gate 的 changedFiles 计数与 U3 Evidence Cross-Check 失真. 检测到 worktree 则
// 重定向到主仓库 .ai_state (与 subagent-tracker 同策略, hook 自包含故内联).
function redirectToMainRepo(aiState, cwd) {
  try {
    const opt = { cwd, encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] };
    const gitDir = execFileSync('git', ['rev-parse', '--git-dir'], opt).trim();
    const commonDir = execFileSync('git', ['rev-parse', '--git-common-dir'], opt).trim();
    if (path.resolve(cwd, gitDir) === path.resolve(cwd, commonDir)) return aiState;
    const mainAiState = path.join(path.dirname(path.resolve(cwd, commonDir)), '.ai_state');
    if (fs.existsSync(mainAiState) && fs.statSync(mainAiState).isDirectory()) return mainAiState;
  } catch (_) {
    // 非 git / git 不可用 → 保持原路径
  }
  return aiState;
}

function getCurrentSprintSlug(aiState) {
  const idxPath = path.join(aiState, '_index.md');
  if (!fs.existsSync(idxPath)) return null;
  const content = fs.readFileSync(idxPath, 'utf-8');
  const m = content.match(/current_sprint_slug:\s*["']?([^"\n]+)["']?/);
  return m ? m[1].trim() : null;
}

function main() {
  try {
    let data = '';
    try { data = fs.readFileSync(0, 'utf-8'); } catch (_) {}
    const payload = data ? JSON.parse(data) : {};

    const cwd = payload?.cwd || process.cwd();
    let aiState = findAiState(cwd);
    if (!aiState) { process.exit(0); }
    // 缺陷1: worktree 副本重定向到主仓库, 防证据随 worktree 清理丢失
    aiState = redirectToMainRepo(aiState, cwd);

    const sprintSlug = getCurrentSprintSlug(aiState);
    if (!sprintSlug) { process.exit(0); }

    const toolName = payload?.tool_name || '';
    const toolInput = payload?.tool_input || {};
    const toolUseId = payload?.tool_use_id || '';
    const exitCode = payload?.tool_output?.exit_code != null ? payload.tool_output.exit_code : 0;

    const ts = new Date().toISOString();

    // 1. 追加 tool-trace.jsonl
    const tracePath = path.join(aiState, 'sprints', sprintSlug, 'tool-trace.jsonl');
    fs.mkdirSync(path.dirname(tracePath), { recursive: true });

    const trace = {
      ts: ts,
      tool: toolName,
      tool_use_id: toolUseId,
      exit: exitCode,
    };

    if (['Edit', 'Write', 'MultiEdit'].includes(toolName)) {
      trace.file = toolInput.file_path || toolInput.path || '';
    } else if (toolName === 'Bash') {
      trace.command = (toolInput.command || '').slice(0, 200);
    }

    fs.appendFileSync(tracePath, JSON.stringify(trace) + '\n');

    // 2. 简化 evidence.yaml: 若 Edit/Write/MultiEdit, 追加 tool_use_id 到 evidence.yaml
    //    (完整实现应该解析 design.md 的 File Structure Plan 对应 task, 但避免复杂度,
    //     先做简单版: 每个写文件操作就追加一条 evidence)
    if (['Edit', 'Write', 'MultiEdit'].includes(toolName) && toolUseId) {
      const evidencePath = path.join(aiState, 'sprints', sprintSlug, 'evidence.yaml');
      if (!fs.existsSync(evidencePath)) {
        const header = `sprint_slug: ${sprintSlug}\ncollected_evidence:\n`;
        fs.writeFileSync(evidencePath, header, 'utf-8');
      }
      const filePath = toolInput.file_path || toolInput.path || '';
      const entry = `  - tool_use_id: "${toolUseId}"\n` +
                    `    tool: "${toolName}"\n` +
                    `    file: "${filePath}"\n` +
                    `    timestamp: "${ts}"\n`;
      fs.appendFileSync(evidencePath, entry);
    }

    process.exit(0);
  } catch (e) {
    process.stderr.write(`[evidence-collector] non-blocking: ${e.message}\n`);
    process.exit(0);
  }
}

main();

#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.4 · CC PostToolUse hook
 *
 * 职责:
 *   1. 收集 tool_use_id, 文件路径, 时间戳
 *   2. 追加到 sprints/{current_slug}/tool-trace.jsonl (每行一个 JSON)
 *   3. 解析 evidence: 若 Edit/Write 写的文件在 design.md 的 File Structure Plan 中提到 → 写 evidence.yaml
 *
 * matcher: Edit|Write|MultiEdit|Bash (在 settings.json 中配置)
 * 源: https://code.claude.com/docs/en/hooks-guide
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

    const aiState = findAiState(process.cwd());
    if (!aiState) { process.exit(0); }

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

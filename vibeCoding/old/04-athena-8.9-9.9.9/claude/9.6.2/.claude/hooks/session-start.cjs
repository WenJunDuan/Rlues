#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.2 · CC SessionStart hook
 *
 * 触发: session 启动 / resume
 * 职责:
 * 1. 注入 .ai_state/_index.md frontmatter 摘要
 * 2. 注入 ~/.claude/rules/_index.md 摘要 (v9.6.2 新)
 *
 * 源:
 * - https://docs.anthropic.com/en/docs/claude-code/hooks#session-start
 * - https://code.claude.com/docs/en/hooks-guide
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

function readRulesSummary() {
  // Order: ~/.claude/rules/_index.md, then $REPO_ROOT/.claude/rules/_index.md
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

function main() {
  try {
    const cwd = process.cwd();
    const aiState = findAiState(cwd);

    const contextParts = [];

    if (aiState) {
      const indexSummary = readFrontmatterSummary(path.join(aiState, '_index.md'));
      if (indexSummary) {
        contextParts.push(`## Athena 项目状态\n\n${indexSummary}`);
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
    // 非阻塞: 任何异常吞掉
    if (e.code !== 'MODULE_NOT_FOUND') {
      process.stderr.write(`[session-start] warning (non-blocking): ${e.message}\n`);
    }
    process.exit(0);
  }
}

main();

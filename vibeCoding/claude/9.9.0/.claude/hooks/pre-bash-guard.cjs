#!/usr/bin/env node
/**
 * v9.9.0 新增: git push 门禁 — CC 2.1.198 起后台 agent 在 worktree 完成工作后
 * 默认自动 commit+push+开 draft PR, 会绕过 Athena 的 review→ship 门禁顺序.
 * 对策: Athena 项目 (有 .ai_state) 中 stage != ship 时 block git push.
 * 逃生: 命令含 ATHENA_ALLOW_PUSH=1 前缀, 或非 Athena 项目不拦.
 * 注意: 仅拦 Bash 层 push; CC 内部自动 PR 机制若不走 Bash 则拦不住 — 部署时确认
 * 后台 agent 自动提交开关 (见 CHANGELOG v9.9.0 已知边界).
 */
'use strict';

const fs = require('fs');
const path = require('path');

function findAiStateStage(cwd) {
  let current = cwd;
  for (let i = 0; i < 5; i++) {
    const idx = path.join(current, '.ai_state', '_index.md');
    if (fs.existsSync(idx)) {
      const m = fs.readFileSync(idx, 'utf-8').match(/^stage:\s*"?([^"\n]*)"?/m);
      return m ? m[1].trim() : '';
    }
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
  return null;   // 非 Athena 项目
}

const P0_PATTERNS = [
  /\brm\s+-rf?\s+\/(\s|$)/,
  /\brm\s+-rf?\s+~(\s|$)/,
  /\brm\s+-rf?\s+\$HOME/,
  /\bcurl\b[^|]*\|\s*bash/,
  /\bwget\b[^|]*\|\s*bash/,
  /\bDROP\s+TABLE\b/i,
  /:\(\)\s*\{/,
  /\bdd\s+.*of=\/dev\/(sda|nvme|xvd)/,
  />\s*\/dev\/(sda|nvme|xvd)/,
];

function main() {
  try {
    let data = '';
    try { data = fs.readFileSync(0, 'utf-8'); } catch (_) {}
    const payload = data ? JSON.parse(data) : {};
    const command = payload?.tool_input?.command || '';
    if (!command) { process.exit(0); }
    for (const pat of P0_PATTERNS) {
      if (pat.test(command)) {
        process.stderr.write(
          `[pre-bash-guard] BLOCKED: 检测到灾难命令模式 (${pat})\n` +
          `命令: ${command.slice(0, 200)}\n`
        );
        process.exit(2);
      }
    }
    // v9.9.0: git push 门禁 (stage != ship 不许推, 防 worktree 自动 PR 绕过 review)
    if (/\bgit\s+push\b/.test(command) && !command.includes('ATHENA_ALLOW_PUSH=1')) {
      const stage = findAiStateStage(process.cwd());
      if (stage !== null && stage !== '' && stage !== 'ship') {
        process.stderr.write(
          `[pre-bash-guard] BLOCKED: stage=${stage} != ship, git push 必须走完 review 门禁后在 ship stage 执行.\n` +
          `解锁: 推进到 ship (delivery-gate 过检) 后再 push; 确需绕过加前缀 ATHENA_ALLOW_PUSH=1 (自负责).\n`
        );
        process.exit(2);
      }
    }
    process.exit(0);
  } catch (e) {
    if (e && e.code !== 'MODULE_NOT_FOUND') {
      process.stderr.write(`[pre-bash-guard] non-blocking: ${e.message}\n`);
    }
    process.exit(0);
  }
}

main();

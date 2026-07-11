#!/usr/bin/env node
/**
 * VibeCoding Athena v9.7.0 · CC Stop hook (pace-continuator, 优先级低于 delivery-gate)
 *
 * 职责:
 *   1. 在 _index.md 历史段追加 "stage=X sprint=N turn-end" 条目 (去重 + 裁剪近 10 条)
 *   2. v9.7.0 新: 通过 hookSpecificOutput.additionalContext 输出软提醒
 *      (当前 stage / next_action), 不 block — 软通道补位 hotfix2 删除的 Stop prompt 类型
 *
 * 协议 [官方 code.claude.com/docs/en/hooks]:
 *   - JSON 仅在 exit 0 时解析 (exit 2 时 JSON 被忽略) → 本 hook 恒 exit 0
 *   - additionalContext 放 hookSpecificOutput + hookEventName; 上限 10,000 字符
 *   - Stop 输入含 stop_hook_active (前一个 Stop hook 已续命时为 true)
 */
'use strict';
const fs = require('fs');
const path = require('path');

const HIST_MARKER = '## 历史';
const HIST_KEEP = 10;
const CTX_LIMIT = 9000; // 留余量, 官方上限 10,000

function findAiState(cwd) {
  for (let i = 0, c = cwd; i < 5; i++) {
    const cand = path.join(c, '.ai_state');
    if (fs.existsSync(cand) && fs.statSync(cand).isDirectory()) return cand;
    const p = path.dirname(c);
    if (p === c) return null;
    c = p;
  }
  return null;
}

function readStdin() {
  try { return fs.readFileSync(0, 'utf-8'); } catch (_) { return ''; }
}

function main() {
  let additional = '';
  try {
    let payload = {};
    try { const d = readStdin(); payload = d ? JSON.parse(d) : {}; } catch (_) {}
    const stopHookActive = payload.stop_hook_active === true;

    const aiState = findAiState(process.cwd());
    if (!aiState) { process.exit(0); }
    const idx = path.join(aiState, '_index.md');
    if (!fs.existsSync(idx)) { process.exit(0); }

    let content = fs.readFileSync(idx, 'utf-8');
    const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (!fmMatch) { process.exit(0); }
    const fm = fmMatch[1];
    const stage = (fm.match(/stage:\s*"?([^"\n]+)"?/) || [])[1] || '';
    const sprint = (fm.match(/current_sprint_slug:\s*"?([^"\n]+)"?/) || [])[1] || '';
    const nextAction = (fm.match(/next_action:\s*"?([^"\n]*)"?/) || [])[1] || '';
    if (!stage) { process.exit(0); }

    const entryKey = `stage=${stage} sprint=${sprint || '?'}`;

    // === 1. 历史条目 (去重: stop_hook_active 续命周期内不重复; 最近一条同 key 也不重复) ===
    if (!stopHookActive) {
      const histIdx = content.indexOf(HIST_MARKER);
      let lastEntryKey = '';
      if (histIdx >= 0) {
        const histBlock = content.slice(histIdx);
        const m = histBlock.match(/^- `[^`]+`: (stage=\S+ sprint=\S+)/m);
        if (m) lastEntryKey = m[1];
      }
      if (lastEntryKey !== entryKey) {
        const ts = new Date().toISOString().slice(0, 19).replace('T', ' ');
        const entry = `- \`${ts}\`: ${entryKey} turn-end\n`;
        if (histIdx >= 0) {
          content = content.replace(/(## 历史[^\n]*\n)/, `$1${entry}`);
        } else {
          content += `\n\n## 历史\n${entry}`;
        }
        // 裁剪: 历史段仅保留近 HIST_KEEP 条
        const hi = content.indexOf(HIST_MARKER);
        if (hi >= 0) {
          const head = content.slice(0, hi);
          const histLines = content.slice(hi).split('\n');
          const kept = [];
          let count = 0;
          for (const line of histLines) {
            if (/^- `/.test(line)) {
              if (count < HIST_KEEP) { kept.push(line); count++; }
            } else {
              kept.push(line);
            }
          }
          content = head + kept.join('\n');
        }
        fs.writeFileSync(idx, content, 'utf-8');
      }
    }

    // === 2. 软提醒 (additionalContext) ===
    // 官方: Stop hook 输出 additionalContext 不是 block, 但会让对话"继续一轮再自然停止"
    // (code.claude.com/docs/en/hooks: "the conversation continues so Claude can act on the feedback").
    // 故必须按 stop_hook_active 关闸 — 仅在首次自然停止 (stopHookActive=false) 提醒一次;
    // 否则续跑后的每个 Stop 都重复喂同一段 → 永远停不下来 → 撞 CLAUDE_CODE_STOP_HOOK_BLOCK_CAP 被强停.
    if (!stopHookActive) {
      const hints = [];
      if (nextAction) {
        hints.push(`next_action="${nextAction}" 未消费 — 下一 turn 应按 athena-dev 的 next_action 表处理.`);
      }
      if (stage === 'review') {
        hints.push('review stage: reviewer/spec 返回后由主 agent 合并最新 reviews/passN.md, evaluator 后跑; 只有最终 PASS 才推进.');
      }
      if (hints.length > 0) {
        additional = `[pace-continuator] stage=${stage}${sprint ? ` sprint=${sprint}` : ''}\n` + hints.join('\n');
      }
    }
  } catch (e) {
    process.stderr.write(`[pace-continuator] non-blocking: ${e.message}\n`);
  }

  // 恒 exit 0; 有软提醒才输出 JSON (stdout 必须是纯 JSON 或空)
  if (additional) {
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'Stop',
        additionalContext: additional.slice(0, CTX_LIMIT),
      },
    }));
  }
  process.exit(0);
}
main();

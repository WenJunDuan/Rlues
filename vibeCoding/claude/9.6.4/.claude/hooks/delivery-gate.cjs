#!/usr/bin/env node
/**
 * VibeCoding Athena v9.6.2 · CC Stop hook (delivery-gate)
 *
 * 触发: 主 agent stop 前
 * 职责:
 * 1. (v9.6.2 新) Refactor/System + stage=ship → 强制检查 cleanup-pass-{sprint}.md
 * 2. PACE 状态机基本合规检查
 *
 * Stop hook 输出协议 (v9.6.1 hotfix2 起):
 * - 用 top-level `decision: "block"`, 不是 `hookSpecificOutput.stopDecision`
 * - 源: https://docs.anthropic.com/en/docs/claude-code/hooks#stop
 */
'use strict';

const fs = require('fs');
const path = require('path');

const EXIT_SUCCESS = 0;
const EXIT_BLOCK = 2;

const REFACTOR_SYSTEM = new Set(['Refactor', 'System']);

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

function parseFrontmatter(content) {
  if (!content.startsWith('---')) return {};
  const parts = content.split('---', 3);
  if (parts.length < 3) return {};
  const fm = {};
  for (const line of parts[1].split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const m = trimmed.match(/^([\w\-_.]+)\s*:\s*(.*)$/);
    if (m) {
      let v = m[2].trim();
      if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
      fm[m[1]] = v;
    }
  }
  return fm;
}

function blockResponse(reason) {
  const output = { decision: 'block', reason };
  process.stderr.write(reason + '\n');
  console.log(JSON.stringify(output));
  return EXIT_BLOCK;
}

function main() {
  try {
    const cwd = process.cwd();
    const aiState = findAiState(cwd);
    if (!aiState) return EXIT_SUCCESS;

    const idx = path.join(aiState, '_index.md');
    if (!fs.existsSync(idx)) return EXIT_SUCCESS;

    const content = fs.readFileSync(idx, 'utf-8');
    const fm = parseFrontmatter(content);

    const pathType = fm.path || '';
    const stage = fm.stage || '';
    const sprintSlug = fm.current_sprint_slug || '';
    const designChanged = (fm.design_changed_after_impl || 'false').toString().toLowerCase() === 'true';
    const skipArch = (fm.skip_architecture_check || 'false').toString().toLowerCase() === 'true';

    // === v9.6.4: design 改后未 re-review, ship 前 block ===
    if (stage === 'ship' && designChanged) {
      return blockResponse(
        `[delivery-gate] design.md 在 impl/review/polish 后被修改, ship 前必须重新 review.\n` +
        `重跑 reviewer + spec-compliance + evaluator, 然后清空 _index.design_changed_after_impl=false.\n`
      );
    }

    // === v9.6.4: Refactor/System ship 前必须有 cleanup-pass.md (新路径) ===
    if (REFACTOR_SYSTEM.has(pathType) && stage === 'ship' && sprintSlug) {
      const cleanupFile = path.join(aiState, 'sprints', sprintSlug, 'cleanup-pass.md');
      if (!fs.existsSync(cleanupFile)) {
        return blockResponse(
          `[delivery-gate] Refactor/System 路径必须先完成 polish stage.\n` +
          `运行 /polish 生成 ${path.relative(cwd, cleanupFile)}\n`
        );
      }
    }

    // === v9.6.4: Refactor/System (≥5 文件) ship 前必须更新 architecture/ (铁律 15) ===
    if (REFACTOR_SYSTEM.has(pathType) && stage === 'ship' && sprintSlug && !skipArch) {
      const evidenceFile = path.join(aiState, 'sprints', sprintSlug, 'evidence.yaml');
      let changedFiles = 0;
      if (fs.existsSync(evidenceFile)) {
        const ev = fs.readFileSync(evidenceFile, 'utf-8');
        const seen = new Set();
        for (const m of ev.matchAll(/^\s*file:\s*["']?([^"\n]+)["']?/gm)) {
          seen.add(m[1].trim());
        }
        changedFiles = seen.size;
      }
      if (changedFiles >= 5) {
        const archDir = path.join(aiState, 'architecture');
        const hasArch = fs.existsSync(archDir) &&
          fs.readdirSync(archDir).some(f => f.endsWith('.md'));
        if (!hasArch) {
          return blockResponse(
            `[delivery-gate] 铁律 15: Refactor/System (改了 ${changedFiles} 文件) ship 前必须更新 architecture/.\n` +
            `运行 /architect-doc update. (不需要则设 _index.skip_architecture_check=true)\n`
          );
        }
      }
    }

    // === v9.6.4-hotfix2: ship 前 spec-compliance 门禁 ===
    // 后台架构下, review agent 后台跑; 主 agent 监控到完成后才推进 stage=ship.
    // 所以 ship 时 pass1.md 必然已存在 → 此处检查安全, 不会死锁 (区别于 review stage 边跑边等).
    // 仅 Feature/Refactor/System 路径要求 (Hotfix/Bugfix/Quick 无 design.md, 跳过).
    if (['Feature', 'Refactor', 'System'].includes(pathType) && stage === 'ship' && sprintSlug) {
      const pass1 = path.join(aiState, 'sprints', sprintSlug, 'reviews', 'pass1.md');
      if (!fs.existsSync(pass1)) {
        return blockResponse(
          `[delivery-gate] ${pathType} 路径 ship 前必须完成 review.\n` +
          `reviews/pass1.md 不存在 — 等后台 review agent 写完再推进 stage=ship.\n`
        );
      }
      const pass1Content = fs.readFileSync(pass1, 'utf-8');
      if (!pass1Content.includes('## Spec Compliance')) {
        return blockResponse(
          `[delivery-gate] pass1.md 缺 '## Spec Compliance' 段.\n` +
          `spec-compliance subagent 未跑或未写完 — 检查后台 agent, 补齐后再 ship.\n`
        );
      }
    }

    // 注意: review stage 本身不设任何 Stop / delivery 门禁.
    // 后台 review agent 写产物是异步的, 任何"等 pass1.md"的同步门都会死锁.
    // 门禁统一放在 ship stage (主 agent 主动推进, 此时产物已落盘).

    // === pace 状态机基本合规 (8 stage) ===
    const validStages = new Set(['brainstorm', 'roadmap', 'plan', 'design', 'impl', 'review', 'polish', 'ship']);
    if (stage && !validStages.has(stage)) {
      process.stderr.write(
        `[delivery-gate] warning: 未知 stage '${stage}', 期望 ${[...validStages].join('|')}\n`
      );
    }

    return EXIT_SUCCESS;
  } catch (e) {
    if (e.code !== 'MODULE_NOT_FOUND') {
      process.stderr.write(`[delivery-gate] warning (non-blocking): ${e.message}\n`);
    }
    return EXIT_SUCCESS;
  }
}

process.exit(main());

#!/usr/bin/env node
/**
 * VibeCoding Athena v9.8.0 · CC Stop hook (delivery-gate)
 *
 * 触发: 主 agent stop 前
 * 职责:
 * 1. Refactor/System + stage=ship → 强制检查 cleanup-pass.md
 * 2. Refactor/System (≥5 文件) + ship → architecture/ 必须存在 (铁律[架构])
 * 3. design_changed_after_impl + ship → block (需重新 review)
 * 4. Feature/Refactor/System + ship → pass1.md 含 '## Spec Compliance'
 * 5. v9.8.0: Refactor/System + ship → runtime-verify.md 必须存在且含实跑证据 (Loop Engineering CHECKER)
 * 6. PACE 状态机基本合规检查
 *
 * v9.7.0 协议 [官方 code.claude.com/docs/en/hooks]:
 * - JSON 仅在 exit 0 时解析; exit 2 时 JSON 被忽略 → block 统一为 exit 0 + {decision:"block", reason}
 * - 读 Stop 输入 background_tasks (2.1.145+) 感知后台 review agent 状态, 字段缺失静默跳过
 * - block reason 必须含明确解锁动作 (Stop 连续 block 上限由 CLAUDE_CODE_STOP_HOOK_BLOCK_CAP 控制)
 */
'use strict';

const fs = require('fs');
const path = require('path');

const EXIT_SUCCESS = 0;

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
  // 官方: exit 0 + JSON 才被解析; reason 直接喂给 Claude 作为续跑指示
  process.stderr.write(reason + '\n');
  console.log(JSON.stringify({ decision: 'block', reason }));
  return EXIT_SUCCESS;
}

function readStdinPayload() {
  try {
    const data = fs.readFileSync(0, 'utf-8');
    return data ? JSON.parse(data) : {};
  } catch (_) {
    return {};
  }
}

function runningBackgroundTasks(payload) {
  const tasks = payload && Array.isArray(payload.background_tasks) ? payload.background_tasks : [];
  return tasks.filter(t => {
    const s = ((t && (t.status || t.state)) || '').toString().toLowerCase();
    return s === 'running' || s === 'pending' || s === 'in_progress';
  });
}

function main() {
  try {
    const payload = readStdinPayload();
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
    const rtSkip = (fm.skip_runtime_verify || 'false').toString().toLowerCase() === 'true';

    // === design 改后未 re-review, ship 前 block ===
    if (stage === 'ship' && designChanged) {
      return blockResponse(
        `[delivery-gate] design.md 在 impl/review/polish 后被修改, ship 前必须重新 review.\n` +
        `解锁动作: 重跑 reviewer + spec-compliance + evaluator, 然后设 _index.design_changed_after_impl=false.\n`
      );
    }

    // === v9.8.0: Bugfix ship 前必须有 fix-note.md (issue 流程最小问责; 原 Bugfix 零门禁) ===
    if (pathType === 'Bugfix' && stage === 'ship' && sprintSlug) {
      const fixNote = path.join(aiState, 'sprints', sprintSlug, 'fix-note.md');
      if (!fs.existsSync(fixNote)) {
        return blockResponse(
          `[delivery-gate] Bugfix ship 前必须有 fix-note.md (改了什么 + 怎么验证的).\n` +
          `解锁动作: 运行 /athena-issue 写 ${path.relative(cwd, fixNote)} (含验证命令 + 输出).\n`
        );
      }
    }

    // === v9.8.0: Refactor/System ship 前必须有 runtime-verify.md (Loop Engineering CHECKER) ===
    // runtime-verify 在 polish 之前发生, 故在 cleanup-pass 检查之前先验.
    if (REFACTOR_SYSTEM.has(pathType) && stage === 'ship' && sprintSlug && !rtSkip) {
      const rtFile = path.join(aiState, 'sprints', sprintSlug, 'runtime-verify.md');
      if (!fs.existsSync(rtFile)) {
        return blockResponse(
          `[delivery-gate] Loop Engineering: Refactor/System ship 前必须完成 runtime-verify (运行时自测自改).\n` +
          `解锁动作: 运行 /athena-runtime-verify 生成 ${path.relative(cwd, rtFile)} (用 /goal 承载实跑).\n` +
          `(确实无可运行环境则设 _index.skip_runtime_verify=true 跳过, 不推荐)\n`
        );
      }
      const rtContent = fs.readFileSync(rtFile, 'utf-8');
      if (!rtContent.includes('## 测试场景')) {
        return blockResponse(
          `[delivery-gate] runtime-verify.md 缺 '## 测试场景 (实跑)' 段 (或仍是空模板).\n` +
          `解锁动作: 在 runtime-verify 环里把实跑命令+输出晒进 runtime-verify.md 再 ship.\n`
        );
      }
    }

    // === Refactor/System ship 前必须有 cleanup-pass.md ===
    if (REFACTOR_SYSTEM.has(pathType) && stage === 'ship' && sprintSlug) {
      const cleanupFile = path.join(aiState, 'sprints', sprintSlug, 'cleanup-pass.md');
      if (!fs.existsSync(cleanupFile)) {
        return blockResponse(
          `[delivery-gate] Refactor/System 路径必须先完成 polish stage.\n` +
          `解锁动作: 运行 /polish 生成 ${path.relative(cwd, cleanupFile)}\n`
        );
      }
    }

    // === Refactor/System (≥5 文件) ship 前必须更新 architecture/ (铁律[架构]) ===
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
            `[delivery-gate] 铁律[架构]: Refactor/System (改了 ${changedFiles} 文件) ship 前必须更新 architecture/.\n` +
            `解锁动作: 运行 /architect-doc update. (不需要则设 _index.skip_architecture_check=true)\n`
          );
        }
      }
    }

    // === ship 前 spec-compliance 门禁 ===
    // 仅 Feature/Refactor/System 路径要求 (Hotfix/Bugfix/Quick 无 design.md, 跳过).
    if (['Feature', 'Refactor', 'System'].includes(pathType) && stage === 'ship' && sprintSlug) {
      const pass1 = path.join(aiState, 'sprints', sprintSlug, 'reviews', 'pass1.md');
      if (!fs.existsSync(pass1)) {
        const running = runningBackgroundTasks(payload);
        const bgHint = running.length > 0
          ? `检测到 ${running.length} 个后台任务仍在运行 — 等它们完成 (产物落盘) 后再推进 stage=ship.\n`
          : `reviews/pass1.md 不存在 — 先跑 review 三件套, 产物落盘后再推进 stage=ship.\n`;
        return blockResponse(
          `[delivery-gate] ${pathType} 路径 ship 前必须完成 review.\n解锁动作: ${bgHint}`
        );
      }
      const pass1Content = fs.readFileSync(pass1, 'utf-8');
      if (!pass1Content.includes('## Spec Compliance')) {
        return blockResponse(
          `[delivery-gate] pass1.md 缺 '## Spec Compliance' 段.\n` +
          `解锁动作: spawn spec-compliance subagent 补齐该段后再 ship.\n`
        );
      }
    }

    // === pace 状态机基本合规 (8 stage; v9.8.0 加 runtime-verify) ===
    const validStages = new Set(['brainstorm', 'roadmap', 'plan', 'design', 'impl', 'runtime-verify', 'review', 'polish', 'ship']);
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

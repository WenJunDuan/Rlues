#!/usr/bin/env node
// VibeCoding Kernel v9.3.8 — Stop: 交付质量门控
// 检查 .ai_state/ JSON 状态, 决定是否允许交付
// 与 prompt hook (Haiku 语义评估) 互补: 本 hook 做确定性检查
'use strict';

const fs = require('fs');
const path = require('path');

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);

    // ── 防循环: stop_hook_active 时放行 ──
    if (data.stop_hook_active) {
      return process.exit(0);
    }

    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const stateDir = path.join(projectDir, '.ai_state');

    // 无 .ai_state/ → 非 VibeCoding 项目或全新项目 → 放行
    if (!fs.existsSync(stateDir)) {
      return process.exit(0);
    }

    // ── 读 state.json ──
    let state = {};
    try {
      state = JSON.parse(fs.readFileSync(path.join(stateDir, 'state.json'), 'utf8'));
    } catch {
      return process.exit(0); // 无状态 → 放行
    }

    // Sprint 0 (未初始化) → 放行
    if (!state.sprint || state.sprint === 0) {
      return process.exit(0);
    }

    // Path A (快速修复) → 宽松检查
    if (state.path === 'A') {
      return process.exit(0);
    }

    const issues = [];

    // ── 检查 feature_list.json 完成度 ──
    try {
      const features = JSON.parse(fs.readFileSync(path.join(stateDir, 'feature_list.json'), 'utf8'));
      if (Array.isArray(features) && features.length > 0) {
        const incomplete = features.filter(f => f.status !== 'done' && f.status !== 'blocked');
        if (incomplete.length > 0) {
          issues.push(`${incomplete.length} 个 Feature 未完成: ${incomplete.map(f => f.id).join(', ')}`);
        }
      }
    } catch {}

    // ── 检查 quality.json 评分 ──
    try {
      const quality = JSON.parse(fs.readFileSync(path.join(stateDir, 'quality.json'), 'utf8'));
      if (quality.average > 0) {
        if (quality.verdict === 'FAIL') {
          issues.push(`Quality Gate FAIL (均分: ${quality.average})`);
        } else if (quality.verdict === 'REWORK') {
          issues.push(`Quality Gate REWORK (均分: ${quality.average}) — 需返回 E 阶段重做`);
        }
      }
    } catch {}

    // ── 无问题 → 放行 ──
    if (issues.length === 0) {
      return process.exit(0);
    }

    // ── 有问题 → 阻断交付 ──
    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'Stop',
        stopDecision: 'block',
        stopDecisionReason: `[delivery-gate] 交付被阻断:\n${issues.map(i => '• ' + i).join('\n')}\n\n请修复上述问题后再次尝试交付。`
      }
    }));
    process.exit(0);

  } catch (e) {
    // 解析失败 → 放行 (不阻断正常工作)
    process.exit(0);
  }
});

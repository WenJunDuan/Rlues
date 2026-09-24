#!/usr/bin/env node
'use strict';

// delivery-gate.cjs — Stop hook: 质量门控
// 检查 4 项 (任一失败 → 阻断):
// 1. tasks.md 中是否有未完成的待办 (Sisyphus)
// 2. reviews/ 目录中是否有当前 Sprint 的审查报告
// 3. 审查报告中是否有外部模型 review 记录
// 4. 审查报告中是否有测试通过记录
// Path A 豁免: 只做宽松检查

const fs = require('fs');
const path = require('path');

const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const stateDir = path.join(projectDir, '.ai_state');

// 读 stdin (CC 传入 hook input)
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  try {
    const hookInput = JSON.parse(input);
    // stop_hook_active = true → 已经在 Stop hook 链中, 放行避免循环
    if (hookInput.stop_hook_active) {
      process.exit(0);
      return;
    }
  } catch (e) { /* ignore parse errors */ }

  const issues = [];

  // ── 读 project.json ──
  let project = { path: '', stage: '', sprint: 0 };
  try {
    project = JSON.parse(fs.readFileSync(path.join(stateDir, 'project.json'), 'utf8'));
  } catch (e) {
    // 无 project.json → 新项目或非 VibeCoding 项目, 放行
    process.exit(0);
    return;
  }

  // Sprint 0 或无 stage → 还没开始工作, 放行
  if (!project.sprint || !project.stage) {
    process.exit(0);
    return;
  }

  // Path A → 宽松: 只要 stage 是 T 就放行
  if (project.path === 'A') {
    process.exit(0);
    return;
  }

  // ── 检查 1: tasks.md 未完成的待办 ──
  try {
    const tasks = fs.readFileSync(path.join(stateDir, 'tasks.md'), 'utf8');
    const pending = (tasks.match(/^- \[ \]/gm) || []).length;
    if (pending > 0) {
      issues.push(`${pending} 个 Task 未完成 (Sisyphus: 全部完成才能交付)`);
    }
  } catch (e) {
    issues.push('tasks.md 不存在');
  }

  // ── 检查 2: 审查报告存在 ──
  const reviewDir = path.join(stateDir, 'reviews');
  const sprintFile = path.join(reviewDir, `sprint-${project.sprint}.md`);
  let reviewContent = '';
  try {
    reviewContent = fs.readFileSync(sprintFile, 'utf8');
  } catch (e) {
    issues.push(`审查报告 reviews/sprint-${project.sprint}.md 不存在`);
  }

  // ── 检查 3: 外部模型 review 记录 ──
  if (reviewContent) {
    const hasExternalReview = /codex:review|codex:result|adversarial|ecc-agentshield/i.test(reviewContent);
    if (!hasExternalReview) {
      issues.push('审查报告中无外部模型 review 记录 (至少需要 codex:review)');
    }
  }

  // ── 检查 4: 测试通过记录 ──
  if (reviewContent) {
    const hasTestResult = /测试|test|通过|pass|✅|PASS/i.test(reviewContent);
    if (!hasTestResult) {
      issues.push('审查报告中无测试通过记录');
    }
  }

  // ── 检查 5: VERDICT ──
  if (reviewContent) {
    const verdictMatch = reviewContent.match(/VERDICT:\s*(PASS|CONCERNS|REWORK|FAIL)/i);
    if (verdictMatch) {
      const verdict = verdictMatch[1].toUpperCase();
      if (verdict === 'REWORK') {
        issues.push('VERDICT 为 REWORK — 需返回 E 阶段重做');
      } else if (verdict === 'FAIL') {
        issues.push('VERDICT 为 FAIL — 需返回 D 阶段重新设计');
      } else if (verdict === 'CONCERNS') {
        issues.push('VERDICT 为 CONCERNS — 需修复问题后重新评分');
      }
    }
  }

  // ── 输出 ──
  if (issues.length > 0) {
    const reason = `[delivery-gate] 交付被阻断:\n${issues.map(i => `• ${i}`).join('\n')}\n\n请修复后再尝试交付。`;
    const output = {
      hookSpecificOutput: {
        hookEventName: 'Stop',
        stopDecision: 'block',
        stopDecisionReason: reason
      }
    };
    process.stdout.write(JSON.stringify(output));
  }

  process.exit(0);
});

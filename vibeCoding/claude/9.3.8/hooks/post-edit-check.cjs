#!/usr/bin/env node
// VibeCoding Kernel v9.3.8 — PostToolUse Edit|Write: 状态文件一致性检查
// 当 .ai_state/ 下的 JSON 被修改时, 验证格式正确性
'use strict';

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => input += d);
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const filePath = (data.tool_input && (data.tool_input.file_path || data.tool_input.path)) || '';

    // 只关心 .ai_state/ 下的文件
    if (!filePath.includes('.ai_state/')) {
      return process.exit(0);
    }

    const fs = require('fs');
    const warnings = [];

    // JSON 文件格式检查
    if (filePath.endsWith('.json')) {
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        const parsed = JSON.parse(content);

        // feature_list.json 必须是数组
        if (filePath.includes('feature_list.json') && !Array.isArray(parsed)) {
          warnings.push('feature_list.json 应该是数组格式 []');
        }

        // quality.json 必须有 scores 和 verdict
        if (filePath.includes('quality.json')) {
          if (parsed.average > 0 && !parsed.verdict) {
            warnings.push('quality.json 有评分但缺少 verdict');
          }
        }

        // state.json path 必须是 A/B/C/D 之一
        if (filePath.includes('state.json')) {
          if (parsed.path && !['A', 'B', 'C', 'D', ''].includes(parsed.path)) {
            warnings.push(`state.json path 值无效: "${parsed.path}" (应为 A/B/C/D)`);
          }
        }
      } catch (e) {
        warnings.push(`JSON 解析失败: ${e.message}`);
      }
    }

    if (warnings.length > 0) {
      process.stderr.write(`[post-edit-check] ${warnings.join('; ')}`);
    }

    process.exit(0);
  } catch {
    process.exit(0);
  }
});

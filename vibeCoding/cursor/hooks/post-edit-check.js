#!/usr/bin/env node
// VibeCoding v3.0-cursor — afterFileEdit: 仅检查新增内容
// 位置: ~/.cursor/hooks/post-edit-check.js
//
// Cursor afterFileEdit 协议:
//   stdin: { file_path, edits: [{old_string, new_string}], workspace_roots }
//   观察型 hook，不能阻断编辑
//   stderr 输出显示在 Cursor Settings → Hooks 面板
//
// 设计原则:
//   - 只检查 edits 中的 new_string（Agent 新写的内容），不扫全文件
//   - 避免对已有代码产生噪音
//   - 只报高置信度问题

const fs = require('fs');
const path = require('path');

try {
  const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
  const filePath = input.file_path || '';
  const edits = input.edits || [];

  if (!filePath || edits.length === 0) process.exit(0);

  // 拼接所有新增内容
  const newContent = edits.map(e => e.new_string || '').join('\n');
  if (!newContent.trim()) process.exit(0);

  const warnings = [];
  const ext = path.extname(filePath).toLowerCase();

  // 检查 1: 新增内容中的 TODO/FIXME/HACK
  const todoMatches = newContent.match(/\b(?:TODO|FIXME|HACK|XXX)\b/gi);
  if (todoMatches && todoMatches.length > 0) {
    warnings.push(`新增 ${todoMatches.length} 个 TODO/FIXME`);
  }

  // 检查 2: 新增的调试语句（JS/TS）
  if (['.js', '.ts', '.jsx', '.tsx', '.mjs', '.cjs'].includes(ext)) {
    const debugLogs = newContent.match(/console\.(log|debug)\(/g);
    if (debugLogs && debugLogs.length > 0) {
      warnings.push(`新增 ${debugLogs.length} 个 console.log`);
    }
  }

  // 检查 3: 新增的 Python 调试语句
  if (ext === '.py') {
    const breakpoints = newContent.match(/\bbreakpoint\s*\(\)/g);
    if (breakpoints && breakpoints.length > 0) {
      warnings.push(`新增 ${breakpoints.length} 个 breakpoint()`);
    }
  }

  // 检查 4: 新增内容中的硬编码密钥（高置信度模式）
  if (/(?:password|secret|api_key|apikey|private_key)\s*[:=]\s*['"][A-Za-z0-9+/=_-]{16,}['"]/i.test(newContent)) {
    warnings.push('⚠️ 新增内容疑似硬编码密钥');
  }

  if (warnings.length > 0) {
    const fileName = path.basename(filePath);
    process.stderr.write(`[VibeCoding] ${fileName}: ${warnings.join('; ')}\n`);
  }

  process.exit(0);
} catch (e) {
  process.exit(0);
}

#!/usr/bin/env node
// VibeCoding v3.0-cursor — afterFileEdit: 编辑后质量检查
// 位置: ~/.cursor/hooks/post-edit-check.js
//
// Cursor afterFileEdit 协议：
//   stdin:  { file_path, edits: [{old_string, new_string}], workspace_roots, ... }
//   stdout: 无响应协议（观察型，不能阻断）
//   stderr: 日志输出，显示在 Cursor Settings → Hooks 面板

const fs = require('fs');
const path = require('path');

try {
  const input = JSON.parse(fs.readFileSync('/dev/stdin', 'utf8'));
  const filePath = input.file_path || '';
  const workspaceRoot = (input.workspace_roots || [])[0] || '';

  if (!filePath) process.exit(0);

  // 解析绝对路径：file_path 可能是相对于 workspace_root 的
  const absPath = path.isAbsolute(filePath)
    ? filePath
    : path.join(workspaceRoot, filePath);

  if (!fs.existsSync(absPath)) process.exit(0);

  const content = fs.readFileSync(absPath, 'utf8');
  const warnings = [];
  const ext = path.extname(absPath).toLowerCase();

  // 检查 1: TODO/FIXME/HACK 标记
  const todoMatches = content.match(/\b(?:TODO|FIXME|HACK|XXX)\b/gi);
  if (todoMatches && todoMatches.length > 0) {
    warnings.push(`${todoMatches.length} 个 TODO/FIXME`);
  }

  // 检查 2: 调试语句（JS/TS/JSX/TSX）
  if (['.js', '.ts', '.jsx', '.tsx'].includes(ext)) {
    const debugLogs = content.match(/console\.(log|debug)\(/g);
    if (debugLogs && debugLogs.length > 3) {
      warnings.push(`${debugLogs.length} 个 console.log 疑似调试`);
    }
  }

  // 检查 3: Python 调试语句
  if (ext === '.py') {
    const prints = content.match(/\bprint\s*\(/g);
    const breakpoints = content.match(/\bbreakpoint\s*\(\)/g);
    if (breakpoints && breakpoints.length > 0) {
      warnings.push(`${breakpoints.length} 个 breakpoint()`);
    }
    if (prints && prints.length > 5) {
      warnings.push(`${prints.length} 个 print() 疑似调试`);
    }
  }

  // 检查 4: 硬编码密钥
  if (/(?:password|secret|api_key|apikey|token|private_key)\s*[:=]\s*['"][^'"]{8,}['"]/i.test(content)) {
    warnings.push('⚠️ 疑似硬编码密钥');
  }

  // 检查 5: 文件过大
  const lineCount = content.split('\n').length;
  if (lineCount > 500) {
    warnings.push(`${lineCount} 行，建议拆分`);
  }

  if (warnings.length > 0) {
    const fileName = path.basename(absPath);
    process.stderr.write(`[VibeCoding] ${fileName}: ${warnings.join('; ')}\n`);
  }

  process.exit(0);
} catch (e) {
  // 静默退出
  process.exit(0);
}

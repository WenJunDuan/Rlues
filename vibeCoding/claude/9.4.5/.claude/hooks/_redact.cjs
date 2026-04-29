'use strict';
// VibeCoding redaction helper (CC 端)
// 用于 lesson-drafter 和 delivery-gate / permission-request / subagent-retry 的 hook-trace 写入
// 在持久化任何包含工具输出 / 用户命令 / stderr 的字符串前调用

const PATTERNS = [
  // Authorization headers (Bearer / Basic)
  [/(authorization\s*[:=]\s*)(bearer|basic)\s+[^\s'"]+/gi, '$1$2 [REDACTED]'],

  // 通用 key=value (shell) 或 "key": "value" (json) 形式
  [/\b(api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|token)\b([\s'"]*[:=][\s'"]*)([^\s'"]{6,})/gi,
   '$1$2[REDACTED]'],

  // OpenAI / Anthropic API keys
  [/sk-[a-zA-Z0-9_-]{20,}/g, '[REDACTED-AI-KEY]'],
  [/sk-ant-[a-zA-Z0-9_-]{20,}/g, '[REDACTED-AI-KEY]'],

  // GitHub tokens
  [/gh[psour]_[a-zA-Z0-9]{30,}/g, '[REDACTED-GH-TOKEN]'],

  // AWS access keys
  [/AKIA[0-9A-Z]{16}/g, '[REDACTED-AWS-KEY]'],
  [/(aws_secret_access_key\s*=\s*)[a-zA-Z0-9/+=]{30,}/gi, '$1[REDACTED]'],

  // JWT (3 段 base64.base64.base64, 各段 ≥ 16 字符) — 头/中/尾段
  [/\beyJ[a-zA-Z0-9_-]{16,}\.[a-zA-Z0-9_-]{16,}\.[a-zA-Z0-9_-]{16,}/g, '[REDACTED-JWT]'],

  // SSH 私钥块
  [/-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----/g, '[REDACTED-PRIVATE-KEY]'],

  // 形如 ghp_xxxx 短前缀的 generic token (40 char hex/base62)
  [/\b[A-Fa-f0-9]{40,}\b/g, (m) => m.length >= 40 ? '[REDACTED-HEX-TOKEN]' : m],
];

function redact(text) {
  if (typeof text !== 'string' || !text) return text;
  let out = text;
  for (const [pat, repl] of PATTERNS) {
    out = out.replace(pat, repl);
  }
  return out;
}

module.exports = { redact };

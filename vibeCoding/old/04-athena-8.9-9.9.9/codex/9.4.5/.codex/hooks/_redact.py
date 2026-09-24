#!/usr/bin/env python3
"""
VibeCoding redaction helper (Codex 端)
用于 lesson-drafter 和 delivery-gate / permission-request / subagent-retry / user-prompt-submit 的 hook-trace 写入。
在持久化任何包含工具输出 / 用户命令 / stderr 的字符串前调用。
"""
import re

PATTERNS = [
    # Authorization headers
    (re.compile(r'(authorization\s*[:=]\s*)(bearer|basic)\s+[^\s\'"]+', re.IGNORECASE),
     r'\1\2 [REDACTED]'),

    # 通用 key=value (shell) 或 "key": "value" (json) 形式
    # \b key \b 然后 灵活分隔符 [\s'":=]+ 然后 value
    (re.compile(r'\b(api[_-]?key|secret[_-]?key|access[_-]?token|refresh[_-]?token|password|passwd|secret|token)\b'
                r'([\s\'"]*[:=][\s\'"]*)'
                r'([^\s\'"]{6,})',
                re.IGNORECASE),
     r'\1\2[REDACTED]'),

    # OpenAI / Anthropic API keys
    (re.compile(r'sk-[a-zA-Z0-9_\-]{20,}'), '[REDACTED-AI-KEY]'),
    (re.compile(r'sk-ant-[a-zA-Z0-9_\-]{20,}'), '[REDACTED-AI-KEY]'),

    # GitHub tokens
    (re.compile(r'gh[psour]_[a-zA-Z0-9]{30,}'), '[REDACTED-GH-TOKEN]'),

    # AWS
    (re.compile(r'AKIA[0-9A-Z]{16}'), '[REDACTED-AWS-KEY]'),
    (re.compile(r'(aws_secret_access_key\s*=\s*)[a-zA-Z0-9/+=]{30,}', re.IGNORECASE),
     r'\1[REDACTED]'),

    # JWT
    (re.compile(r'\beyJ[a-zA-Z0-9_\-]{16,}\.[a-zA-Z0-9_\-]{16,}\.[a-zA-Z0-9_\-]{16,}'),
     '[REDACTED-JWT]'),

    # SSH 私钥块
    (re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----'),
     '[REDACTED-PRIVATE-KEY]'),

    # 40+ 字符 hex (generic high-entropy)
    (re.compile(r'\b[A-Fa-f0-9]{40,}\b'), '[REDACTED-HEX-TOKEN]'),
]


def redact(text):
    if not isinstance(text, str) or not text:
        return text
    out = text
    for pat, repl in PATTERNS:
        out = pat.sub(repl, out)
    return out


if __name__ == "__main__":
    # CLI smoke test
    import sys
    test = sys.stdin.read()
    print(redact(test))

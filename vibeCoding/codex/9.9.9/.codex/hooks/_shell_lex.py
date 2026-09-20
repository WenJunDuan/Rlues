"""Quote-aware control-operator scan for validation-status evidence policy.

scan(command) returns each segment body with the control operator that follows it
('' on the last). Not an AST: no expansion, no heredocs.
"""
from __future__ import annotations


# '&' backgrounds only outside a redirection: 2>&1, >&2, <&0, &>f and &>>f keep it
# inside the segment. '&&' and '|&' are matched as pairs before this is consulted.
def _redirection_ampersand(command: str, i: int) -> bool:
    return (i > 0 and command[i - 1] in '><') or (i + 1 < len(command) and command[i + 1] == '>')


def _control_at(text: str, i: int) -> tuple[str | None, int]:
    pair = text[i:i + 2]
    if pair in ('&&', '||', '|&'):
        return pair, i + 2
    ch = text[i]
    if ch in ';\n|':
        return ch, i + 1
    if ch == '&' and not _redirection_ampersand(text, i):
        return '&', i + 1
    return None, i


def scan(command: str) -> list[dict[str, str]]:
    segments: list[dict[str, str]] = []
    buf: list[str] = []
    quote = ''
    escaped = False
    text = command or ''

    def push(op: str) -> None:
        body = ''.join(buf).strip()
        buf.clear()
        if body:
            segments.append({'text': body, 'op': op})

    i = 0
    while i < len(text):
        ch = text[i]
        if escaped:
            buf.append(ch); escaped = False; i += 1; continue
        if ch == '\\' and quote != "'":
            buf.append(ch); escaped = True; i += 1; continue
        if quote:
            if ch == quote:
                quote = ''
            buf.append(ch); i += 1; continue
        if ch in "'\"":
            quote = ch; buf.append(ch); i += 1; continue
        op, nxt = _control_at(text, i)
        if op is not None:
            push(op); i = nxt; continue
        buf.append(ch); i += 1
    push('')
    return segments

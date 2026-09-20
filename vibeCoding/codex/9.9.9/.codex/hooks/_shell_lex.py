"""Quote-aware control-operator scan for validation-status evidence policy.

scan(command) returns each segment body with the control operator that follows it
('' on the last). Not an AST: no expansion, no heredocs.

simple_heredoc(command) is the single source deciding whether a command opens a
heredoc of the narrow whitelist form; the Bash guard and scan() both consume it.
"""
from __future__ import annotations

import re

# Consumers whose standard input is data, not shell code. The guard has no
# deliberate defence on these channels — writing the same bytes with the Write
# tool never reaches a hook at all — so treating such a body as text removes
# nothing. Shells and wrappers (sudo/env/timeout/nice/…) are not enumerable, so
# everything outside this set keeps today's behaviour: over-block, never under-block.
_CONSUMERS = frozenset({'python3', 'python', 'node', 'tee', 'cat'})

# Closed grammar the whole first line must match, anchored at both ends:
#   LINE  = TOKEN (SP+ TOKEN)* SP* '<<' '-'? SP* DELIM SP* EOL
#   TOKEN = WORD | VAR | REDIR
#   WORD  = [A-Za-z0-9_.,/=+:@%-]+
#   VAR   = '$' NAME          (a bare expansion is substituted after the line is
#                              lexed, so it cannot move a token boundary)
#   REDIR = [0-9]? ('>' | '>>') (WORD | '&' [0-9])?   |   [0-9]? '<' WORD
#   DELIM = "'" NAME "'" | '"' NAME '"' | NAME ;  NAME = [A-Za-z_][A-Za-z0-9_]*
# The grammar admits no ( ) [ ] { } ` \ # ; | & and no expansion operator, so every
# context in which bash reads '<<' as a left shift or as literal text — arithmetic
# commands and expansions, array subscripts, ${…} bodies and substring offsets — is
# refused at the door instead of being enumerated and blacklisted one form at a time.
_WORD = r'[A-Za-z0-9_.,/=+:@%-]+'
_NAME = r'[A-Za-z_][A-Za-z0-9_]*'
_TOKEN = rf'(?:{_WORD}|\${_NAME}|[0-9]?(?:>>|>)(?:{_WORD}|&[0-9])?|[0-9]?<{_WORD})'
_FIRST_LINE = re.compile(
    rf'^({_TOKEN})(?:[ \t]+{_TOKEN})*[ \t]*<<(-?)[ \t]*'
    rf'''(?:'({_NAME})'|"({_NAME})"|({_NAME}))[ \t]*$'''
)


def simple_heredoc(command: str) -> dict | None:
    """The narrow-form heredoc a command opens, or None for "analyze as before".

    Returns ``{start, end, quoted}``: offsets into the original string, end
    exclusive, covering the body up to the terminator line. The body runs from the
    newline that ends the first line to a physical line equal to the delimiter
    name. ``<<-`` additionally strips leading tabs (tabs only, as in bash); a
    trailing space never closes (as in bash); a trailing ``\\r`` does close, a
    deliberate deviation from bash whose only effect is to end the body early and
    hand more text back to the normal analysis.
    """
    text = command or ''
    first_break = text.find('\n')
    if first_break < 0:
        return None
    match = _FIRST_LINE.match(text[:first_break])
    if match is None:
        return None
    first = match.group(1)
    if first[first.rfind('/') + 1:] not in _CONSUMERS:
        return None
    strip_tabs = match.group(2) == '-'
    quoted = match.group(3) is not None or match.group(4) is not None
    name = match.group(3) if match.group(3) is not None else (
        match.group(4) if match.group(4) is not None else match.group(5))
    start = first_break + 1
    line_start = start
    while line_start <= len(text):
        found = text.find('\n', line_start)
        line_end = len(text) if found < 0 else found
        line = text[line_start:line_end]
        if strip_tabs:
            line = line.lstrip('\t')
        if line in (name, name + '\r'):
            return {'start': start, 'end': line_start, 'quoted': quoted}
        if found < 0:
            break
        line_start = found + 1
    return None


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
    # A narrow quoted body is inert text for the consumer: nothing in it separates
    # commands, so it must not split the segment it belongs to.
    heredoc = simple_heredoc(text)
    literal = heredoc if heredoc and heredoc['quoted'] else None

    def push(op: str) -> None:
        body = ''.join(buf).strip()
        buf.clear()
        if body:
            segments.append({'text': body, 'op': op})

    i = 0
    while i < len(text):
        ch = text[i]
        if literal is not None and literal['start'] <= i < literal['end']:
            buf.append(ch); i += 1; continue
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

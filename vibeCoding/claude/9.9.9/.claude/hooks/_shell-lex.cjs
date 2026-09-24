'use strict';
// Quote-aware control-operator scan for the validation-status evidence policy.
// scan(command) -> [{text, op}]: each segment body with the control operator that
// follows it ('' on the last). Not an AST: no expansion, no heredocs.
//
// simpleHeredoc(command) is the single source deciding whether a command opens a
// heredoc of the narrow whitelist form; the Bash guard and scan() both consume it.

// Consumers whose standard input is data, not shell code. The guard has no
// deliberate defence on these channels — writing the same bytes with the Write
// tool never reaches a hook at all — so treating such a body as text removes
// nothing. Shells and wrappers (sudo/env/timeout/nice/…) are not enumerable, so
// everything outside this set keeps today's behaviour: over-block, never under-block.
// git and gh (athena-10-1 S0) read stdin as data too: a commit message (commit -F -),
// a patch (apply), a PR body (--body-file -), an API payload (api --input -).
const CONSUMERS = new Set(['python3', 'python', 'node', 'tee', 'cat', 'git', 'gh']);

// Closed grammar the whole first line must match, anchored at both ends:
//   LINE  = TOKEN (SP+ TOKEN)* SP* '<<' '-'? SP* DELIM SP* EOL
//   TOKEN = WORD | VAR | REDIR
//   WORD  = [A-Za-z0-9_.,/=+:@%-]+
//   VAR   = '$' NAME          (a bare expansion is substituted after the line is
//                              lexed, so it cannot move a token boundary)
//   REDIR = [0-9]? ('>' | '>>') (WORD | '&' [0-9])?   |   [0-9]? '<' WORD
//   DELIM = "'" NAME "'" | '"' NAME '"' | NAME ;  NAME = [A-Za-z_][A-Za-z0-9_]*
// The grammar admits no ( ) [ ] { } ` \ # ; | & and no expansion operator, so every
// context in which bash reads '<<' as a left shift or as literal text — arithmetic
// commands and expansions, array subscripts, ${…} bodies and substring offsets — is
// refused at the door instead of being enumerated and blacklisted one form at a time.
const WORD = '[A-Za-z0-9_.,/=+:@%-]+';
const NAME = '[A-Za-z_][A-Za-z0-9_]*';
const TOKEN = `(?:${WORD}|\\$${NAME}|[0-9]?(?:>>|>)(?:${WORD}|&[0-9])?|[0-9]?<${WORD})`;
const FIRST_LINE = new RegExp(
  `^(${TOKEN})(?:[ \\t]+${TOKEN})*[ \\t]*<<(-?)[ \\t]*(?:'(${NAME})'|"(${NAME})"|(${NAME}))[ \\t]*$`
);

/**
 * The narrow-form heredoc a command opens, as { start, end, quoted } offsets into
 * the original string (end exclusive, covering the body up to the terminator line),
 * or null when the form does not apply — which always means "analyze as before".
 *
 * The body runs from the newline that ends the first line to a physical line equal
 * to the delimiter name. '<<-' additionally strips leading tabs (tabs only, as in
 * bash); a trailing space never closes (as in bash); a trailing \r does close, a
 * deliberate deviation from bash whose only effect is to end the body early and
 * hand more text back to the normal analysis.
 */
function simpleHeredoc(command) {
  const text = String(command || '');
  const firstBreak = text.indexOf('\n');
  if (firstBreak < 0) return null;
  const match = FIRST_LINE.exec(text.slice(0, firstBreak));
  if (!match) return null;
  const first = match[1];
  if (!CONSUMERS.has(first.slice(first.lastIndexOf('/') + 1))) return null;
  const stripTabs = match[2] === '-';
  const name = match[3] !== undefined ? match[3] : (match[4] !== undefined ? match[4] : match[5]);
  const quoted = match[3] !== undefined || match[4] !== undefined;
  const start = firstBreak + 1;
  let lineStart = start;
  while (lineStart <= text.length) {
    const found = text.indexOf('\n', lineStart);
    const lineEnd = found < 0 ? text.length : found;
    const line = stripTabs
      ? text.slice(lineStart, lineEnd).replace(/^\t+/, '')
      : text.slice(lineStart, lineEnd);
    if (line === name || line === `${name}\r`) return { start, end: lineStart, quoted };
    if (found < 0) break;
    lineStart = found + 1;
  }
  return null;
}

// '&' backgrounds only outside a redirection: 2>&1, >&2, <&0, &>f and &>>f keep it
// inside the segment. '&&' and '|&' are matched as pairs before this is consulted.
function redirectionAmpersand(command, i) {
  return (i > 0 && (command[i - 1] === '>' || command[i - 1] === '<')) || command[i + 1] === '>';
}

function scan(command) {
  const segments = [];
  let buf = '';
  let quote = '';
  let escaped = false;
  const text = String(command || '');
  // A narrow quoted body is inert text for the consumer: nothing in it separates
  // commands, so it must not split the segment it belongs to.
  const heredoc = simpleHeredoc(text);
  const literal = heredoc && heredoc.quoted ? heredoc : null;
  const push = (op) => {
    const body = buf.trim();
    if (body) segments.push({ text: body, op });
    buf = '';
  };
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (literal && i >= literal.start && i < literal.end) { buf += ch; continue; }
    if (escaped) { buf += ch; escaped = false; continue; }
    if (ch === '\\' && quote !== "'") { buf += ch; escaped = true; continue; }
    if (quote) {
      if (ch === quote) quote = '';
      buf += ch;
      continue;
    }
    if (ch === "'" || ch === '"') { quote = ch; buf += ch; continue; }
    const pair = text.slice(i, i + 2);
    if (pair === '&&' || pair === '||' || pair === '|&') { push(pair); i += 1; continue; }
    if (ch === ';' || ch === '\n' || ch === '|') { push(ch); continue; }
    if (ch === '&') {
      if (redirectionAmpersand(text, i)) buf += ch;
      else push('&');
      continue;
    }
    buf += ch;
  }
  push('');
  return segments;
}

module.exports = { scan, simpleHeredoc };

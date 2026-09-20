'use strict';

function redirectionAmpersand(command, i) {
  return (i > 0 && (command[i - 1] === '>' || command[i - 1] === '<')) || command[i + 1] === '>';
}

function scan(command) {
  const segments = [];
  let buf = '';
  let quote = '';
  let escaped = false;
  const text = String(command || '');
  const push = (op) => {
    const body = buf.trim();
    if (body) segments.push({ text: body, op });
    buf = '';
  };
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
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

module.exports = { scan };

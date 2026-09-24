'use strict';
// Bash word/segment lexer for H5 (ported from 9.9.9 pre-bash-guard.cjs). Not an AST:
// no expansion; heredoc bodies are handled through shell-lex.simpleHeredoc.
const path = require('path');

/** Strip unquoted "#" comments that start a word, through end of line (bash rule). */
function stripComments(command) {
  let quote = '';
  let escaped = false;
  let result = '';
  let atWordStart = true;
  for (let i = 0; i < command.length; i += 1) {
    const char = command[i];
    if (escaped) { result += char; escaped = false; atWordStart = false; continue; }
    if (char === '\\' && quote !== "'") { result += char; escaped = true; continue; }
    if (quote) { result += char; if (char === quote) quote = ''; continue; }
    if (char === "'" || char === '"') { quote = char; result += char; atWordStart = false; continue; }
    if (char === '#' && atWordStart) {
      const eol = command.indexOf('\n', i);
      if (eol < 0) break;
      result += '\n';
      i = eol;
      atWordStart = true;
      continue;
    }
    result += char;
    atWordStart = /\s/.test(char);
  }
  return result;
}

function matchParen(command, openIndex) {
  let depth = 0;
  let quote = '';
  let escaped = false;
  for (let i = openIndex; i < command.length; i += 1) {
    const char = command[i];
    if (escaped) { escaped = false; continue; }
    if (char === '\\' && quote !== "'") { escaped = true; continue; }
    if (quote) { if (char === quote) quote = ''; continue; }
    if (char === "'" || char === '"') { quote = char; continue; }
    if (char === '(') depth += 1;
    else if (char === ')') { depth -= 1; if (depth === 0) return i; }
  }
  return -1;
}

/**
 * Command substitutions bash would execute ($(...) and `...`, unquoted or inside double
 * quotes; not $((...)) arithmetic). An unbalanced one is {start, end: -1} → fail closed.
 */
function findSubstitutions(command) {
  const spans = [];
  let quote = '';
  let escaped = false;
  for (let i = 0; i < command.length; i += 1) {
    const char = command[i];
    if (escaped) { escaped = false; continue; }
    if (char === '\\' && quote !== "'") { escaped = true; continue; }
    if (quote === "'") { if (char === "'") quote = ''; continue; }
    if (quote === '"' && char === '"') { quote = ''; continue; }
    if (!quote && (char === "'" || char === '"')) { quote = char; continue; }
    if (char === '$' && command[i + 1] === '(') {
      if (command[i + 2] === '(') {
        const close = command.indexOf('))', i + 3);
        if (close < 0) { spans.push({ start: i, end: -1, inner: '' }); break; }
        i = close + 1;
        continue;
      }
      const end = matchParen(command, i + 1);
      if (end < 0) { spans.push({ start: i, end: -1, inner: '' }); break; }
      spans.push({ start: i, end: end + 1, inner: command.slice(i + 2, end) });
      i = end;
      continue;
    }
    if (char === '`') {
      const close = command.indexOf('`', i + 1);
      if (close < 0) { spans.push({ start: i, end: -1, inner: '' }); break; }
      spans.push({ start: i, end: close + 1, inner: command.slice(i + 1, close) });
      i = close;
    }
  }
  return spans;
}

function tokenize(command) {
  const tokens = [];
  let value = '';
  let quoted = false;
  let quote = '';
  let escaped = false;
  const pushWord = () => {
    if (value) tokens.push({ type: 'word', value, quoted });
    value = '';
    quoted = false;
  };
  for (let i = 0; i < command.length; i += 1) {
    const char = command[i];
    if (escaped) { value += char; escaped = false; continue; }
    if (char === '\\' && quote !== "'") { escaped = true; continue; }
    if (quote) {
      if (char === quote) { quote = ''; quoted = true; } else value += char;
      continue;
    }
    if (char === "'" || char === '"') { quote = char; quoted = true; continue; }
    if (char === '$' && command[i + 1] === '(') { // $( … ) / $(( … )) stays one word (its parens are not grouping)
      const end = matchParen(command, i + 1);
      if (end > 0) { value += command.slice(i, end + 1); i = end; continue; }
    }
    if (/\s/.test(char)) { pushWord(); if (char === '\n') tokens.push({ type: 'op', value: ';' }); continue; }
    const pair = command.slice(i, i + 2);
    if (pair === '&&' || pair === '||') { pushWord(); tokens.push({ type: 'op', value: pair }); i += 1; continue; }
    if (char === ';' || char === '|') { pushWord(); tokens.push({ type: 'op', value: char }); continue; }
    // Subshell / group delimiters start a new command: "(rm -rf /)" runs rm (10.1 addition).
    if ((char === '(' || char === ')') && !(char === '(' && command[i - 1] === '$')) { pushWord(); tokens.push({ type: 'op', value: char }); continue; }
    value += char;
  }
  pushWord();
  return tokens;
}

function commandSegments(command) {
  const segments = [];
  let words = [];
  let before = null;
  for (const token of tokenize(command)) {
    if (token.type === 'word') words.push(token);
    else {
      if (words.length) segments.push({ words, before, after: token.value });
      words = [];
      before = token.value;
    }
  }
  if (words.length) segments.push({ words, before, after: null });
  return segments;
}

function executable(segment) {
  let index = 0;
  const env = {};
  while (index < segment.words.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(segment.words[index].value)) {
    const [key, ...rest] = segment.words[index].value.split('=');
    env[key] = rest.join('=');
    index += 1;
  }
  return { env, name: segment.words[index] ? segment.words[index].value : '', args: segment.words.slice(index + 1) };
}

const SUDO_VALUE = new Set(['-u', '-g', '-h', '-p', '-C', '-T']);
const XARGS_VALUE = new Set(['-I', '-n', '-P', '-L', '-d', '-s', '-E']);
const TIMEOUT_VALUE = new Set(['-s', '--signal', '-k', '--kill-after']);
const NICE_VALUE = new Set(['-n', '--adjustment']);
const EXEC_VALUE = new Set(['-a']);
// Reserved words and group openers that precede the real command word.
const RESERVED = new Set(['{', '}', '!', 'if', 'then', 'elif', 'else', 'do', 'while', 'until', 'coproc']);
// Words that make what follows conditional or scoped (pushTarget goes strict on them).
const CONTROL = new Set([...RESERVED, 'fi', 'done', 'for', 'case', 'esac', 'select', 'function']);

/** Peel command/env/sudo/xargs/timeout/nice/nohup/time/exec/stdbuf wrappers (≤4); eval forwards its joined args. */
function unwrap(item) {
  let name = path.basename(item.name);
  let args = [...item.args];
  let forwarded = null;
  const dropOptions = (withValue) => {
    while (args[0] && args[0].value.startsWith('-')) {
      const option = args.shift().value;
      if (withValue.has(option) && args[0]) args.shift();
    }
  };
  for (let depth = 0; depth < 6; depth += 1) {
    if (RESERVED.has(name)) { /* the next word is the command */ }
    else if (name === 'command' || name === 'nohup' || name === 'time' || name === 'stdbuf') { while (args[0] && args[0].value.startsWith('-')) args.shift(); }
    else if (name === 'timeout') { dropOptions(TIMEOUT_VALUE); if (args[0] && /^[0-9.]+[smhd]?$/.test(args[0].value)) args.shift(); }
    else if (name === 'nice') dropOptions(NICE_VALUE);
    else if (name === 'exec') dropOptions(EXEC_VALUE);
    else if (name === 'env') {
      while (args[0] && (args[0].value.startsWith('-') || /^[A-Za-z_][A-Za-z0-9_]*=/.test(args[0].value))) args.shift();
    } else if (name === 'sudo') dropOptions(SUDO_VALUE);
    else if (name === 'xargs') { dropOptions(XARGS_VALUE); if (!args[0]) break; }
    else if (name === 'eval') { forwarded = args.map(token => token.value).join(' '); args = []; break; }
    else break;
    if (!args[0]) break;
    name = path.basename(args.shift().value);
  }
  return { ...item, name, args, forwarded };
}

const GIT_VALUE = new Set(['-C', '-c', '--git-dir', '--work-tree', '--namespace', '--config-env']);

function gitSubcommand(args) {
  for (let index = 0; index < args.length; index += 1) {
    const value = args[index].value;
    if (GIT_VALUE.has(value)) { index += 1; continue; }
    if (/^--(?:git-dir|work-tree|namespace|config-env)=/.test(value)) continue;
    if (value.startsWith('-')) continue;
    return value;
  }
  return '';
}

/** Blank out a heredoc body in place (same length, newlines kept). */
function maskBody(command, span) {
  return command.slice(0, span.start) + command.slice(span.start, span.end).replace(/[^\n]/g, ' ') + command.slice(span.end);
}

/** Parsed segments of a command: [{segment, env, name, args, forwarded}]. */
function parse(command) {
  return commandSegments(command).map(segment => unwrap({ segment, ...executable(segment) }));
}

module.exports = { stripComments, findSubstitutions, tokenize, commandSegments, executable, unwrap, gitSubcommand, maskBody, parse, CONTROL };

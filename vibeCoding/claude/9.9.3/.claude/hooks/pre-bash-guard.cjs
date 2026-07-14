#!/usr/bin/env node
/** Athena v9.9.3 structural Bash guard. */
"use strict";

const fs = require("fs");
const path = require("path");

/**
 * Strip bash comments (an unquoted "#" that starts a word, i.e. at the start
 * of the command or right after whitespace) through end-of-line, the same
 * rule bash itself uses. This runs before substitution scanning and
 * tokenizing so "git push origin main # $(rm -rf /)" is analyzed as a plain
 * push (the trailing text never executes) instead of tripping the rm
 * finding on comment text bash would never run. A "#" embedded in a word
 * ("file#1", "a#b") or inside quotes is not a comment start and is left
 * alone; comments still end at a real newline so later lines keep parsing.
 */
function stripComments(command) {
  let quote = "";
  let escaped = false;
  let result = "";
  let atWordStart = true;
  for (let i = 0; i < command.length; i += 1) {
    const char = command[i];
    if (escaped) { result += char; escaped = false; atWordStart = false; continue; }
    if (char === "\\" && quote !== "'") { result += char; escaped = true; continue; }
    if (quote) {
      result += char;
      if (char === quote) quote = "";
      continue;
    }
    if (char === "'" || char === '"') { quote = char; result += char; atWordStart = false; continue; }
    if (char === "#" && atWordStart) {
      const eol = command.indexOf("\n", i);
      if (eol < 0) break;
      result += "\n";
      i = eol;
      atWordStart = true;
      continue;
    }
    result += char;
    atWordStart = /\s/.test(char);
  }
  return result;
}

/**
 * Find command-substitution segments ($(...) and `...`) that bash would
 * actually execute: unquoted or inside double quotes, but not inside single
 * quotes (literal) and not arithmetic expansion ($((...))).
 *
 * Returns a list of { start, end, inner } spans (end exclusive) covering the
 * substitution including its delimiters. An unresolved/unbalanced attempt at
 * substitution surfaces as { start, end: -1 } so callers can fail closed.
 */
function findSubstitutions(command) {
  const spans = [];
  let quote = "";
  let escaped = false;
  for (let i = 0; i < command.length; i += 1) {
    const char = command[i];
    if (escaped) { escaped = false; continue; }
    if (char === "\\" && quote !== "'") { escaped = true; continue; }
    if (quote === "'") continue;
    if (quote === '"' && char === '"') { quote = ""; continue; }
    if (!quote && (char === "'" || char === '"')) { quote = char; continue; }
    if (char === "$" && command[i + 1] === "(") {
      if (command[i + 2] === "(") {
        // Arithmetic expansion $((...)) — not a command substitution, skip it
        // whole so its contents are never mistaken for a nested command.
        const close = command.indexOf("))", i + 3);
        if (close < 0) { spans.push({ start: i, end: -1, inner: "" }); break; }
        i = close + 1;
        continue;
      }
      const end = matchParen(command, i + 1);
      if (end < 0) { spans.push({ start: i, end: -1, inner: "" }); break; }
      spans.push({ start: i, end: end + 1, inner: command.slice(i + 2, end) });
      i = end;
      continue;
    }
    if (char === "`") {
      const close = command.indexOf("`", i + 1);
      if (close < 0) { spans.push({ start: i, end: -1, inner: "" }); break; }
      spans.push({ start: i, end: close + 1, inner: command.slice(i + 1, close) });
      i = close;
      continue;
    }
  }
  return spans;
}

function matchParen(command, openIndex) {
  let depth = 0;
  let quote = "";
  let escaped = false;
  for (let i = openIndex; i < command.length; i += 1) {
    const char = command[i];
    if (escaped) { escaped = false; continue; }
    if (char === "\\" && quote !== "'") { escaped = true; continue; }
    if (quote) {
      if (char === quote) quote = "";
      continue;
    }
    if (char === "'" || char === '"') { quote = char; continue; }
    if (char === "(") depth += 1;
    else if (char === ")") {
      depth -= 1;
      if (depth === 0) return i;
    }
  }
  return -1;
}

function tokenize(command) {
  const tokens = [];
  let value = "";
  let quoted = false;
  let quote = "";
  let escaped = false;
  const pushWord = () => {
    if (value) tokens.push({ type: "word", value, quoted });
    value = "";
    quoted = false;
  };
  for (let i = 0; i < command.length; i += 1) {
    const char = command[i];
    if (escaped) { value += char; escaped = false; continue; }
    if (char === "\\" && quote !== "'") { escaped = true; continue; }
    if (quote) {
      if (char === quote) { quote = ""; quoted = true; }
      else value += char;
      continue;
    }
    if (char === "'" || char === '"') { quote = char; quoted = true; continue; }
    if (/\s/.test(char)) { pushWord(); if (char === "\n") tokens.push({ type: "op", value: ";" }); continue; }
    const pair = command.slice(i, i + 2);
    if (["&&", "||"].includes(pair)) { pushWord(); tokens.push({ type: "op", value: pair }); i += 1; continue; }
    if ([";", "|"].includes(char)) { pushWord(); tokens.push({ type: "op", value: char }); continue; }
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
    if (token.type === "word") words.push(token);
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
    const [key, ...rest] = segment.words[index].value.split("=");
    env[key] = rest.join("=");
    index += 1;
  }
  return { env, name: segment.words[index]?.value || "", args: segment.words.slice(index + 1) };
}

function unwrap(item) {
  let name = path.basename(item.name);
  let args = [...item.args];
  let forwarded = null;
  for (let depth = 0; depth < 3; depth += 1) {
    if (name === "command") {
      while (args[0]?.value.startsWith("-")) args.shift();
    } else if (name === "env") {
      while (args[0] && (args[0].value.startsWith("-") || /^[A-Za-z_][A-Za-z0-9_]*=/.test(args[0].value))) args.shift();
    } else if (name === "sudo") {
      const optionsWithValue = new Set(["-u", "-g", "-h", "-p", "-C", "-T"]);
      while (args[0]?.value.startsWith("-")) {
        const option = args.shift().value;
        if (optionsWithValue.has(option) && args[0]) args.shift();
      }
    } else if (name === "xargs") {
      const optionsWithValue = new Set(["-I", "-n", "-P", "-L", "-d", "-s", "-E"]);
      while (args[0]?.value.startsWith("-")) {
        const option = args.shift().value;
        if (optionsWithValue.has(option) && args[0]) args.shift();
      }
      // No trailing command means xargs defaults to echo on its stdin words,
      // which is not a forwarding risk — leave name/args as-is (falls through).
      if (!args[0]) break;
    } else if (name === "eval") {
      // eval joins its remaining arguments into one shell command string; the
      // joined text must be re-analyzed, not treated as a literal argv.
      forwarded = args.map(token => token.value).join(" ");
      args = [];
      break;
    } else break;
    if (!args[0]) break;
    name = path.basename(args.shift().value);
  }
  return { ...item, name, args, forwarded };
}

function gitSubcommand(args) {
  const optionsWithValue = new Set(["-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"]);
  for (let index = 0; index < args.length; index += 1) {
    const value = args[index].value;
    if (optionsWithValue.has(value)) { index += 1; continue; }
    if (/^--(?:git-dir|work-tree|namespace|config-env)=/.test(value)) continue;
    if (value.startsWith("-")) continue;
    return value;
  }
  return "";
}

function hasRecursiveForce(args) {
  const flags = args.filter(token => token.value.startsWith("-")).map(token => token.value).join("");
  return flags.includes("r") && flags.includes("f");
}

/**
 * Normalize a shell path-like argument before the exact-target danger check:
 * collapse repeated slashes, then strip trailing "/.", "/*", "/**" and a
 * trailing "/" so that "rm -rf /*", "rm -rf //" and "rm -rf /." are treated
 * the same as their bare root/home form.
 */
function normalizeTarget(value) {
  let normalized = value.replace(/\/{2,}/g, "/");
  let previous;
  do {
    previous = normalized;
    normalized = normalized.replace(/\/(?:\*\*|\*|\.)$/, "");
  } while (normalized !== previous && normalized.length);
  if (normalized.length > 1) normalized = normalized.replace(/\/$/, "");
  return normalized || "/";
}

function dangerousTarget(value) {
  const normalized = normalizeTarget(value);
  return ["/", "~", "$HOME", "${HOME}"].includes(normalized)
    || normalized.startsWith("$HOME/") || normalized.startsWith("${HOME}/");
}

/**
 * Command substitutions ($(...) and `...`) execute even when the whole
 * expression sits inside double quotes, so every span bash would run must be
 * recursively analyzed. A substitution that cannot be parsed (unbalanced
 * parens/backticks) fails closed rather than silently passing through.
 */
function analyzeSubstitutions(command, depth) {
  const spans = findSubstitutions(command);
  for (const span of spans) {
    if (span.end < 0) return { danger: "unparsable command substitution" };
    const nested = analyze(span.inner, depth + 1);
    if (nested.danger) return nested;
    if (nested.push && !nested.allowPush) return { push: true, allowPush: false };
  }
  return {};
}

function analyze(command, depth = 0) {
  if (depth > 2) return { danger: "nested shell depth exceeds policy" };
  const active = stripComments(command);
  const substitution = analyzeSubstitutions(active, depth);
  if (substitution.danger || substitution.push) return substitution;
  const segments = commandSegments(active);
  const parsed = segments.map(segment => unwrap({ segment, ...executable(segment) }));
  for (const item of parsed) {
    const name = item.name;
    const values = item.args.map(token => token.value);
    if (item.forwarded !== null && item.forwarded !== undefined) {
      const nested = analyze(item.forwarded, depth + 1);
      if (nested.danger) return nested;
      if (nested.push) return nested;
      continue;
    }
    if (name === "rm" && hasRecursiveForce(item.args) && values.some(dangerousTarget)) {
      return { danger: "recursive force removal of root/home" };
    }
    if (name === "dd" && values.some(value => /^of=\/dev\/(?:sd|nvme|xvd)/.test(value))) {
      return { danger: "raw block-device write" };
    }
    if (["mysql", "psql", "sqlite3"].includes(name) && /\bdrop\s+table\b/i.test(values.join(" "))) {
      return { danger: "DROP TABLE through database client" };
    }
    if (["bash", "sh", "zsh"].includes(name)) {
      const cIndex = values.findIndex(value => value === "-c");
      if (cIndex >= 0 && values[cIndex + 1]) {
        const nested = analyze(values[cIndex + 1], depth + 1);
        if (nested.danger) return nested;
      }
    }
    if (name === "git" && gitSubcommand(item.args) === "push") {
      return { push: true, allowPush: item.env.ATHENA_ALLOW_PUSH === "1" };
    }
  }
  for (let i = 0; i + 1 < parsed.length; i += 1) {
    const left = path.basename(parsed[i].name);
    const right = path.basename(parsed[i + 1].name);
    if (parsed[i].segment.after === "|" && ["curl", "wget"].includes(left) && ["bash", "sh", "zsh"].includes(right)) {
      return { danger: "network response piped to shell" };
    }
  }
  return {};
}

function findStage(cwd) {
  let current = path.resolve(cwd);
  for (let depth = 0; depth < 8; depth += 1) {
    const index = path.join(current, ".ai_state", "_index.md");
    if (fs.existsSync(index)) {
      const match = fs.readFileSync(index, "utf8").match(/^stage\s*:\s*["']?([^"'\n#]+)/m);
      return match ? match[1].trim() : "";
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return null;
}

function main() {
  try {
    let payload = {};
    try {
      const input = fs.readFileSync(0, "utf8");
      if (input.trim()) payload = JSON.parse(input);
    } catch (_) {}
    const command = String(payload?.tool_input?.command || "");
    if (!command) return;
    const verdict = analyze(command);
    if (verdict.danger) {
      process.stderr.write(`[pre-bash-guard] BLOCKED: ${verdict.danger}\n`);
      process.exitCode = 2;
      return;
    }
    if (verdict.push && !verdict.allowPush) {
      const cwd = path.resolve(payload.cwd || process.cwd());
      const stage = findStage(cwd);
      if (stage !== null && stage !== "ship") {
        process.stderr.write(`[pre-bash-guard] BLOCKED: stage=${stage || "unknown"}; git push requires ship.\n`);
        process.exitCode = 2;
      }
    }
  } catch (error) {
    process.stderr.write(`[pre-bash-guard] BLOCKED: parser failure: ${error.message}\n`);
    process.exitCode = 2;
  }
}

main();

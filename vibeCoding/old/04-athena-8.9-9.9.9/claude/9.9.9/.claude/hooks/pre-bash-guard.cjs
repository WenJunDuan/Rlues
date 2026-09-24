#!/usr/bin/env node
/** Athena v9.9.6 structural Bash guard. */
"use strict";

const fs = require("fs");
const os = require("os");
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
    if (quote === "'") {
      if (char === "'") quote = "";
      continue;
    }
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

/**
 * The narrow whitelist heredoc this command opens, or null for "analyze exactly as
 * before". The lexer is required inside the function on purpose: the guard must
 * load and decide even when _shell-lex is missing or throws, and that path has to
 * fall back to today's analysis — a whitelist that cannot be consulted must
 * over-block, never open a way through.
 */
function narrowHeredoc(command) {
  try { return require("./_shell-lex.cjs").simpleHeredoc(command); }
  catch (_) { return null; }
}

/** Blank out a heredoc body in place, same length, newlines kept. */
function maskBody(command, span) {
  return command.slice(0, span.start)
    + command.slice(span.start, span.end).replace(/[^\n]/g, " ")
    + command.slice(span.end);
}

function analyze(command, depth = 0) {
  if (depth > 2) return { danger: "nested shell depth exceeds policy" };
  const heredoc = narrowHeredoc(command);
  // A quoted body reaches the consumer verbatim, so it is text and not commands.
  // Mask it on the raw string, before stripComments, so no finding is ever raised
  // on characters bash does not execute.
  const active = stripComments(heredoc && heredoc.quoted ? maskBody(command, heredoc) : command);
  const substitution = analyzeSubstitutions(active, depth);
  if (substitution.danger || substitution.push) return substitution;
  // An unquoted body *is* expanded by bash, so the scan above stays byte for byte
  // what it was and the body is additionally scanned on its own, from a clean
  // lexical state. Findings are only ever added — that closes the hole where a
  // body line starting with "#" hid a substitution bash really runs.
  if (heredoc && !heredoc.quoted) {
    const body = analyzeSubstitutions(command.slice(heredoc.start, heredoc.end), depth);
    if (body.danger || body.push) return body;
  }
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
        if (nested.danger || nested.push) return nested;
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

/**
 * A directory named on the command line, resolved without running the shell. Anything
 * that needs expansion ($VAR, `...`, ~user, "-") or does not exist yields null, and the
 * caller falls back to cwd — over-block, never open a way through.
 */
function resolveDir(raw, base) {
  if (typeof raw !== "string" || !raw || raw === "-" || /[$`]/.test(raw)) return null;
  let value = raw;
  if (value === "~" || value.startsWith("~/")) value = path.join(os.homedir(), value.slice(1));
  else if (value.startsWith("~")) return null;
  const resolved = path.resolve(base, value);
  try { return fs.statSync(resolved).isDirectory() ? resolved : null; } catch (_) { return null; }
}

/**
 * athena-10-1 S0 (Q12 #29): the project whose stage governs a push is the one being
 * pushed (see sameProject for what still counts as this project) — the last top-level `cd` joined by && or ; before it, then the push's own
 * `git -C <dir>` options. A push the guard only sees nested (bash -c, eval, $(...)),
 * a --git-dir/--work-tree push, any GIT_DIR-family variable anywhere in the command
 * (inline, export, env wrapper — it redirects the repository behind -C's back), or any
 * unresolvable directory keeps today's rule: cwd.
 */
const REPO_REDIRECT_ENV = /\bGIT_(?:DIR|WORK_TREE|COMMON_DIR|OBJECT_DIRECTORY|ALTERNATE_OBJECT_DIRECTORIES|NAMESPACE)\b/;

function pushTarget(command, cwd) {
  const strict = { dir: cwd, dest: undefined };
  const heredoc = narrowHeredoc(command);
  const active = stripComments(heredoc && heredoc.quoted ? maskBody(command, heredoc) : command);
  if (REPO_REDIRECT_ENV.test(active)) return strict;
  let base = cwd;
  for (const segment of commandSegments(active)) {
    const item = unwrap({ segment, ...executable(segment) });
    const values = item.args.map(token => token.value);
    if (item.name === "cd") {
      const next = values.length ? resolveDir(values[0], base) : os.homedir();
      if (!next || !["&&", ";"].includes(segment.after)) return strict;
      base = next;
      continue;
    }
    if (item.name === "git" && gitSubcommand(item.args) === "push") {
      let dir = base;
      let i = 0;
      for (; i < values.length; i += 1) {
        const value = values[i];
        if (value === "-C") {
          dir = resolveDir(values[i + 1], dir);
          if (!dir) return strict;
          i += 1;
          continue;
        }
        if (/^--(?:git-dir|work-tree)(?:=|$)/.test(value)) return strict;
        if (["-c", "--namespace", "--config-env"].includes(value)) { i += 1; continue; }
        if (!value.startsWith("-")) break;
      }
      return { dir, dest: pushDestination(values.slice(i + 1)) };
    }
  }
  return strict;
}

/**
 * The repository argument of `git push`: undefined when none is named, null when it
 * cannot be read without the shell ($VAR, `...`) — the caller treats null as "the project".
 */
function pushDestination(args) {
  const withValue = new Set(["-o", "--push-option", "--receive-pack", "--exec", "--repo"]);
  for (let i = 0; i < args.length; i += 1) {
    const value = args[i];
    let dest;
    if (value.startsWith("--repo=")) dest = value.slice(7);
    else if (value === "--repo") dest = args[i + 1];
    else if (withValue.has(value)) { i += 1; continue; }
    else if (value.startsWith("-")) continue;
    else dest = value;
    return dest === undefined || /[$`]/.test(dest) ? null : dest;
  }
  return undefined;
}

function gitOut(dir, args) {
  try {
    return require("child_process").execFileSync("git", ["-C", dir, ...args], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] })
      .split("\n").map(line => line.trim()).filter(Boolean);
  } catch (_) { return []; }
}

/** Every remote URL of a repository, as written and as git rewrites it (insteadOf / pushInsteadOf). */
function remoteUrls(dir) {
  const urls = new Set(gitOut(dir, ["config", "--get-regexp", "^remote\\..*\\.(url|pushurl)$"])
    .map(line => line.split(/\s+/).slice(1).join(" ")));
  for (const name of gitOut(dir, ["remote"])) {
    for (const url of gitOut(dir, ["remote", "get-url", "--all", name])) urls.add(url);
    for (const url of gitOut(dir, ["remote", "get-url", "--push", "--all", name])) urls.add(url);
  }
  return [...urls];
}

/** base/value without collapsing "..": the OS resolves ".." against a symlink's target, path.resolve does not. */
function unresolvedJoin(base, value) {
  return path.isAbsolute(value) ? value : `${base}${path.sep}${value}`;
}

/** host/path for network remotes whatever the scheme (https, ssh://, scp-like); an absolute path otherwise. */
function normalizeRemote(url, base) {
  const raw = String(url).trim().replace(/\/+$/, "");
  const trimmed = raw.replace(/\.git$/, "");
  // Local remotes compare by real path (symlinks, macOS /var vs /private/var). The path is
  // kept un-normalised so ".." after a symlink resolves the way the OS and git do; the
  // deepest existing ancestor is resolved when the path itself does not exist; .git last.
  const local = (value) => {
    let head = unresolvedJoin(base, value);
    const tail = [];
    for (;;) {
      try { return path.join(fs.realpathSync.native(head), ...tail).replace(/\.git$/, ""); } catch (_) { /* climb */ }
      const parent = path.dirname(head);
      if (parent === head) return path.resolve(base, value).replace(/\.git$/, "");
      tail.unshift(path.basename(head));
      head = parent;
    }
  };
  if (/^file:\/\//i.test(raw)) return local(raw.replace(/^file:\/\//i, ""));
  let match = trimmed.match(/^[a-z][a-z0-9+.-]*:\/\/(?:[^@/]+@)?([^/:]+)(?::\d+)?\/?(.*)$/i);
  if (match) return `${match[1]}/${match[2]}`.toLowerCase();
  match = trimmed.match(/^(?:[^@/\s]+@)?([^:/\s]+):(?!\/\/)(.*)$/);
  if (match && match[1].length > 1) return `${match[1]}/${match[2].replace(/^\/+/, "")}`.toLowerCase();
  return local(raw);
}

/**
 * Another checkout of the same project must stay under the project's stage: a worktree
 * or subdirectory (same git common dir), a separate clone that shares any remote URL with
 * the project, a clone whose remote is the project itself, or a push whose destination is
 * one of the project's remotes. Only a repository proven unrelated is judged by its own stage.
 */
function sameProject(target, cwd, dest) {
  if (sameRepository(target, cwd)) return true;
  if (dest === null) return true;
  const own = new Set(remoteUrls(cwd).map(url => normalizeRemote(url, cwd)));
  const theirs = remoteUrls(target);
  if (typeof dest === "string") theirs.push(dest, ...gitOut(target, ["ls-remote", "--get-url", dest]));
  for (const raw of theirs) {
    if (own.has(normalizeRemote(raw, target))) return true;
    const local = unresolvedJoin(target, raw);
    try { if (fs.statSync(local).isDirectory() && sameRepository(local, cwd)) return true; } catch (_) { /* not local */ }
  }
  return false;
}

/**
 * A worktree or subdirectory of the project is the same project: its checked-out
 * `_index.md` may lag (an idle commit), so the project's own stage must govern it.
 * Same repository = same `git rev-parse --git-common-dir`; any git failure = not proven.
 */
function sameRepository(a, b) {
  const common = (dir) => {
    try {
      const out = require("child_process").execFileSync("git", ["-C", dir, "rev-parse", "--git-common-dir"],
        { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
      return fs.realpathSync(path.resolve(dir, out));
    } catch (_) { return null; }
  };
  const left = common(a);
  return left !== null && left === common(b);
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
    const command = String(payload?.tool_input?.command || payload?.tool_input?.cmd || "");
    if (!command) return;
    const verdict = analyze(command);
    if (verdict.danger) {
      process.stderr.write(`[pre-bash-guard] BLOCKED: ${verdict.danger}\n`);
      process.exitCode = 2;
      return;
    }
    if (verdict.push && !verdict.allowPush) {
      const cwd = path.resolve(payload.cwd || process.cwd());
      const target = pushTarget(command, cwd);
      const stage = findStage(target.dir === cwd || sameProject(target.dir, cwd, target.dest) ? cwd : target.dir);
      // P8: idle (empty stage, no sprint in flight) allows maintenance pushes —
      // closed-out projects must be able to sync state without opening a sprint.
      if (stage !== null && stage !== "ship" && stage !== "") {
        process.stderr.write(`[pre-bash-guard] BLOCKED: stage=${stage || "unknown"}; git push requires ship.\n`);
        process.exitCode = 2;
      }
    }
    if (!process.exitCode) {
      try { require('./_input-binding.cjs').captureBefore(payload); }
      catch (error) { process.stderr.write('[evidence-input] unavailable: ' + error.message + '\n'); }
    }
  } catch (error) {
    process.stderr.write(`[pre-bash-guard] BLOCKED: parser failure: ${error.message}\n`);
    process.exitCode = 2;
  }
}

if (require.main === module) {
  main();
} else {
  module.exports = { findSubstitutions, analyze };
}

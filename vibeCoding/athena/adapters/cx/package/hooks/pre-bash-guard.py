#!/usr/bin/env python3
"""Athena v9.9.6 Codex PreToolUse(Bash) guardrail.

v9.9.6 安全对齐: 9.9.3 的实现是对原始命令串做平坦正则匹配, 与 CC 端的
shell 分析器差 4 倍覆盖面。在 Codex 的 ``approval_policy=never`` +
``sandbox_mode=danger-full-access`` 下, 这是最弱的护栏配最大的爆炸半径。

实测可绕过样本 (旧实现放行, CC 端拦截):
    rm -rf /*        rm -rf //        rm -rf /.        rm -rf $HOME/
    rm -rf `echo /`  $(echo rm) -rf /

本版对齐 CC ``pre-bash-guard.cjs`` 的判定面:
  1. 递归解析命令替换 ``$(...)`` / 反引号 (不可解析 → fail-closed);
  2. 目标路径归一化 (``//`` ``/*`` ``/**`` ``/.`` 尾斜杠) 后再比对根/家目录;
  3. env 前缀剥离、``bash -c`` / ``sh -c`` 内层重新分析、``eval`` / ``xargs`` 转发;
  4. ``git`` 子命令按 ``-C`` / ``-c`` 等带值选项正确定位, 而非松散正则;
  5. 管道 ``curl|wget → shell``;
  6. 嵌套深度上限 2, 超限即 block。

Hook 是纵深防御, 不是安全边界。
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

EXIT_SUCCESS = 0
EXIT_BLOCK = 2
MAX_DEPTH = 2

DANGEROUS_ROOTS = {"/", "~", "$HOME", "${HOME}"}
DB_CLIENTS = {"mysql", "psql", "sqlite3", "mariadb"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
REPO_REDIRECT_ENV = re.compile(r"\bGIT_(?:DIR|WORK_TREE|COMMON_DIR|OBJECT_DIRECTORY|ALTERNATE_OBJECT_DIRECTORIES|NAMESPACE)\b")


def strip_comments(command: str) -> str:
    quote = ""
    escaped = False
    result = []
    at_word_start = True
    i = 0
    while i < len(command):
        ch = command[i]
        if escaped:
            result.append(ch)
            escaped = False
            at_word_start = False
            i += 1
            continue
        if ch == "\\" and quote != "'":
            result.append(ch)
            escaped = True
            i += 1
            continue
        if quote:
            result.append(ch)
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            result.append(ch)
            at_word_start = False
            i += 1
            continue
        if ch == "#" and at_word_start:
            eol = command.find("\n", i)
            if eol < 0:
                break
            result.append("\n")
            i = eol + 1
            at_word_start = True
            continue
        result.append(ch)
        at_word_start = bool(re.match(r"\s", ch))
        i += 1
    return "".join(result)


def find_substitutions(command: str) -> list[str | None]:
    """返回每个 $(...) / `...` 的内层文本; None 表示括号不闭合 (fail-closed)。

    单引号内的内容是字面量，不参与命令替换（对齐 bash / CC pre-bash-guard）。
    """
    out: list[str | None] = []
    i, n = 0, len(command)
    quote = ""
    escaped = False
    while i < n:
        ch = command[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if ch == "\\" and quote != "'":
            escaped = True
            i += 1
            continue
        if quote == "'":
            if ch == "'":
                quote = ""
            i += 1
            continue
        if quote == '"':
            if ch == '"':
                quote = ""
                i += 1
                continue
        elif ch in "'\"":
            quote = ch
            i += 1
            continue
        if command.startswith("$((", i):          # 算术展开, 不是命令替换
            depth, j = 0, i + 1
            while j < n:
                if command[j] == "(":
                    depth += 1
                elif command[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            i = j + 1
            continue
        if command.startswith("$(", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if command[j] == "(":
                    depth += 1
                elif command[j] == ")":
                    depth -= 1
                j += 1
            out.append(command[i + 2:j - 1] if depth == 0 else None)
            i = j
            continue
        if command[i] == "`":
            j = command.find("`", i + 1)
            out.append(command[i + 1:j] if j > 0 else None)
            i = (j + 1) if j > 0 else n
            continue
        i += 1
    return out


def normalize_target(value: str) -> str:
    v = re.sub(r"/{2,}", "/", value.strip().strip("'\""))
    prev = None
    while prev != v and v:
        prev = v
        v = re.sub(r"/(?:\*\*|\*|\.)$", "", v)
    if len(v) > 1:
        v = v.rstrip("/")
    return v or "/"


def dangerous_target(value: str) -> bool:
    v = normalize_target(value)
    return v in DANGEROUS_ROOTS or v.startswith("$HOME/") or v.startswith("${HOME}/")


def has_recursive_force(args: list[str]) -> bool:
    tokens = {a.strip("'\"") for a in args}
    if "--recursive" in tokens and "--force" in tokens:
        return True
    flags = "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))
    return "r" in flags.lower() and "f" in flags.lower()


def split_segments(command: str) -> list[tuple[str, str]]:
    """切成 (片段, 其后的连接符)。"""
    parts, buf, sep = [], [], ""
    i, n = 0, len(command)
    while i < n:
        two = command[i:i + 2]
        if two in ("&&", "||"):
            parts.append(("".join(buf), two)); buf = []; i += 2; continue
        if command[i] in "|;\n":
            parts.append(("".join(buf), command[i])); buf = []; i += 1; continue
        buf.append(command[i]); i += 1
    parts.append(("".join(buf), ""))
    return [(p.strip(), s) for p, s in parts if p.strip()]


def tokenize(segment: str) -> list[str]:
    try:
        return shlex.split(segment, comments=False, posix=False)
    except ValueError:
        return segment.split()


def executable(tokens: list[str]) -> tuple[dict[str, str], str, list[str]]:
    """剥掉 VAR=value 前缀, 返回 (env, 命令名, 参数)。"""
    env: dict[str, str] = {}
    i = 0
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        k, _, v = tokens[i].partition("=")
        env[k] = v.strip("'\"")
        i += 1
    if i >= len(tokens):
        return env, "", []
    return env, Path(tokens[i].strip("'\"")).name, tokens[i + 1:]


def git_subcommand(args: list[str]) -> str:
    i = 0
    while i < len(args):
        v = args[i]
        if v in GIT_OPTS_WITH_VALUE:
            i += 2; continue
        if re.match(r"^--(?:git-dir|work-tree|namespace|config-env)=", v) or v.startswith("-"):
            i += 1; continue
        return v
    return ""


def analyze_substitutions(command: str, depth: int) -> dict[str, Any]:
    """Command substitutions ($(...) and `...`) execute even when the whole
    expression sits inside double quotes, so every span bash would run must be
    recursively analyzed. A substitution that cannot be parsed (unbalanced
    parens/backticks) fails closed rather than silently passing through.
    """
    for inner in find_substitutions(command):
        if inner is None:
            return {"danger": "unparsable command substitution"}
        nested = analyze(inner, depth + 1)
        if nested.get("danger"):
            return nested
        if nested.get("push") and not nested.get("allow_push"):
            return {"push": True, "allow_push": False}
    return {}


def narrow_heredoc(command: str) -> dict[str, Any] | None:
    """The narrow whitelist heredoc this command opens, or None for "analyze exactly
    as before". The lexer is imported inside the function on purpose: the guard must
    load and decide even when _shell_lex is missing or throws, and that path has to
    fall back to today's analysis — a whitelist that cannot be consulted must
    over-block, never open a way through.
    """
    try:
        from _shell_lex import simple_heredoc
        return simple_heredoc(command)
    except Exception:
        return None


def mask_body(command: str, span: dict[str, Any]) -> str:
    """Blank out a heredoc body in place, same length, newlines kept."""
    return (command[:span["start"]]
            + re.sub(r"[^\n]", " ", command[span["start"]:span["end"]])
            + command[span["end"]:])


def analyze(command: str, depth: int = 0) -> dict[str, Any]:
    if depth > MAX_DEPTH:
        return {"danger": "nested shell depth exceeds policy"}
    heredoc = narrow_heredoc(command)
    # A quoted body reaches the consumer verbatim, so it is text and not commands.
    # Mask it on the raw string, before strip_comments, so no finding is ever raised
    # on characters bash does not execute.
    active = strip_comments(mask_body(command, heredoc) if heredoc and heredoc["quoted"] else command)

    substitution = analyze_substitutions(active, depth)
    if substitution.get("danger") or substitution.get("push"):
        return substitution
    # An unquoted body *is* expanded by bash, so the scan above stays byte for byte
    # what it was and the body is additionally scanned on its own, from a clean
    # lexical state. Findings are only ever added — that closes the hole where a
    # body line starting with "#" hid a substitution bash really runs.
    if heredoc and not heredoc["quoted"]:
        body = analyze_substitutions(command[heredoc["start"]:heredoc["end"]], depth)
        if body.get("danger") or body.get("push"):
            return body

    segments = split_segments(active)
    parsed = []
    for seg, sep in segments:
        env, name, args = executable(tokenize(seg))
        parsed.append((env, name, args, sep))

    for env, name, args, _sep in parsed:
        name = name.lstrip("\\")
        vals = [a.strip("'\"") for a in args]
        unwrap_depth = 0
        while unwrap_depth < 3 and name in {"sudo", "env", "command"} and vals:
            unwrap_depth += 1
            if name == "command":
                while vals and vals[0].startswith("-"):
                    vals.pop(0)
            elif name == "env":
                while vals and (vals[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", vals[0])):
                    vals.pop(0)
            elif name == "sudo":
                options_with_value = {"-u", "-g", "-h", "-p", "-C", "-T"}
                while vals and vals[0].startswith("-"):
                    option = vals.pop(0)
                    if option in options_with_value and vals:
                        vals.pop(0)
            if not vals:
                break
            name = Path(vals.pop(0)).name.lstrip("\\")
        if name in {"eval", "xargs"} and vals:
            nested = analyze(" ".join(vals), depth + 1)
            if nested.get("danger") or nested.get("push"):
                return nested
            continue
        if name == "rm" and has_recursive_force(args) and any(dangerous_target(v) for v in vals):
            return {"danger": "recursive force removal of root/home"}
        if name == "dd" and any(re.match(r"^of=/dev/(?:sd|nvme|xvd)", v) for v in vals):
            return {"danger": "raw block-device write"}
        if name in DB_CLIENTS and re.search(r"\bdrop\s+table\b", " ".join(vals), re.I):
            return {"danger": "DROP TABLE through database client"}
        if name in SHELLS and "-c" in vals:
            idx = vals.index("-c")
            if idx + 1 < len(vals):
                nested = analyze(vals[idx + 1], depth + 1)
                if nested.get("danger") or nested.get("push"):
                    return nested
        if re.match(r"^:\s*\(\s*\)", " ".join([name] + vals)) or re.search(r":\(\)\s*\{", active):
            return {"danger": "fork bomb"}
        # athena-10-1 S0: the subcommand is read after unwrapping, as CC does; reading the raw
        # args let `env X=1 git push` and `sudo git push` pass as non-push commands.
        if name == "git" and git_subcommand(vals) == "push":
            return {"push": True, "allow_push": env.get("ATHENA_ALLOW_PUSH") == "1"}

    for i in range(len(parsed) - 1):
        if parsed[i][3] == "|" and parsed[i][1] in {"curl", "wget"} and parsed[i + 1][1] in SHELLS:
            return {"danger": "network response piped to shell"}
    return {}


def resolve_dir(raw: str | None, base: Path) -> Path | None:
    """A directory named on the command line, resolved without running the shell.

    Anything that needs expansion ($VAR, `...`, ~user, "-") or does not exist yields
    None, and the caller falls back to cwd -- over-block, never open a way through.
    """
    if not isinstance(raw, str) or not raw or raw == "-" or re.search(r"[$`]", raw):
        return None
    value = raw
    if value == "~" or value.startswith("~/"):
        value = str(Path.home()) + value[1:]
    elif value.startswith("~"):
        return None
    resolved = (base / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    return resolved if resolved.is_dir() else None


def _unwrap(name: str, vals: list[str]) -> tuple[str, list[str]]:
    depth = 0
    while depth < 3 and name in {"sudo", "env", "command"} and vals:
        depth += 1
        if name == "command":
            while vals and vals[0].startswith("-"):
                vals.pop(0)
        elif name == "env":
            while vals and (vals[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", vals[0])):
                vals.pop(0)
        elif name == "sudo":
            options_with_value = {"-u", "-g", "-h", "-p", "-C", "-T"}
            while vals and vals[0].startswith("-"):
                option = vals.pop(0)
                if option in options_with_value and vals:
                    vals.pop(0)
        if not vals:
            break
        name = Path(vals.pop(0)).name.lstrip("\\")
    return name, vals


def push_target(command: str, cwd: Path) -> tuple[Path, str | None | bool]:
    """athena-10-1 S0 (Q12 #29): the project whose stage governs a push is the one pushed.

    Last top-level ``cd`` joined by && or ; before the push, then the push's own
    ``git -C <dir>`` options. A nested push (bash -c, eval, $(...)), a --git-dir /
    --work-tree push, any GIT_DIR-family variable anywhere in the command (inline,
    export, env wrapper -- it redirects the repository behind -C's back), or any
    unresolvable directory keeps today's rule: cwd.
    """
    strict: tuple[Path, str | None | bool] = (cwd, False)   # False = no destination named
    heredoc = narrow_heredoc(command)
    active = strip_comments(mask_body(command, heredoc) if heredoc and heredoc["quoted"] else command)
    if REPO_REDIRECT_ENV.search(active):
        return strict
    base = cwd
    for seg, sep in split_segments(active):
        _env, name, args = executable(tokenize(seg))
        name, vals = _unwrap(name.lstrip("\\"), [a.strip("'\"") for a in args])
        if name == "cd":
            nxt = resolve_dir(vals[0], base) if vals else Path.home()
            if nxt is None or sep not in ("&&", ";", "\n"):
                return strict
            base = nxt
            continue
        if name == "git" and git_subcommand(vals) == "push":
            target: Path | None = base
            i = 0
            while i < len(vals):
                value = vals[i]
                if value == "-C":
                    target = resolve_dir(vals[i + 1] if i + 1 < len(vals) else None, target)
                    if target is None:
                        return strict
                    i += 2
                    continue
                if re.match(r"^--(?:git-dir|work-tree)(?:=|$)", value):
                    return strict
                if value in {"-c", "--namespace", "--config-env"}:
                    i += 2
                    continue
                if not value.startswith("-"):
                    break
                i += 1
            return target, push_destination(vals[i + 1:])
    return strict


def push_destination(args: list[str]) -> str | None | bool:
    """The repository argument of ``git push``: False when none is named, None when it
    cannot be read without the shell ($VAR, `...`) -- the caller treats None as the project."""
    with_value = {"-o", "--push-option", "--receive-pack", "--exec", "--repo"}
    i = 0
    while i < len(args):
        value = args[i]
        if value.startswith("--repo="):
            dest: str | None = value[len("--repo="):]
        elif value == "--repo":
            dest = args[i + 1] if i + 1 < len(args) else None
        elif value in with_value:
            i += 2
            continue
        elif value.startswith("-"):
            i += 1
            continue
        else:
            dest = value
        return None if dest is None or re.search(r"[$`]", dest) else dest
    return False


def git_out(directory: Path, args: list[str]) -> list[str]:
    try:
        out = subprocess.run(["git", "-C", str(directory), *args], capture_output=True, text=True, check=True).stdout
    except Exception:  # noqa: BLE001
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def remote_urls(directory: Path) -> list[str]:
    """Every remote URL of a repository, as written and as git rewrites it (insteadOf / pushInsteadOf)."""
    urls = {" ".join(line.split()[1:]) for line in git_out(directory, ["config", "--get-regexp", r"^remote\..*\.(url|pushurl)$"])
            if line.split()[1:]}
    for name in git_out(directory, ["remote"]):
        urls.update(git_out(directory, ["remote", "get-url", "--all", name]))
        urls.update(git_out(directory, ["remote", "get-url", "--push", "--all", name]))
    return sorted(urls)


def normalize_remote(url: str, base: Path) -> str:
    """host/path for network remotes whatever the scheme (https, ssh://, scp-like); an absolute path otherwise."""
    raw = re.sub(r"/+$", "", url.strip())
    trimmed = re.sub(r"\.git$", "", raw)

    def local(value: str) -> str:
        # Real path (symlinks, macOS /var vs /private/var); Path.resolve resolves the
        # existing prefix when the path itself does not exist; .git dropped after.
        resolved = (base / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
        return re.sub(r"\.git$", "", str(resolved))

    if re.match(r"^file://", raw, re.I):
        return local(re.sub(r"^file://", "", raw, flags=re.I))
    match = re.match(r"^[a-z][a-z0-9+.-]*://(?:[^@/]+@)?([^/:]+)(?::\d+)?/?(.*)$", trimmed, re.I)
    if match:
        return f"{match.group(1)}/{match.group(2)}".lower()
    match = re.match(r"^(?:[^@/\s]+@)?([^:/\s]+):(?!//)(.*)$", trimmed)
    if match and len(match.group(1)) > 1:
        return f"{match.group(1)}/{match.group(2).lstrip('/')}".lower()
    return local(raw)


def same_project(target: Path, cwd: Path, dest: str | None | bool) -> bool:
    """Another checkout of the same project stays under the project's stage: a worktree or
    subdirectory (same git common dir), a separate clone sharing any remote URL with the
    project, a clone whose remote is the project itself, or a push whose destination is one
    of the project's remotes. Only a repository proven unrelated is judged by its own stage."""
    if same_repository(target, cwd):
        return True
    if dest is None:
        return True
    own = {normalize_remote(url, cwd) for url in remote_urls(cwd)}
    theirs = remote_urls(target)
    if isinstance(dest, str):
        theirs.extend([dest, *git_out(target, ["ls-remote", "--get-url", dest])])
    for raw in theirs:
        if normalize_remote(raw, target) in own:
            return True
        local = Path(raw) if Path(raw).is_absolute() else target / raw
        try:
            if local.is_dir() and same_repository(local.resolve(), cwd):
                return True
        except OSError:
            pass
    return False


def same_repository(a: Path, b: Path) -> bool:
    """A worktree or subdirectory of the project is the same project (its checked-out
    ``_index.md`` may lag), so the project's own stage governs it. Same repository =
    same ``git rev-parse --git-common-dir``; any git failure = not proven."""
    def common(directory: Path) -> Path | None:
        try:
            out = subprocess.run(["git", "-C", str(directory), "rev-parse", "--git-common-dir"],
                                 capture_output=True, text=True, check=True).stdout.strip()
            return (directory / out).resolve()
        except Exception:  # noqa: BLE001
            return None
    left = common(a)
    return left is not None and left == common(b)


def find_ai_state(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for _ in range(8):
        if (current / ".ai_state").is_dir():
            return current / ".ai_state"
        if current.parent == current:
            break
        current = current.parent
    return None


def read_field(idx_path: Path, field: str) -> str:
    try:
        m = re.search(rf'^{re.escape(field)}:\s*["\']?([^"\n#]*)["\']?', idx_path.read_text(encoding="utf-8"), re.M)
        return m.group(1).strip() if m else ""
    except OSError:
        return ""


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except (json.JSONDecodeError, OSError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return EXIT_SUCCESS
        command = tool_input.get("command") or tool_input.get("cmd")
        if not isinstance(command, str) or not command.strip():
            return EXIT_SUCCESS

        try:
            verdict = analyze(command)
        except Exception as exc:  # 解析失败 fail-closed, 与 CC 一致
            sys.stderr.write(f"[pre-bash-guard] BLOCKED: parser failure: {exc}\n")
            return EXIT_BLOCK

        if verdict.get("danger"):
            sys.stderr.write(f"[pre-bash-guard] BLOCKED: {verdict['danger']}\n")
            return EXIT_BLOCK

        if verdict.get("push") and not verdict.get("allow_push"):
            cwd = payload.get("cwd")
            cwd = Path(cwd).expanduser() if isinstance(cwd, str) and cwd.strip() else Path.cwd()
            origin = cwd.resolve()
            target, dest = push_target(command, origin)
            ai_state = find_ai_state(origin if target == origin or same_project(target, origin, dest) else target)
            if ai_state:
                stage = read_field(ai_state / "_index.md", "stage")
                # 与 CC P8 对齐: stage 为空 (idle, 无 sprint 在飞) 放行维护性 push
                if stage and stage != "ship":
                    sys.stderr.write(
                        f"[pre-bash-guard] BLOCKED: stage={stage}; git push requires ship. "
                        "Emergency override: ATHENA_ALLOW_PUSH=1 (owner accepts risk).\n"
                    )
                    return EXIT_BLOCK
        try:
            from _input_binding import capture_before
            capture_before(payload)
        except Exception as exc:  # Evidence failure is advisory; ship rejects missing binding.
            sys.stderr.write(f"[evidence-input] unavailable: {exc}\n")
        return EXIT_SUCCESS
    except Exception as exc:
        sys.stderr.write(f"[pre-bash-guard] BLOCKED: parser failure: {exc}\n")
        return EXIT_BLOCK


if __name__ == "__main__":
    raise SystemExit(main())

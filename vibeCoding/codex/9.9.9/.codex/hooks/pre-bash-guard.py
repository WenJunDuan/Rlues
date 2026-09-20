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
    """递归分析 bash 真会执行的每个命令替换; 不可解析 fail-closed。"""
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
    """窄形白名单 heredoc, 或 None 表示"与改动前逐字节同样分析"。

    lexer 的 import 刻意放在函数内: guard 必须在 _shell_lex 缺失或抛异常时照样
    加载并判定, 而该路径必须回落到今日分析 —— 查不到白名单只能过拦, 绝不放行。
    """
    try:
        from _shell_lex import simple_heredoc
        return simple_heredoc(command)
    except Exception:
        return None


def mask_body(command: str, span: dict[str, Any]) -> str:
    """把 heredoc 正文原地抹成等长空白, 保留换行。"""
    body = "".join(ch if ch == "\n" else " " for ch in command[span["start"]:span["end"]])
    return command[:span["start"]] + body + command[span["end"]:]


def analyze(command: str, depth: int = 0) -> dict[str, Any]:
    if depth > MAX_DEPTH:
        return {"danger": "nested shell depth exceeds policy"}
    heredoc = narrow_heredoc(command)
    # quoted 正文原样抵达消费者, 是文本不是命令: 在原始串上、先于 strip_comments
    # 掩码, 使检出永远不落在 bash 不执行的字符上。
    active = strip_comments(mask_body(command, heredoc) if heredoc and heredoc["quoted"] else command)

    substitution = analyze_substitutions(active, depth)
    if substitution.get("danger") or substitution.get("push"):
        return substitution
    # unquoted 正文确实被 bash 展开, 因此上面的主扫描逐字节不变, 另把正文按干净
    # 词法态单独再扫一遍: 检出只增不减 —— 这关掉了正文行首 "#" 遮蔽真实替换的洞。
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
        if name == "git" and git_subcommand(args) == "push":
            return {"push": True, "allow_push": env.get("ATHENA_ALLOW_PUSH") == "1"}

    for i in range(len(parsed) - 1):
        if parsed[i][3] == "|" and parsed[i][1] in {"curl", "wget"} and parsed[i + 1][1] in SHELLS:
            return {"danger": "network response piped to shell"}
    return {}


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
            ai_state = find_ai_state(cwd)
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

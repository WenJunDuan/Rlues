#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.2 · Codex UserPromptSubmit hook

触发: 用户提交 prompt 前
职责:
- 轻量预检 (无重负载)
- 不阻塞 (任何异常都 exit 0)

源: https://developers.openai.com/codex/hooks (UserPromptSubmit 事件)
"""
import json
import sys

EXIT_SUCCESS = 0


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}
        # 当前版本 user-prompt-submit 仅作占位 + 与 index-updater 并行触发的 hook 入口
        # 未来可扩: 检测 user prompt 含 /pace, /polish 等命令时主动加载相应 skill 摘要
        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[user-prompt-submit] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())

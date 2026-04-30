# lesson-drafter — Codex 端说明

Codex CLI 当前只支持 process-based hooks (shell 命令), **不支持** CC 的 `type: "agent"` hook。
因此 Codex 端只有 Python 版本 (`lesson-drafter.py`) 一个轨道, 没有 agent 双轨。

如果你需要 agent 智能识别能力, 在 CC 端启用 agent 版本即可 (见 `~/.claude/hooks/lesson-drafter-agent-mode.md`)。
两端用同一份 .ai_state/, 在 CC 端起草的 lesson 在 Codex session 里也能 R₀ 阶段读到。

---
name: antigravity
description: 把可并行的重任务外包给 Google Antigravity CLI (agy -p)。用户要求并行跑或批量外包时触发。
---

# /antigravity — Athena 端 agy 调度 skill (v9.6.2)

## 概念

Antigravity CLI (命令 `agy`) 是 Google 在 2026-05-19 替代 Gemini CLI 的 Go 编写的终端 agent.
- 官方文档: https://antigravity.google/docs/cli-using
- 官方 transition: https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli
- Headless 调用: `agy -p "<prompt>"` (单次, 适合 Athena 外包)
- TUI 模式: `agy` (用户直接交互, 但 Athena 场景下不用)

## 例外与降级

- 若 `agy` 命令存在但调用失败 (网络 / 认证): 主 agent 在 `sprints/{current_sprint_slug}/runtime-events.md` 记录 `ag-call-failed`, 自动降级
- 若 `agy` 输出明显是垃圾 (例如长度 > 50KB 或包含 prompt 泄漏): 主 agent 拒绝 merge, 重新发更精确的 prompt
- agy 连续失败 ≥ 3 次 → 当 session 禁用 agy, 后续都走降级路径

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。

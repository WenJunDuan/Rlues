# /vibe-review $ARGUMENTS

单独运行质量审查, 不走完整开发流程。

有 .ai_state/project.json → 按当前 Path 深度触发 $pace skill 的审查阶段逻辑:
- Quick: 只跑 /review 内置
- Feature+: /review 内置 + spawn_agent reviewer 并行 → 合并 findings
- System: 上述 + npx ecc-agentshield scan

无 .ai_state/ → 快速审查: `/review` (Codex 内置, 看当前 diff)

焦点: $ARGUMENTS

# Route Note — 2026-07-10-claude-code-9-9-1-design

- **输入**: 以 CC 9.9.0 为基线，设计 CC 9.9.1；对齐当前 CX，并吸收 Claude Code 当前最优原生能力，交 Fable5 review。
- **候选**: Refactor（只补 CC parity）vs System（settings/hooks/agents/skills/migrate/validation 全链设计）。
- **权衡**: 爆炸半径=6 子系统 · 可逆=高（版本目录）· 紧急=中 · 不确定性=中（stable/latest 与 experimental 边界）。
- **决策**: **System + roadmap + design-only** · 置信度 0.98。
- **基线**: Git object `eb1ab06bae8e9a9bd576643e941c4e5d59360fb1`（CC 9.9.0 `.claude` tree）只读。
- **假设**: CC/CX 对齐状态语义和门禁强度，不对齐工具名、模型或 hook payload。
- **廉价退出**: Fable5 判定超出 patch → 只保留 P0/P1 兼容层，其余拆到后续版本；未 review 不实现。

# 决策记录（ADR）

何时写：选了一条难以回退、或会约束后续 sprint 的路（数据模型、协议、依赖、架构边界）。可逆的实现细节不写。

- 位置：`.ai_state/decisions/<YYYY-MM-DD>-<slug>.md`，一事一档，≤100 行。
- 模板：`~/.athena/current/templates/decision.md`（背景 / 选项 / 决定 / 权衡 / 影响）。
- 至少两个选项，各写优缺点；「决定」一句话；「影响」写对后续 sprint 的约束，以及是否要更新 `architecture/`。
- 推翻旧决定：新档写 `supersedes: <旧 slug>`，旧档改 `status: superseded`、`superseded_by: <新 slug>`；不删旧档。
- design.md 引用决策用相对路径。

经验与技巧（原 compound learning / trick）：值得复用的写成 decision 或 rules 条目（附出处与删除条件，见源码仓 `core/rules.md`）；一次性的记在 sprint log.md。

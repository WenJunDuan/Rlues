# Git

- commit：`<type>(<scope>): <subject>`；type ∈ feat fix refactor perf docs test chore ci style revert；subject ≤50 字符，祈使句，不加句号；body 写 why，引用 `Closes #n` / `Refs #n`。
- 署名按当前会话的 attribution 规则；子 agent 按它自己会话的规则，不照抄主会话。
- `.ai_state` 记账随代码同一提交；不单独提交记账。
- branch：`<type>/<short>` 或 `<type>/<issue>-<short>`，≤40 字符，英文。
- PR：变更类型、说明、关联 issue、验证步骤、检查清单（测试、lint、文档、R/S 已 polish）。
- 禁止：force push 受保护分支；amend 或 reset 已推送的公共提交；提交密钥（删了历史里仍在）。
- 推送、建 PR、打 tag 推远端先确认；推送本项目仓库在 ship 前被 H5 拦。

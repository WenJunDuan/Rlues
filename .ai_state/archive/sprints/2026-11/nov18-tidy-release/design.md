---
sprint: "nov18-tidy-release"
path: "Bugfix"
created: "2026-11-18"
req: "/tmp/athena-nov18-review-req.md"
roadmap: ""
item: ""
base_commit: "5fceafb"
repro_test: ""
review_ignore: []
---

# Bugfix — nov18-tidy-release

## 当前与预期
归档拆散跨空行的 Markdown 子项，轮转可能覆盖并发追加，当前发行说明仍指向旧候选。保留 CLI 和安装配置边界。
- AC1: 跨空行的未完成子项和父项整组保留并出现在 brief。
- AC2: 轮转期间追加的事件仍可找到，保留热 sprint 来源，回归可重复。
- AC3: 发布包内说明与 VERSION、路径一致，保留历史说明并验证构建。
- AC4: 核查本机与模板的 Codex、Claude 能力和配置，区分已配置和已实测。

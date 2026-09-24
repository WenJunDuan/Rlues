---
name: athena-init
description: 初始化 Athena 项目：建 .ai_state、复制 _index 模板。已存在则跳过，不清空。
---

# /athena-init — 项目初始化

PACE 的项目状态在 `.ai_state/`。本 skill 只做这件事。已 init → 用 `/athena-status`，不覆盖。

## 触发

新项目首次 `/athena-init` 或用户说初始化。详细步骤 `references/playbook.md`。

## 例外

- 非 git 仓库：拒绝，先 `git init`
- `_index` 模板缺失：用 playbook 最小 frontmatter，不准丢掉 path/stage/sprint 字段
- 已有 `.ai_state/`：不覆盖，不清空

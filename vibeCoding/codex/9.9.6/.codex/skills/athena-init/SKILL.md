---
name: athena-init
description: Athena 项目初始化：探测平台与工具、建 .ai_state/、填 _index 模板。用户显式调用时触发。
---

# /athena-init — 项目初始化 (Codex, v9.9.6)

Memory contract: **Tier1 working memory** is non-authoritative; **Tier2 persistent memory** is the created `.ai_state`; **_index.md retrieval router** owns bounded recovery pointers/history.

## 触发

用户在新项目首次要求初始化 Athena. 已 init 的项目 → 跳过, 提示用 athena-status 查状态.

## 例外

- 非 git 项目: 拒绝, 提示先 `git init`
- 模板缺失: fallback 内置 minimum template (保留 Athena 核心 frontmatter 字段)
- 已 init 又跑: 不覆盖, 显式问"重新初始化?会清空 .ai_state/"

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。

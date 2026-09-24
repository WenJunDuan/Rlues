---
name: athena-init
description: 初始化 Athena 项目状态并按用户选择探测当前端 CLI，保留既有 .ai_state。
disable-model-invocation: true
---

# /athena-init — 项目初始化 (v9.9.9)

Memory contract: **Tier1 working memory** is non-authoritative; **Tier2 persistent memory** is the created `.ai_state`; **_index.md retrieval router** owns bounded recovery pointers/history.

## 触发

用户在新项目首次运行 `/athena-init`. 已 init 的项目 → 跳过, 提示用户用 `/athena-status` 查状态.

用户要求初始化时调用 `scripts/init-platforms.py`，完整命令见 `references/playbook.md`。重复执行保留已有项目状态，不清空 `.ai_state`。用户选单端时不探测另一端认证或 CLI；模型、effort、provider 与权限由原生配置决定。

## 例外

- 若用户在非 git 项目跑: 主 agent 拒绝, 提示先 `git init`
- 若 pace/templates/_index.md 不存在: 主 agent fallback 用内置 minimum template (不要去掉 Athena 核心 frontmatter 字段)
- 若用户已 init 又跑 /athena-init: 不覆盖, 显式问 "重新初始化吗?会清空 .ai_state/"

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。

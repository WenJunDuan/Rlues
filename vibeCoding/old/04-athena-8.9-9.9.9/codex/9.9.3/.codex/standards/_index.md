---
version: "9.9.3"
purpose: "用户项目规范 / 上下文提示词 (与 skills/ 平级独立)"
note: "本文件供 SessionStart hook 注入摘要 (≤ 600 字符) 进 system prompt. 详细规则按 stage 触发条件加载."
---

# Athena Rules · 项目规范索引

## 概念

`standards/` 是 **用户规范上下文提示词** — 项目特有的代码规范、UI 要求、文档要求、Git 约定、安全自查。

⚠️ **不要混淆**:
- `standards/` (本目录, CX 端) ≠ `~/.codex/rules/*.rules` (Starlark 权限) 或 `permissions` profile (命令权限, 由 settings.json 控制)
- `standards/` (CX) ⟷ `rules/` (CC) 内容对称, 仅目录名不同 (避免和 Codex 原生 `.rules` Starlark 命令权限冲突)

## 文件清单 (5 个)

| 文件 | 用途 | 注入 stage |
|---|---|---|
| coding-standards.md | 代码规范 (P0/P1/P2 分级) | impl, review, polish |
| ui-guidelines.md | UI 设计规范 | design, impl, review |
| doc-style.md | 文档 / 注释规范 | review, polish |
| git-conventions.md | commit 前缀, branch 命名, PR 模板 | ship |
| security-checklist.md | 安全自查 (密钥 / 输入 / 依赖) | impl, review |

## 加载机制 (三入口)

1. **SessionStart hook** 注入本 `_index.md` 摘要 (≤ 600 字符) 进 system prompt
2. **PACE SKILL.md** 在 stage 切换时显式 `Read ~/.codex/standards/<file>.md`
3. **Subagent frontmatter** `attach_to_rules: [...]` 字段在 spawn subagent 时拼接对应 rule 全文进 developer_instructions

## 规则覆盖原则

- 当一个 finding 同时违反多条规则时, **取严重度最高的那条**作为主因
- P0 (违反 = REWORK): 安全 / 类型安全 / DRY / SRP / Sisyphus 完整性
- P1 (违反 = CONCERNS): 长度 / 命名 / 错误处理 / 测试覆盖
- P2 (建议): 注释 / 嵌套 / magic number

## 项目自定义

每个使用 Athena 的项目可以**覆盖**这些 standards:
- 在项目 `~/.codex/standards/` (USER) 或 `.codex/standards/` (REPO) 放同名文件 → 覆盖 USER 级
- 项目级的规则与 USER 级合并, 项目级胜出

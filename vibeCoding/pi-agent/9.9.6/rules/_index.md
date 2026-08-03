---
version: "9.9.6"
purpose: "用户项目规范 / 上下文提示词 (pi 端)"
note: "pi 端无 SessionStart hook 注入; 加载走 AGENTS.md 指令 + prompt 模板内引用."
---

# Athena Rules · 项目规范索引 (pi 端)

`rules/` 是用户规范上下文提示词 — 项目特有的代码规范、UI 要求、文档要求、Git 约定、安全自查。内容与 CC 端 `rules/`、CX 端 `standards/` 对称 (铁律[跨平台 schema parity])。

## 文件清单 (5 个)

| 文件 | 用途 | 加载 stage |
|---|---|---|
| coding-standards.md | 代码规范 (P0/P1/P2 分级) | impl, review, polish |
| ui-guidelines.md | UI 设计规范 | design, impl, review |
| doc-style.md | 文档 / 注释规范 | review, polish |
| git-conventions.md | commit 前缀, branch 命名, PR 模板 | ship |
| security-checklist.md | 安全自查 (密钥 / 输入 / 依赖) | impl, review |

(另含 iron-law-provenance.md: 铁律出处档案, 不注入, 供人查阅)

## 加载机制 (pi 端, 两入口)

1. **AGENTS.md 指令**: agent 在进入对应 stage 时按上表自行 `read rules/<file>.md`
2. **prompts/ 模板**: 角色模板内显式要求先读对应 rule

CC 端的 SessionStart 注入 / subagent `attach_to_rules` 在 pi 无对应机制; Phase-2 extensions 落地后可用 `before_agent_start` 事件恢复注入。

## 规则覆盖原则

- 一个 finding 同时违反多条规则时, 取严重度最高的那条作为主因
- P0 (违反 = REWORK): 安全 / 类型安全 / DRY / SRP / Sisyphus 完整性
- P1 (违反 = CONCERNS): 长度 / 命名 / 错误处理 / 测试覆盖
- P2 (建议): 注释 / 嵌套 / magic number

## 项目自定义

项目 `.pi/rules/` 放同名文件 → 覆盖 USER 级 (~/.pi/agent/rules/), 项目级胜出。

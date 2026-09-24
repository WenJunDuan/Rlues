# PACE References · Plugins 编排 (v9.9.0 · U6, Codex)

> enabledPlugins 是 CC settings.json 概念, CX 端等价物: 已注册 skills (playwright/context7 已在 config.toml) + AgentShield CLI (通用) + commit 规范手写. 原则只有一条:
> **插件是能力, 不是工作流** — 与 Athena 流程冲突时, Athena workflow 赢 (铁律[三原语]: Workflow 统领).

## PACE stage × plugin 路由表

| stage | 用什么 | 怎么用 | 不要 |
|---|---|---|---|
| brainstorm | Athena brainstorm skill | superpowers (brainstorming) 是 CC 端插件, CX 无对应 — 用 Athena 自有 skill | 不让提问技术接管产出格式 (产出必须落 brainstorm.md) |
| plan / design | **context7** | 查库/框架官方文档, 出处引用 (铁律[出处优先]); CX 已注册 context7 skill (config.toml) | 不用记忆里的 API 签名 |
| impl | — | Athena generator subagent (TDD); feature-dev 是 CC 端插件, CX 无对应 — 用 Athena 自有 skill (它有自己的 plan/impl 环, 与 PACE 撞车, 本就不该进 Athena 项目) | 不引入任何自带工作流的外部实现环 |
| runtime-verify | **$playwright** | 前端/E2E 实跑, 证据晒 transcript; CX 已注册 playwright skill (config.toml, 见 $playwright / athena-runtime-verify) | 不用 browser 截图代替断言 |
| review | Athena 三件套 | reviewer+spec-compliance+evaluator 是**正典**; code-review 是 CC 端插件, CX 无对应 — 用 Athena 自有 skill, Refactor/System 需要对照时 spawn_agent reviewer.toml 二跑, findings 并入 pass1.md | 不用外部审查替代三件套 (它不懂 design.md 与 checklist) |
| security-review | ECC-AgentShield | `npx ecc-agentshield` CLI 扫描 (CLI 通用, 双端一致) | — |
| ship | 手写 conventional commit | CX 无 commit 插件 — 按 standards/git-conventions.md 手写规范 message | 不自动 push (push 受 stage 门禁) |
| 跨端 | codex-plugin-cc (≥1.0.5) | 本端即 Codex, transfer 的接收方 — CC 端 /codex:transfer (M5c) 移交的持久线程在本端执行, 接手前先读 .ai_state | v1.0.4 以下有 Skill 递归 bug, 禁用旧版 |

## 冲突仲裁 (记住这三条就够)

1. **产出位置**: 任何插件产出想留下来 → 必须落 `.ai_state/` 对应文件 (文档即真相), 不允许只活在对话里
2. **门禁豁免**: 没有. 插件干的活同样过 delivery-gate (workflow 产物不豁免的同一原则)
3. **重复能力**: Athena 自有 skill 与插件重叠 (brainstorm/context7/playwright) 时, Athena skill 是入口, 插件是它调的工具

## 例外

- 非 Athena 项目 (无 .ai_state): 插件自由使用, 本表不适用
- 插件被禁用/缺失: 全部有降级路径 (context7→WebSearch 官方文档 / playwright→curl+CLI 实跑 / commit→手写 conventional commit), 缺插件不 block 流程

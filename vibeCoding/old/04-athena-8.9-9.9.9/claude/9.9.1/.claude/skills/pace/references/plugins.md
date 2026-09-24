# PACE References · Plugins 编排 (v9.9.0 · U6)

> settings.json enabledPlugins 里的 8 个插件如何进 PACE. 原则只有一条:
> **插件是能力, 不是工作流** — 与 Athena 流程冲突时, Athena workflow 赢 (铁律[三原语]: Workflow 统领).

## PACE stage × plugin 路由表

| stage | 用什么 | 怎么用 | 不要 |
|---|---|---|---|
| brainstorm | superpowers (brainstorming) | Athena brainstorm skill 为主, superpowers 的提问技术做补充 | 不让它接管产出格式 (产出必须落 brainstorm.md) |
| plan / design | **context7** | 查库/框架官方文档, 出处引用 (铁律[出处优先]) | 不用记忆里的 API 签名 |
| impl | — | Athena generator subagent (TDD) | **feature-dev 插件的完整工作流不用** — 与 PACE 撞车 (它有自己的 plan/impl 环); 只在非 Athena 项目里用 |
| runtime-verify | **playwright-skill** | 前端/E2E 实跑, 证据晒 transcript (见 $playwright / athena-runtime-verify) | 不用 browser 截图代替断言 |
| review | code-review (可选第 4 审) | Athena 三件套 (reviewer+spec-compliance+evaluator) 是**正典**; Refactor/System 可追加 code-review 插件跑一遍作对照, findings 并入 pass1.md | 不用它替代三件套 (它不懂 design.md 与 checklist) |
| security-review | ECC-AgentShield | `npx ecc-agentshield` CLI 扫描 (权限已放行) | — |
| ship | commit | commit message 规范化 | 不让它自动 push (push 受 stage 门禁) |
| 跨端 | codex-plugin-cc (≥1.0.5) | /codex:transfer 移交 (M5c), /codex:rescue 救援 | v1.0.4 以下有 Skill 递归 bug, 禁用旧版 |

## 冲突仲裁 (记住这三条就够)

1. **产出位置**: 任何插件产出想留下来 → 必须落 `.ai_state/` 对应文件 (文档即真相), 不允许只活在对话里
2. **门禁豁免**: 没有. 插件干的活同样过 delivery-gate (workflow 产物不豁免的同一原则)
3. **重复能力**: Athena 自有 skill 与插件重叠 (brainstorm/context7/playwright) 时, Athena skill 是入口, 插件是它调的工具

## 例外

- 非 Athena 项目 (无 .ai_state): 插件自由使用, 本表不适用
- 插件被禁用/缺失: 全部有降级路径 (context7→WebSearch 官方文档 / playwright→curl+CLI 实跑 / commit→手写 conventional commit), 缺插件不 block 流程

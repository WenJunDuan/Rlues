---
doc_type: decision
slug: "retire-local-telemetry-collection"
created: "2026-08-27"
sprint_slug: "2026-08-27-athena-9-9-8"
status: accepted
deciders: ["用户 (2026-08-27 拍板)", "claude-fable-5 (复盘建议)"]
---

# Decision: retire-local-telemetry-collection

## 背景 (context)

Athena 自建 token-usage-collector (CC 454 行 / CX 495 行) + tool-trace 写入面，在 PostToolUse 上持续记账。9.9.8 已把遥测移出 Git (`.runtime/` ignored + retention)，design rev2 F8 留了"降级为仅补 harness 不给的字段"的可选项。同时 CC 2.1.243 起 `/usage` 已有 per-loop 用量拆分，官方 OTEL 遥测可用。本 sprint 实测也暴露自建链的脆弱性：AC11 的冻结 baseline 文件在本机已消失、标签粒度 (stage+model) 分不开 impl 内混合角色。

## 选项 (options considered)

### 选项 A: 降级保留 (design F8 原案)
- ✅ 保留 role 标签扩展空间，AC11 类度量可继续
- ❌ 双端 ~950 行 hook 维护税继续；PostToolUse 记账面仍在；baseline/retention 的证据存续问题仍要治

### 选项 B: 整体退役，依赖官方 `/usage` (+需要时 OTEL)
- ✅ 直接删掉双端最大的两个绿区 hook；PostToolUse 面大幅收窄；无自建账本就无"账本证据悬空"问题
- ❌ 失去 per-turn 细粒度归因；AC11 式"控制面占比"度量不再可复算

## 决定 (decision)

**选 B。用户 2026-08-27 拍板：本地不再需要遥测采集，`/usage` 就够了。**

## 权衡 (trade-offs)

放弃 per-turn 归因意味着"降本/占比"类验收不能再用自家账本证明。替代度量工具改为**代表性任务 eval 套件**（借 Anthropic AI-native SDLC playbook 的 CI evals play：10–20 个真实任务 + 可接受结果，CLAUDE.md/skill/hook/模型变更时重跑）+ `/usage` 读数。

## 影响 (consequences)

- 对后续 sprint: hotfix 候选——拆除双端 token-usage-collector 与 tool-trace 写入注册；`.gitignore` 遥测段与 `.runtime/` retention 逻辑随之简化；AC 里不得再写依赖自建账本的量化门槛
- 使 explore `athena-9-9-8-post-ship-directions` 的第 1 条 (role-labeled telemetry) **作废**、第 8 条从"降级"改为"整体拆除"（已同步修订）
- 对 architecture/: 下次 System sprint 更新 athena-9.9.8.md 后继档时，把"telemetry 退出 Git"条目改写为"本地采集已退役"

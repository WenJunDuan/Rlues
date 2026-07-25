---
roadmap_slug: "athena-9-9-6-prompt-engineering"
created: "2026-07-25"
trigger: "user_explicit"
estimated_total_complexity: "XXL"
status: "awaiting-user-confirmation"
---

# Roadmap — Athena 9.9.6 Prompt Engineering

## 背景

Claude Code 已进入 Opus 5 / 2.1.219 合同，Codex 当前模型解析目标为 GPT-5.6 Sol，稳定 CLI 为 0.144.4。Athena 9.9.3 的 PACE / `.ai_state` 内核仍有效，但双端配置、角色模型、skill discovery、prompt context 和平台默认出现明显漂移。

本 roadmap 先做研究与行为基线，再更新共享语义和双端 adapter，最后通过迁移、runtime、review、polish 和 release gate 收口。

## 总体方案

建立一个小型跨端语义合同，根 prompt、stage 名、role/skill catalog 从该合同生成或校验；CC/CX 保留真实机制 adapter。把平台已默认开启的能力和用户个人偏好从发行模板移除，把模型与 effort 放回角色边界，把 `_index` 收缩成当前状态索引。所有删减先用 9.9.3 场景观察失败/冗余，再用 9.9.6 对照验证。

## 子 feature 拆分

详见 `items.yaml`。

| # | slug | title | 复杂度 | 依赖 |
|---|---|---|---|---|
| 1 | research-and-audit | 官方/外部调研与 9.9.3 现状审计 | M | 无 |
| 2 | shared-kernel-and-evals | 共享语义核、skill catalog 与 prompt eval baseline | XL | 1 |
| 3 | claude-opus5-adapter | Claude Code 2.1.219 / Opus 5 配置与角色 adapter | L | 2 |
| 4 | codex-gpt56-adapter | Codex 0.144.4 / GPT-5.6 配置与角色 adapter | L | 2 |
| 5 | skills-pace-state-convergence | skills / PACE / `.ai_state` 提炼与迁移 | XL | 2 |
| 6 | integration-release | 双端集成、迁移、runtime、review、polish 与发布 | XL | 3, 4, 5 |

## 推进顺序

1. 冻结 item 1 的研究、现状统计和 source map。
2. item 2 先建立共享合同与 9.9.3 baseline；没有 baseline 不删 prompt。
3. item 3 / 4 在独立 worktree 中并行，只改各自 adapter；共享合同由 item 2 锁定。
4. item 5 串行调整 skill catalog、stage references 与 state schema，避免两个写者同时改共享语义。
5. item 6 合并后执行 exact-version runtime、migration、prompt A/B、2+1 review、polish 和 architecture 更新。

## 版本与兼容策略

- Claude Code floor：`2.1.219`，发布时核对最新稳定 patch。
- Codex floor：`0.144.4`，发布时核对最新稳定 patch，不跟 alpha。
- 模型使用 alias / current resolver，不在一方 API 基线中 pin dated model ID。
- 9.9.3 为迁移基线；9.9.6 不就地改旧版本目录。
- 用户自有 provider、privacy、desktop、approval/sandbox 设置只 preserve，不由迁移静默覆盖。

## 风险与权衡

- 风险：删 prompt 后 gate compliance 下降。
  - 缓解：先运行无变更 baseline；按指令组一次删一组；每组跑同一场景集。
- 风险：共享生成机制自身变成复杂新框架。
  - 缓解：只生成根 prompt / catalog 元数据并校验关键语义；不把全部 5000 行 skills 模板化。
- 风险：CC/CX 为追求 parity 而伪造 API 对称。
  - 缓解：合同共享“为何/必须满足什么”，adapter 单独实现“如何”。
- 风险：移除全局模型 override 后成本上升。
  - 缓解：角色矩阵 + Sol/Terra、Opus/Sonnet A/B；高价模型只用于高价值边界。
- 风险：state schema 精简破坏历史 consumer。
  - 缓解：consumer inventory、fixture migration、fresh HOME 和旧项目恢复测试全部通过才删除字段。
- 风险：当前 subagent raw binding event 未产生，无法独立 critic。
  - 缓解：本轮 design 标为 research draft；进入 item 2 前先修复/验证 binding harness，再完成正式 plan critique。

## 历史决策对齐

- quantum skills 保持 7→2，不恢复旧入口：`compound/2026-07-13-decision-quantum-7-to-2-consolidation.md`。
- 9.9.2 的 `_index` consumer audit 在当时有效；9.9.6 只在迁移 consumer 与测试后重审低价值字段：`compound/2026-07-13-decision-index-field-audit.md`。
- 未知证据仍为 `null/unknown`，不得因 prompt 减重改成成功：`compound/2026-07-08-decision-token-usage-null-and-subagent-stop.md`。
- worktree ledger 与 canonical skill path 必须有 runtime 覆盖，不能只做静态扫描。

## 整体验收

- [ ] `items.yaml` 全部 `completed`。
- [ ] Claude / Codex release 配置只含当前官方支持且有意偏离默认的项。
- [ ] stale/legacy/undocumented 配置 denylist 为零。
- [ ] CC 角色模型不再被全局 env 覆盖，`opus` 在 floor 上解析为 Opus 5。
- [ ] CX 使用 built-in OpenAI provider，模型/compact metadata 无手工伪造。
- [ ] 双端 skill catalog trigger metadata ≤ 6500 chars，26 skills 均可发现；维护类 skill 不隐式运行。
- [ ] `_index.md` ≤ 4 KiB，恢复所需状态完整；易变 capability 有时间戳。
- [ ] 9.9.3 vs 9.9.6 prompt eval 在正确性不下降前提下，至少一个效率指标显著改善。
- [ ] CC/CX runtime、迁移、fresh install、validator、2+1 review、runtime-verify、polish 全绿。
- [ ] 9.9.6 current-state architecture 与一事一档 compound learning 已更新。

## 用户确认点

本 roadmap 确认后才进入 item 2 的正式 plan/design gate。另有一个独立授权点留到实现前确认：是否继续把 `approval_policy=never` + `danger-full-access` 作为 Codex 发行默认；本研究不会静默改变该权限边界。

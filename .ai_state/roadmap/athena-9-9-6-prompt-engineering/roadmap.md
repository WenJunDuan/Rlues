---
roadmap_slug: "athena-9-9-6-prompt-engineering"
created: "2026-07-25"
revision: "v3.1"
status: "superseded-by-user-closure"
implementation_authorized: false
git_commit_authorized: false
estimated_total_complexity: "XXL"
---

# Roadmap — Athena 9.9.6 Prompt Engineering v3.1

## Closure

2026-07-28 用户决定停止 9.9.6 prompt-engineering / gate-descaling 方向：原本的改动反复且叙述冗长，后续不再考虑同类扩展。已完成实现、同步、验证输出与历史会话保留；未执行的剩余 adapter、验证、review、polish 与 release 不改写为 completed，本 roadmap 仅作为历史记录。

## Direction

以 9.9.3 为不可变模板，构建 Claude Code 与 Codex 两个自包含的 9.9.6 endpoint。保留 PACE + `.ai_state` 双内核，不增加 shared contracts、renderer、第二状态树或 tracked tests。

关键平台合同：

- CC floor 2.1.219+，`opus` 解析到 Opus 5，移除 dated model pins、全局 subagent override 和 default-on noise；
- CX floor 0.145.0+，使用 built-in `openai` provider，保留 App/CLI、WSL、`[desktop]`、plugins 和 API Key 用户；
- Skills 保持 26 个，明确隐式/显式调用控制；
- PACE 保持 4 core + 5 conditional；
- AI state 优化自动注入和 retention，不新建 capability state layer；
- 测试资产按用户指定放 `vibeCoding/scripts/`，只在本地存在，不提交 Git。

详细设计与 AC：`../../sprints/2026-07-25-athena-9-9-6-prompt-engineering/design.md`。

## Sequence

```text
research/audit
  → design baseline + v3.1 critic
      → platform contract + Opus 5 design decisions
          → Skills/PACE/AI-state/hooks design freeze
              → reviewable dual-endpoint bottom draft
                  ├→ CC 9.9.6 final adapter
                  └→ CX 9.9.6 final adapter
                      → local validation/migration
                          → review/polish/release
```

## Delivery boundaries

- 9.9.3 目录零修改；
- 9.9.6 release adapters 可 tracked，根 `.claude/` 用户目录仍 ignored；
- 本地 test/eval 资产不得出现在 Git diff；
- 未经后续授权不得 commit、push 或 release；
- 未经 exact-version 或 N≥3 eval 证明的模型/effort/hook 行为保持候选。

## External ecosystem extraction

- Pi：薄 root prompt、lazy skill 与 always-on token audit；
- grill-me：brainstorm 一次一问 + strawman；
- Trellis/GSD：最小 task context packet、验证后知识晋升；
- Superpowers：skill 行为测试、原实现者 resume、branch finishing；
- Spec Kit：轻量 roadmap→design→checklist 一致性；
- Amp：异构 review 可用时优先；
- Beads：只吸收依赖意识，不建 DAG scheduler。

## 编号收敛 (2026-07-28, C3)

自本日起**唯一权威编号 = 本 roadmap `items.yaml` 的 item slug**。checklist 任务号 (B/G 系列) 与
update-plan 的 F1-F7 均须在条目内注明所属 item slug, 不再独立成体系。历史 F↔item 映射:
F1-F4→claude-adapter/codex-adapter · F5→local-validation-and-migration · F7→review-polish-release ·
F6 已砍换 dogfood 指标 (update-plan 2026-07-28)。计划外批次 (harness-gate / gate-descaling) 已补录为
completed items — roadmap 必须描述实际发生的工作, 否则它是装饰 (二刀 review C4)。

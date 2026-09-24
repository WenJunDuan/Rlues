---
sprint_slug: "2026-09-24-s5-prompts-v2"
path: "Feature"
created: "2026-09-24"
roadmap: "athena-10-1"
item: "s5-prompts-v2"
branch: "athena-10.1"
base_commit: "934545a"
---

# Design — S5 · 提示词 v2

> 设计真相：`roadmap/athena-10-1/design.md` §9；consolidation 标 S5 的条目。本片让宪法 / 规则 / skills / agents 与 S2–S6 的门禁和 CLI 一致。

## 方案

- build：`platform.json` 增 `rename`（core 路径前缀改名：CC `AGENTS.md→CLAUDE.md`、CX `rules/→standards/`）、`extra`（Pi 从 core 取宪法与规则）、`stages_md`（由 stages.yaml 生成 stages.md，三端同源，禁止手改）。
- 宪法：`core/package/AGENTS.md` 一份（§9.1 + consolidation 措辞条），三端生成，≤2,500 B。
- 规则：`core/package/rules/*` 一份，进上下文合计 ≤300 行；`core/rules.md`（不安装）逐条溯源：补偿的失败 / 删除条件 / 位置。
- skills：删 antigravity；athena-preferences→athena-init；athena-checkpoint、athena-issue→athena-status；compound→pace/references/decisions.md；全部 SKILL.md ≤60 行（长内容进 references/）；description 合计 ≤6,500 字符；pace references 改写为 10.1（H1–H5/A1–A10、CLI 流程），删除 9.9.9 门禁细节。
- agents：保留 architect、generator、polish-worker、reviewer；删 critic、evaluator、spec-compliance（CX 另删 docs_researcher、pr_explorer）；CC 头 `omitClaudeMd: true`；派工模板两句（不带 model:；署名按子会话规则）。

## 验收标准

- AC1: 三端宪法由同一源生成，逐字相同（除 {{athena:}} 变量），≤2,500 B，不含全大写强调与「CC 无原生 /goal」。
- AC2: 进上下文规则合计 ≤300 行；`core/rules.md` 每条规则有「补偿的失败 / 删除条件 / 位置」。
- AC3: 所有 SKILL.md ≤60 行；description 合计 ≤6,500 字符；被删/合并的 skill 不再出现在 dist；dist 中不再引用已删的 9.9.9 hook 文件名、review-binding、tdd-evidence、review-packet、critic、setup-athena.py。
- AC4: agents 只剩 4 个（三端）；CC 头含 `omitClaudeMd: true`；派工模板两句在 pace references 中。
- AC5: consolidation 中 S5 措辞类条目逐条落地（清单见 session-log）。

## 不做

模型实测评测（S8 已取消）；Pi 0.87 硬停（S7 已取消）。

# Rlues (VibeCoding Athena) · 技术栈 / 阻碍 / 完善设计

> 2026-07-14 重排 (v9.9.3 发布后; 首版 2026-07-11 基于 9.9.1, 过时部分已全部更新)。
> 总路线: **① 完善 quantum → ② 本仓收尾 (本文档) → ③ AI infra (S5 chat 产品, 单开项目)**。
> quantum 侧对应文档: `quantum-backend/.ai_state/architecture/blockers-and-roadmap.md`。

## 技术栈 (9.9.3 形态)

| 层 | 选型 |
|---|---|
| 本体 | 提示词架构 (Athena PACE): 9-stage 状态机 + 铁律 + 三原语; **gate 档案 schema 已文档化进 pace/references/stages.md** |
| CC 端分发 | `vibeCoding/claude/{version}/` → `~/.claude`: CLAUDE.md + skills + hooks (.cjs; subagent-tracker **自动写** assignments/events.jsonl) + agents + rules/ |
| CX 端分发 | `vibeCoding/codex/{version}/` → `~/.codex`: AGENTS.md + prompts + standards + hooks (.py) + agents.toml; **gate 与 CC 同 schema 同 fail-closed 语义 (双端对称)** |
| 全栈生成 | **`quantum-codegen` 单 skill 六 mode** (page/module/db/unit/security/e2e) — 9.9.3 将原 scaffold-page-gen / scaffold-module-gen / db-schema-gen / unit-test-gen / security-test / playwright-e2e 家族合并; pack contract + playbook + adapter 全收进 references/ |
| 运行期读取 | `quantum-data` (原 project-data-reader 更名) — MCP client 读目标系统能力 |
| 编排 | `biz-delivery-loop` (需求→db→module→page→unit→security→e2e→交付报告 全链编排) |
| 回归载体 | ~~scripts/test-*.py~~ **9.9.3 已 prune** — 验证职责移交 quantum-codegen 各 mode 的自校验闭环 + PACE runtime-verify |

## 当前状态 (2026-07-14 核实)

- **9.9.2 + 9.9.3 双端已发布并部署本机** (`~/.claude` 与 `~/.codex` 均 v9.9.3); `next_action: release_complete`。
- 原 9.9.1 时代的 proposals 积压大部分已被 9.9.2/9.9.3 消化, 对账见下。

## proposals 消化对账 (原 quantum-backend proposals.md 7 条 + 1 追加)

| 条目 | 9.9.3 状态 |
|---|---|
| P1 gate schema 文档化/自动化 | ✅ **已消化**: stages.md 收录 schema + subagent-tracker 自动写 assignments/events.jsonl |
| P6 delivery-gate CX 证据互认 | ✅ **随双端 schema 对称消化** (gate 头注: same schema and fail-closed semantics as CX 9.9.3) |
| P2 drill 路径重复 / 文件级校验 | ♻️ **标的物已删** (scripts/ prune) — 作废; 验证职责移交 quantum-codegen mode=e2e |
| P3 drill 增补 F7 动态段 | ♻️ **转化**: F7 不再挂 drill, 改由 biz-delivery-loop + quantum-codegen(mode=e2e) 承载 (见 quantum 侧路线) |
| P4 G4 门禁产物级校验 | ⏳ **待核**: 是否已吸收进 quantum-codegen page-playbook 校验环, 下次 mode=page 实跑时核验 |
| P5 frontmatter 解析共享库 | ❌ **仍开放** (`~/.claude/hooks/lib` 不存在, 多份拷贝仍在) |
| skip_impl_subagent_check sprint 级粒度 (追加) | ❌ **仍开放** (delivery-gate 无 no_generator 声明支持; cowork 仓当前带 ⚠️ 注释绕行) |
| P7 DEPT/SELF fail-open | 归 quantum-backend 自留, 与本仓无关 |

## 当前阻碍 / 未完成 (重排后)

1. **[小] 残余 proposals 2 条**: P5 frontmatter 共享库 + sprint 级豁免粒度 (+P4 若核验未吸收) — 攒一个小维护 sprint / 9.9.4 patch 即可清。
2. **[验证缺口·主体] 9.9.3 新形态实跑验证**: quantum-codegen 六 mode 是**合并重构后从未在真实项目实跑过的新路径** (旧家族 skill 在 S2/S4 被验证过, 合并后等价性未实证); CX 端同样未经实战。**最佳验证载体 = 阶段① quantum 完善本身** — 在 quantum 上用新 skill 干真活, 一石二鸟。
3. [依赖·外部] F7 等 quantum 环境 (postgres+redis, 见 quantum 侧阻碍 1)。

## 完善设计 (阶段 ②, 重排后)

| 步 | 内容 |
|---|---|
| 1 | **不单独立项验证 9.9.3** — 阶段① 的 quantum 完善直接充当 9.9.3 实战验证 (六 mode 逐个在真实业务上过火); 发现的 skill 缺口按铁律[Hook 是进化器] 回流 proposals |
| 2 | 攒 P5 + sprint 级豁免 + (P4 若未吸收) 一个维护 sprint; 触发分发包则出 9.9.4 patch 双端同发 |
| 3 | CX 端实战: 阶段① 中挑一个 sprint 全程用 CX 跑 (与 CC 对称验证) |

> 阶段 ③ (AI infra / S5 chat 产品): 单开项目独立维护 — 消费本仓 `quantum-data` skill + quantum-mcp 契约,
> 接口已冻结 (quantum-backend `docs/ai-sprint-design.md` §9.1), 本仓无前置工作。

# Rlues (VibeCoding Athena) · 技术栈 / 阻碍 / 完善设计

> 2026-07-11 由全景对账产出。总路线: **① 完善 quantum → ② 本仓 9.9.1 双端收尾 (本文档) → ③ AI infra (S5 chat 产品, 单开项目)**。
> quantum 侧对应文档: `quantum-backend/.ai_state/architecture/blockers-and-roadmap.md` (含环境/F7 设计)。

## 技术栈

| 层 | 选型 |
|---|---|
| 本体 | 提示词架构 (Athena PACE): 9-stage 状态机 + 铁律 15 条 + 三原语 (Workflow/SubAgent/Skill) |
| CC 端分发 | `vibeCoding/claude/{version}/` → 部署至 `~/.claude`: CLAUDE.md + skills/ + hooks (Node `.cjs`: delivery-gate / pace-continuator / index-updater / subagent-tracker 等) + agents (`.md` frontmatter) + rules/ |
| CX 端分发 | `vibeCoding/codex/{version}/` → 部署至 `~/.codex`: AGENTS.md + prompts + standards/ (与 rules 对称) + hooks (Python) + agents (`.toml`) |
| 回归 | `scripts/test-*.py` (biz-delivery-loop / scaffold-page-gen / db-unit-gen / security-e2e / delivery-gate / end-to-end-drill / token-usage-collector) |
| 消费方 | quantum 三仓 (平面 B 目标脚手架) 通过 Convention Pack + runtime-env 契约被 skills 消费 |

## 当前状态 (2026-07-11 核实)

- **9.9.1 双端 roadmap 全部 completed**: CC 优化 (`claude-code-9-9-1-optimization` 6/6) + 双端 release
  (`athena-9-9-1-release` 4/4, 含 cx-runtime-contract / installer / validation), 发布 `25d4883`。
- **双端均已部署本机**: `~/.claude/CLAUDE.md` 与 `~/.codex/AGENTS.md` 均为 v9.9.1。
- fullstack-delivery F1–F6 completed; drill 当前 `status: ok / blockers: [] / failures: []`。

## 当前阻碍 / 未完成

1. **[主体] proposals 积压回流** — quantum-backend `.ai_state/proposals.md` 攒了 7 条框架改进,
   其中 **6 条归本仓** (第 7 条 DEPT/SELF fail-open 归 quantum-backend 自留):

   | # | 提案 | 性质 |
   |---|---|---|
   | P1 | delivery-gate 档案 schema 文档化/自动化 (S4 曾因 schema 不透明反复被拦) | DX·高频痛点 |
   | P2 | drill `test_account_doc` 检查路径重复 (与 runtime-env 同路径, mcp-test-access.md 永不被校验) + cowork 检查升级文件级 | 正确性 |
   | P3 | drill 增补 F7 真·动态 E2E 到 fullstack-delivery roadmap (当前 drill 只是静态基线) | roadmap |
   | P4 | G4 门禁升级为构建产物层校验 (shell→production 向量, S4 review P0 的教训固化) | 安全 |
   | P5 | frontmatter 解析单一共享实现 (CC 4 份 .cjs 拷贝 + CX 5+ 份 Python, 曾产脏 sprint 目录) | 技术债 |
   | P6 | delivery-gate 跨平台 generator 证据互认 (CX 侧 impl 的项目免 skip 豁免) | 双端对称 |

2. **[验证缺口] 9.9.1 双端"实跑验证"** — roadmap 的 validation 项已过, 但 9.9.1 新契约在真实项目上的
   双端实际使用 (尤其 CX 端 hooks/goal 链路) 尚未像 CC 端这样被 quantum 系列 sprint 高强度碾压过。
3. [依赖·外部] F7 承载 skills (`playwright-e2e` / `biz-delivery-loop` 动态段) 未经真动态使用 — 等 quantum 环境 (其阻碍 1)。

## 完善设计 (阶段 ②, 建议一个维护 sprint 收口)

| 步 | 内容 | 对应 |
|---|---|---|
| 1 | **Rlues 维护 sprint**: 按 P1→P2→P4→P5→P6 顺序清 proposals (P3 并入 F7 立项时做); 每条改完跑对应 `scripts/test-*.py` 回归; CC/CX 双端同步改 (铁律[三原语] 语义对齐) | 阻碍 1 |
| 2 | 版本策略: 若改动触分发包 → 出 9.9.2 (patch) 双端同发 + `athena-migrate` 路径; 纯 drill/scripts 修复可不升版 | — |
| 3 | 9.9.1 CX 端实跑验证: 挑一个 quantum 小 sprint 全程用 CX 端跑 (对称于 CC 已被 S4/BE/cowork 验证过) | 阻碍 2 |
| 4 | F7 落地时回填: drill 增 F7 动态段 (P3) + skills 动态使用结论 | 阻碍 3 |

> 阶段 ③ (AI infra / S5 chat 产品): 单开项目独立维护 — 消费本仓 `project-data-reader` skill + quantum-mcp 契约,
> 接口已冻结 (quantum-backend `docs/ai-sprint-design.md` §9.1), 本仓无前置工作。

# Athena 9.9.2 — Implementation Plan (file-level)

> 配套 `design.md` (权威合同) 的落地映射。design 定 what/why + 验收 (AC1–12)，本文件定 how/order/file:line。
> 基线: 9.9.1 已回滚纯净; 9.9.2 双端目录已 cp。已落地项见 CHANGELOG 9.9.2「已落地」段。
> 与 fable 复分析的偏差裁决: **design §4.5 胜** — 不加宽 `skip_spec_gate` 默认逃生; spec-gate 主门禁在 impl-entry, ship 复核 (design §4.2/§4.4)。fable 之前建议的 broad skip flag 作废。

## 批次顺序 (TDD: 行为变更先写失败测试 — design §8)

### B1 · 文档层结构项 (低风险, 不依赖 harness) — 本批
| 项 | 文件 (双端) | 动作 | AC |
|---|---|---|---|
| 四原语 | CLAUDE.md:15 / AGENTS.md:16 铁律 | 三原语→四原语, 加 MCP=连接层(reach) 子句 | AC4 |
| 四原语引用面 | pace/SKILL.md:5 · orchestration.md:3 · plugins.md:4 | `铁律[三原语]`→`铁律[四原语]`; orchestration 枚举补 · MCP 连接 | AC4 |
| references/mcp.md | skills/pace/references/mcp.md (新增) | MCP × PACE stage 定位 + 5 条仲裁 (design §6) | AC9 |
| plugins.md | skills/pace/references/plugins.md | 仲裁 3→5 条 (design §6); 默认态刷新 (feature-dev off/ECC on/superpowers off); feature-dev「仅借单点能力」注; 指针→mcp.md | AC9 |

### B2 · CX review 门禁真 bug (fable 复分析已核验) — 本批可带
| 项 | 文件 | 动作 |
|---|---|---|
| skip_impl_subagent_check 契约断裂 | codex/.../hooks/delivery-gate.py | wire gate 读取该 flag (对齐 CC cjs:360), 否则删文档承诺 |
| CONCERNS 文案矛盾 | codex/.../skills/athena-review/SKILL.md:35 · agents/evaluator.toml | 改「不得直接 ship」对齐 CC; evaluator 补「gate 只接受 PASS」 |

### B3 · harness fork 9.9.1→9.9.2 (P0 发布阻塞 · spec-gate 前置) — 下批
- fork scripts/test-athena-*-runtime + validate-athena-*.py 到 9.9.2 路径参数化 (design §8/§225)。
- fixture 加 `## Acceptance Criteria` 段 (spec-gate 上线后 ship-happy-path 会翻红)。

### B4 · spec-gate (行为变更, TDD) — 下批
- 主门禁 @ impl-entry (design §4.2): pace/athena-dev impl stage 进入前, 主 agent 验 design.md 有机器可识别验收标准 (`## Acceptance Criteria` + 编号/checkbox, 或 requirements 链接); 占位符/空标题 fail-closed (design §4.3)。
- ship 复核 (design §4.4): delivery-gate.cjs:359 GENERATOR_PATHS 块首 + delivery-gate.py:586 validate_generator_chain 前, 加 `validate_spec_gate`; 复核 spec 存在 + spec↔evidence 映射 + design-changed-after-impl。
- 逃生 (design §4.5): 无宽默认; 命名 sprint + reason + 用户授权 + 到期, review 里报 CONCERNS。
- 风险: 存量 design 标题变体误挡 → 宽 heading regex (`#{2,3}` + 可选强调) + requirements 替代。

### B5 · 两层记忆 + _index 字段治理 — 下批
- templates/_index.md + athena-init/checkpoint/session-start/status 文档: 显式 Tier1(工作)/Tier2(.ai_state 持久) + _index=检索路由 (design §5)。
- 字段消费者审计: 无消费者字段删或归位; route_confidence 仅当 hook/status 用才留 index (design §5.3)。

### B6 · 安装/迁移 (design §7) — 下批
- setup: VERSION=9.9.2, 发现 vibeCoding/{claude,codex}/9.9.2, 同版校验。
- 新增 9.9.1→9.9.2 migration (CC+CX): 保留私有 hook/provider/MCP/plugin/权限/trust/未知字段; 事务备份+回滚+dry-run+幂等。

### B7 · 收尾 — 下批
- CHANGELOG/RELEASE 双端定稿 (修正: 删 skip_spec_gate 宽逃生表述, 对齐 design §4.5)。
- 全套 validator + runtime + 2+1 review 到 PASS (AC10/AC11)。
- .ai_state 补 runtime-verify.md / reviews/passN / cleanup-pass / architecture 更新 (AC12)。

## P2 对齐 (随批夹带, 非阻塞)
reviewer effort CX medium→high; changed-files 并入 evidence.yaml; verdict 跳过 fenced code; 删 RELEASE.md 陈旧 inline-* handoff 注 (bug 实际已修)。

## 非目标 (design §10)
不弱化 generator 生命周期 / design-change fail-closed; 不使插件/MCP 成核心必需; 不覆盖用户配置; 不强求 CC/CX 字节一致; 不重开 9.9.2 版本名。

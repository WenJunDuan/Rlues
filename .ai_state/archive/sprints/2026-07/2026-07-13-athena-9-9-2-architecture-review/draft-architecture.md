# Athena 9.9.2 架构梳理 (DRAFT)

> 定位: 围绕 **pace + .ai_state 双内核**收敛; 插件 / skills / MCP 是外围能力层, 一律服务内核.
> 状态: 方案草案, 未落地. 决策点见文末「版本纪律」与「待你拍板」.

---

## 0. 结论 (先看这段)

1. **禁用大模块插件不会让 pace / ai_state 降级** — delivery-gate 9 检查零插件依赖; 每个插件都有降级路径 (plugins.md:28). 降级的只有「工具便利层」, 内核 (状态机 / 门禁 / 记忆) 完好.
2. **Athena 方向已领先 2026 主流** — 外网正从 prompt engineering 转向 context engineering + spec-driven development (SDD), 而 .ai_state 就是「context as infrastructure」, requirements/design/route-note 就是「spec as source of truth」. 你不用追潮流, 是**把已有的打成旗号 + 补 3 个缺口**.
3. **9.9.2 的 3 个缺口**: ①心智模型缺 MCP 这一层 (三原语→四原语); ②spec 层 (requirements/) 未升为一等公民, 而「intent drift」是 2026 头号失败模式; ③两层记忆 (context=RAM / .ai_state=disk) 未显式化.
4. **版本纪律警告**: 若做 ①②③ (改心智模型 + PACE 入口语义) = **结构变化 → 应是 9.10.0 minor**, 不是 patch. 只做 pace 去重 + 插件 + skill 描述治理 = 9.9.2 patch. 二选一, 见文末.

---

## 1. 插件禁用的降级影响 (回答你的问题)

判据: `plugins.md:28`「插件被禁用/缺失全部有降级路径, 缺插件不 block 流程」+ delivery-gate 门禁零插件依赖 + 铁律[三原语]「Workflow 统领, 插件是能力不是流程」.

| 插件 | 当前 | 禁用后果 | 影响内核? |
|---|---|---|---|
| codex-plugin-cc | **on** (你要的) | 失去 CC↔CX 跨端移交 /codex:transfer | 否 (CC 单端流程完整) |
| code-review | **on** | 少第 4 审对照, 三件套仍是正典 | 否 |
| feature-dev | **on** | ⚠️ 见下「注意」 | 否 |
| commit | **on** | 手写 conventional commit (git-conventions.md 仍在) | 否 |
| context7 | on | 出处引用降级 WebSearch, 摩擦↑ | 否 (铁律[出处优先]靠自查, 非插件) |
| playwright-skill | on | E2E 降级 curl+CLI, 前端断言弱 | 否 |
| superpowers | **off** | brainstorm/polish 少提问/重构技法 (**已内联进 skill 正文**) | 否, 零实质损失 |
| ECC-AgentShield | **off** | security-review 从 `npx ecc-agentshield` 自动扫描 → 降级 security-checklist.md 手工自查 | 否 (security P0 门禁仍在), 但**这是唯一实打实的能力损失** |

**一句话**: pace 状态机 / delivery-gate 门禁 / .ai_state 记忆 **一个都不降级**; 只有 security 自动扫描 (ECC-AgentShield) 是真损失 — 手工 checklist 易漏, **建议也开**.

**⚠️ feature-dev 注意**: 框架自述 (plugins.md:12)「feature-dev 完整工作流与 PACE 撞车 — 它有自己的 plan/impl 环」. 启用它当**工具**可以, 但**别调它的端到端工作流**, 否则和 PACE 双头指挥. 9.9.2 建议: 在 plugins.md 明确「feature-dev 仅借单点能力, 工作流入口永远是 PACE」.

---

## 2. 外网趋势对标 (2026)

| 趋势 | 外网共识 | Athena 现状 | 缺口 |
|---|---|---|---|
| **prompt → context engineering** | 「把知识放进基础设施, 不是指令」「context 当基础设施来版本化治理」; 89% 团队今年投 context 管理 | ✅ .ai_state 就是持久 context 基础设施, _index 是入口 | 没打成旗号; context 「装配管线」未显式 |
| **spec-driven development (SDD)** | 可执行/版本化的 spec 是唯一真相; 头号失败模式=**intent drift** (自信地解错问题); AGENTS.md / constitution.md 成标配 | ✅ requirements/ + design.md + route-note + checklist 已是 spec 层 | requirements/ 未升一等公民; 无 spec-gate 强制「先 spec 后码」 |
| **skills 渐进披露** | 每 skill 描述 ~100 token 常驻, 全文按需加载 (<5k); 大库低成本 | ✅ 已 references/ 下沉 + 热路径精简 | 31 skill 的 description 预算未审计; 有版本漂移 (rules/_index 9.6.2) |
| **agent memory 两层** | Tier1 上下文=RAM / Tier2 持久层=disk; checkpoint 固化; MemSync 跨会话同步 | ✅ 会话=RAM, .ai_state=disk, checkpoint/compact hook 已有 | 两层模型未显式写进心智; _index 未定位为「检索路由器」 |
| **skill / subagent / MCP 分工** | Skill=做什么(what) · MCP=连接/够得着(reach) · SubAgent=谁做(who); 多 agent 4-7x token, 3-5 并发甜点 | ✅ 三原语 Workflow/SubAgent/Skill + 红黄绿区 + token-collector | **MCP 在心智模型里隐身** — 三原语没给 MCP 位置 |

**判断**: Athena 不是落后要追赶, 是**踩在 2026 正确路线上但有 3 处没说透**. 9.9.2 是「命名 + 补缺」, 不是重构.

---

## 3. 9.9.2 目标架构: 双内核同心圆

```
              ┌─────────────────────────────────────────┐
              │  外层 · 连接与能力 (可插拔, 可降级)        │
              │  MCP 连接器 · 插件 · 官方 skill           │
              │   ├ 都不进 delivery-gate (门禁零依赖)     │
              │   └ 产出必落 .ai_state (文档即真相)       │
              │  ┌───────────────────────────────────┐  │
              │  │ 中层 · 四原语 (执行机制)            │  │
              │  │  Workflow 统领 (PACE)              │  │
              │  │  SubAgent 执行 (红黄绿区)          │  │
              │  │  Skill 赋能 (what/知识)            │  │
              │  │  MCP 连接 (reach/外部) ← 9.9.2 新  │  │
              │  │  ┌─────────────────────────────┐  │  │
              │  │  │ 内核 · 双真相源              │  │  │
              │  │  │  ① pace   = 控制平面 (怎么走) │  │  │
              │  │  │  ② .ai_state = 数据平面(真相) │  │  │
              │  │  │     spec 层: requirements/    │  │  │
              │  │  │     索引: _index.md (检索路由) │  │  │
              │  │  └─────────────────────────────┘  │  │
              │  └───────────────────────────────────┘  │
              └─────────────────────────────────────────┘
```

**读法 (从内到外)**:
- **内核不可替换**: pace (控制/状态机) + .ai_state (数据/记忆). 一切外围为它俩服务.
- **中层是机制**: 四原语回答「用什么执行」. 9.9.2 把 MCP 从隐身提为显式第四原语.
- **外层可插拔**: MCP / 插件 / 官方 skill 全部「能力不是流程」, 禁用即降级, 永不进门禁.

---

## 4. pace 强化 (你要的重点)

| # | 强化项 | 现状 | 9.9.2 动作 | 类型 |
|---|---|---|---|---|
| P1 | **路由真相源单一化** | 已去一半重复 (pace 指针化 athena-dev) | 彻底: 路由协议只活在 athena-dev; pace 只留「6路径×9stage」状态表 + 护栏地板 | patch |
| P2 | **spec-gate (对标 SDD, 治 intent drift)** | 有 requirements/design 但进 impl 不强制 spec | 门禁化: Feature+ 进 impl 前, delivery-gate 验「design.md 有可验收标准 或 requirements/{slug} 存在」; 写不出验收标准=intent 未定=挡回 brainstorm | **minor** (入口语义变) |
| P3 | **re-route 减负** | 机械触发(文件数) + 语义触发(agent自查) 并存 | 机械触发保留 (hook 强制, 确定性); 语义触发降为**提示**不强制 (靠 agent 诚实本就不可靠) | patch |
| P4 | **stage 命名诚实化** | 「9 stage」实为 4 核心+5 条件 | 文案已改; 补 stages.md 同步 | patch |
| P5 | **_index 定位为检索路由器** | 是索引但未明确两层记忆角色 | 文档层: 声明 _index = Tier2 检索入口; 字段按「有消费者」审计 (保留 route_history/plan_model; 审计位 route_confidence 归一到 route-note 内文) | patch |

**不做** (fable 建议但驳回, 属削弱内核): 简化 generator 生命周期门禁 (P0 fail-closed 核心) · 删 design-change-detector (有意防御纵深). 保守档不动门禁.

---

## 5. skills / 插件 / MCP 围绕内核的定位规则 (9.9.2 定稿)

三条铁规 (扩展 plugins.md 的三条仲裁, 覆盖 MCP):

| 规则 | 内容 |
|---|---|
| **R1 产出归位** | 任何 skill/插件/MCP 的产出想留下 → 必落 `.ai_state/` 对应文件. 只活在对话里的产出 = 不存在 (文档即真相) |
| **R2 门禁无豁免** | 外围干的活同样过 delivery-gate. 插件/MCP/workflow 产物零豁免 |
| **R3 能力非流程** | 重叠时 Athena skill 是入口, 外围是它调的工具. 流程入口永远是 PACE (feature-dev 撞车即此规则兜底) |
| **R4 MCP 定位 (新)** | MCP = 连接层 (reach), 只解决「够得着外部」, 不承载「怎么做」(那是 skill) 或「谁做」(那是 subagent). MCP 拿到的数据同样落 .ai_state 才算数 |

**MCP 分类建议** (9.9.2 新增 references/mcp.md):
- 连接类 (github/db/api): plan/design 取真相 (对标 context7 的出处优先), 数据落 .ai_state
- 禁止: 用 MCP 绕过 PACE stage 或 delivery-gate; MCP 不是「第二工作流」

---

## 6. 9.9.2 变更清单 (可执行)

| 优先级 | 文件 | 动作 | patch/minor |
|---|---|---|---|
| P0 | settings.json | 插件策略已改 (codex/code-review/feature-dev/commit on; superpowers/ECC off) — **确认 ECC 是否也开** | patch |
| P0 | rules/_index.md, athena-status/SKILL.md | 修版本漂移 (9.6.2/9.6.4 → 9.9.2); validate 脚本纳入版本一致性校验 | patch |
| P1 | pace/SKILL.md | P1 路由真相源单一化 (删残余重复, 只留状态表) | patch |
| P1 | plugins.md | 加 R4 + feature-dev「仅借单点能力」注; 8 插件默认启用态刷新 | patch |
| P1 | CLAUDE.md 铁律15 | 三原语 → **四原语** (加 MCP=连接层) | **minor** |
| P1 | 新 references/mcp.md | MCP × PACE stage 定位表 | minor |
| P2 | delivery-gate + pace | P2 spec-gate (intent-drift 门禁) | **minor** |
| P2 | pace/SKILL.md + hooks | P3 re-route 语义触发降级为提示 | patch |
| P2 | _index 模板 + doc | P5 两层记忆定位 + 字段审计 | patch |
| P3 | skills/*/SKILL.md | description 预算审计 (渐进披露成本) | patch |

---

## 7. 版本纪律判断 (框架自己的规矩)

依据 9.9.0 CHANGELOG:「结构变化才递增 minor; 半月最少」.

- **纯 patch 版 (9.9.2)**: P0 + P1 路由去重 + plugins.md + 版本漂移 + P3/P5 文档. **不动心智模型, 不加门禁**. 安全, 快.
- **minor 版 (9.10.0)**: 上面 + 四原语 (加 MCP) + spec-gate 门禁 + references/mcp.md. **改了心智模型和 PACE 入口语义 = 名副其实的结构变化**. 别硬塞进 patch 号骗自己.

**建议**: 9.9.2 走 patch (清账 + 插件 + 去重), 把「四原语 + spec-gate」这两个结构项攒进 9.10.0 一起验证. 理由: spec-gate 是门禁改动, 要重跑全套冒烟; 混进 patch 违反框架自己的版本纪律 (9.9.0 就因这条破例挨过).

---

## 8. 风险 + 下一步

**风险**:
- spec-gate (P2) 若门槛设太死 → 小改动被挡, 需 skip flag 逃生 (对齐现有 skip_impl_subagent_check 模式). **待验证**门槛松紧, 上线前跑真实 sprint.
- 四原语改 CLAUDE.md 铁律 → 牵动 CC/CX 双端 `铁律[三原语]` 全部引用, 改名成本不低. **待评估**引用面.
- feature-dev 启用 → 若 agent 误入其工作流与 PACE 双头. 靠 R3 + plugins.md 注解兜, 但**待观察** dogfood.

**下一步 (按你的选择推进)**:
1. 先定 9.9.2 = patch 还是 minor (见 §7).
2. ECC-AgentShield 要不要也开 (security 自动扫描).
3. 拍板后我用 opus 落地 P0/P1, 跑 validate + node --check 验证.

---

## 附: 外网来源

- Context engineering: [Sourcegraph](https://sourcegraph.com/blog/context-engineering) · [Packmind](https://packmind.com/context-engineering-ai-coding/context-engineering-vs-prompt-engineering/)
- Skills 渐进披露: [Claude Platform Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) · [levelup.gitconnected](https://levelup.gitconnected.com/a-mental-model-for-claude-code-skills-subagents-and-plugins-3dea9924bf05)
- Spec-driven development: [BCMS](https://thebcms.com/blog/spec-driven-development) · [Augment Code AGENTS.md](https://www.augmentcode.com/guides/how-to-build-agents-md) · [Towards Data Science](https://towardsdatascience.com/from-vibe-coding-to-spec-driven-development/)
- Agent memory: [Indium 状态持久化](https://www.indium.tech/blog/7-state-persistence-strategies-ai-agents-2026/) · [mem0 memory benchmark](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- Skill/subagent/MCP 分工: [Claude blog](https://claude.com/blog/skills-explained) · [AntStack field guide](https://www.antstack.com/blog/claude-agents-subagents-agent-teams-skills-and-mcp-a-developer-s-field-guide/)

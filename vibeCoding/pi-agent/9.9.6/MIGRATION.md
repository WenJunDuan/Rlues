# CC → pi 迁移对照 · v9.9.6

来源: `vibeCoding/claude/9.9.6/.claude/`。原则: 内容能平移的平移, 机制不对等的不伪造 (铁律[四原语]: 只对齐语义, 不伪造对称工具)。

## 迁移状态总表

| CC 资产 | pi 对应 | 状态 |
|---|---|---|
| `CLAUDE.md` (宪法) | `AGENTS.md` (pi 原生也认 CLAUDE.md, 统一用 AGENTS.md) | ✅ 已迁移, 3 处平台适配 (见下) |
| `agents/*.md` × 7 | `prompts/*.md` 模板, `/name` 手动调用 | ✅ 内容迁移; **subagent 自动调度语义丢失** |
| `rules/` × 7 | `rules/` 原样 + AGENTS.md 指令按需 Read | ✅ (_index.md 改写加载机制说明) |
| `settings.json` env/model | pi `settings.json` (defaultProvider/defaultModel) | ✅ 改为 deepseek |
| `settings.json` permissions deny (危险命令) | `athena-gates.ts` → pre-bash-guard.cjs | ✅ 核心覆盖 (rm -rf 根/home、块设备写、DROP TABLE、curl\|sh); allow 白名单无对应 → pi 默认确认机制兜底 |
| `hooks/` 门禁+生命周期 6 个 | `extensions/athena-{gates,lifecycle}.ts` + cc-core 原样复用 | ✅ 已落地 (2026-08-03), 冒烟 8/8 |
| `hooks/` 其余 (evidence-collector, index-updater, subagent-*, notification-router, config-change-audit, token-usage-collector, stop-failure-recorder) | — | ⛔ 未迁移: 状态记账/subagent 类, 等 dogfood 数据再定 |
| API key | `~/.pi/agent/auth.json` (600) + models.json `!node -p` 现读 | ✅ 类 codex, 仓库零明文 |
| plugins / marketplaces | `pi install` 包生态 | ⛔ 不迁移, 按需单独评估 |
| `isolation: worktree` | 手动 `git worktree add` + 独立 session | ⚠ 降级, 写入 AGENTS.md 铁律[零写入] |
| skills/ (26 个) | pi skills/ (Agent Skills 标准, 兼容) | ⏸ 本次不迁移 — 先验证宪法+prompts 跑通再说 |

## AGENTS.md 相对 CLAUDE.md 的 3 处适配

1. 铁律[门禁即律法]: fail-closed hooks 未移植 → 标注"模型自律 + 交付自查证据", 不谎称有门禁
2. 铁律[零写入]: `Agent subagent + isolation: worktree` → 手动 git worktree + 独立 pi session
3. 面包屑/SessionStart 注入 → 改为 agent 自行声明 stage + 按需 Read rules/

## Hooks → Extensions 事件映射 (Phase-2 依据, 事件名引自官方 docs/extensions.md)

| CC hook (.cjs) | pi extension 事件 | 语义损失 |
|---|---|---|
| pre-bash-guard (PreToolUse Bash) | `tool_call` → `{ block: true, reason }` | 无, 等价 |
| delivery-gate (PreToolUse Edit/Write) | `tool_call` (edit/write) | 无, 等价 |
| delivery-gate (Stop, fail-closed) | `agent_end`/`agent_settled` + `pi.sendMessage(deliverAs:"followUp")` | **有** — pi 不能硬 block 停止, 只能追加纠偏消息 |
| session-start | `session_start` | 无 |
| compact-snapshot / compact-restore | `session_before_compact` / `session_compact` | 无 |
| stage-breadcrumb (UserPromptSubmit) | `before_agent_start` (注入 message/systemPrompt) | 无 |
| evidence-collector / index-updater (PostToolUse) | `tool_result` / `tool_execution_end` | 无 |
| subagent-tracker / retry / worktree-check | 无原生 subagent 事件 | **有** — 依赖 @tintinweb/pi-subagents 或放弃 |
| notification-router | `ctx.ui.notify` / @pi-lab/notify | 弱化 |
| config-change-audit (InstructionsLoaded/ConfigChange) | 无对应事件 | 放弃 |
| stop-failure-recorder | `agent_end` 内错误分支 | 合并进 delivery 扩展 |
| token-usage-collector | `ctx.getContextUsage()` + `tool_result` | 可实现 |

## Phase-2 执行记录 (2026-08-03, GO 已执行)

原计划"按 pi 事件模型重设计" → 实际采用**适配器模式**更优: cc-core/*.cjs 原样复用 (零转写错误风险, 双端逻辑单一真相), TS 适配器只转协议 (~200 行)。delivery-gate 65KB 一行未动。

- ✅ `athena-gates.ts` — pre-bash-guard + delivery-gate (PreToolUse + Stop)
- ✅ `athena-lifecycle.ts` — session-start + breadcrumb + compact 双件
- ✅ tsc 对真实包类型通过; cc-core 冒烟 8/8 (详见 README「已验证」)
- ⚠ 真机完整回路 (before_agent_start 注入 / agent_end followUp) 未跑 — dogfood 第一优先
- evidence/index-updater/subagent 类: 仍未迁移, 属状态记账, 缺失不破坏门禁; 等 dogfood 数据

## 待验证清单

- [ ] DeepSeek v4 模型 ID (`/models` 实测) — models.json 数据来自 api-docs.deepseek.com/quick_start/pricing (2026-08 抓取)
- [ ] pi 内置 deepseek provider 与 models.json 是否重名冲突
- [ ] prompts 模板对 HTML 注释头/frontmatter 的处理
- [ ] `@tintinweb/pi-subagents` 质量 (装前读源码, 铁律[证据与出处])

# Athena Claude Code 9.9.2

Baseline: committed Athena 9.9.1 packages (`vibeCoding/claude/9.9.1`, `vibeCoding/codex/9.9.1`). 类型: 完整改动 (含结构项; 用户拍板沿用 9.9.2 号).

## 定位
一切围绕 **pace (控制平面) + .ai_state (数据平面)** 双内核收敛; 插件 / skills / MCP 是可插拔外围。

## 本版要点 (详见 CHANGELOG.md)
- **四原语**: 三原语 + MCP (连接层 reach)。
- **spec-gate**: Feature+ impl-entry 先拦不可测试意图，ship 再验逐 AC passing evidence、最新 PASS review 与设计/实现/状态 manifest 绑定。
- **两层记忆**: Tier1 非权威；Tier2 `.ai_state` 为持久真相；`_index` 是有界检索路由器。
- pace 路由真相源单一化 (`athena-dev`) + stage 命名诚实化 (4 核心 + 5 条件)。
- **插件策略 (CC)**: feature-dev / superpowers off; ECC-AgentShield / code-review / commit / context7 / playwright-skill / codex-plugin-cc on。
- **skill 合并 7→2**: `quantum-codegen` (前后端生成 6 合 1, mode 分发) + `quantum-data` (运行期数据读取)。
- CX review 门禁修 (`skip_impl_subagent_check` wire / CONCERNS 文案)。

## 安装 / 升级 / 迁移 (AI 引导)
9.9.2 起**推荐由 AI 引导**执行安装、升级、`.ai_state` 数据迁移 (弃脚本化 migrate: 脆、易漏字段)。见包根 `AI-MIGRATION-GUIDE.md` + `skills/athena-migrate`。`skills/athena-setup/scripts/setup-athena.py` 仍可用作可选后备。

## 兼容
| Level | Claude Code | Contract |
|---|---:|---|
| Floor | 2.1.203 | Core hooks / agents / PACE state / native worktree 强隔离 |
| Target | 2.1.206 | Full settings / hooks / subagent contract |

## 验证
- `python3 vibeCoding/scripts/test-athena-9.9.2-runtime.py` — 当前 **60/60 PASS**。
- `node vibeCoding/scripts/test-athena-claude-9.9.2-runtime.cjs` — 正式 host 基线 **101 PASS / 0 FAIL / 0 SKIP**。
- `python3 vibeCoding/scripts/validate-athena-9.9.2.py` — Python 3.11+；包含双端 runtime、fresh temp-HOME、strict doctor、prompt-input 与 F-series。
- 正式 2+1 review 是 `.ai_state` 的外部发布门禁；最新数字 passN 必须含 Spec Compliance、Evidence Cross-Check、三项 freshness binding 且最终 PASS，包文档不伪造自证 verdict。

## 官方引用
Hooks / Subagents / Worktrees / Settings / Model / MCP / Plugins — https://code.claude.com/docs/en/

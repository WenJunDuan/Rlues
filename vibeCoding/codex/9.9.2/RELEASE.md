# Athena Codex 9.9.2

Baseline: committed Athena 9.9.1 packages (`vibeCoding/claude/9.9.1`, `vibeCoding/codex/9.9.1`). 类型: 完整改动 (含结构项; 用户拍板沿用 9.9.2 号).

## 定位
一切围绕 **pace (控制平面) + .ai_state (数据平面)** 双内核收敛; 插件 / skills / MCP 是可插拔外围。

## 本版要点 (详见 CHANGELOG.md)
- **四原语**: 三原语 + MCP (连接层 reach)。
- **spec-gate**: Feature+ ship 复核机器可识别验收标准 (治 2026 头号失败模式 intent-drift)。
- **两层记忆**: `_index` 为 Tier2 检索路由器。
- pace 路由真相源单一化 (`athena-dev`) + stage 命名诚实化 (4 核心 + 5 条件)。
- **技法 (CX 插件集独立: openai-bundled)**: feature-dev / superpowers off; ECC-AgentShield / code-review / commit / context7 / playwright-skill / codex-plugin-cc on。
- **skill 合并 7→2**: `quantum-codegen` (前后端生成 6 合 1, mode 分发) + `quantum-data` (运行期数据读取)。
- CX review 门禁修 (`skip_impl_subagent_check` wire / CONCERNS 文案)。

## 安装 / 升级 / 迁移 (AI 引导)
9.9.2 起**推荐由 AI 引导**执行安装、升级、`.ai_state` 数据迁移 (弃脚本化 migrate: 脆、易漏字段)。见包根 `AI-MIGRATION-GUIDE.md` + `skills/athena-migrate`。`skills/athena-setup/scripts/setup-athena.py` 仍可用作可选后备。

## 兼容
| Level | Codex | Contract |
|---|---:|---|
| Floor | 2.1.203 | Core hooks / agents / PACE state / native worktree 强隔离 |
| Target | 2.1.206 | Full settings / hooks / subagent contract |

## 验证
- `node vibeCoding/scripts/test-athena-9.9.2-runtime.py` (本仓: **83 PASS / 0 FAIL / 2 SKIP (sandbox py3.10); codex py3.11: CC 73/0/0 live + CX 33/33**; SKIP = npm 无网, 需网络载 CC 2.1.203/206)。
- `python3 vibeCoding/scripts/test-athena-9.9.2-runtime.py` + `python3 vibeCoding/scripts/validate-athena-9.9.2.py` (需 **Python 3.11+**, tomllib)。
- 发布前 **codex 2+1 review 到 PASS** (本包留待 review)。

## 官方引用
Hooks / Subagents / Worktrees / Settings / Model / MCP / Plugins — https://code.claude.com/docs/en/

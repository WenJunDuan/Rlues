# Athena Codex 9.9.3

Baseline: committed Athena 9.9.2 packages (`vibeCoding/claude/9.9.2`, `vibeCoding/codex/9.9.2`). 类型: 完整改动 (含 minor 级项; 用户拍板沿用 9.9.3 号, 先例同 9.9.2)。

## 定位
一切围绕 **pace (控制平面) + .ai_state (数据平面)** 双内核收敛; 插件 / skills / MCP 是可插拔外围。本版主题: **反过度工程入宪 + 热路径减重** (规训→门禁, 贬值层→耐久层)。

## 本版要点 (详见 CHANGELOG.md · 设计推演见 build-spec-final.md)
- **宪法收敛**: CC 铁律 15→9 / CX 16→10; 门禁已覆盖的散文折叠为 `铁律[门禁即律法]`; 删 SOLID 背诵。
- **新增 `铁律[反过度工程]`**: 无第二消费者不抽象 / 防御只设信任边界 / 删掉仍绿=删; 布线 critic·reviewer·evaluator·coding-standards·polish 五处, 不新增 gate (自反一致)。
- **brainstorm grill-me 化**: 一次一问 + strawman + 先查库再问人; 模板改 distilled-log。
- **stage 面包屑** (借 Trellis): UserPromptSubmit 每轮注入当前 stage 义务 ≤10 行, parser-only (真相=stages.md), fail-open, `_index.breadcrumb` 可关; pace SKILL "每 sprint 必读" 降级; session-start stageHints 双写删除。
- **harness-iteration v1.1**: dogfood 分级 / 四轮规模分级 / 超前设计条款。它是包根可分发文档 `harness-iteration-v1.1.md`, 不安装为内置 skill, skill 数仍为 26。

## 安装 / 升级 / 迁移 (AI 引导)
9.9.2 起**推荐由 AI 引导**执行安装、升级、`.ai_state` 数据迁移 (弃脚本化 migrate: 脆、易漏字段)。见包根 `AI-MIGRATION-GUIDE.md` + `skills/athena-migrate`。`skills/athena-setup/scripts/setup-athena.py` 仍可用作可选后备。9.9.2→9.9.3 升级注意: 宪法/agents/brainstorm/pace 为 release-owned 覆盖; settings.json 新增 UserPromptSubmit 注册需合并; 用户项目 `_index.md` 可选补 `breadcrumb` 字段 (缺省=on)。

## 兼容
CX 端以 config.toml + hooks.json 注册为准; 面包屑落在既有 user-prompt-submit.py (UserPromptSubmit 已注册, 零 hooks.json 改动)。model pin 为 `gpt-5.6-sol`。

## 验证
- `node vibeCoding/scripts/test-athena-claude-9.9.3-runtime.cjs` — **107 PASS / 0 FAIL / 0 SKIP**。
- `python3 vibeCoding/scripts/test-athena-9.9.3-runtime.py` — **67/67 PASS**。
- `ATHENA_CODEX_BIN=<codex-0.144.1> NPM_CONFIG_PREFIX=<matching-prefix> python3 vibeCoding/scripts/validate-athena-9.9.3.py` — **223 PASS / 0 FAIL / 0 SKIP**；fresh setup、doctor、prompt-input 与 52 个官方 skill 校验全过。
- 面包屑 fresh-install/canonical-path/≤10 行、evaluator unresolved finding、M5 双端工件与 9.9.2 baseline 均有回归覆盖。

## 官方引用
Hooks / Subagents / Worktrees / Settings / Model / MCP / Plugins — https://code.claude.com/docs/en/

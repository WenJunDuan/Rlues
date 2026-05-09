---
name: vibe-setup
effort: xhigh
disable-model-invocation: true
description: >
  VibeCoding Hermes 全局安装。检查 CC 版本、装插件、配置 Codex、部署 hooks。首次使用运行一次。
---

# /vibe-setup (v9.5)

## 设计哲学（启动时告诉用户）

```
v9.5 减重原则:
- permissions.deny 列表 = 空 (用流程约束 + design boundary 替代硬规则)
- pre-bash-guard = 3 条灾难命令 (rm 根/curl-pipe/mkfs-dd)
- 全局 lessons 系统已删除 (Hermes 不做跨项目知识管理)
- 跨项目记忆 → 推荐装 claude-mem 或 superpowers
```

## Step 0: CC 版本检查

```bash
claude --version
```

要求 v2.1.121 或更高（hooks `updatedToolOutput` 全工具支持）。低于 → `claude update` 或 `npm install -g @anthropic-ai/claude-code@latest`。

## Step 1: 插件安装（按 PACE 节点 best-fit，非强依赖）

逐个安装，跳过已有的。**每装一个，问自己"这个真的会用吗"**——多余的插件 = context 浪费。

### 工程主线（强烈推荐）

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
```

### 跨项目记忆（替代删除的全局 lessons）

```
# claude-mem: 用 SQLite + 向量做跨 session 记忆
# https://github.com/AnyResearch/claude-mem
/plugin install claude-mem@<对应 marketplace>
```

未装 claude-mem → vibe-setup 会软提示一次。继续不装也行，Hermes 仍可用。

### PACE 节点 best-fit 推荐（按需）

| 路径 | 推荐插件 |
|------|---------|
| Bugfix | debugger / bug-fix / metronome |
| Feature 实现 | superpowers / dev-workflows / context7 |
| Feature 审查 | codex-plugin-cc / agent-peer-review / local-review |
| Refactor | TypeScript LSP / Rust LSP / ast-grep |
| Refactor 审查 | codex-plugin-cc / AgentLint |
| System | shipyard (IaC) / mcp-builder |
| 跨节点优化 | context-mode (大输出 sandbox 化, 节省 98%) / skill-bus |

### 官方插件（claude-plugins-official 已内置）

```
/plugin install feature-dev
/plugin install code-review
/plugin install commit-commands
/plugin install security-guidance
/plugin install frontend-design
```

`/reload-plugins` 后生效。

## Step 2: context7（skill 模式）

```bash
npx ctx7 setup --claude
```

无需全局安装 ctx7 CLI，npx 按需拉取。OAuth 登录后自动在 `~/.claude/skills/` 生成 context7 skill。
触发方式: "use context7" 或 "use context7 with /owner/repo for <query>"。

## Step 3: Codex 配置

```
/codex:setup
```

未登录 → `!codex login`

**不要启用 review gate**（`/codex:setup --enable-review-gate`）—— 会造成 Claude ↔ Codex 死循环。

settings.json codex 权限：

```json
"Bash(codex:*)",
"Bash(node:*)"
```

首次 `/codex:status` 弹 prompt 时选 "Yes, and don't ask again"，CC 会写到 `.claude/settings.local.json`。

Codex 独立配置 `~/.codex/config.toml`：

```toml
model = "gpt-5.4-mini"
model_reasoning_effort = "high"
```

## Step 4: Hooks 安装

```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/*.cjs ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.cjs
```

v9.5 hook 列表（9 个，比 v9.4.5 净 -2）：
- session-start · pre-bash-guard · subagent-retry · delivery-gate
- permission-request · pre-compact-save · post-compact-restore
- output-evidence-augmentor (默认 disable, 见 Step 5)
- session-end-reminder (async) · task-created-advisor (async)

## Step 5: 可选 hook 启用

`output-evidence-augmentor` 默认禁用。启用方式：

```bash
# 编辑 ~/.claude/settings.json，把对应 hook 段的 disabled 字段改为 false
```

启用后：审查阶段 Edit/Write 后没找到 review-report.md → 工具输出尾部追加 "⚠ 未发现 review-report.md"。

## Step 6: 验证

```bash
claude --version                         # ≥ 2.1.121
/plugin list                             # superpowers / codex 已装
npx ctx7 library express                 # context7 CLI 通
/codex:setup                             # Codex ready
ls ~/.claude/hooks/*.cjs | wc -l         # 应 ≥ 7
```

通过 → "安装完成。每个新项目 `/vibe-init`，然后 `/vibe-dev`。"

## 为什么删了一些东西（用户视角）

| v9.4.5 有 | v9.5 删除原因 |
|-----------|-------------|
| 18 条 permissions.deny | agent 频繁撞墙，正常 Read 都被拦。改用流程+边界约束 |
| 9 条 pre-bash-guard | 同上，重复管控。改 3 条灾难级 |
| `~/.claude/lessons/` 系统 | 知识管理不是 Hermes 职责，删除。需要装 claude-mem |
| lesson-drafter / archiver / curator | 同上 |
| 反 LLM 偏见段（6 条禁止）| 反复"禁止 X" 是 anti-pattern。改铁律 6 正向证据要求 |
| 铁律 8/9（流程描述）| 不是约束是 SOP，移到 pace/SKILL.md 失败处理协议 |

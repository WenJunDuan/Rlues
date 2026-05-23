# /athena-setup (Codex) v9.6.1

参考: <https://developers.openai.com/codex/config-basic>

## Step 0: Codex 版本检测

```bash
codex --version
```

最低要求 ≥ v0.124 (hooks stable).

**版本能力解析** (写入 `_index.md.platform_features`):

| 版本 | 解锁能力 |
|------|---------|
| ≥ v0.124 | hooks GA (本框架最低要求) |
| ≥ v0.128.0 | **`/goal` GA** (持久化 autonomous loop, 2026-04-30 release) |
| ≥ v0.129+ | `/hooks` TUI menu |

参考: <https://developers.openai.com/codex/changelog>

低于 v0.124 → `codex update` 或重装 (`npm install -g @openai/codex@latest`).

把解析结果写入:
- `_index.md.platform_features.cx_version` = 实际版本字符串
- `_index.md.platform_features.goal_supported` = (cx_version ≥ "0.128.0")

## Step 1: 验证 config.toml

`~/.codex/config.toml` 应包含 (从 cx/.codex/config.toml 拷贝):

- `model = "gpt-5.5"` (或当前最新)
- `[features] hooks = true`
- `[[hooks.SessionStart]]`, `[[hooks.PreToolUse]]`, `[[hooks.PostToolUse]]`, `[[hooks.Stop]]`
- `[agents] max_threads = 6`
- `[[skills.config]]` 包含 pace / compound / context7 / superpowers

```bash
codex check config 2>&1 | head -20
```

⚠️ **安全提示**: 模板 config.toml **不应** 包含真实 token / 真实工作目录路径 / 真实 hooks 信任哈希. 这些字段由用户在本机运行时自己填写或由 Codex 自动写入, 不要提交到任何模板/分发包.

## Step 2: 部署 hooks

```bash
mkdir -p ~/.codex/hooks
cp cx/.codex/hooks/*.py ~/.codex/hooks/
chmod +x ~/.codex/hooks/*.py
```

Codex hook 列表 (Python, 6 个):
- session-start.py
- user-prompt-submit.py
- pre-bash-guard.py
- index-updater.py
- subagent-retry.py
- delivery-gate.py

⚠️ Codex hooks 当前 Windows 不支持 (官方限制, 参考 <https://developers.openai.com/codex/hooks>)

## Step 3: 部署 skills

```bash
mkdir -p ~/.codex/skills/pace ~/.codex/skills/compound
cp -r cx/.codex/skills/pace/* ~/.codex/skills/pace/
cp -r cx/.codex/skills/compound/* ~/.codex/skills/compound/
```

## Step 4: 部署 prompts (slash commands)

```bash
mkdir -p ~/.codex/prompts
cp cx/.codex/prompts/*.md ~/.codex/prompts/
```

## Step 5: 部署 subagents (单 TOML 文件, 非子目录)

参考: <https://developers.openai.com/codex/subagents>

```bash
mkdir -p ~/.codex/agents
cp cx/.codex/agents/*.toml ~/.codex/agents/
```

部署后:
- `~/.codex/agents/evaluator.toml` — 评分员 (read-only)
- `~/.codex/agents/generator.toml` — 实现者 (workspace-write)
- `~/.codex/agents/reviewer.toml` — 审查员 (read-only)

验证:
```bash
codex /agents 2>&1 | head -20
# 应列出 evaluator, generator, reviewer 三个 custom agent
```

## Step 6: 跨项目记忆 (推荐)

Codex 暂无 claude-mem 等价物。推荐:
- 用 `~/.codex/AGENTS.md` 全局 "## Tool Preferences" 段做轻量记忆
- 多项目用同一 ~/.codex/AGENTS.md (跨项目人工同步)

## Step 7: 验证

```bash
codex --version                # ≥ 0.124; 期望 ≥ 0.128 (/goal 已 GA)
ls ~/.codex/hooks/*.py | wc -l # 应 = 6
ls ~/.codex/prompts/*.md       # 7 个 athena-* prompt
codex /hooks 2>&1 | head       # v0.129+ TUI 显示 hook 树
cat .ai_state/_index.md | head -5  # schema_version: "9.6"
grep "athena_version" .ai_state/_index.md  # 期望: "9.6.1"
```

通过 → "Codex 端 Athena v9.6.1 已就绪。"

如 `goal_supported: true` → 提示用户:
"Codex /goal 已对齐 v0.128+. PACE 各 stage 可用 `/goal "<condition>"` 启动持久化 loop, 模板见 `~/.codex/skills/pace/templates/goal-conditions.md`."

# /vibe-setup — VibeCoding Hermes Codex 端安装 (v9.5)

## 设计哲学（启动时告诉用户）

```
v9.5 减重原则:
- pre-bash-guard = 3 条灾难命令 (其他靠 sandbox + approval_policy)
- 全局 lessons 系统已删除 (Hermes 不做跨项目知识管理)
- 跨项目记忆 → 用 @plugin-creator 自建技能 / 接入 superpowers
```

## Step 0: Codex 版本

```bash
codex --version
```

要求 v0.124.0 或更高（codex_hooks stable 起点）。低于 → `npm i -g @openai/codex@latest` 或 `brew upgrade codex`。

## Step 1: 模型选择确认

- ChatGPT 订阅用户 (Plus/Pro/Business/Enterprise) → 默认 `model = "gpt-5.5"`
- API key 用户 → `codex --profile api`（用 gpt-5.4）
- 需要快速响应 → `codex --profile codex-spark`

## Step 2: hooks 启用

```bash
grep "codex_hooks = true" ~/.codex/config.toml || codex features enable codex_hooks
```

## Step 3: 部署 VibeCoding 文件

本 `.codex/` 目录已是正确结构。合并到 `~/.codex/`：

```bash
cp -rf .codex/AGENTS.md ~/.codex/AGENTS.md
cp -rf .codex/agents/* ~/.codex/agents/
cp -rf .codex/hooks/* ~/.codex/hooks/
cp -rf .codex/prompts/* ~/.codex/prompts/
cp -rf .codex/skills/* ~/.codex/skills/

chmod +x ~/.codex/hooks/*.py
```

`~/.codex/config.toml` 已存在则**手动合并**：
- 重点合并 `[features]`, `[[hooks.*]]` 内联块, `[[agents.list]]` 块

无现有 config.toml → 直接 `cp .codex/config.toml ~/.codex/config.toml`

## Step 4: 插件市场（Codex 3/27/2026 上线）

Codex 现已支持插件市场（90+ 插件）。**v9.5 新接入**：

```
/plugins                 # 浏览/安装插件
@plugin-creator          # 内置 skill, scaffold 自定义插件
```

### PACE 节点 best-fit 推荐

| 路径 | 推荐插件 |
|------|---------|
| Quick / Feature | superpowers / context7 |
| 终端密集任务 | Codex Terminal-Bench 比 CC 强 12pp，路由建议默认 Codex |
| 集成 | Slack / Linear / Notion / Figma / GitHub / Sentry plugins (官方 marketplace) |
| 跨项目记忆 | superpowers (`/using-superpowers` 命令) |

未装 superpowers 也行——Hermes 仍可用。

## Step 5: context7 安装

```bash
npx ctx7 setup --codex
```

OAuth 登录后 ~/.codex/skills/ 下生成 context7 skill。
触发: 输入 "use context7" 或 "$context7"。

## Step 6: 验证

```bash
ls ~/.codex/AGENTS.md                                  # 全局铁律 v9.5
ls ~/.codex/skills/pace/SKILL.md                       # PACE 路由
ls ~/.codex/skills/compound/SKILL.md                   # 经验沉淀
ls ~/.codex/agents/{evaluator,generator,reviewer}/AGENTS.md
ls ~/.codex/hooks/*.py                                 # 6 个 hook 脚本 (v9.5 净 -2)
ls ~/.codex/prompts/*.md                               # slash 命令
grep "codex_hooks = true" ~/.codex/config.toml
grep "VIBECODING_VERSION" ~/.codex/config.toml         # 应为 9.5-codex
npx ctx7 library express                               # context7 可用
```

通过 → 重启 Codex 进入新 session，`/status` 显示 VibeCoding 已加载。
每个新项目 → `/vibe-init`，然后 `/vibe-dev`。

## 为什么删了一些东西（用户视角）

| v9.4.5 有 | v9.5 删除原因 |
|-----------|-------------|
| `~/.codex/lessons/` 全局系统 | 知识管理不是 Hermes 职责，删除。需要跨项目记忆 → superpowers |
| `lesson-drafter` / `lesson-archiver` hooks | 同上 |
| 反 LLM 偏见段（6 条禁止）| 反复"禁止 X" 是 anti-pattern。改铁律 6 正向证据要求 |
| 铁律 8/9（流程描述）| 不是约束是 SOP，移到 pace/SKILL.md |
| pre-bash-guard 9 条 | 减到 3 条灾难级，sandbox + approval_policy 已足够 |

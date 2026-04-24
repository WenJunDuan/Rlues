# /vibe-setup — VibeCoding 全局安装 (Codex 端)

执行以下步骤安装 VibeCoding Codex 端:

## Step 0: Codex 版本检查

```bash
codex --version
```

要求是当前稳定版本。若太旧 → `npm i -g @openai/codex@latest` 或 `brew upgrade codex`。

## Step 1: 启用 hooks feature

VibeCoding 强依赖 Stop hook 做 delivery-gate。Codex hooks 当前是实验性 feature, 默认关闭。

```bash
codex features enable codex_hooks
```

这会写入 `~/.codex/config.toml` 的 `[features]` 表 (字段名是 `codex_hooks`, 不是 `hooks`)。

## Step 2: 部署 VibeCoding 文件

本 `.codex/` 目录已经是正确结构。把它合并到 `~/.codex/`:

```bash
# 假设你在 vibecoding-codex-9.4.4 解压目录
cp -r .codex/AGENTS.md ~/.codex/AGENTS.md
cp -r .codex/hooks/* ~/.codex/hooks/
cp -r .codex/agents/* ~/.codex/agents/
cp -r .codex/prompts/* ~/.codex/prompts/
cp -r .codex/skills/* ~/.codex/skills/
# config.toml 和 hooks.json 要合并 (看下面)
```

对 `~/.codex/config.toml` 和 `~/.codex/hooks.json` 做**合并**而非覆盖 (如果你已有配置)。完全没有 → 直接复制本包的 config.toml 和 hooks.json。

```bash
chmod +x ~/.codex/hooks/*.py
```

## Step 3: context7 skill 安装

```bash
npx ctx7 setup --codex
```

OAuth 登录后会自动在 `~/.codex/skills/` 下生成 context7 skill。
触发方式: `$context7` 或 "use context7"。

## Step 4: 验证

```bash
ls ~/.codex/AGENTS.md                   # 铁律在位
ls ~/.codex/skills/pace/SKILL.md        # PACE 路由
ls ~/.codex/skills/compound/SKILL.md    # 经验沉淀
ls ~/.codex/agents/evaluator.toml       # 评审 subagent
ls ~/.codex/agents/reviewer.toml        # 审查 subagent
ls ~/.codex/agents/generator.toml       # 生成 subagent
ls ~/.codex/hooks/*.py                  # 3 个 hook 脚本 (session-start / pre-bash-guard / delivery-gate)
cat ~/.codex/hooks.json | python3 -m json.tool   # hooks 注册有效
grep "codex_hooks = true" ~/.codex/config.toml         # features.codex_hooks 已开
npx ctx7 library express                         # context7 可用
npx ecc-agentshield --version                    # ECC 可用 (npx, 无需 plugin)
```

全部通过 → 重启 Codex: `codex` 进入新 session, `/status` 应显示 VibeCoding 已加载。
每个新项目 → `/vibe-init`，然后 `/vibe-dev`。

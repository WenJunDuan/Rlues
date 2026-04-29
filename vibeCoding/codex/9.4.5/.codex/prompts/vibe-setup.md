# /vibe-setup — VibeCoding Hermes Codex 端安装

## Step 0: Codex 版本

```bash
codex --version
```

要求 v0.124.0 或更高 (codex_hooks stable 起点)。低于 → `npm i -g @openai/codex@latest` 或 `brew upgrade codex`。

## Step 1: 模型选择确认

- ChatGPT 订阅用户 (Plus/Pro/Business/Enterprise) → 默认 model = "gpt-5.5" 直接可用
- API key 用户 → 切到 profile: `codex --profile api` (用 gpt-5.4)
- 需要快速响应 → `codex --profile codex-spark`

## Step 2: hooks 启用

v0.124.0 之后 codex_hooks 已 stable 默认 on, 但本 config.toml 显式声明保险:

```bash
grep "codex_hooks = true" ~/.codex/config.toml || codex features enable codex_hooks
```

## Step 3: 部署 VibeCoding 文件

本 `.codex/` 目录已是正确结构。合并到 `~/.codex/`:

```bash
cp -rf .codex/AGENTS.md ~/.codex/AGENTS.md
cp -rf .codex/agents/* ~/.codex/agents/
cp -rf .codex/hooks/* ~/.codex/hooks/
cp -rf .codex/prompts/* ~/.codex/prompts/
cp -rf .codex/skills/* ~/.codex/skills/
cp -rf .codex/lessons ~/.codex/

chmod +x ~/.codex/hooks/*.py
```

`~/.codex/config.toml` 已存在则**手动合并**而非覆盖:
- 重点合并 `[features]`, `[[hooks.*]]` 内联块, `[[agents.list]]` 块
- proxy 占位按需取消注释

无现有 config.toml → 直接 `cp .codex/config.toml ~/.codex/config.toml`

## Step 4: context7 安装

```bash
npx ctx7 setup --codex
```

OAuth 登录后 ~/.codex/skills/ 下生成 context7 skill。
触发: 输入 "use context7" 或 "$context7"。

## Step 5: 全局 lessons 初始化

```bash
mkdir -p ~/.codex/lessons/archive
test -f ~/.codex/lessons/INDEX.md || cp .codex/lessons/INDEX.md ~/.codex/lessons/
test -f ~/.codex/lessons/README.md || cp .codex/lessons/README.md ~/.codex/lessons/
```

## Step 6: 验证

```bash
ls ~/.codex/AGENTS.md                                  # 全局铁律
ls ~/.codex/skills/pace/SKILL.md                       # PACE 路由
ls ~/.codex/skills/compound/SKILL.md                   # 经验沉淀
ls ~/.codex/agents/{evaluator,generator,reviewer}/AGENTS.md
ls ~/.codex/hooks/*.py                                 # 7 个 hook 脚本
ls ~/.codex/prompts/*.md                               # slash 命令
ls ~/.codex/lessons/INDEX.md                           # 全局 lessons
grep "codex_hooks = true" ~/.codex/config.toml         # hooks 启用
grep "model = " ~/.codex/config.toml | head -1         # 默认模型
npx ctx7 library express                                # context7 可用
npx ecc-agentshield --version                           # ECC 可用
```

通过 → 重启 Codex: `codex` 进入新 session, `/status` 应显示 VibeCoding 已加载。
每个新项目 → `/vibe-init`，然后 `/vibe-dev`。

## Step 7: 权限和隐私核查 (重要)

VibeCoding 默认 config.toml 配置了较宽松的开发模式。安装后**自检以下**:

### 你启用了什么权限

```bash
grep -E "approval_policy|sandbox_mode|network_access" ~/.codex/config.toml
```

**默认值**:
- `approval_policy = "on-request"` — 每个非读操作问你 (推荐保持)
- `sandbox_mode = "workspace-write"` — 项目内可写, 项目外只读, 无网络 (推荐保持)

### 不要做的事

- ❌ `--dangerously-bypass-approvals-and-sandbox` 或 `--yolo` 在不熟悉的项目用
- ❌ 把 `approval_policy` 改成 `"never"` 在交互场景
- ❌ 在生产服务器装 VibeCoding (本工具是开发助手, 不是部署工具)

### 数据落盘说明

VibeCoding hooks 会把以下信息持久化到本地:

| 文件 | 内容 | 安全 |
|------|------|------|
| `<project>/.ai_state/hook-trace.jsonl` | hook 触发日志 (cmd 前 80 字符) | ✅ 写盘前 redact 脱敏 (token/secret/JWT/SSH-key) |
| `~/.codex/lessons/draft-*.md` | 失败时自动起草的 lesson (含 stderr 前 2000 字符) | ✅ 写盘前 redact 脱敏 |
| `~/.codex/state/retry-counter.json` | subagent-retry hook 的 per-session 计数 | 不含敏感信息 |

**仍建议**:
- 不把生产 .env 放在 Codex 工作目录里
- 定期看 `~/.codex/lessons/draft-*.md`, 不放心就 archive

### 隐私 env

Codex 本身没有显式 telemetry 开关 (走 OpenAI/ChatGPT 标准协议)。如果你需要走代理或第三方中转, 在 `[shell_environment_policy.set]` 里设 `HTTPS_PROXY` 或 `OPENAI_BASE_URL`。


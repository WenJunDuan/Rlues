---
name: vibe-setup
effort: xhigh
disable-model-invocation: true
description: >
  VibeCoding 全局安装。检查 CC 版本、装插件、装 Gstack、装 context7 skill、配置 Codex、部署 hooks、初始化全局 lessons。首次使用运行一次。
---

# /vibe-setup

## Step 0: CC 版本检查

```bash
claude --version
```

要求 v2.1.111 或更高 (Opus 4.7 最低要求)。低于 → `claude update` 或 `npm install -g @anthropic-ai/claude-code@latest`。

## Step 1: Gstack 安装

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup
```

安装后确认 /office-hours 可用。

## Step 2: 插件安装 (CC 原生)

逐个安装，跳过已有的:

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex

/plugin marketplace add lackeyjb/playwright-skill
/plugin install playwright-skill@playwright-skill

/reload-plugins
```

官方插件 (claude-plugins-official 已内置):
```
/plugin install feature-dev
/plugin install code-review
/plugin install commit-commands
/plugin install security-guidance
/plugin install frontend-design
```

## Step 3: context7 安装 (skill 模式，非 plugin)

```bash
npx ctx7 setup --claude
```

无需全局安装 ctx7 CLI，npx 会按需拉取。OAuth 登录后会自动在 `~/.claude/skills/` 下生成 context7 skill。
触发方式: "use context7" 或 "use context7 with /owner/repo for <query>"。

## Step 4: Codex 配置 (关键, 含 permission 修正)

```
/codex:setup
```

未登录 → `!codex login`

**不要启用 review gate** (`/codex:setup --enable-review-gate`)——会造成 Claude ↔ Codex 死循环。

**Codex permission 修正 (v9.4.5 修了 v9.4.4 的错误 pattern)**:

settings.json 的 codex 权限只用冒号语法 (CC 不认 `Bash(!...)`):

```json
"Bash(codex:*)",
"Bash(node:*)"   // codex plugin 内部用 node /path/codex-companion.mjs
```

**首次 `/codex:status` 弹 prompt 时的最佳实践**:
- 选 "Yes, and don't ask again"
- CC 会写到 `.claude/settings.local.json` (项目级最精确 pattern)
- 之后同 project 不再弹

Codex 用独立配置 `~/.codex/config.toml`:

```toml
model = "gpt-5.4-mini"
model_reasoning_effort = "high"
```

## Step 5: Hooks 安装

```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/*.cjs ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.cjs
```

`/hooks` 确认 6 个事件:
SessionStart · PreToolUse · Stop · PermissionRequest · PreCompact · PostCompact
(还有 2 个 PostToolUse hook 在同一事件下: subagent-retry, lesson-drafter)

## Step 6: 全局 lessons 初始化

```bash
mkdir -p ~/.claude/lessons/archive
test -f ~/.claude/lessons/INDEX.md || cat > ~/.claude/lessons/INDEX.md <<'INDEX'
# Global Lessons Index

跨项目工具链/基础设施经验。Claude R₀ 阶段扫此索引找命中主题。

## 主题分类
<!-- lesson-drafter hook 会自动维护此索引 -->

## 文件清单
<!-- 自动维护, 按时间倒序 -->
INDEX
echo "✓ ~/.claude/lessons/ 已初始化"
```

## Step 7: 验证

```bash
ls ~/.claude/skills/gstack/SKILL.md         # Gstack
ls ~/.claude/skills/context7*               # context7 skill
npx ctx7 library express                    # context7 CLI 通
/plugin list                                # 确认 codex / superpowers 已装
npx ecc-agentshield --version               # ECC (npx 调用, 无需 plugin)
/codex:setup                                # Codex 端 ready
ls ~/.claude/lessons/INDEX.md               # 全局 lessons 已初始化
ls ~/.claude/hooks/*.cjs                    # 6+ hook 脚本
```

通过 → "安装完成。每个新项目 `/vibe-init`，然后 `/vibe-dev`。"

## Step 8: 权限和隐私核查 (重要)

VibeCoding 默认 settings.json 启用了较宽的开发权限。安装后**自检以下问题**:

### 你启用了什么权限

```bash
grep '"Bash(' ~/.claude/settings.json | grep -v deny
```

**主要风险点**:
- `Bash(node:*)` — 任意 node 调用 (codex plugin 必需, 范围较宽)
- `Bash(npx *)` — 任意 npx 包 (开发常用, 但等价于"运行任意 npm 包")
- `Bash(npm run *)` `Bash(cargo *)` `Bash(go *)` — 各语言 build, build script 内的代码会被执行

**这些权限对 VibeCoding 工作流是必要的, 但意味着**:
- 在不可信项目里 `/vibe-dev` 时, 项目的 `package.json` `Cargo.toml` 等 build script 会被执行
- agent 路由到任何 npm/cargo 包都不会触发额外 prompt

### 收紧建议 (按需要)

```jsonc
// ~/.claude/settings.json 的 permissions.deny 加你不想被碰的:
"deny": [
  // 已有的危险拦截 (rm -rf /, force push 等)
  "Read(./.env.production)",      // 已有
  "Read(./secrets/**)",            // 已有

  // 按需添加:
  "Read(/etc/**)",                 // 系统配置
  "Bash(sudo *)",                  // 提权
  "Bash(docker *)",                // 容器操作 (如果不开发 docker)
]
```

### 数据落盘说明

VibeCoding hooks 会把以下信息持久化到本地:

| 文件 | 内容 | 安全 |
|------|------|------|
| `<project>/.ai_state/hook-trace.jsonl` | hook 触发日志 (cmd 前 80 字符) | ✅ 写盘前 redact 脱敏 (token/secret/JWT/SSH-key) |
| `~/.claude/lessons/draft-*.md` | 失败时自动起草的 lesson (含 stderr 前 2000 字符) | ✅ 写盘前 redact 脱敏 |

**仍建议**:
- 不要把生产 .env 放在 CC 工作目录里
- 定期看 `~/.claude/lessons/draft-*.md`, 不放心就 `mv` 到 archive/

### 隐私 env 已默认开

```bash
grep -E "DISABLE_NONESSENTIAL_TRAFFIC|FEEDBACK_SURVEY|TELEMETRY" ~/.claude/settings.json
```

应该看到一组 `_DISABLED=1` / `_DISABLED=true`。这些关闭了 Anthropic 非必要遥测、各前端框架的 telemetry。


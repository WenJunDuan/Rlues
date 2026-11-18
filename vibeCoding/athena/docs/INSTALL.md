# Athena 安装指南（给执行安装的 AI）

读者：替用户安装 / 升级 / 回滚 Athena 的 AI agent。每步给命令、判据、失败处理。

**授权**：`install`、`rollback`、改 PATH 都会写用户家目录，执行前向用户列出 dry-run 清单并取得明确同意；`--dry-run` 与 `doctor` 只读，可直接跑。

## 0. 前提

| 检查 | 命令 | 通过条件 |
|---|---|---|
| Node | `node --version` | ≥ 22 |
| 发行物 | `ls vibeCoding/dist/athena/*/cli.cjs`；没有就 `node vibeCoding/athena/build.mjs` | 存在 |
| 版本 | `cat vibeCoding/athena/VERSION` | 与要装的版本一致 |

下文 `CLI` = `node vibeCoding/dist/athena/<ver>/cli.cjs`；装好并加入 PATH 后可直接用 `athena`。

## 1. 选平台

| 平台 | 参数 | 说明 |
|---|---|---|
| Claude Code | `cc` | 默认部署 |
| Codex | `cx` | 默认部署 |
| Pi | `pi` | 可选，默认不部署；用户明确要求才加 |

只装用户选的平台。检测到某个 CLI 存在 ≠ 用户要启用它。

## 2. 预演

```bash
CLI install --platform cc,cx --dry-run
```

把输出里的 `write / merge / retire` 清单给用户看。`retire` = 9.9.x 残留或上次安装写过、本版不再发布的文件（如 CC 的 `rules/session-workflow.md`、`rules/_index.md`；`_index.md` 有用户行时只保留用户部分），会移进备份，不是删除。

## 3. 安装

```bash
CLI install --platform cc,cx
export PATH="$HOME/.athena/bin:$PATH"   # 并写进用户的 shell rc（先问）
athena doctor                            # 必须输出 doctor: no drift
```

失败：安装是事务式的，中途失败会自动回滚；按报错修（常见：用户 JSON 损坏、路径冲突），再跑。

## 4. 合并规则（安装不覆盖用户配置）

| 文件 | 规则 |
|---|---|
| `~/.claude/settings.json` | 包里有、用户没有的顶层键才补；`env` 包补缺、用户已有键优先（`VIBECODING_ATHENA_VERSION` 除外）；`permissions.deny` / `ask` 取并集；用户已有 `permissions` 时包的 `allow` 不加；`enabledPlugins` 用户值优先；`hooks` 替换 Athena 自己的条目、保留第三方 hook |
| `~/.codex/hooks.json` | 同上 hook 规则 |
| `~/.codex/config.toml` | **只在首装时写入包模板**；已有文件只改写 `[shell_environment_policy.set]` 的 `VIBECODING_VERSION` |
| 会话数据 | `sessions`、`history.jsonl`、`projects`、SQLite 等不动 |

包模板的安全基线（首装时生效）：CC 拒读/拒改密钥文件（`.env*`、`~/.ssh`、`~/.aws`、`*.pem` 等），force push / publish 需确认；CX 为官方默认 `on-request` + `workspace-write`。用户自己的放宽（如 `danger-full-access`）属于个人配置，安装器不改。

### Codex 模型与自定义代理参考

Codex 首装模板默认模型为 `gpt-6.2-sol`。已有用户需在自己的 `~/.codex/config.toml` 中修改，升级不会覆盖模型选择。

使用兼容 Responses API 的代理时，按[官方自定义 provider 格式](https://developers.openai.com/codex/config-advanced/#custom-model-providers)配置独立的 `proxy`。下面的根级键替换文件开头已有的对应项，provider 表追加到文件末尾；将示例 URL 换成实际代理地址。

```toml
model_provider = "proxy"
model = "gpt-6.2-sol"
model_reasoning_effort = "high"

[model_providers.proxy]
name = "Codex Proxy"
base_url = "https://proxy.example.com/v1"
wire_api = "responses"
requires_openai_auth = true
```

此示例复用 `~/.codex/auth.json` 中已配置的代理 API 凭据。替换原有自定义 provider 后，删除其旧表并重新启动 Codex；凭据不写进模板或仓库。

### 版本与能力核查（2026-11-18）

- [Codex 发布历史](https://learn.chatgpt.com/docs/changelog)列出 0.169.1 和 GPT-6.2 Sol/Astra。用 `codex features list` 核对当前进程支持的开关。0.169.1 将 `multi_agent_v2` 列为 stable，`multi_agent` 列为 deprecated，`js_repl` 列为 removed。并发数配置见[官方配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)。
- [Claude Code 2.1.327 发布记录](https://github.com/anthropics/claude-code/releases/tag/v2.1.327)包含 Remote Control 和项目 MCP 配置修复。用 `claude --version`、`claude doctor` 和 `/mcp` 核对本机版本、运行条件和连接。模板启用了六个插件。`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 限制可选联网能力，包含 Remote Control 的功能评估。见[官方环境变量说明](https://code.claude.com/docs/en/env-vars)。

## 5. 安装后检查

| 检查 | 判据 |
|---|---|
| `athena doctor` | `no drift` |
| `readlink ~/.athena/current` | 指向新版本 |
| 新开一个 CC / CX 会话 | SessionStart hook 正常，无报错 |
| `~/.claude/settings.json` 的 `enabledPlugins` | 键为 `<plugin>@<marketplace>`，marketplace 是 `claude-plugins-official` 或已在 `extraKnownMarketplaces` 声明。旧版遗留的无效键（如 `@anthropic-official`）安装器不会删，列给用户决定 |

## 6. 回滚

```bash
athena rollback     # 逐文件还原到安装前，current 链接一并还原
athena doctor       # 应输出 not installed（或上一版的 no drift）
```

安装后用户改过的文件留在 `~/.athena/backups/<ts>/after-install/`。备份里可能含密钥，不自动删除，也不要贴进对话。

## 7. 新项目 / 已有项目

- 新项目需要跟踪状态时：`athena init --dry-run` → `athena init`（先问用户）。
- 已有 9.9.x `.ai_state` 的项目：见同目录 `MIGRATION.md`。

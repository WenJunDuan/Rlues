# VibeCoding Hermes Kernel (Codex CLI 端) v9.4.5-hotfix

> 给 Codex CLI 装一个工程纪律。让它不偷懒、不伪装、不替你出馊主意。

## 这是什么

一套 Codex CLI 配置 + hooks + skills + subagents，把 **PACE 工作流路由**、**6 阶段 RIPER 流程**、**双层经验沉淀**、**自动 lesson 起草**、**spawn_agent 协作** 装进 `~/.codex/`。

它**不是**新功能集合，是**纪律层**。

## Quick Start (3 分钟)

```bash
# 0. 检查 Codex 版本 ≥ v0.124.0 (codex_hooks stable 起点)
codex --version

# 1. 解压到家目录 (会覆盖 ~/.codex/config.toml, 先备份)
cp ~/.codex/config.toml ~/.codex/config.toml.bak 2>/dev/null
unzip vibecoding-hermes-v945-hotfix-codex.zip -d ~/

# 2. 给 hook 脚本加执行权限
chmod +x ~/.codex/hooks/*.py

# 3. 验证 codex_hooks 启用 + model 配置
grep "codex_hooks = true" ~/.codex/config.toml
grep "^model = " ~/.codex/config.toml    # 默认 gpt-5.5

# 4. 重启 Codex
codex

# 5. 在任意项目里:
/vibe-init                # 初始化项目状态目录 .ai_state/
/vibe-dev "我要做的事"     # 开发主入口
```

## ChatGPT 订阅 vs API key 用户

- **ChatGPT 订阅** (Plus/Pro/Business/Enterprise): 默认 `model = "gpt-5.5"` 直接可用
- **API key 用户**: GPT-5.5 还没上 API → `codex --profile api` (走 gpt-5.4)
- **快速场景** (1000+ tok/s): `codex --profile codex-spark`

## 必选 vs 可选

| 项                                                         | 必需?    | 说明                                    |
| ---------------------------------------------------------- | -------- | --------------------------------------- |
| `~/.codex/AGENTS.md`                                       | ✅ 必需  | 9 条铁律 + 调度协议, agent 启动会读     |
| `~/.codex/skills/pace/`                                    | ✅ 必需  | PACE 路由器                             |
| `~/.codex/hooks/*.py`                                      | ✅ 必需  | 7 个 hook 脚本                          |
| `~/.codex/config.toml`                                     | ✅ 必需  | inline `[hooks]` + subagent 注册 + 模型 |
| `~/.codex/agents/{evaluator,generator,reviewer}/AGENTS.md` | ✅ 必需  | 3 个 subagent 角色定义                  |
| `~/.codex/lessons/`                                        | ⚠️ 推荐  | 全局工具链经验库                        |
| `context7` (`npx ctx7 setup --codex`)                      | 强烈推荐 | 库文档查询                              |
| `npx ecc-agentshield`                                      | 可选     | 安全扫描 (System 路径用)                |

## 核心命令

| 命令               | 用途                    |
| ------------------ | ----------------------- |
| `/vibe-setup`      | 全局安装向导            |
| `/vibe-init`       | 项目根创建 `.ai_state/` |
| `/vibe-dev <需求>` | **主入口**              |
| `/vibe-review`     | 单独跑审查              |
| `/vibe-status`     | 状态面板                |
| `/lesson-curator`  | 整理 draft 落档         |

## PACE 6 路径速查

| 路径     | 触发     | 文件量 | 工作流                                             |
| -------- | -------- | ------ | -------------------------------------------------- |
| Hotfix   | 1 行修改 | 1      | 直接改                                             |
| Bugfix   | 调试问题 | 1-5    | TDD 复现 + 修                                      |
| Quick    | 小需求   | 1-10   | impl → review → ship                               |
| Feature  | 中需求   | 5-20   | plan → impl → review → ship + spawn_agent reviewer |
| Refactor | 改结构   | 10-50  | 同上 + spawn_agent generator 并行                  |
| System   | 跨模块   | 20+    | 上述 + design 阶段 + ECC + E2E                     |

## subagent 体系 (Codex 独有)

3 个 subagent 通过 spawn_agent 调起, 用 AGENTS.md 文件定义角色:

| subagent  | sandbox         | 职责                                       |
| --------- | --------------- | ------------------------------------------ |
| evaluator | read-only       | 质量评审, F/SC/B/C/R 五维评分              |
| generator | workspace-write | 隔离环境 TDD 实现                          |
| reviewer  | read-only       | 独立代码审查 (对位 /review 内置, 第二视角) |

System 路径 impl 阶段会 spawn_agent generator 并行做 (同模式 Task 成组)。

## hooks 全景

| Hook                                  | 作用                                                    |
| ------------------------------------- | ------------------------------------------------------- |
| SessionStart (startup\|resume\|clear) | 注入铁律 + INDEX + project state, 顺手 archive 老 draft |
| **UserPromptSubmit** (Codex 独有)     | 关键词驱动注入 R₀/铁律 8/反伪造提醒                     |
| PreToolUse Bash                       | 拦截危险命令 (rm -rf 根、force push 等)                 |
| PostToolUse                           | subagent-retry (治懒惰) + lesson-drafter (自动起草)     |
| PermissionRequest                     | systemMessage 提示 (Codex 协议受限)                     |
| Stop                                  | delivery-gate 质量门                                    |

## lessons 双层

```
~/.codex/lessons/                        全局工具链经验 (跨项目)
<project>/.ai_state/lessons.md          项目级业务经验
```

工具失败 (sandbox 拒绝 / spawn_agent 放弃 / approval 流程问题) 自动起草 draft, `/lesson-curator` 整理落档。

## 安全提示

- `sandbox_mode = "workspace-write"` 默认 - 项目内可写, 项目外只读, 无网络
- `approval_policy = "on-request"` - 每个非读操作问你
- `lesson-drafter` 和 `hook-trace` 写盘前过 **redact 脱敏** (token/secret/key/JWT/SSH-key 全自动)
- 仍建议: 不把生产 .env 放在工作目录, 定期审 draft

## 跨平台

`.ai_state/` schema 与 CC 端 **完全一致**, 同项目可在两端切换。

## 出问题

1. `/vibe-status` 健康面板
2. `.ai_state/hook-trace.jsonl` 最近 hook 记录
3. `~/.codex/lessons/draft-*.md` 自动起草问题
4. 完整说明: `RELEASE-NOTES.md`

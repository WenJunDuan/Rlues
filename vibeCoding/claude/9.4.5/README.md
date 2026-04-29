# VibeCoding Hermes Kernel (Claude Code 端) v9.4.5-hotfix

> 给 Claude Code 装一个工程纪律。让它不偷懒、不伪装、不替你出馊主意。

## 这是什么

一套 Claude Code 配置 + hooks + skills，把 **PACE 工作流路由**、**6 阶段 RIPER 流程**、**双层经验沉淀**、**自动 lesson 起草** 装进 `~/.claude/`。

它**不是**新功能集合，是**纪律层**——通过 hook 强制 agent 按规矩工作，通过 lesson 系统让经验跨项目复用。

## Quick Start (3 分钟)

```bash
# 1. 解压到家目录 (会覆盖 ~/.claude/settings.json, 先备份)
cp ~/.claude/settings.json ~/.claude/settings.json.bak 2>/dev/null
unzip vibecoding-hermes-v945-hotfix-claude-code.zip -d ~/

# 2. 给 hook 脚本加执行权限
chmod +x ~/.claude/hooks/*.cjs

# 3. 重启 Claude Code (hooks 在启动时 snapshot, 必须重启)

# 4. 进入 CC, 在任意项目里跑:
/vibe-init                # 初始化项目状态目录 .ai_state/
/vibe-dev "我要做的事"     # 开发主入口 (会自动路由到合适的 PACE 路径)
```

完成。

## 必选 vs 可选

| 项                                     | 必需?    | 说明                                                      |
| -------------------------------------- | -------- | --------------------------------------------------------- |
| `~/.claude/CLAUDE.md`                  | ✅ 必需  | 9 条铁律 + 调度协议, agent 启动会读                       |
| `~/.claude/skills/pace/`               | ✅ 必需  | PACE 路由器, /vibe-dev 触发它                             |
| `~/.claude/hooks/*.cjs`                | ✅ 必需  | 7 个 hook 脚本: 危险命令拦截、质量门、自动起草 lessons 等 |
| `~/.claude/settings.json`              | ✅ 必需  | hooks 注册 + 权限 + 模型 + 隐私 env                       |
| `~/.claude/lessons/`                   | ⚠️ 推荐  | 全局工具链经验库, lesson-drafter hook 自动起草            |
| `superpowers` plugin                   | 可选     | brainstorming 阶段增强                                    |
| `codex` plugin                         | 可选     | 跨模型审查 (Codex), `/codex:review` 触发                  |
| `playwright-skill` plugin              | 可选     | E2E 测试                                                  |
| `context7` (`npx ctx7 setup --claude`) | 强烈推荐 | 库文档查询                                                |

> **如果你只想先试试**: 跑完 Quick Start 4 步就行, 其他都是渐进增强。

## 核心命令

| 命令               | 用途                                           |
| ------------------ | ---------------------------------------------- |
| `/vibe-setup`      | 全局安装向导 (插件、context7、ECC AgentShield) |
| `/vibe-init`       | 在项目根创建 `.ai_state/` 状态目录             |
| `/vibe-dev <需求>` | **主入口** - 路由 + 完整流程                   |
| `/vibe-review`     | 单独跑审查 (不走完整流程)                      |
| `/vibe-status`     | 状态面板 (PACE / hooks / lessons 健康)         |
| `/lesson-curator`  | 整理待审 draft → 落档全局 lessons              |

## PACE 6 路径速查

| 路径     | 触发     | 文件量 | 工作流                                 |
| -------- | -------- | ------ | -------------------------------------- |
| Hotfix   | 1 行修改 | 1      | 直接改                                 |
| Bugfix   | 调试问题 | 1-5    | TDD 复现 + 修                          |
| Quick    | 小需求   | 1-10   | impl → review → ship                   |
| Feature  | 中需求   | 5-20   | plan → impl → review → ship + 交叉审查 |
| Refactor | 改结构   | 10-50  | 同上 + spawn_agent 并行 worker         |
| System   | 跨模块   | 20+    | 上述 + design 阶段 + ECC + E2E         |

`/vibe-dev` 接收需求后自动判定路径。impl 中途发现复杂度超标 → 暂停询问升级。

## lessons 双层

```
~/.claude/lessons/                       全局工具链经验 (跨项目)
  INDEX.md                                主题索引
  2026-04-28-codex-permission.md          已确认的 lesson
  draft-*.md                              自动起草, 待你审 (lesson-drafter hook 写)
  archive/                                7 天未审的自动归档

<project>/.ai_state/lessons.md           项目级业务经验
                                          Sprint Gate 通过后由 compound skill 写
```

工具失败时（permission denied / hook 协议错 / codex 调用挂）会**自动起草** draft, 你 `/lesson-curator` 整理一下落档, 下次同类问题 R₀ 阶段自动命中。

## 安全提示

启用本配置默认开启的权限:

- `Bash(node:*)` - 任意 node 调用 (codex plugin 必需, 但范围较宽)
- `Bash(npx *)` - 任意 npx 包
- `Bash(npm run *)` `Bash(cargo *)` `Bash(go *)` `Bash(python *)` - 各语言 build

如果在生产或敏感环境用, 收紧建议:

- 把 `Bash(node:*)` 改成 `Bash(node */codex-companion*)` (虽然 CC 中段通配支持有限, 至少更窄)
- 在 `permissions.deny` 加你不想被碰的路径
- 关掉不需要的 plugin (`/plugin disable <n>`)

**lesson-drafter 和 hook-trace 写盘前会过 redact (token/secret 脱敏)**, 但仍建议:

- 不要把生产环境的 `.env` 放在 CC 工作目录里
- 定期看 `~/.claude/lessons/draft-*.md` 是否含敏感信息, 不放心就 archive

## 跨平台

`.ai_state/` schema 与 Codex 端 (`vibecoding-hermes-v945-hotfix-codex.zip`) **完全一致**。同一项目可:

- 早上在 CC 里 plan
- 下午在 Codex 里 impl
- 晚上回 CC 里 review

两端共享状态文件无障碍。

## 出问题怎么办

1. `/vibe-status` 看健康面板
2. 看 `.ai_state/hook-trace.jsonl` 最近 hook 触发
3. 看 `~/.claude/lessons/draft-*.md` 是否有自动起草的相关问题
4. 完整说明: `RELEASE-NOTES.md` (本目录)

## 文档

- `RELEASE-NOTES.md` - v9.4.5-hotfix 的全部变更 + 设计哲学
- `CLAUDE.md` - 给 agent 看的铁律 (你也可以读, 看 agent 被怎么约束)
- `lessons/README.md` - 全局 lessons 系统说明

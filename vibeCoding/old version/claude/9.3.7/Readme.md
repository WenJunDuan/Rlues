# VibeCoding Kernel v9.3.7 — README

## 它是什么

VibeCoding 是运行在 Claude Code 之上的 **Harness Coding Agent** — 32 个文件, 1641 行。

它不是新平台，不重写任何已有能力。它做三件事：

1. **编排** — 告诉 Agent 每一步调哪个原生命令或插件
2. **状态** — 4 个 JSON 文件记录进度，hooks 程序化验证
3. **门禁** — 6 个 hooks 读 JSON，不达标就阻断交付

**核心原则：CC 原生能做的用原生，原生不够的调插件，插件也做不到的才自己写。**

---

## 快速开始

```
/vibe-install          # 首次：安装全部插件（只需一次）
/vibe-init             # 每个项目：初始化环境和状态文件
/vibe-dev [需求描述]    # 开始开发
/vibe-resume           # 中断后恢复
/vibe-status           # 查看进度
```

---

## 版本演进

| 版本       | 文件   | 行数     | 核心变化                        | 教训                       |
| :--------- | :----- | :------- | :------------------------------ | :------------------------- |
| v9.3.0     | 59     | 789      | gstack + 7 插件                 | 提示词被砍太薄             |
| v9.3.5     | 48     | 1774     | +三 Agent +codex-plugin-cc      | hooks 格式/exit codes 全错 |
| v9.3.5h    | 48     | 1774     | 修 8 个 bug                     | 提示词≠程序强制            |
| v9.3.6     | 57     | 2348     | +JSON 状态 +hooks 读 JSON       | 自写 186 行评分=重写插件   |
| **v9.3.7** | **32** | **1641** | **原生优先+插件编排+hook 验证** | **调轮子不造轮子**         |

---

## 架构

```
┌────────────────────────────────────────────────┐
│  VibeCoding Harness (32 文件, 1641 行)          │
│                                                 │
│  编排: workflow skill (PACE→RIPER-7→每阶段调谁)  │
│  状态: 4 JSON (state/features/quality/progress)  │
│  门禁: 6 hooks (读 JSON→放行/阻断)              │
├────────────────────────────────────────────────┤
│  CC 原生                                        │
│  /review · /plan · /diff · /compact · git       │
│  + 8 插件                                       │
│  GSD · codex · superpowers · ECC                │
│  code-review · feature-dev · commit-cmds        │
│  playwright                                     │
├────────────────────────────────────────────────┤
│  CC Platform                                    │
│  Agent core · Hooks · Subagents · Worktree      │
└────────────────────────────────────────────────┘
```

---

## 文件清单

### 入口 + 配置 (3)

| 文件          | 行数 | 作用                                                            |
| :------------ | :--- | :-------------------------------------------------------------- |
| CLAUDE.md     | 204  | 身份 + 铁律 + 架构 + 原生命令 + 插件表 + 隐私 + 工具安装指南    |
| settings.json | 174  | 8 plugins + 6 hooks + 36 allow/12 deny + 11 env vars (6 隐私=1) |
| .mcp.json     | 19   | cunzhi (人工检查点) + augment-context (语义搜索)                |

### Agents (3 subagent)

| 文件          | 行数 | 做什么                                                                 |
| :------------ | :--- | :--------------------------------------------------------------------- |
| generator.md  | 45   | 调 GSD execute → codex:rescue → superpowers → TDD                      |
| evaluator.md  | 129  | 调 /review → codex:adversarial → playwright → ECC，综合出 quality.json |
| scaffolder.md | 17   | /vibe-init 时创建脚手架                                                |

### Hooks (6 程序化强制，已通过 9 场景模拟验证)

| 文件                  | 行数 | 事件                                | 读什么                  | 做什么                                                      |
| :-------------------- | :--- | :---------------------------------- | :---------------------- | :---------------------------------------------------------- |
| context-loader.cjs    | 52   | SessionStart                        | state+progress+features | state.path 非空时注入恢复上下文                             |
| delivery-gate.cjs     | 62   | Stop                                | state+features+quality  | Path A 宽松；Path B+ 检查 features passes + quality verdict |
| post-edit-check.cjs   | 40   | PostToolUse(Write\|Edit\|MultiEdit) | features+quality        | 防篡改 + 结构验证（0=未评分，允许）                         |
| pre-bash-guard.cjs    | 7    | PreToolUse(Bash)                    | —                       | 6 种危险命令正则拦截                                        |
| permission-denied.cjs | 9    | PermissionDenied                    | —                       | hookSpecificOutput: retry=false                             |
| stop-failure.cjs      | 14   | StopFailure                         | —                       | 写 .ai_state/recovery.json                                  |

**Hook 输出格式全部对齐官方文档**：

- SessionStart: `hookSpecificOutput.additionalContext`
- Stop: exit 0 放行 / exit 2 + stderr 阻断
- PostToolUse: stderr 警告（官方确认不能阻断）
- PreToolUse: exit 2 阻断
- PermissionDenied: `hookSpecificOutput.retry`

**模板防误报**：

- state.json.path 为空 → context-loader 不输出
- feature_list.json description 以 `[` 开头（占位符）→ delivery-gate 跳过
- quality.json.sprint === 0（模板）→ delivery-gate 跳过
- quality.json scores === 0（未评分）→ post-edit-check 允许

### Skills (4 VibeCoding 独有)

| 文件                     | 行数 | 为什么不能用插件替代                           |
| :----------------------- | :--- | :--------------------------------------------- |
| workflow/SKILL.md        | 270  | PACE+RIPER-7：没有工具做"何时调哪个命令"       |
| sprint-contract/SKILL.md | 177  | 验收合同协商：Generator↔Evaluator 动手前谈清楚 |
| kaizen/SKILL.md          | 23   | 经验沉淀：无工具做跨项目知识积累               |
| reflexion/SKILL.md       | 18   | 自我反思：superpowers 没有自检机制             |

### Commands (5)

| 文件            | 行数 | 用途                                   |
| :-------------- | :--- | :------------------------------------- |
| vibe-install.md | 79   | 安装全部插件和工具（全局一次）         |
| vibe-init.md    | 57   | 初始化项目环境和状态文件（每项目一次） |
| vibe-dev.md     | 14   | 主入口：需求→workflow→PACE→RIPER-7     |
| vibe-resume.md  | 14   | 中断恢复：get-your-bearings 7 步       |
| vibe-status.md  | 17   | 看板：读 JSON                          |

### Rules (1)

| 文件                | 行数 |
| :------------------ | :--- | -------------------- |
| coding-standards.md | 110  | 11 编程原则 P0/P1/P2 |

### Templates (10)

| 文件                                                        | 格式     | 用途                       |
| :---------------------------------------------------------- | :------- | :------------------------- |
| state.json                                                  | JSON     | 总控状态（hooks 读写）     |
| feature_list.json                                           | JSON     | 验收真值源（hooks 验证）   |
| quality.json                                                | JSON     | 评分（hooks 验证）         |
| progress.json                                               | JSON     | 跨 session 日志            |
| design.md / plan.md / contract.md / doing.md / knowledge.md | Markdown | 人类可读文档               |
| init.sh                                                     | Shell    | 启动 dev server + 基线验证 |

---

## 原生 vs 插件

### CC 原生（不需要安装）

| 命令                     | 用途         | RIPER-7 阶段 |
| :----------------------- | :----------- | :----------- |
| `/review`                | 内置代码审查 | T            |
| `/plan` 或 `Shift+Tab`   | Plan Mode    | P            |
| `/diff`                  | 查看变更     | T            |
| `/compact`               | 压缩上下文   | 任意         |
| `git commit/push`        | 版本控制     | V            |
| `/effort` + `ultrathink` | 调整推理深度 | 复杂问题     |
| `/loop`                  | 定时执行     | 监控         |

### 8 个插件（原生不够时增强）

| 插件                | enabledPlugins key                            | 增强了什么                              |
| :------------------ | :-------------------------------------------- | :-------------------------------------- |
| **GSD**             | gsd@gsd-build                                 | spec 访谈 + fresh context + 原子 commit |
| **Codex**           | codex@openai-codex                            | GPT-5.4 写代码 + 对抗审查               |
| **Superpowers**     | superpowers@superpowers-marketplace           | brainstorm + execute-plan + plan-review |
| **ECC**             | everything-claude-code@everything-claude-code | 102 条安全规则 + 红蓝对抗               |
| **Playwright**      | playwright-skill@playwright-skill             | E2E 测试 + 截图                         |
| **feature-dev**     | feature-dev@claude-plugins-official           | 7 阶段开发参考                          |
| **code-review**     | code-review@claude-plugins-official           | 4-agent 并行审查                        |
| **commit-commands** | commit-commands@claude-plugins-official       | git 增强格式                            |

---

## settings.json 配置说明

### enabledPlugins（对象格式）

```json
{ "pluginName@marketplaceName": true }
```

声明插件启用意图。未安装时 CC 启动提示 trust and install。

### extraKnownMarketplaces（嵌套 source 格式）

```json
{
  "marketplaceName": { "source": { "source": "github", "repo": "owner/repo" } }
}
```

第三方 marketplace 源。Anthropic 官方插件不需要声明。

### environmentVariables（11 个，6 个隐私=1）

- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`：总开关
- `DISABLE_TELEMETRY=1`：遥测
- `DISABLE_ERROR_REPORTING=1`：错误上报
- `DISABLE_BUG_COMMAND=1`：bug 命令
- `DISABLE_NON_ESSENTIAL_MODEL_CALLS=1`：非必要模型调用
- `CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY=1`：问卷弹窗
- `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-4-6`：subagent 模型

### hooks（6 个事件，三层嵌套）

```json
{
  "event": [
    { "matcher?": "regex", "hooks": [{ "type": "command", "command": "..." }] }
  ]
}
```

注意：Stop 不支持 matcher（官方文档确认：silently ignored）。

### permissions（36 allow + 12 deny）

对齐 v9.3.2 基线，新增 python/pip/sed/awk 等。

---

## RIPER-7 工作流

```
需求 → PACE 评估 (5维) → Path A/B/C/D

Path A: 快速修复
  GSD quick / 直接写 → 原生 git commit → 交付

Path B/C/D: 完整 Sprint 循环
  R₀ → GSD discuss + superpowers brainstorm + augment-context
  R  → GSD map-codebase + augment-context + context7
  D  → superpowers plan-review + @evaluator 审合同 → feature_list.json
  P  → GSD plan-phase + /plan (原生) + superpowers plan-review
  E  → @generator: GSD execute → codex:rescue → superpowers → TDD
  T  → @evaluator: /review + /diff + codex:adversarial + playwright + ECC
       → quality.json → delivery-gate 放行/阻断
  V  → git commit + kaizen + progress.json + context reset (C/D)
```

---

## Sprint Contract

VibeCoding 独有的 Generator↔Evaluator 协商机制：

1. Planner 基于 design.md 草拟合同（Features + 验收步骤 + 边界条件 + 不在范围）
2. @evaluator 5 条审核（可测性 / 边界覆盖 / 范围明确 / 与 design 一致 / 时间合理）
3. 最多 2 轮协商，超过→用户拍板
4. 合同锁定→展开为 feature_list.json（hooks 程序化验证）

---

## 外部工具安装

### 插件

```bash
/plugin marketplace add [publisher]
/plugin install [name]@[marketplace]
/plugins              # 查看状态
/reload-plugins       # 重载
```

### Skills

```bash
# 项目级: .claude/skills/[name]/SKILL.md
# 全局级: ~/.claude/skills/[name]/SKILL.md
# 查看: /skills
```

### MCP

```bash
# 项目级: .claude/.mcp.json
# 全局级: ~/.claude/.mcp.json
# 查看: /mcp
```

### Hooks

```bash
# 配置: settings.json → hooks
# 查看: /hooks
# 禁用: "disableAllHooks": true
```

---

## 设计哲学

```
CC 原生能做的 → 用原生       (/review /plan /diff git)
原生做不好的   → 调插件       (GSD codex ECC playwright)
插件也做不到的 → 我们才写     (PACE RIPER-7 Sprint Contract JSON闭环)
```

> "The model is the brain. The harness is everything else." — Anthropic

VibeCoding 就是那个 "everything else"。

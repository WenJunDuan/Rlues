# VibeCoding Kernel v9.3.8

> 将工程化思维融入 AI 编程的 Coding Harness。
> 让粗通 vibe coding 的人也能产出工程级代码。

---

## 快速开始

```bash
# 1. 把 .claude/ 目录复制到你的系统根目录
cp -r .claude/ /path/to/target/

# 2. 在 Claude Code 中安装插件 (首次)
/vibe-install

### 如果自动不成功手动安装插件

# 3. 初始化项目
/vibe-init

# 4. 开始开发
/vibe-dev 做一个用户登录功能, 支持邮箱密码注册和登录
```

---

## 它做了什么

VibeCoding 在 Claude Code 上层搭建了一个工程化的工作流:

```
用户需求 → PACE 路由 (评估复杂度) → RIPER 编排 (按阶段执行)
         → 需求精炼 → 技术调研 → 方案定稿 → 计划排期
         → 代码实现 (TDD + 跨模型委托)
         → 质量审查 (Codex 跨模型审查 + 4 维评分)
         → 交付 (delivery-gate 程序化门控)
```

核心原则: **用确定性机制 (hooks, state, rules) 包裹概率性系统 (LLM), 使其行为可预测、可追溯、可恢复。**

---

## 架构概览

### 三层分工

| 层     | 角色              | 回答的问题     | 载体                                         |
| ------ | ----------------- | -------------- | -------------------------------------------- |
| 编排层 | VibeCoding Kernel | WHEN + WHERE   | CLAUDE.md, RIPER-PACE, rules/, .ai_state/    |
| 能力层 | Plugins + Skills  | HOW            | codex-plugin-cc, superpowers, ECC, context7  |
| 执行层 | Hooks + State     | DID IT HAPPEN? | hooks/_.cjs, .ai_state/_.json, delivery-gate |

### 插件栈

| 插件                 | 来源                            | 核心能力                                                                                 |
| -------------------- | ------------------------------- | ---------------------------------------------------------------------------------------- |
| **codex-plugin-cc**  | OpenAI 官方 (3.4K⭐)            | `/codex:review` 标准审查, `/codex:adversarial-review` 对抗审查, `/codex:rescue` 委托执行 |
| **superpowers**      | obra/superpowers                | brainstorming (自动激活需求发散), writing-plans, subagent-driven-development             |
| **ECC AgentShield**  | affaan-m/everything-claude-code | `npx ecc-agentshield scan` 安全扫描 (红蓝对抗)                                           |
| **context7**         | nicobailon/context7             | `npx ctx7 resolve {{库名}}` 查库文档                                                     |
| **playwright-skill** | lackeyjb/playwright-skill       | 前端 E2E 浏览器自动化测试                                                                |
| **CC 内置**          | Anthropic                       | `/review` 本地审查, `@agent` subagent 调用                                               |

### RIPER-PACE 工作流

**PACE 路由** — 五维评估选择执行路径:

| Path     | 适用场景                | 阶段                              |
| -------- | ----------------------- | --------------------------------- |
| A (快速) | 修 bug, 改配置, <30min  | E → T                             |
| B (标准) | 新功能, 重构, 30min-4h  | R₀ → R → D → P → E → T → V        |
| C (复杂) | 跨模块, 架构变更, 4h-2d | 同 B + 并行 @generator + 对抗审查 |
| D (系统) | 跨服务, 全栈, >2d       | 同 C + 设计评审                   |

**RIPER 阶段:**

- R₀ 需求精炼 → R 技术调研 → D 方案定稿 → P 计划排期 → E 执行 → T 测试验证 → V 归档

### 用户命令

| 命令                | 用途                              |
| ------------------- | --------------------------------- |
| `/vibe-dev <需求>`  | 完整开发流程 (引导式, 推荐新手用) |
| `/vibe-plan <需求>` | 只规划不执行                      |
| `/vibe-work`        | 只执行 (需先有 plan)              |
| `/vibe-review`      | 只审查                            |
| `/vibe-install`     | 安装所有插件 (首次)               |
| `/vibe-init`        | 初始化项目 .ai_state/             |

---

## 目录结构

```
.claude/
├── CLAUDE.md                       # Agent 角色剧本 + 操作手册 (234 行)
├── settings.json                   # CC 配置: 插件 + hooks + 权限 (191 行)
│
├── rules/                          # 条件规则 (自动加载, <important> 标签)
│   ├── iron-rules.md                 5 条铁律
│   ├── code-standards.md             编程标准 P0/P1/P2
│   └── plugin-dispatch.md            工具调度表 (哪个阶段用哪个插件)
│
├── skills/                         # 技能 (按需触发, 有 effort frontmatter)
│   ├── riper-pace/SKILL.md           核心引擎: PACE 路由 + RIPER 编排 (273 行)
│   ├── plan/SKILL.md                 规划: 需求→设计→Sprint (199 行)
│   ├── execute/SKILL.md              执行: 三级委托 + TDD (154 行)
│   ├── review/SKILL.md               审查: 多工具编排 + 4 维评分 (152 行)
│   ├── reflexion/SKILL.md            反思: Task 完成后自我审查
│   └── conventions/SKILL.md          规范: 项目知识库 + Gotchas
│
├── agents/                         # Subagents (独立上下文)
│   ├── generator.md                  @generator: 代码生成 (worktree 隔离)
│   ├── evaluator.md                  @evaluator: 质量评审 + 4 维评分
│   └── scaffolder.md                 @scaffolder: 项目初始化
│
├── commands/                       # 用户命令 (slash commands)
│   ├── vibe-dev.md                   完整开发流程
│   ├── vibe-plan.md                  只规划
│   ├── vibe-work.md                  只执行
│   ├── vibe-review.md                只审查
│   ├── vibe-install.md               安装插件栈
│   └── vibe-init.md                  项目初始化
│
├── hooks/                          # 程序化执行 (不可绕过, JSON output)
│   ├── context-loader.cjs            SessionStart: 恢复 .ai_state/ 上下文
│   ├── delivery-gate.cjs             Stop: 交付质量门控
│   ├── pre-bash-guard.cjs            PreToolUse: 危险命令拦截
│   ├── post-edit-check.cjs           PostToolUse: 状态文件一致性
│   ├── permission-denied.cjs         PermissionDenied: auto mode 降级
│   └── stop-failure.cjs              StopFailure: API 错误恢复
│
└── templates/ai-state/             # 状态模板 (8 个文件)
```

---

## 与 v9.3.7 对比

| 维度          | v9.3.7                     | v9.3.8                                       |
| ------------- | -------------------------- | -------------------------------------------- |
| 文件数 / 行数 | 32 / 1162                  | 34 / 2188                                    |
| CLAUDE.md     | 108 行 (目录索引)          | 234 行 (角色剧本 + 操作手册)                 |
| Codex 集成    | gstack (社区)              | **codex-plugin-cc (OpenAI 官方)**            |
| 核心引擎      | workflow/SKILL.md (267 行) | riper-pace/SKILL.md (273 行) + 3 verb skills |
| Rules         | 内嵌 CLAUDE.md             | **独立 rules/ 目录** + `<important>` 标签    |
| Hooks 输出    | exit code 0/2              | **hookSpecificOutput JSON 结构化**           |
| Hook 事件     | 4 个                       | **6 个** (+StopFailure, +PermissionDenied)   |
| Stop 评估     | delivery-gate 单一         | **prompt hook (Haiku) + delivery-gate 双重** |
| Hook 过滤     | matcher only               | **matcher + `if` condition** (减少误触发)    |
| Skill 设计    | 无 effort / 无 gotchas     | **effort frontmatter + Gotchas section**     |
| 用户界面      | RIPER-7 直接暴露           | **verb skills** (plan/execute/review)        |
| 插件命令      | 未验证 / 多处错误          | **逐个对照官方源验证**                       |

---

## 5 条铁律

1. **设计先行** — 设计未经用户确认前不写实现代码 (Path A 例外)
2. **TDD 强制** — 先写测试, 再写实现
3. **Sisyphus 完整性** — plan.md 所有 Task 全部完成才能离开 E 阶段
4. **Reflexion 强制** — 每个 Task 完成后自我审查
5. **Quality Gate 4 级** — PASS (≥4.0) / CONCERNS / REWORK / FAIL

违反铁律 → delivery-gate hook 程序化阻断交付。

---

## Review 审查报告

v9.3.8 经过三轮审查:

**第一轮: 程序化审计** — 10 项检查全绿 (JSON 合法性、交叉引用、effort frontmatter、hook 语法、Gotchas 覆盖)

**第二轮: Agent 视角走查** — 发现并修复 7+2 个问题:

| #   | 类型   | 问题                                          | 修复                                        |
| --- | ------ | --------------------------------------------- | ------------------------------------------- |
| 1   | BUG    | riper-pace 写 state.json 时 .ai_state/ 不存在 | 加前置检查 + CLAUDE.md 步骤 3               |
| 2   | DESIGN | superpowers 调用方式不明确                    | plan/execute/plugin-dispatch 加调用说明     |
| 3   | BUG    | D 阶段用 adversarial-review (无代码可审)      | 三处统一改为 @evaluator + plan-review       |
| 4   | DESIGN | review 后台与 @evaluator 时序不明确           | Path B/C 改为明确的 status→result→evaluator |
| 5+7 | DESIGN | riper-pace 不引用 verb skills                 | 每阶段加 "详细指引 → xxx/SKILL.md"          |
| 6   | BUG    | curl\|bash pipe injection hook 不可达         | settings.json 加 if: Bash(curl/wget \*)     |
| 8   | 追加   | plan skill D 阶段残留 adversarial-review      | 同 #3                                       |
| 9   | 追加   | riper-pace Gotchas 缺 D 阶段陷阱              | 新增条目                                    |

**第三轮: 3 个场景完整走查** — 全新项目 + 恢复中断 + Path A 快速修复 — 全部通过

**第四轮: 插件命令官方源验证** — 逐个去 GitHub/npm 查实际命令格式, 发现并修复 4 个致命问题:

| #   | 类型     | 问题                               | 影响               | 修复                                   |
| --- | -------- | ---------------------------------- | ------------------ | -------------------------------------- |
| 10  | **致命** | superpowers 命令全部写错 (无斜杠)  | agent 调不到插件   | 全部改为 `/superpowers:brainstorm` 等  |
| 11  | **致命** | `plan-review` 命令不存在           | D 阶段降级不可执行 | 替换为 `/review` (CC 内置)             |
| 12  | **致命** | context7 `npx ctx7 resolve` 不存在 | 库文档查询不可执行 | 改为 `/context7:docs` + "use context7" |
| 13  | **配置** | context7 不在 settings.json        | 插件不会安装       | 加入 marketplace + enabledPlugins      |

**最终验证:** 5 marketplace ✅ / 8 plugins ✅ / 所有命令对照官方源 ✅ / 0 残留错误 ✅

**Hook 模拟测试** — 12 个场景全部行为正确 (含 curl\|bash 拦截修复验证)

**第四轮: 全链路运行模拟** — 50 步完整 Path B 场景走查, 发现并修复 4 个问题:

| #   | 类型         | 问题                                                                                        | 影响                               | 修复                               |
| --- | ------------ | ------------------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------- |
| C1  | **CRITICAL** | superpowers 三个 slash 命令全部废弃 (`disable-model-invocation: true`)                      | Agent 无法调用, 整个 R₀/E 阶段断裂 | 改为 skill 自动激活描述            |
| C2  | **CRITICAL** | Level 2 降级路径 (`/superpowers:execute-plan`) 断裂                                         | Codex 不可用时无法降级             | Level 2 改为 @generator subagent   |
| S1  | SIGNIFICANT  | superpowers brainstorming 输出位置冲突 (`docs/superpowers/plans/` vs `.ai_state/design.md`) | 后续阶段找不到设计文档             | 明确要求整理到 .ai_state/design.md |
| S2  | SIGNIFICANT  | superpowers writing-plans 可能自动激活干扰 P 阶段 plan 格式                                 | plan.md 格式不一致                 | P 阶段注明 VibeCoding 格式优先     |

**插件命令验证 (对照官方文档):**

- codex-plugin-cc: 7 个命令全部正确 ✅ (对照 github.com/openai/codex-plugin-cc README)
- ECC AgentShield: `npx ecc-agentshield scan/--fix/--opus/init` 全部正确 ✅ (对照 npmjs.com/package/ecc-agentshield)
- context7: `npx ctx7 resolve` 正确 ✅
- superpowers: 改为自动激活描述, 不再引用已废弃的 slash 命令 ✅ (对照 obra/superpowers issue #669, #756, RELEASE-NOTES.md)

**第五轮: 全文件逐个 Review + 边界场景** — 发现并修复 3 个问题:

| #   | 类型 | 问题                                                                         | 修复                                   |
| --- | ---- | ---------------------------------------------------------------------------- | -------------------------------------- |
| 14  | BUG  | execute skill 前置检查要求 plan.md, 但 Path A 没有 plan                      | 加 Path A 判断分支 + Path A 快速执行段 |
| 15  | BUG  | generator agent 用 `/context7:docs` (不存在的命令)                           | 改为 `npx ctx7 resolve`                |
| 16  | BUG  | review skill Path D 引用 "步骤 1-4" 但 Path C 有 5 步, 丢了 @evaluator       | 改为 "步骤 1-5"                        |
| 17  | BUG  | context7 命令在 CLAUDE.md + plan + riper-pace 共 6 处写错为 `/context7:docs` | 全部改为 `npx ctx7 resolve`            |
| 18  | BUG  | vibe-install 验证命令 `/context7:docs --help`                                | 改为 `npx ctx7 --version`              |

**五轮审查累计:** 发现并修复 **18 个问题** (4 CRITICAL + 6 SIGNIFICANT + 8 BUG)

---

## 平台兼容

- **Claude Code**: v2.1.89 (2026-04-01)
- **codex-plugin-cc**: openai/codex-plugin-cc (2026-03-30)
- **Node.js**: 18.18+
- **本包仅 CC (Claude Code)**。CX (Codex CLI) 包在独立 session 迭代。

---

## 设计哲学

> "Agent 是模型。Harness 是 agent 运行的世界。世界的质量决定智能的表达。"
> — shareAI-lab/learn-claude-code

VibeCoding 不重写插件已有的能力。它只做三件事:

1. **路由** — PACE 评估复杂度, 选择执行路径
2. **编排** — RIPER 按阶段调度插件
3. **执行** — Hooks + State 程序化检查, 确保每一步真正完成

插件做 HOW, VibeCoding 做 WHEN + WHERE + DID IT HAPPEN。

---

## 给新用户的快速入门

如果你是第一次使用 VibeCoding:

1. **安装插件**: `/vibe-install` (只需一次)
2. **初始化项目**: `/vibe-init` (每个项目一次)
3. **开始开发**: `/vibe-dev 你的需求描述`

VibeCoding 会引导你走完: 需求分析 → 设计确认 → 代码实现 → 质量审查 → 交付。
过程中会在关键节点请你确认。你不需要记住 RIPER-PACE 的阶段名称。

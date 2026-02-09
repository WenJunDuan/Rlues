# VibeCoding Kernel — 版本演进记录

> 从 v7.x 单文件 prompt 到 v8.2.1 模块化 agent 架构的完整历程

---

## 版本全景

| 版本 | 日期 | 核心事件 | 文件数 | AI 上下文 |
|:---|:---|:---|:---|:---|
| v7.x | ~2025 | 单文件 prompt, RIPER-5 | 1 | ~3000L |
| v8.0 | 2026-02-08 | 模型适配重构 (Opus 4.6 + Codex 5.3) | ~60 | ~2500L |
| v8.0.1 | 2026-02-08 | RIPER-5 → RIPER-7 缺陷分析 | — | — |
| v8.1 | 2026-02-09 | Superpowers 集成 + RIPER-7 实现 | 76 | 2090L |
| v8.2 | 2026-02-09 | 架构审计 + 67% 冗余删除 | 43 | 935L |
| v8.2.1 | 2026-02-09 | 13 项 bug/优化修复 | 38+32 | 1417L / 1175L |

---

## v7.x → v8.0 (2026-02-08)

**触发**: Claude Opus 4.6 + GPT-5.3-Codex 发布

### 模型变化分析

| 能力 | v7.x 时代 | v8.0 适配 |
|:---|:---|:---|
| 上下文窗口 | 200K | 1M (Opus 4.6 beta) |
| 输出 tokens | 64K | 128K |
| Thinking | `type: "enabled"` | `type: "adaptive"` (4 级 effort) |
| Agent Teams | 无 | Claude Code 研究预览 |
| Compaction | 无 | 服务端自动压缩 |
| Codex | GPT-5.2-Codex | GPT-5.3-Codex (SWE-Bench Pro SOTA) |

### 架构变化

```
v7.x: 单文件 CLAUDE.md (~3000行)
  ↓
v8.0: 模块化目录
  .claude/
  ├── CLAUDE.md (入口)
  ├── agents/ (7个角色文件)
  ├── skills/ (16个)
  ├── workflows/ (P.A.C.E. v2.0)
  ├── commands/ (16个 vibe-*)
  ├── references/
  └── install scripts
```

### 关键决策

- 移除 `sequential-thinking` MCP (两个平台均移除)
- `.ai_state` 从单文件拆分为 plan/todo/doing/done 四文件
- 所有自定义命令统一 `vibe-` 前缀
- MCP 精简为 3 个核心: augment-context-engine, cunzhi, mcp-deepwiki
- P.A.C.E. v2.0: 4 条路径 (A/B/C/D), Path D 使用 Agent Teams

---

## v8.0 → v8.0.1 缺陷分析 (2026-02-08)

**触发**: 用户质疑 "当前流程是否匹配我期望的 7 步?"

### 发现的 3 个结构性缺陷

| # | 缺陷 | 影响 |
|:---|:---|:---|
| 1 | **R1 和 I 职责错位** — R1 在"看代码"不是"听需求", I 直接出方案没有备选讨论 | 跳过需求理解和方案发散 |
| 2 | **E 和 R2 之间缺一步** — 没有"自我审查" (执行者检查交付完整性) | 交付质量无保障 |
| 3 | **R2 太弱** — 只是 todo vs done 打勾, 没有质量审查 | 代码质量无审查 |

### 修正方案

```
旧 RIPER-5:  R1(看代码) → I(出方案) → P(列TODO) → E(写代码) → R2(打勾)

新 RIPER-7:  R(需求) → D(讨论) → P(计划) → C(确认) → E(执行) → V(验证) → Rev(审查)
```

新增 **D(Discuss)** — 2-3 备选方案 + trade-off + 推荐
新增 **C(Confirm)** — 逐项确认目标/细节/验收标准 (寸止)
新增 **V(Verify)** — 自检交付完整性 (测试+覆盖+残留检查)
重定义 **Rev** — Linus 六维质量审查 + 经验提取

---

## v8.0.1 → v8.1 (2026-02-09)

**触发**: Superpowers 官方插件发现 + RIPER-7 实现

### 新增集成

- **Superpowers Plugin**: 7 个 skill (brainstorming, writing-plans, tdd, subagent-driven-dev, verification-before-completion, requesting-code-review, debugging)
- **9 个官方 Plugins**: code-review, commit-commands, feature-dev, frontend-design, hookify, plugin-dev, pr-review-toolkit, security-guidance, superpowers

### v8.1 规模

| 指标 | 值 |
|:---|:---|
| 总文件 | 76 |
| 总行数 | ~2800 |
| AI 上下文 (max) | 2090L |
| Skills | 16 |
| Commands | 16 |
| Agents | 7 角色文件 |
| RIPER-7 定义次数 | **18 次** (严重冗余) |
| 包大小 | 32K |

### 问题积累

v8.1 功能完整但严重臃肿:
- RIPER-7 在 18 个文件中重复描述
- 7 个 agent 文件含零执行价值 (纯角色描述)
- orchestrator.yaml 写给人看但 AI 永远不读
- 16 个 skill 中多个重叠 (knowledge-base ≈ continuous-learning ≈ experience)
- 16 个 command 中多个低价值 (vibe-todos ≈ vibe-status)

---

## v8.1 → v8.2 (2026-02-09)

**触发**: 40% 冗余审计 → 用户确认 8 点重构方案

### 核心架构原则确立

```
command → workflow (编排) → skill (执行)
```

- **Workflow**: 调度表 — "什么阶段、什么复杂度、用什么技能"
- **Skill**: 执行体 — "怎么做"
- **Command**: 用户接口 — 触发 workflow

### 删除项

| 删除 | 原因 | 数量 |
|:---|:---|:---|
| agents/ 目录 | 角色概念内联到 RIPER 阶段 | -7 文件 |
| orchestrator.yaml | 移到 docs/ (人看, 非 AI 上下文) | -1 文件 |
| 重复 workflow | 与 skill 合并 | -N 文件 |
| references/ | 合并到 CLAUDE.md 或 docs/ | -N 文件 |
| install scripts | 用户要求手动放置 | -3 文件 |
| 低价值 commands | 合并 (vibe-todos→status, vibe-exp→knowledge 等) | -7 command |

### 合并项

| 合并 | 从 | 到 |
|:---|:---|:---|
| 知识管理 | knowledge-base + experience + continuous-learning | skills/knowledge |
| 归档 | smart-archive + iterative-retrieval | skills/archive |
| 规则 | 7 个规则文件 | 1 个 rules.md |

### v8.2 指标

| 指标 | v8.1 | v8.2 | 变化 |
|:---|:---|:---|:---|
| 总文件 | 76 | 43 | **-43%** |
| 总行数 | 2800 | 1713 | **-39%** |
| AI 上下文 (max) | 2090 | 935 | **-55%** |
| RIPER-7 定义 | 18 次 | 3 次 | **-83%** |
| Skills | 16 | 10 | -38% |
| Commands | 16 | 9 | -44% |
| 包大小 | 32K | 17K | -47% |
| Codex 自包含 | 否 | 是 (271L) | ✓ |

### v8.2 遗留问题 (用户审查发现 5 项)

1. Skills 缺触发条件 — workflow 没说"何时加载哪个 skill"
2. 9 个官方 plugin 没映射到 workflow/skill
3. Codex 无 plugin 系统, 替代方案不清
4. Skills 不写 plugin/MCP 具体用法
5. scripts 在项目目录, 应在系统目录

---

## v8.2 → v8.2.1 (2026-02-09)

**触发**: Claude Code 视角模拟审计发现 4 严重 + 5 中等 + 4 优化问题

### 🔴 严重修复 (4)

| ID | 问题 | 修复 |
|:---|:---|:---|
| BUG-1 | verification 假设 plan.md 存在, 但 Path A 没有 P 阶段 | 验证清单按 Path 分级 (A=基础/B=标准/C=严格) |
| BUG-2 | R/D 阶段无 VibeCoding skill (brainstorm-bridge 被删) | 恢复精简 brainstorm skill (52L, 只做增强) |
| BUG-3 | riper-7.md E 阶段漏了 worktrees (pace 写了 riper 没写) | E 阶段添加 "Path C/D: 加载 skill/worktrees" |
| BUG-4 | settings.json 权限 `"node scripts/*"` 路径过期 | 改为 `"node .claude/scripts/*"` |

### 🟡 中等修复 (5)

| ID | 问题 | 修复 |
|:---|:---|:---|
| WARN-1 | 官方 plugin 调用方式不明确 | 全部 skill + workflow 添加"调用方式"列 |
| WARN-2 | archive skill 在 workflow 零引用 | Rev 阶段添加 ">500K 加载 archive" |
| WARN-3 | session.md 模板零引用 | CLAUDE.md 描述 + riper-7 启动检查 + vibe-resume 使用 |
| WARN-4 | Agent Teams teammate 不知道项目约定 | agent-teams skill 添加 "Lead 分配模板" |
| WARN-5 | Path A 加载 470 行配置改一行 CSS | CLAUDE.md 内联 Path A 快速通道 (不加载 workflow) |

### 🔵 优化 (4)

| ID | 问题 | 修复 |
|:---|:---|:---|
| OPT-1 | Superpowers 降级策略只有 cunzhi 有 | 全部 7 个 SP 引用添加降级方案 |
| OPT-2 | vibe-init 没声明用什么工具 | 添加工具标注 (sou, deepwiki, grep, find) |
| OPT-3 | commit 策略不清 | tdd skill 按 Path 定义: A=改完/B=每TASK/C=每GREEN |
| OPT-4 | 中断恢复无精度 | session.md 追踪 riper_phase + current_task |

### v8.2.1 最终指标

| 指标 | Claude Code | Codex CLI |
|:---|:---|:---|
| 入口文件 | CLAUDE.md (123L) | AGENTS.md (128L) |
| Workflows | 2 (365L) | 2 (343L) |
| Skills | 11 (607L) | 10 (431L) |
| Commands | 9 (292L) | 9 (246L) |
| 总文件 | 38 | 32 |
| AI 上下文 (max) | 1417L | 1175L |
| Path A 上下文 | **123L** | **128L** |
| Path B 上下文 | **~414L** | **~403L** |
| 官方 Plugins | 9 个原生 | 0 (SP + 手动替代) |
| Path D Agent Teams | ✓ | → Path C 降级 |
| chrome-devtools | ✗ | ✓ (Codex 专属) |
| 工具调用方式文档 | 11/11 skill | 10/10 skill |
| SP 降级策略 | 7/7 | 7/7 |
| 阶段恢复 | session.md 追踪 | session.md 追踪 |
| 包大小 | 17K | 13K |

---

## 架构演进总结

```
v7.x   单文件 prompt (~3000L)
         │
v8.0   模块化拆分 (agents + skills + workflows)
         │ 发现: RIPER-5 缺 3 步
         │
v8.0.1 RIPER-5 → RIPER-7 设计
         │
v8.1   完整实现 (76 文件, Superpowers 集成)
         │ 发现: 40% 冗余, RIPER 定义 18 次
         │
v8.2   冗余审计删除 (76→43, -55% 上下文)
         │ 发现: 声明了没用, 用了没声明, 13 个 bug
         │
v8.2.1 13 项修复 (Claude Code 38 files + Codex CLI 32 files)
         │
         ├── workflow = 调度表 (什么阶段用什么工具)
         ├── skill = 执行体 (怎么用工具)
         ├── Path A = 极简内联 (123L 改一行 CSS)
         └── Path C = 九步展开 + 每步寸止 (完整工程)
```

---

## 经验教训

1. **只说 AI 不知道的** — 从 3000L 降到 123L (Path A), AI 已有的能力不需要解释
2. **先跑一遍再优化** — v8.1 先做完再审计, 比边做边优化效率高
3. **声明必须绑定使用** — 声明了 9 个 plugin 但没写用法 = 白装
4. **分级不是可选** — Path A/B/C 的验证清单、TDD 强度、commit 策略必须不同
5. **降级是强制项** — 外部依赖 (SP, MCP) 必须有降级方案, 否则 workflow 断裂
6. **Codex ≠ 删减版** — Codex 有自己的优势 (chrome-devtools), 不是 Claude Code 的阉割版
# VibeCoding Kernel v8.9 — 架构演进计划

> "The hallmark of good taste in code is simplicity in complexity." — Linus Torvalds

**基线**: v8.6.5 (2026-02-20)
**目标**: v8.9 (2026-02-23)
**核心定位**: 让粗通 vibe 开发的人也能工程化地用 AI 写代码

---

## 一、v8.6.5 → v8.9 变更总览

### 1.1 平台新特性接入

#### Claude Code (v2.1.49+)

| 新特性                                | VibeCoding 适配                            | 优先级 |
| :------------------------------------ | :----------------------------------------- | :----- |
| `--worktree (-w)` 隔离                | agent 定义加 `isolation: worktree`         | P0     |
| `background: true` agent              | explorer/security-auditor 改为后台运行     | P0     |
| `WorktreeCreate/WorktreeRemove` hooks | 新增 hook: worktree 创建时初始化 .ai_state | P1     |
| `ConfigChange` hook                   | 监控配置变更自动重载                       | P2     |
| `claude agents` CLI                   | vibe-status 增强: 列出活跃 agents          | P1     |
| Plugins ship settings.json            | VibeCoding 作为 plugin 分发 (future)       | P2     |
| Sonnet 4.6 1M context (GA)            | 移除 DISABLE_1M env, 子代理默认 sonnet 4.6 | P0     |
| Sonnet 4.5 1M 移除                    | 清理所有 sonnet 4.5 引用                   | P0     |

#### Codex CLI (v2026.02+)

| 新特性                       | VibeCoding 适配                 | 优先级 |
| :--------------------------- | :------------------------------ | :----- |
| GPT-5.3-Codex-Spark          | config.toml 支持 spark 模型选择 | P1     |
| 并发 shell 命令              | AGENTS.md 标注并发执行能力      | P1     |
| JS REPL (实验)               | 跟踪但不接入 (unstable)         | P3     |
| Memory slash commands        | 替代 .knowledge/ 手动管理       | P1     |
| Sandbox read access 配置     | permissions 段更新              | P1     |
| Commit co-author attribution | hooks 配置自动归因              | P2     |

### 1.2 架构优化 (从历史 Review 提炼)

| 问题                             | 来源        | v8.9 修复                                   |
| :------------------------------- | :---------- | :------------------------------------------ |
| Path A 加载全量配置改一行 CSS    | v8.2 审计   | **分级加载**: Path A 只读 CLAUDE.md + rules |
| verification 假设 plan.md 存在   | v8.2 审计   | verification 按 Path 分级, A 不查 plan.md   |
| Skills 间无数据流                | v8.6 审计   | 管道协议: 上游输出 = 下游输入               |
| 对 vibe 新手不友好               | 核心宗旨    | **新增 Quick Start 引导流**                 |
| delivery-gate 运算符优先级       | v8.3.5 审计 | 已修, v8.9 验证                             |
| .knowledge/ 模板缺失             | v8.3.5 审计 | 补全模板                                    |
| context-loader 不恢复 V/Rev 断点 | v8.3.5 审计 | 智能断点恢复                                |

### 1.3 精华提取 & 糟粕清除

#### 取 (从历史版本提炼)

| 精华           | 来源版本    | 说明                                  |
| :------------- | :---------- | :------------------------------------ |
| Token 效率原则 | v5.5        | "只说 AI 不知道的" — 减少冗余描述     |
| 三层分工       | v8.3.5      | SP 方法论 / Plugin 工具 / VK 编排     |
| 管道完整性     | v8.6.1      | brainstorm→context7→plan-first 数据流 |
| 寸止降级链     | v7.6        | cunzhi → mcp-feedback → 对话确认      |
| 工程化看板     | v8.0        | kanban.md TODO→DOING→DONE             |
| worktree 隔离  | CC v2.1.50+ | 多代理并行零冲突                      |

#### 去 (历史累赘清除)

| 糟粕                           | 说明                                                  |
| :----------------------------- | :---------------------------------------------------- |
| 角色详细描述                   | AI 天然会多角色思考, 不需要 6x150 tokens 描述每个角色 |
| 重复铁律                       | "必须" 出现 27 次的问题, 合并为 5 条核心原则          |
| 假 hook stubs                  | 不工作的 bash hooks 全部移除, 只保留可运行的          |
| 过度工程化 Path A              | 改一行 CSS 不需要加载 1000 行配置                     |
| continuous-learning v1/v2 重复 | 合并为 .knowledge/ 一套                               |
| 13 agents 肥胖 (ECC)           | 保留 5 个核心, 其余 SP/Plugin 覆盖                    |

---

## 二、v8.9 目录结构

### Claude Code

```
.claude/
├── CLAUDE.md                              # 入口 (~100L) — AI 读这个
├── settings.json                          # CC 配置 + 权限 + 插件注册
├── workflows/
│   ├── pace.md                            # P.A.C.E. 复杂度路由 + 分级加载
│   └── riper-7.md                         # RIPER-7 阶段编排 + 统一工具调度表
├── skills/
│   ├── brainstorm/SKILL.md                # R₀b: 苏格拉底需求精炼
│   ├── cunzhi/SKILL.md                    # 寸止检查点协议
│   ├── tdd/SKILL.md                       # TDD 分级策略
│   ├── verification/SKILL.md              # 分级验证清单
│   ├── code-quality/SKILL.md              # 代码审查编排
│   ├── knowledge/SKILL.md                 # .knowledge/ 经验管理
│   ├── agent-teams/SKILL.md               # 并行分工 + worktree 隔离
│   ├── context7/SKILL.md                  # 库文档按需拉取
│   ├── plan-first/SKILL.md                # 强制先规划后执行
│   ├── smart-archive/SKILL.md             # 智能压缩归档
│   ├── e2e-testing/SKILL.md               # Playwright E2E
│   ├── security-review/SKILL.md           # 安全审查
│   └── quickstart/SKILL.md                # 🆕 新手引导流
├── commands/
│   ├── vibe-dev.md                        # 智能开发入口
│   ├── vibe-init.md                       # 项目初始化
│   ├── vibe-resume.md                     # 中断恢复
│   ├── vibe-status.md                     # 状态查看 + agent 列表
│   └── vibe-brainstorm.md                 # 显式触发头脑风暴
├── agents/
│   ├── builder.md                         # 构建者 (isolation: worktree)
│   ├── validator.md                       # 验证者 (isolation: worktree)
│   ├── explorer.md                        # 探索者 (background: true)
│   ├── e2e-runner.md                      # E2E 测试 (isolation: worktree)
│   └── security-auditor.md                # 安全审计 (background: true)
├── rules/rules.md                         # 项目硬规则 (从 skills 提取)
├── hooks/
│   ├── context-loader.cjs                 # SessionStart: 加载上下文+断点恢复
│   ├── delivery-gate.cjs                  # Stop: 质量门控
│   ├── worktree-init.cjs                  # 🆕 WorktreeCreate: 初始化隔离环境
│   └── ts-check.cjs                       # PostToolUse: async tsc
├── scripts/
│   └── vibe-lint.cjs                      # 配置健康检查
└── templates/
    ├── ai-state/                          # .ai_state 模板
    │   ├── session.md / doing.md / design.md
    │   ├── plan.md / verified.md / review.md
    │   └── conventions.md
    └── knowledge/                         # 🆕 .knowledge 模板
        ├── patterns.md                    # 成功模式
        ├── pitfalls.md                    # 已知陷阱
        ├── decisions.md                   # ADR 记录
        └── tools.md                       # 工具使用经验
```

### Codex CLI

```
.codex/
├── config.toml                            # Codex 配置 (GPT-5.3 + Spark)
├── workflows/
│   ├── pace.md                            # 自包含 P.A.C.E. (Codex 原生)
│   └── riper-7.md                         # 自包含 RIPER-7 (Codex 原生)
├── skills/                                # 与 CC 共享目录结构
│   └── (13 个 skills, 内容 Codex 适配)
├── hooks/
│   ├── context-loader.cjs
│   └── delivery-gate.cjs
└── templates/                             # 共享模板
    ├── ai-state/
    └── knowledge/
AGENTS.md                                  # Codex 入口 (~80L) — 完全自包含
```

---

## 三、核心重构: 新手引导体系

### 3.1 设计哲学

```
粗通 vibe 的用户          工程化 AI 开发
      │                        │
      │  VibeCoding v8.9       │
      │  ══════════════        │
      │                        │
      ▼                        ▼
   "做个登录功能"     →    P.A.C.E. 自动路由
                      →    RIPER-7 自动编排
                      →    Skills 自动加载
                      →    MCP 自动调用
                      →    质量门控自动拦截
                      →    看板自动更新
```

**关键原则**: 用户只需要说**做什么**, VibeCoding 负责**怎么做**。

### 3.2 quickstart skill (新增)

```
触发: 首次使用 / 用户说"不知道怎么开始" / vibe-init 检测无 .ai_state
流程:
  1. 检测项目类型 (前端/后端/全栈/脚本)
  2. 推荐 Path (A/B/C) + 解释为什么
  3. 展示本次任务的执行计划预览
  4. cunzhi 确认后开始
```

### 3.3 Workflow 引导增强

每个 RIPER 阶段入口增加:

```
💡 当前阶段: R (研究)
📋 本阶段做什么: 理解需求、调研技术方案
🔧 自动使用工具: augment-context → deepwiki → cunzhi
⏭️ 下一阶段: D (设计)
⏱️ 预计: Path B ~15 分钟
```

---

## 四、数据流管道 (完整版)

```
用户输入
  │
  ▼
P.A.C.E. 路由器
  │ 关键词/描述长度/需求数 → Path A/B/C/D
  │
  ├─ Path A (≤30 min) ─────────────────────┐
  │   加载: CLAUDE.md + rules.md            │
  │   跳过: brainstorm, plan-first          │
  │   直达: E → cunzhi → Done              │
  │                                         │
  ├─ Path B (6-12h) ───────────────────────┐│
  │   R₀b: brainstorm                     ││
  │   │ augment-context 扫描现有代码        ││
  │   │ deepwiki 查候选库文档               ││
  │   │ 输出 → .ai_state/design.md         ││
  │   ▼                                    ││
  │   R: 研究                              ││
  │   │ context7 深入调研                   ││
  │   │ 对照 design.md 验证                ││
  │   ▼                                    ││
  │   D: 设计                              ││
  │   │ context7 查 API 细节                ││
  │   │ 更新 design.md                     ││
  │   │ cunzhi [DESIGN_READY]              ││
  │   ▼                                    ││
  │   P: 规划                              ││
  │   │ plan-first: 读 design.md           ││
  │   │ 输出 → .ai_state/plan.md           ││
  │   │ cunzhi [PLAN_CONFIRMED]            ││
  │   ▼                                    ││
  │   E: 执行                              ││
  │   │ TDD 分级 / code-quality            ││
  │   │ agent-teams (Path B+)              ││
  │   ▼                                    ││
  │   T: 测试                              ││
  │   │ verification 分级清单               ││
  │   │ e2e-testing (如适用)               ││
  │   ▼                                    ││
  │   V: 验证                              ││
  │   │ delivery-gate hook 自动门控         ││
  │   │ cunzhi [DELIVERY_CONFIRMED]        ││
  │   ▼                                    ││
  │   Done → smart-archive                 ││
  │                                         │
  └─ Path C (1-3w) ── 同 Path B + ─────────┘
      额外: worktree 隔离
      额外: security-review
      额外: 多代理并行
```

---

## 五、统计对比

| 指标          | v8.6.5 | v8.9     | 变化                                                |
| :------------ | :----- | :------- | :-------------------------------------------------- |
| CC 文件       | 45     | 48       | +3 (quickstart, worktree-init, knowledge templates) |
| CC 总行数     | ~1016  | ~1100    | +8% (有效增量: 新手引导+平台特性)                   |
| Codex 文件    | 30     | 32       | +2 (quickstart, knowledge templates)                |
| Skills        | 13     | 14       | +quickstart                                         |
| Agents        | 5      | 5        | 不变 (升级 frontmatter)                             |
| Hook Events   | 9      | 11       | +WorktreeCreate, +ConfigChange                      |
| 新手可用性    | 低     | 高       | quickstart + 阶段引导                               |
| Path A 上下文 | ~470L  | ~130L    | -72% (分级加载)                                     |
| Agent 隔离    | 无     | worktree | 零冲突并行                                          |

---

## 六、实施顺序

```
Phase 1: 平台特性接入 (CC + Codex)
  ├─ agent frontmatter: isolation/background
  ├─ 新 hooks: WorktreeCreate, ConfigChange
  ├─ 模型更新: Sonnet 4.6 / GPT-5.3-Spark
  └─ settings.json 权限更新

Phase 2: 核心优化
  ├─ P.A.C.E. 分级加载
  ├─ verification 按 Path 分级
  ├─ context-loader 断点恢复
  └─ .knowledge/ 模板补全

Phase 3: 新手引导
  ├─ quickstart skill
  ├─ RIPER 阶段引导增强
  ├─ vibe-init 完善
  └─ README 快速上手指南

Phase 4: 审计 & 打包
  ├─ 跨平台污染检查
  ├─ vibe-lint 验证
  ├─ 文件树/行数统计
  └─ 双平台独立打包
```

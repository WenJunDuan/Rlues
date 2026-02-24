# VibeCoding Kernel v8.9 — 综合更新日志

> 基于 v8.6.5 迭代 · 2025-02-23 构建 · 含 self-review 修复

---

## 一、版本总览

| 指标                        | v8.6.5 | v8.9 (构建后) | v8.9 (review 后) | Δ                              |
| :-------------------------- | :----- | :------------ | :--------------- | :----------------------------- |
| CC 文件                     | 45     | 44            | 43               | -2 (合并冗余 + 删空壳)         |
| CC 行数                     | ~1016  | ~1294         | ~1299            | +28% (有效增量)                |
| Codex 文件                  | 30     | 30            | 30               | 持平                           |
| Codex 行数                  | ~450   | ~523          | ~539             | +20%                           |
| Skills                      | 13     | 14            | 14               | +quickstart                    |
| Agents                      | 5      | 5             | 5                | frontmatter 升级               |
| Hook 文件                   | 3      | 4→3           | 3                | +worktree-init, -ts-check 空壳 |
| Hook Events (settings.json) | 4      | 5             | 5                | +WorktreeCreate                |
| Path A 上下文               | ~470L  | ~130L         | ~130L            | -72%                           |
| 跨平台污染                  | 0      | 0             | 0                | 保持清洁                       |

---

## 二、Self-Review 发现与修复

### Bugs (6 个, 全修)

| #   | 位置                       | 问题                                                     | 修复                           |
| :-- | :------------------------- | :------------------------------------------------------- | :----------------------------- |
| B1  | pace.md (双平台)           | Path A RIPER 缺 T(测试) 阶段, 与 verification skill 矛盾 | `R(轻)→E→T(轻)→V(cunzhi)→Done` |
| B2  | cunzhi/SKILL.md (双平台)   | Path B 检查点规则漏 [DESIGN_DIRECTION]                   | 补全为 4 个检查点              |
| B3  | agents/validator.md        | frontmatter 含无效字段 `Task: [validator]`               | 改为 `description:`            |
| B4  | riper-7.md (双平台)        | E 阶段步骤"逐个执行 plan.md 任务", Path A 无 plan.md     | 加 Path A 分支: "直接开始开发" |
| B5  | delivery-gate.cjs (双平台) | var/let 混用 (isStrictPath, hasEslintConfig 用 var)      | 统一改 const                   |
| B6  | hooks/ts-check.cjs         | 空壳文件 (3 行注释), 实际 hook 内联在 settings.json      | 删除文件                       |

### Issues (6 个, 全修)

| #   | 位置                        | 问题                                                           | 修复                                            |
| :-- | :-------------------------- | :------------------------------------------------------------- | :---------------------------------------------- |
| I1  | Codex pace.md               | 路由信号表只有 3 行, CC 有 5 行, 判定精度下降                  | 补全"描述长度"和"需求数"                        |
| I2  | settings.json               | `CLAUDE_CODE_ENABLE_AGENT_TEAMS` env 存疑, v2.1.50+ 已默认启用 | 删除                                            |
| I3  | smart-archive (双平台)      | 唯一没有降级说明的 skill                                       | 补上降级策略                                    |
| I4  | Codex riper-7.md            | V 阶段只说"沉淀经验", 未指明加载哪个 skill                     | 补 `skills/knowledge` 和 `skills/smart-archive` |
| I5  | context-loader.cjs (双平台) | design.md 存在但 session.md 缺失时, 断点恢复有盲区             | 加异常中断提示                                  |
| I6  | CLAUDE.md + AGENTS.md       | token 估算偏乐观 (Path B 写 600 实际约 900)                    | 加"约行数"列, 重新估算                          |

---

## 三、新增特性

### 3.1 quickstart — 新手引导 skill (NEW)

**解决**: v8.6.5 对 vibe 新手完全不友好, 不知道怎么开始。

**触发**:

- `vibe-init` 检测无 .ai_state/
- 用户说"不知道怎么开始"/"help"
- 首次在项目中使用

**流程**: 检测项目类型 → 引导描述需求 (给 3 个示例) → P.A.C.E. 自动路由 → cunzhi 确认

**设计原则**: 不暴露内部术语 (RIPER/P.A.C.E.), 用户只说"做什么"。

### 3.2 worktree-init hook (NEW)

**解决**: Agent Teams 在 worktree 中启动时没有 .ai_state/, 子代理无法记录进度。

**机制**: WorktreeCreate 事件 → 自动在 worktree 中创建最小 .ai_state/doing.md。

### 3.3 .knowledge/ 模板 (NEW)

**解决**: v8.6.5 的 .knowledge/ 模板缺失, vibe-init 无法初始化完整结构。

**新增 4 个模板**: patterns.md / pitfalls.md / decisions.md / tools.md
每个含格式示例, 降低使用门槛。

### 3.4 RIPER 阶段引导 (NEW)

**解决**: 用户 (尤其新手) 不知道每个阶段在做什么。

**每个阶段入口显示**:

```
💡 本阶段做什么: 理解需求, 探索方案, 不写代码
🔧 自动使用: augment-context → deepwiki → cunzhi
⏭️ 下一阶段: R (研究)
```

---

## 四、核心优化

### 4.1 Path A 分级加载 (-72% 上下文)

| 对比        | v8.6.5                                      | v8.9                         |
| :---------- | :------------------------------------------ | :--------------------------- |
| Path A 加载 | 全量 CLAUDE.md + workflows + skills (~470L) | CLAUDE.md + rules.md (~130L) |
| 效果        | 改一行 CSS 等 30 秒                         | 即时响应                     |

### 4.2 verification 按 Path 分级

- Path A: 功能验证 + lint (不检查 plan.md, 因为没有 P 阶段)
- Path B: + 单测 + 类型检查 + plan.md 全 DONE
- Path C+: + E2E + 安全 + 性能

### 4.3 context-loader 智能断点恢复

检测策略 (逆序, 越晚的阶段优先):

1. review.md 存在 → V(验收) 阶段中断
2. verified.md 存在 → T(测试) 阶段中断
3. doing.md 存在 → E(执行) 阶段中断
4. design.md 存在但 session.md 缺失 → 异常中断提示

### 4.4 Agent frontmatter 升级

| Agent            | 旧配置                     | v8.9                                                     |
| :--------------- | :------------------------- | :------------------------------------------------------- |
| builder          | 无 isolation               | `isolation: worktree`                                    |
| validator        | `Task: [validator]` (无效) | `description: 测试验证`                                  |
| explorer         | 无 background              | `background: true` + `permissionMode: bypassPermissions` |
| e2e-runner       | 无 isolation               | `isolation: worktree`                                    |
| security-auditor | 无 background              | `background: true`                                       |

### 4.5 delivery-gate 修复

- v8.6.5 bug: 运算符优先级导致 ESLint 检查条件错误
- v8.9: `const` 统一声明, 逻辑清晰, 双平台一致

---

## 五、组件全景

### 5.1 MCP 工具

| MCP Server             | 平台  | 用途                        | 调用阶段  | 降级方案            |
| :--------------------- | :---- | :-------------------------- | :-------- | :------------------ |
| augment-context-engine | 双    | 语义代码搜索, 理解项目结构  | R₀b/R/D/E | grep + find         |
| cunzhi (寸止)          | 双    | 人工确认检查点, AI 暂停等待 | 全阶段    | 对话确认 (不可跳过) |
| mcp-deepwiki           | 双    | 开源库文档查询              | R₀b/R/D   | web search          |
| chrome-devtools        | Codex | 浏览器调试                  | T         | 手动测试            |
| desktop-commander      | Codex | 桌面操作                    | E         | shell 命令          |

**降级通则**: MCP 不可用 → CLI 替代 → AI 内置能力。流程不中断。

### 5.2 Skills (14 个)

| Skill               | 阶段        | Path | 核心职责                                                 |
| :------------------ | :---------- | :--- | :------------------------------------------------------- |
| **quickstart** 🆕   | 入口        | ALL  | 新手引导: 检测项目→引导描述→自动路由                     |
| **brainstorm**      | R₀b         | B+   | 苏格拉底式需求精炼, 2-3 方案对比, 输出 design.md         |
| **context7**        | R₀b/R/D/E   | B+   | 库文档按需拉取 (deepwiki → ctx7 CLI → web search)        |
| **cunzhi**          | 全阶段      | ALL  | 检查点协议: 6 个确认点, 按 Path 分级                     |
| **plan-first**      | P           | B+   | 强制规划: 读 design.md → 生成 plan.md → cunzhi 确认      |
| **tdd**             | E           | ALL  | TDD 分级: A=手动 / B=关键路径60% / C+=全覆盖80%          |
| **code-quality**    | T/V         | B+   | 代码审查编排: 联动 Plugins, 补充 VibeCoding 特有规则     |
| **verification**    | T           | ALL  | 分级验证清单: A=功能+lint / B=+单测+类型 / C+=+E2E+安全  |
| **e2e-testing**     | T           | C+   | Playwright E2E: 提取用户流, 3 轮重试, 截图保存           |
| **security-review** | T           | C+   | 安全 6 项: 密钥/SQL/XSS/认证/日志/依赖漏洞               |
| **agent-teams**     | E           | C+   | CC: worktree 隔离并行 / Codex: /collab + 并发 shell      |
| **knowledge**       | V(写)/R(读) | B+   | 经验持久化: patterns/pitfalls/decisions/tools            |
| **smart-archive**   | V           | B+   | 智能归档: .ai_state/ → archive/{date}/, 保留 conventions |

### 5.3 Plugins (8 个, CC 专属)

| Plugin                | 来源                    | 触发阶段  | VibeCoding 如何编排                                         |
| :-------------------- | :---------------------- | :-------- | :---------------------------------------------------------- |
| **superpowers**       | superpowers-marketplace | R₀b/R/D/T | 核心方法论引擎: brainstorming/research/writing-plans/review |
| **code-review**       | 官方                    | T         | `code-quality` skill 在 T 阶段自动触发                      |
| **commit-commands**   | 官方                    | V         | `riper-7` V 阶段编排: A=单次/B=squash/C+=按功能分           |
| **feature-dev**       | 官方                    | E         | E 阶段自动: 功能开发方法论                                  |
| **frontend-design**   | 官方                    | E         | E 阶段: 前端项目自动触发                                    |
| **hookify**           | 官方                    | E         | E 阶段: hook 创建辅助                                       |
| **pr-review-toolkit** | 官方                    | V         | `code-quality` skill 在 V 阶段 PR 时触发                    |
| **security-guidance** | 官方                    | T         | `security-review` skill 在 Path C+ T 阶段触发               |

**编排原则**: VibeCoding 编排 WHEN/WHERE, Plugins 提供 HOW。用户不需要知道 Superpowers 存在。

### 5.4 Hooks

| Hook 文件          | 事件                     | 功能                                         | 平台 |
| :----------------- | :----------------------- | :------------------------------------------- | :--- |
| context-loader.cjs | SessionStart             | 加载 conventions + .knowledge + 智能断点恢复 | 双   |
| delivery-gate.cjs  | Stop                     | 按 Path 分级拦截: plan 完成度/test/lint/tsc  | 双   |
| worktree-init.cjs  | WorktreeCreate           | agent worktree 自动初始化 .ai_state          | CC   |
| _(内联)_ ts-check  | PostToolUse (Write/Edit) | .ts/.tsx 文件编辑后自动 tsc --noEmit         | CC   |
| _(内联)_ md-guard  | PreToolUse (Write)       | 拦截非白名单目录的 .md 随意创建              | CC   |

### 5.5 Commands (5 个, CC 专属)

| 命令                      | 用途                           | 典型场景         |
| :------------------------ | :----------------------------- | :--------------- |
| `/vibe-dev "描述"`        | 智能开发入口, 自动路由完整流程 | 最常用, 新手首选 |
| `/vibe-init`              | 初始化项目 VibeCoding 结构     | 新项目首次使用   |
| `/vibe-resume`            | 中断恢复, 从上次中断点继续     | 超时/崩溃后恢复  |
| `/vibe-status`            | 查看当前任务状态和进度看板     | 随时查进度       |
| `/vibe-brainstorm "话题"` | 只做头脑风暴, 不进入开发       | 还没想好怎么做   |

### 5.6 Agent Teams (5 个, CC Path C+)

| Agent            | 模型       | 隔离              | 角色                   | 触发           |
| :--------------- | :--------- | :---------------- | :--------------------- | :------------- |
| builder          | sonnet-4-6 | worktree          | 按 plan.md 实现代码    | P 阶段分配     |
| validator        | sonnet-4-6 | worktree          | 运行测试/类型检查/lint | builder 完成后 |
| explorer         | sonnet-4-6 | background (只读) | 扫描依赖/导入/集成点   | 持续运行       |
| e2e-runner       | sonnet-4-6 | worktree          | Playwright E2E 测试    | T 阶段         |
| security-auditor | sonnet-4-6 | background        | 安全扫描 6 项检查      | T 阶段         |

---

## 六、精华提取 & 糟粕清除

### 取 (精华, 来源版本)

| 精华                                        | 来源        | v8.9 体现                                   |
| :------------------------------------------ | :---------- | :------------------------------------------ |
| Token 效率: "只说 AI 不知道的"              | v5.5        | 5 条铁律, 无冗余角色描述                    |
| 三层分工: SP 方法论 / Plugin 工具 / VK 编排 | v8.3.5      | CLAUDE.md 三层分工表                        |
| 管道完整性: brainstorm→context7→plan-first  | v8.6.1      | riper-7.md 统一调度表 + plan-first 管道声明 |
| 寸止降级链                                  | v7.6        | cunzhi skill 降级规则                       |
| 工程化看板                                  | v8.0        | doing.md TODO→DOING→DONE                    |
| worktree 隔离                               | CC v2.1.50+ | 5 个 agent frontmatter                      |
| ECC 精华 agents                             | v8.6        | e2e-runner + security-auditor 保留          |

### 去 (糟粕)

| 糟粕                           | 原版      | v8.9 处理                 |
| :----------------------------- | :-------- | :------------------------ |
| 6×150 tokens 角色详细描述      | v5.1-v7.x | 三层分工表 (10 行)        |
| "必须" 出现 27 次              | v7.x      | 5 条铁律 + rules.md 13 条 |
| 假 hook stubs (bash hooks)     | v7.6      | 全部可执行 .cjs           |
| ECC 13 agents 肥胖             | v8.6      | 5 个核心 agents           |
| continuous-learning v1/v2 重复 | v7.9      | knowledge skill 统一      |
| 过度工程化 Path A              | v8.0      | 分级加载 -72%             |
| ts-check.cjs 空壳              | v8.9 初版 | review 时删除             |
| ENABLE_AGENT_TEAMS env 残留    | v8.9 初版 | review 时删除             |

---

## 七、平台对比

| 维度       | Claude Code                       | Codex CLI                                    |
| :--------- | :-------------------------------- | :------------------------------------------- |
| 入口文件   | .claude/CLAUDE.md                 | AGENTS.md                                    |
| 配置       | settings.json (权限/hook/plugin)  | config.toml                                  |
| 子代理     | Agent Teams (worktree/background) | /collab + 并发 shell                         |
| 模型       | Sonnet 4.6 (子代理)               | GPT-5.3-Codex / Spark                        |
| Hooks      | 5 events (3 文件 + 2 内联)        | 2 文件                                       |
| Plugins    | 8 个                              | 无 (MCP 替代)                                |
| Commands   | 5 个 /vibe-\*                     | 无 (自然语言触发)                            |
| MCP        | 3 个                              | 5 个 (多 chrome-devtools, desktop-commander) |
| 文件       | 43                                | 30                                           |
| 行数       | ~1299                             | ~539                                         |
| 跨平台引用 | 0                                 | 0                                            |

---

## 八、目录结构 (最终)

### Claude Code (.claude/)

```
.claude/
├── CLAUDE.md                    # 入口 (~100L)
├── settings.json                # 配置/权限/hooks/plugins
├── workflows/
│   ├── pace.md                  # P.A.C.E. 路由
│   └── riper-7.md               # RIPER-7 编排
├── skills/                      # 14 个 skills
│   ├── quickstart/SKILL.md      # 🆕 新手引导
│   ├── brainstorm/SKILL.md      # R₀b 需求精炼
│   ├── context7/SKILL.md        # 库文档拉取
│   ├── cunzhi/SKILL.md          # 确认检查点
│   ├── plan-first/SKILL.md      # P 强制规划
│   ├── tdd/SKILL.md             # E TDD 分级
│   ├── code-quality/SKILL.md    # T/V 审查编排
│   ├── verification/SKILL.md    # T 分级验证
│   ├── e2e-testing/SKILL.md     # T E2E 测试
│   ├── security-review/SKILL.md # T 安全审查
│   ├── agent-teams/SKILL.md     # C+ 并行分工
│   ├── knowledge/SKILL.md       # V 经验沉淀
│   └── smart-archive/SKILL.md   # V 智能归档
├── commands/                    # 5 个命令
│   ├── vibe-dev.md
│   ├── vibe-init.md
│   ├── vibe-resume.md
│   ├── vibe-status.md
│   └── vibe-brainstorm.md
├── agents/                      # 5 个子代理
│   ├── builder.md
│   ├── validator.md
│   ├── explorer.md
│   ├── e2e-runner.md
│   └── security-auditor.md
├── rules/rules.md               # 13 条硬规则
├── hooks/                       # 3 个 hook 文件
│   ├── context-loader.cjs       # SessionStart
│   ├── delivery-gate.cjs        # Stop
│   └── worktree-init.cjs        # WorktreeCreate
├── scripts/
│   └── vibe-lint.cjs            # 配置健康检查
└── templates/
    ├── ai-state/                # 7 个模板
    │   ├── session.md
    │   ├── doing.md
    │   ├── design.md
    │   ├── plan.md
    │   ├── verified.md
    │   ├── review.md
    │   └── conventions.md
    └── knowledge/               # 🆕 4 个模板
        ├── patterns.md
        ├── pitfalls.md
        ├── decisions.md
        └── tools.md
```

### Codex CLI

```
AGENTS.md                        # 入口 (~80L, 完全自包含)
.codex/
├── config.toml                  # Codex 配置
├── workflows/
│   ├── pace.md
│   └── riper-7.md
├── skills/                      # 13 个 skills (同名, Codex 适配)
│   └── [同 CC, 无 plugin 引用]
├── hooks/
│   ├── context-loader.cjs
│   └── delivery-gate.cjs
└── templates/
    ├── ai-state/ (7 个)
    └── knowledge/ (4 个)
```

---

## 九、数据流管道 (完整)

```
用户输入
  │
  ├─ 有 .ai_state/session.md? → /vibe-resume (断点恢复)
  │
  ├─ 无 .ai_state/? → quickstart (新手引导)
  │
  └─ 正常 → P.A.C.E. 路由
       │
       ├─ Path A (≤30 min)
       │   加载: CLAUDE.md + rules.md (~130L)
       │   R(轻): augment-context 快速扫描
       │   E: 直接开发, 手动验证
       │   T(轻): 功能验证 + lint
       │   V: cunzhi [DELIVERY_CONFIRMED]
       │   Done
       │
       ├─ Path B (6-12h)
       │   加载: + workflows + 6 skills (~540L)
       │   R₀b: brainstorm → design.md → cunzhi [DESIGN_DIRECTION]
       │   R: context7 深入调研 → 更新 design.md
       │   D: context7 查 API → design.md 终稿 → cunzhi [DESIGN_READY]
       │   P: plan-first → plan.md → cunzhi [PLAN_CONFIRMED]
       │   E: tdd 分级 → doing.md 看板
       │   T: verification + code-review → verified.md
       │   V: delivery-gate → cunzhi [DELIVERY_CONFIRMED] → knowledge → archive
       │   Done
       │
       └─ Path C/D (1-3 周+)
           加载: 全量 (~700L)
           同 Path B + :
           E: agent-teams (builder×N / validator / explorer / e2e-runner / security-auditor)
              worktree 隔离, 并行执行
           T: + e2e-testing (Playwright) + security-review → cunzhi [SECURITY_PASSED]
           V: 按功能分 commit
```

---

_VibeCoding Kernel v8.9 · CC 43 files / Codex 30 files · 零跨平台污染 · 12 个 review 问题全修_

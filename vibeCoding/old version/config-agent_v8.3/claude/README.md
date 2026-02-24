# VibeCoding Kernel v8.3.5 — 交付物说明

## 0. 版本变更: v8.3 spec → v8.3.5 实装

| 维度 | v8.3 (spec) | v8.3.5 (交付) |
|:---|:---|:---|
| MCP (CC) | sou/cunzhi/deepwiki (假设15个) | augment-context-engine / cunzhi / mcp-deepwiki (**3个, 真实**) |
| MCP (Codex) | 同上 | augment-context-engine / chrome-devtools / cunzhi / mcp-deepwiki (**4个**) |
| Skills 自写 | 7 个 | 7 个 + **context7** = 8 个 |
| Skills 社区 | 无评估 | 全网评估, 推荐 2 个 (见下文) |
| Plugins (CC) | 列表 | 全部官方编码插件开机自装 (8 个) |
| Hooks | 2 个 spec | 2 个 **可运行代码** |
| Codex 支持 | spec | **config.toml + AGENTS.md + 同步脚本** |

---

## 1. 社区 Skills 全网评估

### 1.1 评估结果

搜索范围: awesome-claude-skills (travisvn)、VoltAgent/awesome-agent-skills (300+)、SkillsMP marketplace、scriptbyai.com 排行榜、ComposioHQ 列表

| 候选 Skill | Stars | 与 VibeCoding 关系 | 推荐 |
|:---|:---|:---|:---|
| `obra/superpowers` | 45.5k | ✅ 已装 (Layer 1 方法论) | **已集成** |
| `planning-with-files` | 9.7k | ⚠️ 与 .ai_state 部分重叠 | **推荐安装** |
| `context7` | — | ✅ 用户已引入 | **已集成** |
| `ui-ux-pro-max-skill` | 16.9k | 前端 UI 设计, 与 frontend-design plugin 功能重叠 | 按需 |
| `Agent-Skills-for-Context-Engineering` | 7.8k | 多 agent 架构, 与 agent-teams skill 重叠 | 不推荐 |
| `claude-memory-skill` | — | 与 .knowledge/ 重叠 | 不推荐 |
| `playwright-skill` | 1.5k | 浏览器测试, Codex 有 chrome-devtools | 按需 |

### 1.2 推荐: planning-with-files

**理由**: Manus 式持久化规划与 VibeCoding 的 .ai_state 互补而非替代:

```
planning-with-files:
  task_plan.md → 阶段进度追踪 (类似我们的 doing.md)
  findings.md  → 研究发现存储 (类似我们的 session.md)
  progress.md  → 会话日志 (我们没有的)
  + PreToolUse hook: 每次操作前自动读 plan
  + Stop hook: 未完成不让停
  + session-catchup.py: context 满了自动恢复

VibeCoding .ai_state:
  session.md / design.md / plan.md / doing.md /
  verified.md / review.md / conventions.md
  + PACE 路由 (planning-with-files 没有)
  + cunzhi 人工确认 (planning-with-files 没有)
  + Path 分级参数 (planning-with-files 没有)
```

**集成策略**: 不替换 .ai_state, 而是安装 planning-with-files 作为 **context 恢复增强**:
- 利用它的 `session-catchup.py` 解决 context compact 后的状态丢失
- 利用它的 PreToolUse hook 在每次写代码前自动读 plan
- VibeCoding 的 PACE/RIPER-7/cunzhi 保持不变

安装:
```bash
# Claude Code
claude plugins install OthmanAdi/planning-with-files

# Codex (手动复制)
cp -r ~/.claude/plugins/cache/planning-with-files/*/skills/planning-with-files ~/.codex/skills/
```

---

## 2. 实际工具拓扑

### 2.1 Claude Code 全栈

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 0: 平台能力 (Claude Code v2.1.x + Opus 4.6)          │
│   Hooks(10) · Plugins · Skills · Subagents · Agent Teams    │
│   MCP · Resume · Compact · Plan Mode · Web Search           │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Superpowers (方法论, 自动触发)           ⭐ 45.5k  │
│   brainstorming · writing-plans · tdd ·                     │
│   subagent-driven-dev · verification ·                      │
│   code-review · debugging · worktree workflows              │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: 官方 Plugins (能力增强, 开机自装)                   │
│   code-review · commit-commands · feature-dev ·             │
│   frontend-design · pr-review-toolkit ·                     │
│   security-guidance · learning-output-style · hookify       │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: VibeCoding Kernel v8.3.5 (编排层)                  │
│   ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐        │
│   │  PACE   │→│ RIPER-7  │→│ cunzhi │→│.ai_state │        │
│   │ 路由器  │ │ 7阶段编排 │ │ 门控   │ │ 状态追踪 │        │
│   └─────────┘ └──────────┘ └────────┘ └──────────┘        │
│   ┌──────────┐ ┌──────────────┐ ┌──────────┐              │
│   │.knowledge│ │ Path 分级参数 │ │agent-teams│              │
│   │ 经验复用 │ │ A/B/C/D 策略 │ │ 并行分工  │              │
│   └──────────┘ └──────────────┘ └──────────┘              │
├─────────────────────────────────────────────────────────────┤
│ MCP 工具层                                                  │
│   augment-context-engine · cunzhi · mcp-deepwiki            │
├─────────────────────────────────────────────────────────────┤
│ Skills 层 (按需加载, 每个 <5k tokens)                       │
│   cunzhi · agent-teams · knowledge · brainstorm ·           │
│   tdd · verification · code-quality · context7              │
├─────────────────────────────────────────────────────────────┤
│ 可选增强                                                    │
│   planning-with-files (context 恢复) ·                      │
│   superpowers-lab (语义去重)                                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Codex CLI 全栈

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 0: 平台能力 (Codex CLI + GPT-5.3)                     │
│   notify hook(1) · Skills · Plan Mode · Web Search          │
│   MCP · Resume · Compact · Sandbox · Explorer               │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: VibeCoding Kernel v8.3.5 (编排层)                  │
│   PACE → RIPER-7 → cunzhi → .ai_state → .knowledge         │
│   (与 CC 共享 skills/workflows, 无 Hooks/Plugins)           │
├─────────────────────────────────────────────────────────────┤
│ MCP 工具层                                                  │
│   augment-context-engine · chrome-devtools ·                │
│   cunzhi · mcp-deepwiki                                     │
├─────────────────────────────────────────────────────────────┤
│ AGENTS.md 指令替代 Hooks:                                   │
│   质量门控 (npm test + tsc) · 上下文恢复 (.ai_state)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 真实开发流程: 需求 → 交付

以 "给用户管理模块添加批量导入功能" 为例, 完整走一遍:

### Phase 0: 接收需求

```
用户: "给用户管理模块添加 CSV 批量导入功能"
→ /vibe-dev 或直接描述需求
```

### Phase 1: PACE 路由

```
判定依据:
  - 新增文件: upload API + parser + validator + UI = 4+ 文件 ✓
  - 新依赖: csv-parse ✓
  - API 变更: 新增 POST /api/users/import ✓
→ Path C (Comprehensive)
→ 读 workflows/riper-7.md
```

### Phase 2: R (Research) — 搜索 + 理解

```
动作:
  1. augment-context-engine 搜 "user" "import" "csv" "upload"
     → 发现 src/api/users.ts, src/models/User.ts, 已有单用户创建
  2. mcp-deepwiki 查 csv-parse 库文档
  3. 读 .knowledge/ → 上次文件上传踩过 multer 内存坑
  4. 读 .ai_state/conventions.md → 项目用 Express + Prisma + Zod

写入: .ai_state/session.md
  需求: CSV 批量导入用户
  Path: C
  发现: 已有 User model, 需要新增 upload 中间件 + validation
  经验: multer 要用 disk storage, 不用 memoryStorage (见 .knowledge)

检查点: cunzhi "Research 完成, 发现已有 User 模型和单用户创建 API, 继续设计?"
  → 用户确认
```

### Phase 3: D (Design) — 方案 + ADR

```
动作:
  1. 提出 2 方案:
     A: 前端解析 CSV → 逐条调用现有 API (简单, 慢)
     B: 后端接收文件 → 批量 upsert (快, 需要新 API)
  2. augment 搜索类似批量操作 → 项目里有 bulk-create 先例
  3. 选方案 B, 写 ADR

写入: .ai_state/design.md
  ADR-1: CSV 批量导入采用后端处理
  - 背景: 前端逐条太慢, 项目已有 bulk-create 先例
  - 决策: 后端 multer + csv-parse + Prisma createMany
  - 后果: 需要新增 API endpoint + 文件大小限制

检查点: ● cunzhi DESIGN_READY
  → 展示设计方案, 用户确认或修改
```

### Phase 4: P (Plan) — 任务拆解

```
动作:
  1. 从 design.md 拆解:
     ☐ T1: 安装 csv-parse, multer — package.json
     ☐ T2: 创建 Zod schema (ImportUserRow) — src/validators/
     ☐ T3: 写 CSV parser 函数 — src/services/csvParser.ts
     ☐ T4: 写 POST /api/users/import endpoint — src/api/users.ts
     ☐ T5: 写前端上传组件 — src/components/UserImport.tsx
     ☐ T6: 集成测试 — tests/integration/
  2. 标注依赖: T1→T2→T3→T4, T5 可并行
  3. feature-dev plugin 辅助检查拆解合理性

写入:
  .ai_state/plan.md — 6 个任务 + 依赖图
  .ai_state/doing.md — 初始化, T1 为当前任务

检查点: ● cunzhi PLAN_APPROVED
  → 用户确认任务拆解
```

### Phase 5: E (Execute) — 编码 + 测试

```
循环 (T1 → T6):
  1. 读 doing.md → 当前任务 T1
  2. Path C 强制 TDD:
     - 写失败测试 (RED)
     - 写最小实现 (GREEN)
     - 重构 (REFACTOR)
  3. T3 需要 csv-parse API → npx ctx7 resolve csv-parse
  4. commit-commands plugin 格式化: "feat(users): add CSV parser"
  5. doing.md: T1 ☑, 进入 T2
  ... 重复 ...

写入: .ai_state/doing.md 实时更新
检查点: ○ T4 修改 >100 行 → cunzhi 确认方向
```

### Phase 6: V (Verify) — 验证

```
Path C 检查清单:
  ☑ npm test — 全部通过
  ☑ npx eslint . — clean
  ☑ npx tsc --noEmit — 通过
  ☑ 覆盖率 87% > 80%
  ☑ 无 TODO/FIXME
  ☐ 无 console.log → 发现 T3 有 1 处 → 删除 → 重新验证 ✓

写入: .ai_state/verified.md
```

### Phase 7: Rev (Review) — 审查

```
Plugin 编排:
  1. code-review plugin → 发现: csvParser 缺少行号错误报告
  2. security-guidance plugin → 发现: 文件大小没限制
  3. 修复两个问题, 重新 commit

Linus 四问:
  ✓ 逻辑正确 (空文件、格式错误都处理了)
  ✓ 边界处理 (10MB 限制, 重复 email 跳过)
  ✓ 命名清晰 (parseCSVToUsers, validateImportRow)
  ✓ 最简实现 (没有过度抽象)

经验沉淀:
  → .knowledge/pitfalls.md: "CSV 解析要加行号到错误信息, 否则用户不知道哪行出错"
  → .knowledge/patterns.md: "批量操作用 Prisma createMany + skipDuplicates"

检查点: ● cunzhi REVIEW_DONE
写入: .ai_state/review.md
```

### Phase 8: A (Archive)

```
  mv .ai_state/*.md .ai_state/archive/2026-02-12/
  更新 .knowledge/
  交付完成
```

### Phase 9: Delivery Gate (Stop Hook)

```
delivery-gate.cjs 自动检查:
  ☑ npm test 通过
  ☑ tsc --noEmit 通过
  ☑ doing.md 无 ☐
→ PASSED ✓ → 允许 Stop
```

---

## 4. 文件清单

```
v8.3.5/
├── .claude/
│   ├── CLAUDE.md                        (92L)    # CC 入口
│   ├── workflows/
│   │   ├── pace.md                      (56L)    # 复杂度路由
│   │   └── riper-7.md                   (130L)   # 7阶段编排
│   ├── skills/
│   │   ├── cunzhi/SKILL.md              (48L)    # 检查点协议
│   │   ├── agent-teams/SKILL.md         (72L)    # 并行分工
│   │   ├── knowledge/SKILL.md           (47L)    # 经验管理
│   │   ├── brainstorm/SKILL.md          (28L)    # R/D 增强
│   │   ├── tdd/SKILL.md                 (29L)    # TDD 分级
│   │   ├── verification/SKILL.md        (32L)    # 验证清单
│   │   ├── code-quality/SKILL.md        (27L)    # Rev 编排
│   │   └── context7/SKILL.md            (22L)    # 库文档拉取
│   ├── commands/
│   │   ├── vibe-dev.md                  (28L)    # 开发入口
│   │   ├── vibe-init.md                 (27L)    # 项目初始化
│   │   ├── vibe-resume.md               (24L)    # 中断恢复
│   │   └── vibe-status.md               (23L)    # 状态查看
│   ├── rules/rules.md                   (31L)    # 项目规则
│   ├── settings.json                    (52L)    # CC 配置
│   ├── hooks/
│   │   ├── context-loader.cjs            (78L)    # SessionStart
│   │   └── delivery-gate.cjs             (109L)   # Stop gate
│   └── templates/ai-state/              (6 files) # 模板
│       ├── session.md / doing.md / design.md
│       ├── plan.md / verified.md / review.md
│       └── conventions.md
├── .codex/
│   └── config.toml                      (22L)    # Codex 配置
├── AGENTS.md                            (73L)    # Codex 入口
├── scripts/
│   └── sync-platforms.sh                (55L)    # 跨平台同步
└── README.md                            (本文件)
```

### 统计

| 指标 | v8.2.1 | v8.3.5 | 变化 |
|:---|:---|:---|:---|
| 文件数 | 38 | 26 | **-32%** |
| 总行数 | 1558 | ~780 | **-50%** |
| Skills | 11 | 8 | -3 (SP 覆盖) |
| Commands | 9 | 4 | -5 (RIPER-7 编排) |
| 工具矩阵 | 4 张 | 1 张统一 | 合并 |
| 三层重复 | ~200L | 0L | 消除 |
| Hooks | 4 stub (不工作) | 2 可运行 | 质>量 |
| MCP 假设工具 | 15 个 | 3-4 真实 | 去虚存实 |
| Codex 支持 | 无 | 完整 | 新增 |

---

## 5. 安装指南

### Claude Code

```bash
# 1. 复制文件到项目根目录
cp -r v835/.claude/ .claude/

# 2. 安装 Superpowers
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace

# 3. (可选) 安装 planning-with-files
claude plugins install OthmanAdi/planning-with-files

# 4. 确保 MCP 工具已配置
#    augment-context-engine / cunzhi / mcp-deepwiki

# 5. 官方插件 (开机自装, 无需手动)
#    code-review / commit-commands / feature-dev / frontend-design
#    pr-review-toolkit / security-guidance / learning-output-style / hookify

# 6. 初始化项目
/vibe-init
```

### Codex CLI

```bash
# 1. 复制文件
cp -r v835/.codex/ .codex/
cp v835/AGENTS.md ./AGENTS.md

# 2. 链接共享 Skills
ln -sf .claude/skills .codex/skills

# 3. 确保 MCP 工具已配置
#    augment-context-engine / chrome-devtools / cunzhi / mcp-deepwiki
```

---

## 6. 回退方案

| 阶段 | 回退方式 | 耗时 |
|:---|:---|:---|
| 安装后不满意 | `git checkout .claude/` | 秒级 |
| Hook 出问题 | `VIBECODING_HOOKS_DISABLED=1` | 秒级 |
| 某个 Skill 冲突 | 删除对应 `skills/xxx/` 目录 | 秒级 |
| 全部回退 | `git tag` before install → `git reset --hard` | 秒级 |

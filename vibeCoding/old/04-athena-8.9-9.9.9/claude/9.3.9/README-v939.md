# VibeCoding Kernel v9.3.9

> PACE 是大脑, CC 是平台, 插件是工具, Hooks 是守卫。

---

## 快速开始

```bash
# 1. 把 .claude/ 复制到项目根目录
cp -r .claude/ /path/to/target/

# 2. 安装插件 (首次)
/vibe-setup

# 3. 开始开发
/vibe-dev 做一个用户登录功能, 支持邮箱密码注册和登录
```

---

## 与 v9.3.8 对比

| 维度           | v9.3.8                     | v9.3.9                                |
| -------------- | -------------------------- | ------------------------------------- |
| 文件数 / 行数  | 34 / 2205                  | **23 / 1209**                         |
| Skills 风格    | 步骤教学 (150-270 行)      | **目标+约束+工具** (60-150 行)        |
| 状态注入       | "请先读 state.json"        | **`!command` 动态注入** (17 处)       |
| 隔离           | 描述 worktree              | **`context: fork`** (execute, review) |
| 工具限制       | 无                         | **`allowed-tools`** (execute, review) |
| 并行执行       | 手动描述                   | **CC `/batch`**                       |
| 代码清理       | 无                         | **CC `/simplify`**                    |
| commands/      | 6 个旧格式                 | **全部迁移到 skills/**                |
| Hooks          | 6 个 (含 3 个低价值)       | **3 个** (每个有明确价值)             |
| context-loader | SessionStart hook          | **删除** (`!command` 替代)            |
| .ai_state/     | 8 文件 (JSON 重)           | **6 文件** (tasks.md checkbox)        |
| review 报告    | 无                         | **reviews/sprint-N.md**               |
| 跨模型交接     | 无                         | **handoff.md**                        |
| 废弃命令       | /superpowers:brainstorm 等 | **零**                                |
| 幻觉命令       | /context7:docs 等          | **零**                                |

精简 45%, 但能力更强。

---

## 架构

### PACE 是大脑

```
PACE (路由+调度)
    │
    ├── codex-plugin-cc (委托/审查)
    ├── superpowers (brainstorming/TDD — 自动激活)
    ├── ECC AgentShield (安全扫描)
    ├── context7 (库文档)
    ├── playwright-skill (E2E)
    ├── CC /batch (并行)
    ├── CC /simplify (清理)
    └── CC /review (本地审查)
```

所有插件都是 PACE 调度的工具, 不是平行系统。

### 目录结构

```
.claude/
├── CLAUDE.md                       # Agent 角色 + PACE 优先级 (120 行)
├── settings.json                   # CC 配置
├── rules/
│   ├── iron-rules.md                 铁律 + 编程标准 + Path A 豁免
│   └── tool-dispatch.md              工具调度表
├── skills/
│   ├── vibe-dev/SKILL.md             /vibe-dev (用户入口)
│   ├── riper-pace/                   核心引擎
│   │   ├── SKILL.md                    PACE 路由 + RIPER 调度
│   │   └── templates/                  .ai_state/ 模板 (6 个)
│   ├── plan/SKILL.md                 R₀/R/D/P 阶段
│   ├── execute/SKILL.md              E 阶段 (context:fork)
│   ├── review/SKILL.md               T/V 阶段 (context:fork)
│   ├── vibe-setup/SKILL.md           安装向导
│   └── vibe-review/SKILL.md          单独审查
├── agents/
│   ├── generator.md                  @generator (worktree 隔离)
│   └── evaluator.md                  @evaluator (独立评审)
└── hooks/
    ├── delivery-gate.cjs             Stop: 质量门控链
    ├── pre-bash-guard.cjs            PreToolUse: 危险命令拦截
    └── permission-retry.cjs          PermissionDenied: 重试策略
```

### .ai_state/ (运行时状态, 不提交 git)

| 文件                | 用途                                      |
| ------------------- | ----------------------------------------- |
| project.json        | Path/Stage/Sprint + conventions + gotchas |
| design.md           | 需求 + 方案 + 验收标准                    |
| tasks.md            | Task 清单 (markdown checkbox)             |
| reviews/sprint-N.md | 审查报告 (多模型结果汇总)                 |
| handoff.md          | 跨模型交接上下文                          |
| lessons.md          | 经验教训                                  |

---

## 关键设计决策

### 1. 给目标不给步骤

v9.3.8: "步骤 1 搜索代码 → 步骤 2 查文档 → 步骤 3 写 design.md"
v9.3.9: "目标: 需求→Spec。工具: brainstorming + ctx7。产出: design.md"

Agent 是 Opus 4.6, 不需要被教怎么搜索代码。

### 2. `!command` 替代 "请先读"

v9.3.8: skills 里写 "开始前请先读 .ai_state/state.json"
v9.3.9: `!cat .ai_state/project.json` — agent 打开 skill 就看到状态

### 3. 不重造轮子

CC 有 `/batch` → 不写并行逻辑
CC 有 `/simplify` → 不写清理逻辑
superpowers 有 TDD → 不写 TDD 教学

### 4. tasks.md 替代 3 个 JSON

plan.md + feature_list.json + progress.json → 一个 tasks.md (markdown checkbox)

- Agent 读写 markdown 比 JSON 更自然
- `grep -c "\- \[x\]"` 比 JSON parse 更简单
- 人和 agent 都能直接读

### 5. Hooks: 效率 + 质量

3 个 hook, 每个有明确价值:

- delivery-gate: 检查 tasks 完成度 + review 报告存在 + 外部 review + 测试 + VERDICT
- pre-bash-guard: 拦截 rm -rf, curl|bash, force push
- permission-retry: 安全拒绝不重试, 其他建议授权

---

## 审查报告

四轮审查:

| 轮次   | 方法                   | 结果                     |
| ------ | ---------------------- | ------------------------ |
| 第一轮 | 程序化审计 (10 项)     | 全绿                     |
| 第二轮 | Path B 10 步全链路走查 | 全通过                   |
| 第三轮 | 7 个边界场景           | 全通过                   |
| 第四轮 | 命令正确性 + 一致性    | 1 处修复 (reviews/ 目录) |

插件命令全部对照官方文档验证:

- codex-plugin-cc: ✅ (github.com/openai/codex-plugin-cc)
- ECC AgentShield: ✅ (npmjs.com/package/ecc-agentshield)
- context7: ✅ (npx ctx7 resolve)
- superpowers: ✅ 自动激活, 零废弃 slash 命令

---

## 兼容性

- Claude Code: v2.1.90+ (利用 `!command`, `context:fork`, `allowed-tools`)
- codex-plugin-cc: 当前版本
- Node.js: 18.18+

# VibeCoding Kernel v8.6 → v8.6.1 CHANGELOG

## 审计发现 & 修复清单

### 🔴 CRITICAL BUGS (会导致执行失败)

| # | 问题 | 位置 | 修复 |
|:--|:-----|:-----|:-----|
| 1 | Codex pace.md 引用 `CLAUDE.md` | `.codex/workflows/pace.md` | → `AGENTS.md` |
| 2 | Codex pace.md 引用 `Agent Teams` | `.codex/workflows/pace.md` Path D | → `Collab Parallel` (collab 模式) |
| 3 | Codex pace.md 工具矩阵引用 CC 子代理 | `.codex/workflows/pace.md` | 全部替换为 collab/chrome-devtools/desktop-commander |
| 4 | Codex riper-7.md 引用子代理 | T/V 阶段 `**子代理:** validator, e2e-runner` | 全部移除, 改为直接执行命令描述 |

### 🟡 FUNCTIONAL GAPS (降低有效性)

| # | 问题 | 修复 |
|:--|:-----|:-----|
| 5 | **brainstorm skill 缺失** (用户报告) | 新增 `skills/brainstorm/SKILL.md` (CC+Codex) |
| 6 | brainstorm→context7→workflow 断层 | 重构三者管道: brainstorm(R₀b) 调用 context7 验证 → 输出 design.md → plan-first 消费 |
| 7 | Anthropic 官方插件未引用 | CLAUDE.md/AGENTS.md 新增 Plugins 段落, 声明 Superpowers 等默认启用 |
| 8 | 无 vibe-brainstorm 命令 | 新增 `commands/vibe-brainstorm.md` |

### 🟢 QUALITY IMPROVEMENTS (优化体验)

| # | 问题 | 修复 |
|:--|:-----|:-----|
| 9 | PreToolUse .md 阻断过于激进 | 白名单新增 `API/ARCHITECTURE/SECURITY/MIGRATION.md` + `docs//src//plans/` 目录 |
| 10 | Codex `streamable_shell = false` | → `true` (最大化模型能力) |
| 11 | 版本号仍为 8.6 | 全部更新为 8.6.1 |

---

## 新增组件

### brainstorm skill (CC + Codex)
```
skills/brainstorm/SKILL.md — 苏格拉底式需求精炼
├─ 1. 探索项目上下文 (augment-context + .ai_state)
├─ 2. 逐个提问 (一次一问, 优先选择题, YAGNI)
├─ 3. 提出 2-3 方案 (context7 验证可行性)
├─ 4. 分段呈现设计 (每段≤200字, 逐段确认)
└─ 5. 输出 design.md → cunzhi → plan-first
```

### vibe-brainstorm 命令 (CC only)
```
commands/vibe-brainstorm.md — 显式触发 brainstorm skill
```

---

## 管道重构: brainstorm → context7 → plan-first

v8.6 的问题: 三个 skill 各自独立, 没有数据流连接。

v8.6.1 的修复:
```
R₀b (brainstorm)
  │ context7 查库文档验证方案
  │ 输出 → .ai_state/design.md
  ▼
R (研究)
  │ context7 深入调研
  │ 对照 design.md 验证
  ▼
D (设计)
  │ context7 查 API 细节
  │ 更新 design.md
  ▼
P (plan-first)
  │ 读 design.md 作为输入
  │ context7 确保技术细节准确
  │ 输出 → .ai_state/plan.md
  ▼
E (开发)
```

每个阶段都有 context7 作为贯穿式文档支撑, brainstorm 的 design.md 是上游产物, plan-first 的 plan.md 是下游消费。

---

## 数据对比

| 指标 | v8.6 | v8.6.1 | 变化 |
|:---|:---|:---|:---|
| CC 文件 | 43 | 45 | +brainstorm skill, +vibe-brainstorm cmd |
| CC 行数 | 930 | 1016 | +9.2% |
| Codex 文件 | 29 | 30 | +brainstorm skill |
| Codex 行数 | 470 | 548 | +16.6% |
| Skills | 12 | 13 | +brainstorm |
| Commands | 4 | 5 | +vibe-brainstorm |
| Bugs fixed | — | 4 critical + 4 functional + 3 quality | 11 total |
| Pipeline integrity | 断层 | brainstorm→context7→plan-first 完整连接 | ✓ |
| Cross-platform | 1 泄漏 (v8.6 已修) | 0 泄漏 | ✓ |

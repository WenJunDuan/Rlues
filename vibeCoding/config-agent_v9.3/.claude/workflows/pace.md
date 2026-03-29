# P.A.C.E. 复杂度路由 v9.3.1

## 路由判定

分析用户输入, 按以下规则选择 Path:

| 信号     | Path A      | Path B       | Path C         | Path D         |
| -------- | ----------- | ------------ | -------------- | -------------- |
| 文件数   | 1-2         | 3-10         | 10+            | 20+            |
| 预估时间 | ≤30 min     | 30min-4h     | 4h-3天         | 3天+           |
| 关键词   | 修/改/加/删 | 做/实现/开发 | 重构/迁移/系统 | 架构/平台/全栈 |
| 描述长度 | ≤50 字      | 50-200 字    | 200+ 字        | 200+ 字+多模块 |
| 需求数   | 1           | 2-5          | 5-15           | 15+            |

> 不确定时: 问用户, 不猜。用 cunzhi 确认 Path 选择。

## 分级加载

### Path A — 敏捷

```
加载: CLAUDE.md
跳过: R₀, R, D, P 阶段
RIPER: 直接 E→T → Done
状态文件: 无 (不需要 .ai_state/)
Codex: 可选
```

### Path B — 标准

```
加载: CLAUDE.md + pace.md + riper-7.md + 相关 skills
RIPER: R₀ → R → D → P → E → T → V → Done
Skills: context7, reflexion, verification, code-review, kaizen
Plugins: superpowers 全流程, gstack /codex 审查+委托, feature-dev, code-review, commit-commands
确认点: [DESIGN_READY] [PLAN_CONFIRMED] [DELIVERY_COMPLETE]
Codex: P 对抗审查 + E 委托写代码 + T 交叉审查
```

### Path C — 复杂

```
加载: 全量 (所有 skills + agent-teams)
RIPER: 同 Path B + 并行分工
额外: agent-teams (worktree 隔离), e2e skill, security-review skill
子代理: builder + validator + explorer (background)
Plugins: 同 Path B + playwright-skill, ECC AgentShield
确认点: 同 Path B + [SECURITY_PASSED]
Codex: 同 Path B
```

### Path D — 系统

```
加载: 同 Path C
额外: 按里程碑拆分, 每个里程碑 = 一个 Path B/C 子任务
Codex: 同 Path C
```

## 路由输出格式

选定 Path 后, 向用户展示:

```
📊 任务分析
├─ 复杂度: Path B (标准)
├─ 预估: ~3 小时
├─ 文件涉及: ~6 个
├─ 关键技术: React + Supabase Auth
├─ Codex 参与: P 审查 + E 委托 + T 互审
└─ 执行计划: R₀→R→D→P→E→T→V

确认后开始？
```

然后调用 cunzhi 等待确认 (降级: 对话确认)。

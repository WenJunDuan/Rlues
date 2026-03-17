# VibeCoding Kernel v9.1.7 — CHANGELOG

## 核心理念: 从"教 AI 思考"到"帮 AI 执行"

基于 agent 视角自省, 重新审视每一行提示词:
- 砍掉 AI 已知的编程常识
- 合并重复出现的指令
- 模板用真实例子替代空壳结构
- TDD 检查从每次文件修改合并到交付门控

## 平台同步 (2026-03-17)

### CC v2.1.76
- PostCompact hook → compact 后自动保存状态
- /plan {摘要} → P 阶段集成
- /effort low|medium|high → E 阶段复杂任务
- /loop → V 阶段持续监控
- MCP elicitation → 自动支持, 无需额外配置
- HTTP hooks → 文档记录, 不默认启用
- ExitWorktree → agent-teams skill 提及

### Codex 最新
- GPT-5.4 默认模型
- Plugin 系统 (config + marketplace)
- spawn_agents_on_csv + wait_agent
- @plugin mentions
- steer flag 移除 (always-on)
- GPT-5.3-Codex-Spark 注释配置

## 改刀清单

### 刀1: 砍重复 (-300 行估计)
- 思维协议: 不再每个阶段重复, riper-7 顶部写一次
- TDD: CLAUDE.md 铁律写一次, tdd skill 只写操作细节
- 检查点: delivery-gate 是唯一执行层

### 刀2: 砍 AI 已知 (-150 行估计)
- 删除: "注释解释 WHY", "函数 <50 行", "不用 any/as any"
- rules.md + conventions.md → 合并为 conventions.md (只写项目特有)

### 刀3: 砍未用路径 (-80 行估计)
- pace.md: 纯路由表 (~15 行)
- riper-7: 条件标注替代完整分支描述

### 刀4: 模板用例子替代结构
- design.md, plan.md 模板带真实小例子 (JWT 认证)
- 空壳占位符 → 具体 pattern

### 刀5: TDD hook 合并到 Stop
- 删除: PostToolUse TDD prompt hook (N 次/session)
- 新增: Stop delivery-gate 用 git diff 一次性检查 (1 次/session)

### 刀6: 状态文件合并 (10 → 7)
- session.md + doing.md → status.md
- verified.md + review.md → quality.md
- archive.md → 删除 (kaizen 直接写 knowledge + lessons)

### 新增: PostCompact hook
- CC v2.1.76 新增事件
- compact 后自动保存 status.md 时间戳

### 新增: Codex hooks 正式配置
- config.toml [hooks] 段 (v0.114+ 实验性)

## 外部仓库精华

- shanraisshan: "CLAUDE.md < 200 行" → 硬约束
- Anthropic 官方: "interview first (AskUserQuestion)" → brainstorm skill
- Anthropic 官方: "hooks 是强制的, CLAUDE.md 是建议的" → 架构原则
- trailofbits: "两次 compact = 任务太大" → 铁律
- 社区共识: "document what Claude gets wrong" → 核心原则

## 文件统计

| 包 | 文件数 | 行数 |
|----|--------|------|
| CC | 38 | ~830 |
| Codex | 30 | ~470 |
| 总计 | 68 | ~1300 |

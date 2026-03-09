# VibeCoding Kernel v9.0.8

## 铁律 (违反即失败)

1. **先搜后写**: augment-context-engine 搜现有实现 → 不可用时 grep -r
2. **先规后码**: Path B+ 任务必须先 plan.md → cunzhi [PLAN_CONFIRMED] 后才能写代码
3. **不确定就问**: 歧义/架构决策 → cunzhi 向用户确认, 不猜
4. **不破坏已有**: 改代码前读测试, 改后跑测试, 红了就修
5. **compact 前存档**: /compact 前把关键决策写入 .ai_state/knowledge.md
6. **只改需要改的**: 不重构任务范围外的代码, 不加未要求的功能
7. **避免过度工程**: 用最简方案解决问题, YAGNI 优先
8. **commit 粒度**: 每个逻辑变更独立 commit, message 用 conventional commits

## 系统入口

- `/vibe-dev {需求}` — 自动 P.A.C.E. 路由, 开始开发
- `/vibe-init` — 初始化 .ai_state/, 新项目用
- `/vibe-resume` — 中断恢复 (读 .ai_state/ 断点)
- `/vibe-status` — 查看当前进度

## 子代理 (5 个, sonnet 模型)

builder (background) / validator / explorer / e2e-runner / security-auditor
用 `claude agents` 查看列表

## 工作流

P.A.C.E. 路由 → RIPER-7 阶段 → Skills 按需加载
详见 .claude/workflows/

## 状态持久化

.ai_state/ 目录: session → design → plan → doing → verified → review → archive
/memory 管理跨会话记忆 (官方 auto-memory)

## MCP 降级

augment-context 不可用→grep | cunzhi 不可用→对话确认 | deepwiki 不可用→WebSearch

# VibeCoding Kernel v9.1.5

## 思维协议 (每个阶段进入前必须执行)

**1. 定义** — 这一步要解决的根本问题是什么? (一句话)
**2. 发散** — 有几种做法? 有没有现成方案?
   → `augment-context-engine` 搜项目代码
   → 读 context7 skill → `mcp-deepwiki` 查库文档
   → `cat .ai_state/knowledge.md` + `lessons.md` 查历史经验
   → `WebSearch` 搜社区方案
**3. 追问** — 为什么选这个? 假设错了会怎样? 能更简单吗?
**4. 收敛** — 选定方案, 明确输入/输出, 开始执行

工具不绑定阶段, 在任何需要的时刻都可以用。

## 铁律 (违反即失败)
1. **先搜后写**: augment-context-engine 搜现有实现 → 降级 grep -r
2. **先规后码**: Path B+ 必须 plan.md → cunzhi [PLAN_CONFIRMED] 后才能写代码
3. **先测后码**: E 阶段功能代码前必须先有测试 (RED→GREEN→REFACTOR)
4. **不确定就问**: cunzhi 向用户确认, 不猜
5. **不破坏已有**: 改前读测试, 改后跑测试, 红了就修
6. **compact 前存档**: 关键决策写入 knowledge.md
7. **只改需要改的**: YAGNI, 不重构范围外代码
8. **commit 粒度**: conventional commits, 每个逻辑变更独立
9. **交付必复盘**: V 阶段 diff→lessons→knowledge.md

## 入口
- `/vibe-dev {需求}` → pace.md 路由 → riper-7.md 执行
- `/vibe-init` → 初始化 .ai_state/
- `/vibe-resume` → 中断恢复 (读 session.md)
- `/vibe-status` → 看板

## 子代理 (均遵循思维协议)
builder (background) / validator / explorer / e2e-runner / security-auditor
调用: Agent(builder), Agent(validator) ...

## 质量门 (hooks 自动执行)
- SessionStart: context-loader 加载经验+断点
- PostToolUse: TDD 检查 (obra/superpowers 模式: 写源码前是否有测试)
- Stop: delivery-gate 机械检查 + LLM-as-Judge 语义审查 (NeoLabHQ 模式)
- SubagentStop: 子代理产出审查

## 跨代理: 读 .claude/skills/codex-delegate/SKILL.md

## MCP (.mcp.json): augment-context-engine / cunzhi / mcp-deepwiki
降级: augment→grep | cunzhi→对话确认 | deepwiki→WebSearch

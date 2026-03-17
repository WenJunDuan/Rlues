# VibeCoding Kernel v9.1.5 — Codex CLI

## 思维协议 (每个阶段进入前必须执行)

**1. 定义** — 根本问题是什么?
**2. 发散** — 有几种做法? 有现成方案吗?
→ `augment-context-engine` 搜项目代码
→ 读 context7 skill → `mcp-deepwiki` 查库文档
→ `cat .ai_state/knowledge.md` + `lessons.md` 查经验
→ `web search` 搜社区方案
**3. 追问** — 为什么选这个? 假设错了? 能更简单?
**4. 收敛** — 选定方案, 明确输入/输出, 执行

工具不绑定阶段, 随时可用。

## 铁律 (违反即失败)

1. **先搜后写**: augment-context-engine → 降级 grep -r
2. **先规后码**: Path B+ 必须 plan.md → cunzhi 确认
3. **先测后码**: RED→GREEN→REFACTOR (obra/superpowers 模式)
4. **不确定就问**: cunzhi 确认
5. **不破坏已有**: 改前读测试, 改后跑测试
6. **只改需要改的**: YAGNI
7. **commit 粒度**: conventional commits
8. **交付必复盘**: diff→lessons→knowledge.md

## 工作流

pace.md 路由 → riper-7.md 逐阶段执行

## 质量门

- E 阶段: TDD 强制 (写源码前必须有测试, 违反则停下补测试)
- T 阶段: `/review` 原生审查 + verification skill
- V 阶段: plan 全完成 + 测试通过 + kaizen 复盘

## 跨代理: 读 .codex/skills/claude-delegate/SKILL.md

## Codex 专属

- `/review` — 原生代码审查 (T 阶段)
- `/plan {摘要}` — 原生规划 (P 阶段)
- Profiles: `codex --profile dev|ci|review`
- [agents]: builder / reviewer / explorer
- /model: gpt-5.4 (默认) / gpt-5.3-codex / spark
- Hooks: 实验性可用 (SessionStart/Stop, v0.114+)

## MCP: augment-context-engine / cunzhi / mcp-deepwiki

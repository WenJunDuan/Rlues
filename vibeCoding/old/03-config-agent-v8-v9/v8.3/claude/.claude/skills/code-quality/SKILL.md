---
name: code-quality
description: Rev 阶段 Plugin 编排顺序 + Linus 四问 + 经验沉淀
context: main
---

# Code Quality — Rev 阶段 Plugin 编排

## 调用顺序 (Claude Code)

1. `code-review` plugin → 自动化审查 (6 个 sub-agent)
2. `security-guidance` plugin → 安全扫描 (Path C+)
3. `pr-review-toolkit` plugin → PR 格式化 (如有 PR)

## Codex 替代

1. 手动代码审查 (按 AGENTS.md 指令)
2. `npm audit` + 手动安全检查
3. `git diff` review

## Linus 四问 (所有 Path)

- 逻辑正确? (不只是能跑, 边界 case 覆盖)
- 边界处理? (空值、并发、溢出、断网)
- 命名清晰? (不需要注释解释意图)
- 最简实现? (删到不能再删, 没有"以防万一")

## 经验沉淀

审查发现的问题 → 写入 `.knowledge/pitfalls.md`
发现的好模式 → 写入 `.knowledge/patterns.md`
格式: `## {日期} — {标题}\n**教训**: {一句话}`

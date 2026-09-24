---
description: Bug-Fix 快速通道 — 跳过完整 PACE, 直接定位-复现-修复-学习
---

执行 Bug-Fix 快速通道:

1. 读取错误日志/堆栈/截图, 用 augment-context-engine 定位根因代码
2. 写一个失败测试精确复现 Bug
3. 修复根因 (不是症状), 使测试通过
4. 按项目栈运行全量测试 + 类型检查
5. 只 `git add` 相关文件, commit (`fix: ...`)
6. 读 `skills/lessons-loop/SKILL.md` — 记录根因和修复模式到 `.ai_state/knowledge.md` 教训段
7. 改动 > 20 行或涉及架构 → 升级到 Path B, 读 `workflows/pace.md`

用户描述: $ARGUMENTS

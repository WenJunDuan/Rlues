---
name: debugging
description: 调试 — 验证失败时触发
context: main
---
验证失败时自动进入:
1. 复现: 确认失败的测试/命令可稳定复现
2. 定位: `augment-context-engine` 搜索相关代码, `/debug` 辅助分析
3. 修复: 改动 + 更新测试
4. 验证: 重跑验证清单
循环直到通过。修复后更新 `.ai_state/pitfalls.md`。

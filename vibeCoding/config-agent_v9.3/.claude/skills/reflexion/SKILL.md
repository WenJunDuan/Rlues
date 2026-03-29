---
name: reflexion
description: E 阶段每 Task 自我反思。superpowers execute-plan 循环中叠加使用, 在 micro-review 之前触发。
---
# Reflexion

## 触发
E 阶段每个 Task 实现完成后, review 之前。

## 自问清单
1. 走捷径了? (as any, 空 catch, TODO)
2. 忽略边界了? (空/超长/并发/null)
3. 硬编码了? (URL/端口/阈值)
4. 过度工程了? (需求没要求的功能)
5. 偏离 design.md 了?
6. 6 个月后能读懂?

发现问题 → 立即修复, 不留 TODO。
值得记录 → lessons.md。
模式性错误 → conventions.md "Agent 易犯错误"。

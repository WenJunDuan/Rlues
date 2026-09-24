---
sprint_slug: "2026-09-20-runtime-secret-false-positive"
result: PASS
polish_commits: "4e6ea3e 5f69247 77cfad6"
---

# Cleanup Pass — runtime secret 假阳性

polish-worker（唯一 writer，主仓串行）五项检查，主 agent 复核后落盘。

| 项 | 结论 |
|---|---|
| 临时代码 | 无发现（print 均为 CLI 协议；TODO/TBD 仅作 FILLER 正则字面数据） |
| 注释 | 补 1 处三端不一致：钩子侧 is_placeholder 契约说明 + 「空值语义与 runtime-run 相反是有意的」声明，三端对齐 |
| 冗余 | 1 处测试缺陷顺带修正：明文行断言固定取 RUNTIMES[0] 致 CX 侧从未被断言，改取当前 runner；三份跨端谓词属原生对等非可消除重复 |
| 低效 | 无发现（finditer 受 MAX_BYTES 约束已声明） |
| 过度防御 | 删 1 处不可达空值分支（SECRET 取值组最短 12 字符），语义逐分支等价；BRACKETED len≤48 属门禁纵深保留 |

主 agent 复核：66/66 绿 + 扩跑 claude_rework/vm_install 绿；CC==CX runtime-run 与 CC==Pi _input-binding 字节不变量保持；生产判定逻辑与消息零变更（+10/−6，全为注释/死分支/测试）。

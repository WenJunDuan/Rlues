---
name: athena-session
description: 会话工作流：用户说「开工 / 按会话流程」、要派写者、合入 review、多人协同或收尾时用。
---

# athena-session（开场 → 执行 → 验证 → 收尾）

用户 2026-10-27 裁定。适用于用 Athena 管理 sprint、多写者协作的会话。项目自己的命令与环境细节写在项目 rules，本 skill 只放通用流程。

## 阶段

| 阶段 | 何时 | 要点 | Read |
|---|---|---|---|
| 开场 | 用户说「开工 / 按会话流程」 | 读交接 / 队列 / 状态，漏项对账；表格核对 5 类，再给 sprint 清单；确认后立即派满写者 | [open.md](references/open.md) |
| 写者 | 派工、简报、续做、代提交 | 同时 ≤3 个写者，按难度分档；简报写明推理档位、允许写集、AC 原文、验证命令 | [writers.md](references/writers.md) |
| 验证 | 每刀、会话末 | 每刀本刀测试 + 守卫快检 + typecheck；会话末根全量一次；证据单条 `athena run` | [verify.md](references/verify.md) |
| 合入与 review | collect、prepare、accept | packet 发出后到 accept 前不动主树（含未跟踪文件）；先 accept 落盘再改 | [merge-review.md](references/merge-review.md) |
| 收尾 | 会话结束 | 全量 + 整体 review → 交接 / tidy → 清理 → 推送 | [close.md](references/close.md) |
| 多人协同 | 多开发者 / 多 AI 会话 | 写集不相交、认领一行、一个人类 DRI、主干为准 | [collab.md](references/collab.md) |

进入哪个阶段就读哪份 reference，不整读。写入分区以 [stages.md](../pace/references/stages.md) 为准；门禁拦截按 reason 里的参考路径读。

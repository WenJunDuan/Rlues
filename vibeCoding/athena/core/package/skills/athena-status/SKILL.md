---
name: athena-status
description: 看项目状态、记检查点、记或关问题账；用户问进度/状态、会话要结束或交接、发现要留痕的问题时用。
---

# athena-status（状态 · 检查点 · 问题账）

## 看状态（只读）

`athena status`（机器可读用 `--json`）：路由（path / stage / sprint / next_action）、热 sprint、队列前 10、等待项（resume 条件满足标 ready）、roadmap 进度、未关 issue、豁免、提示项。
没有 `.ai_state` → 提示 `athena init`，不自动初始化。回答用户时给结论与下一步，不贴整段输出。

## 检查点（会话结束、交接、上下文将满）

1. 在当前 sprint `log.md` 末尾追加一段：`## <日期 时刻>`，写做了什么（文件、决定、跑过的 `athena run`）、卡在哪、下一步。只写本会话增量，不复述历史。
2. 更新 `_index.md` 的 `next_action` 为一句可执行的下一步。
3. 要暂停：`athena sprint pause --resume-when "<条件>"`（条件可写 `after <roadmap>/<item>`，满足时 status 标 ready）。
4. 检查点改动随下一次代码提交；不单独提交记账。

## 问题账（`issues.md`，唯一）

| 类型 | 用于 |
|---|---|
| bug (B) | 发现的缺陷，不在本 sprint 修 |
| gate (G) | 门禁误拦或熔断（熔断自动写） |
| upstream (U) | 上游工具/平台问题 |
| env (E) | 环境问题（余额、版本、网络） |
| debt (D) | 技术债 |
| question (Q) | 待用户裁定 |

- 记：`athena issue add --type <类型> --text "<一句话>" [--sev P0..P3] [--next <去向>]`。
- 关：`athena issue close <id> --note "<怎么解决>" [--status dropped]`。
- 查：`athena issue list [--type T] [--all]`。
- 一行一事；细节放 sprint log 或 decision，issue 行里只放指针。不直接手改表格。

## 完成条件

状态问答：给出路由、当前阻塞与下一步。检查点：log.md 有本会话段落，`next_action` 可执行。问题账：CLI 返回 id。

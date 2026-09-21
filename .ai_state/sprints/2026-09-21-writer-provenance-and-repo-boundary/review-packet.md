---
source_design_sha256: "a24cb0e322a672445790637e7ce2ea517a88876680049887a601d068a0c6aa1d"
mode: "design"
---

# Review Packet — writer provenance 与仓库边界（rev 2）

## Decision

首轮两 P0 结构性落实：①`validateGeneratorChain` 拆「账本完整性（无条件）+ generator 证据（三态）」，call site 外层 flag 短路删除，flag 降级为状态③绿区例外申报——八格矩阵全定义（第 3 格账本校验不因回执失效、第 7 格断裂链 block 出口=续跑或重新集成、第 8 格=②）；②containment 加 `harness_target_outside_repo_sprint` 归属伴随字段，stale 判定机械化且不锁死 impl 期合法窗口。P1 六条全落：evidence 走 currentRecord 重算、备份判据改路径 existsSync、require 适配式保 `''` 契约、tracker 归属链改 assignment 优先 + `sprint_source` 审计（worktree `_index` 提交版残余如实声明）、#2 no-change 断言、自指双缓解。附录 A canonical 字段/消息表供 grok 逐字实现（P2-3）。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | 附录 A 逐字段负向矩阵 ≥9 + currentRecord 重算（伪造 sha 先红）+ 唯一命中 + required() 假 block |
| AC2 | 八格三态×flag 矩阵逐格；R/S 裸 flag 先红；绿区不变；外层短路删除 |
| AC3 | 伴随字段三分支（stale 先红）；备份路径 existsSync（历史两记法夹具）；仓外写入 no-change |
| AC4 | Stop 走 assignment 归属（错位夹具先红）；Start 回退链 + `sprint_source`；可观察降级；CX/Pi 负向；主路径等价 |
| AC5 | exports + 适配式复写删除 + governance 续绿 + 无仓/空根/`.git` 边界三用例 + CC==Pi 字节 |
| AC6 | CC/CX 消息逐字矩阵 + Pi 同源文本断言 |
| AC7 | 自指双缓解（主 agent 独立复算落 log + 先红经 review 核实）+ gate-contracts 三端（schema/免责/流程建议） |
| AC8 | 全套回归绿 |

## 审查焦点（rev 2 定向）

- P0-1 闭合：八格矩阵是否仍有漏格（尤其账本文件存在但为空/仅坏行、多 generator 行、role 大小写）；「回执不豁免账本结构」与「断裂链出口」的机械可执行性。
- P0-2 闭合：伴随字段方案对 P9 死锁与空分支两个失败方向的免疫；字段本身被伪造（手改 slug）的面与既有 flag 同级——是否需入免责。
- P1-4 残余声明的诚实性：`sprint_source` 审计是否真优于今日（错位仍发生但可判别）。
- 附录 A 完备性：字段表与三态/containment 消息是否覆盖全部新 block 路径，无消息的 block 分支=漂移温床。
- evidence currentRecord 重算在外部执行器场景的可行性（grok 施工期间 evidence 由主仓复跑生成——重算时点与 HEAD 移动的相容性）。

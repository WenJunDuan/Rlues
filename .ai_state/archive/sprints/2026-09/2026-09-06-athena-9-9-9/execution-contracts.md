---
target_release: "9.9.9"
status: design-proposal
scope: "扩展既有记录的恢复与接收合同，实施期生效"
---
# 审查、writer 恢复与真实项目准入

本文件补充 design.md 的 AC5/7/8/11。所有记录进入既有 sprint 文件；PACE 与 items.yaml 继续拥有阶段/切片状态。没有新增任务数据库或固定审议轮次。

## 一次审查如何派发和接受

派发前由主 agent 在 session-log 保存一条可恢复记录，复用 review-manifest 与现有 packet/hash：

| 字段 | 来源与作用 |
|---|---|
| review_run_id / mode | 本次唯一调用标识；区分 design 与 implementation |
| reviewer_target | 工具返回的实际 target；可回读原生结果，不能由昵称猜测 |
| packet_sha256 | 从实际发送 packet 计算 |
| base_commit / input_manifest_sha256 | Git 实际基线及待审文件/增量清单；覆盖未提交内容 |
| evidence_refs | 本次适用的证据摘要路径与校验值；纯设计可为空并声明不验证实现 |
| output / native_output_ref | 预期结果与原生原文落点 |

调用尚未返回 target 时只记录已知 run 和输入；收到工具真实 ID 后补齐。原生调用身份无法恢复则保持未知，不能伪造目标。只读 reviewer 不进入 generator assignment 链。
结果须关联同一 run、mode、packet 与输入绑定；平台原生结果没附元数据时，主 agent 可从实际调用句柄与原始请求建立接收封装，但不得改写原文或声称模型返回了缺失字段。
接收者现场重算当前待审输入并对照持久派发记录。任一不符、缺失或无法读取均不接受为当前 PASS；历史结果保存为 superseded，不覆盖新 run。只在确认旧请求结束/失效且仍需审查时重新派发，等待期间不重复请求。
implementation 继续兼容现有 review-manifest 的 commit/design/state 绑定；新增覆盖不能放松已有校验。design 用所列文档的内容清单，不伪造 reviewed implementation commit。
审查后改动先判断影响；涉及待审内容则更新输入绑定并做针对性复核，原结果保留。验收 fixture 至少覆盖晚到旧结果、错 run、缺结果、未提交改动及有效结果一次接收。

## writer 交接与恢复

继续使用 subagent-assignments.jsonl 的真实 agent_id + sprint_slug 和独立原生事件；不新增第二份角色或生命周期状态真相。session-log 仅保存下列恢复事实及原始记录引用：

| 记录时机 | 最小内容 |
|---|---|
| 已绑定、放行写入前 | assignment 引用、agent_id、任务/切片 slug、基线、绝对 worktree、允许写集、唯一整合者 |
| 收到产物或发生中断 | 原生事件/消息引用、实际 commit 或受控增量工件与 hash、未提交内容、已知失败、下一动作 |
| 整合前后 | 实际输入工件与顺序、冲突文件归属、整合后的内容标识、测试/审查引用 |

恢复者先读此摘要，再现场检查 worktree/原生任务是否仍运行；不能仅据摘要重新派工、终止 writer 或覆写其文件。工件丢失/哈希不符保持未完成；无提交不能丢掉未提交内容。跨机器交接参照 vm-design.md 的受控输入清单。
整合顺序由现有 blocked_by 与共享文件单一写者决定，不实现通用调度器。由唯一整合者处理共享变更并在最终代码上验证；多个独立工作树的 PASS 不能相加为集成 PASS。
AC8 fixture：两个真实绑定的互斥 writer，在收到一份产物后中断主会话；恢复能从持久引用定位双方工作树、识别人为共享文件冲突及责任者、保留增量，并完成整合测试，无重复派工。

## 全栈切片准入

切片5开始前由主 agent 在该切片 design 的输入部分写一份选择记录：

- 真实仓库路径/远端标识、基线 commit 和允许改动范围；目标业务动作及 AC11 覆盖。
- 可用 Convention Pack、runtime-env 的路径/版本；FE 路由、API 与 DB 入口，现场探活结果。
- 已授权的测试角色与权限差异；只记录账号引用，不记录凭证。
- 可重复种子、隔离测试数据与清理步骤；所需 OS/服务的 required/advisory。
- 正常、拒绝、越权、失败四类输入及预期 UI/API/DB/审计状态；明确哪些失败注入可执行。

缺任一运行必需条件则该切片/AC11 未具备准入，不伪造运行结果或缩为 mock。继续其他可执行切片；真实业务规则有未授权的新选择时再提出具体问题。当前仅定义选择合同，没有声称已选好业务仓库。

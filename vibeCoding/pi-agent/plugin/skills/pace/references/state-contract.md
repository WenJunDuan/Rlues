# PACE state、恢复与证据 (9.9.9)

`.ai_state` 是唯一持久真相；PACE 和 items.yaml 拥有工作状态，不新增任务数据库或续跑循环。

## 索引与恢复

`_index.md` 是有界检索入口：≤12 KiB，route/current-state 各≤10条，每条≤160 B。热层是索引和当前 sprint；requirements/architecture/compound 命中才读；archive/.runtime 不默认扫描。
stage、next_action、当前 sprint 与必要指针在实际转换时更新，ship 前集中写结论。通过既有串行/锁机制修改；溢出原文和指针在同一事务边界持久化；空更新不写，不截断丢原文。

中断、交接或关键纠偏时主动更新现有 `session-log.md`，只写目标、合同引用、实际基线/未提交内容、已知失败、下一动作与证据引用。恢复顺序：
1. `_index.md` → 当前 design Done Contract 与 session-log。
2. 现场 `git status`、基线与 `git worktree list`；核实未提交文件和正在运行的原生任务。
3. 核对相关证据输入绑定 → 下一未完成动作。不能凭历史 PASS 或上一模型总结直接宣称完成。
writer/review 的记录格式和冲突归属见 [execution-contracts.md](execution-contracts.md)。

## 证据有效范围

design.md Done Contract 是唯一验收；review-packet 机械派生并绑定 design hash 与完整 AC 集；可选 checklist 只追踪进度。
既有 evidence.yaml/runtime-verify.md 由采集方记录实际代码内容、合同、非敏感环境摘要、结果和原始输出引用。主 agent 补 AC 映射，不伪造执行记录；秘密不进入摘要或 hash。
代码、合同或相关环境变化使对应证据失效；来源缺失、Git/文件读取失败、超时或未知执行状态均不可验证，不能当 PASS。影响范围不能可靠判断时保守复验。
业务应用证据可由另一平台核验复用；CC hook/原生协议测试不能替代 CX 证明。已通过检查只因新增变更、失败或未消除风险扩大/重复。

## 兼容与耐久知识

platforms_enabled 新写 `["cc"]`、`["cx"]` 或 `["cc", "cx"]`；旧 `["both"]` 继续可读。安装选择来自用户，能力探测只描述事实。缓存可放 ignored `.runtime`，失效后重建，不成为第二状态。
耐久决定注明 proposed / accepted / superseded；旧经验不得覆盖新决定。保留既有字段兼容直到消费者迁移完成，不新设无消费者字段。

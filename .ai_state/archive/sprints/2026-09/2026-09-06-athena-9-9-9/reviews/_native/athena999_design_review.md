---
schema_version: 1
mode: design
packet_sha256: cfcfcf5e3514caa3acf85ffecbce75ba8413d1e3c9f183332aaafda9f82c6207
reviewed_packet_sha256: cfcfcf5e3514caa3acf85ffecbce75ba8413d1e3c9f183332aaafda9f82c6207
reviewed_diff_sha256: null
review_run_id: athena999_design_review
native_output_ref: reviews/_native/athena999_design_review.md
reviewer: Athena native design reviewer (fallback)
verdict: REWORK
finding_counts:
  P0: 0
  P1: 4
  P2: 1
  INFO: 0
dimensions:
  spec_coverage:
    status: R
    evidence: "AC7/8/11/13 已列出目标，但 review 绑定、并行交接、全栈场景选择和效率判定仍缺可执行合同。"
  correctness:
    status: R
    evidence: "VM 协议区分了 commit 与未提交工作树，但未规定可验证的远端输入快照。"
  security:
    status: R
    evidence: "VM 传输未默认排除 ignored/secret 文件，可能将本地非受管内容带入远端。"
  test_risk:
    status: R
    evidence: "故障类型覆盖充分，但 AC13 没有固定任务清单、采集来源和通过规则。"
  over_engineering:
    status: S
    evidence: "设计坚持复用 PACE、items.yaml、session-log 与现有 runner，明确排除第二状态机和通用调度器。"
---

# Design Review — Athena 9.9.9

已核对 review packet 及其列出的六项输入 SHA-256，均与 packet 一致。设计的单平台基础、多平台增强、PACE/.ai_state 单一真相源和 VM 三层可用性边界清楚；以下缺口会使关键 AC 在实施期无法可靠验收。

## Findings

1. **P1 — VM 未提交输入没有可验证且安全的传输合同**  
   **维度：Security, Correctness**  
   **证据：** [vm-design.md:42] 允许以“包含未提交文件的工作树内容”作为输入，但 [vm-design.md:43-46] 只要求“同步”和“源内容标识”，没有规定快照构成、忽略规则或接收端校验。故 `git` 提交、未追踪文件和 ignored 文件可能得到不同结果；远端还可能得到本地 `.env` 或其他非受管秘密。  
   **影响：** AC6、AC9、AC10 可在远端执行了旧代码或错误输入时误报通过，并扩大对 VM 的秘密暴露面。  
   **修正：** 在 VM 协议中定义唯一输入清单：提交 SHA、受控 diff、显式允许的未追踪文件及其 SHA-256；默认拒绝 ignored/secret 文件。传输前生成清单，远端在执行前逐项校验；校验失败即不可验证。秘密只经既有 VM 凭证配置提供，不进入工作树快照或证据哈希。

2. **P1 — 异步 review 缺少可接受结果的持久绑定格式**  
   **维度：Spec coverage, Correctness**  
   **证据：** [design.md:60-61] 要求异步结果缺失时保持未完成、代码变化触发复核；[design.md:70] 仅说明 packet 有 hash；AC7（[design.md:149]）要求审查绑定最终内容。文档未定义派发前记录什么、回传结果需携带什么，以及谁依据哪些字段拒绝陈旧回调。  
   **影响：** 同一 reviewer 的晚到结果可被误关联到已变更的 packet、基线或代码，无法证明 AC7 的“最终内容”约束。  
   **修正：** 为一次 review 明确最小持久记录：`review_run_id`、packet SHA、派发时 diff/base SHA、证据摘要引用和目标输出路径。仅当回传中的同组字段匹配当前待审记录时接受结果；否则保留为过期结果并重新派发。该记录可放入现有 sprint/session-log，不新增状态树。

3. **P1 — 并行 writer 的归属与整合输入没有持久恢复点**  
   **维度：Correctness, Spec coverage**  
   **证据：** [design.md:98-102] 要求派工消息包含写集、基线和真实 agent ID，并要求主 agent 整合；但这些内容只定位在“原生派工消息”，没有规定保存其实际 ID、worktree、输出工件校验值及整合顺序。恢复路径 [design.md:76-77] 因而无法定位中断 writer 的真实产物。  
   **影响：** AC5、AC8 的冲突归属、未提交改动恢复和整合后验证会依赖短暂会话上下文，跨端/重启后可能重复派工或整合错误分支。  
   **修正：** 用现有 `items.yaml` 关联的 session-log 或 sprint 恢复摘要持久记录每个 writer 的真实 ID、基线、绝对 worktree、允许写集、产物/commit SHA、状态与唯一整合者。把“模拟冲突可定位归属”验收为读取此记录并定位到具体 writer 的 fixture。

4. **P1 — 效率目标没有预注册的测量与判定规则**  
   **维度：Test risk, Spec coverage**  
   **证据：** AC13（[design.md:155]）与评测说明（[design.md:160-161]）要求记录达标率、往返、返工与耗时；[roadmap.md:52-56] 也只规定“重点记录”。两处均未定义代表任务清单、数据来源、比较窗口或“不恶化/改进”的发布判断。  
   **影响：** “减少卡顿重复”可在没有任何可复查改善的情况下宣称完成，也无法区分环境噪声和规则回归。  
   **修正：** 在切片 1 前增加小型、版本化的任务矩阵，逐项固定起点、权限、模型/effort、采集方法及通过规则。规则应至少要求功能达标率不回退，并预先声明哪些效率指标必须改善或仅作为报告；继续沿用官方可得用量，不能取得时标 unavailable。

5. **P2 — 全栈真实切片的目标选择被推迟，缺少可执行准入条件**  
   **维度：Spec coverage, Test risk**  
   **证据：** [roadmap.md:41-43] 承认项目场景尚未 ready，并把具体业务项目与入口延后到切片计划；AC11（[design.md:153]）同时要求真实 FE/BE/DB/权限链与可核对的正常、拒绝、越权、失败路径。  
   **影响：** 实施时可能选择没有可用 Convention Pack、runtime-env、可清理数据或权限角色的项目，导致 AC11 被临时缩减而没有明确 block。  
   **修正：** 在切片 5 开始前写入一份简短选择记录：仓库/基线、Convention Pack 与 runtime-env 可用性、测试角色、种子与清理方案、FE/API/DB 入口和四类路径断言。没有合格目标时明确阻塞 AC11，不以文档或模拟结果替代。

实施阶段仍需实测单端隔离、实际平台 review/worktree 能力、VM Docker 与项目场景就绪，以及选定全栈项目的真实运行结果。

VERDICT: REWORK

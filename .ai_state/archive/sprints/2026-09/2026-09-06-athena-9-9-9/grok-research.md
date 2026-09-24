---
doc_type: external-research-opinion
created: "2026-09-06"
target_release: "9.9.9"
provider: "Grok CLI 1.0.13"
requested_model: "grok-4.6"
source_mode: "主agent提供的一手来源摘要；不冒充Grok自行完成联网核验"
status: completed
session_id: "01a07632-cb59-7171-93a6-5c9e15321c5f"
stop_reason: "end_turn"
---

## Athena 9.9.9 架构建议（独立观点）

以下只基于已提供的一手证据摘要，不声称复核原文。本版仍以 PACE 为唯一工作流、`.ai_state` 为唯一持久真相；CC-only / CX-only 各自闭环。只加能服务效率、复杂并行、全栈交付的机制。

### 五条值得加入的机制

**1. 会话 / 编排 / 沙箱身份分列**  
落点：`.ai_state/_index` 增补 `session_id`、`harness=PACE`、`sandbox_kind∈{worktree,user-vm}`，不改 stage 名。  
最小实现：现有 worktree 与 SSH VM 各记一条沙箱记录；PACE 仍只读写 `_index`。  
验收：两端都能从索引读出当前沙箱并独立走完闭环；换沙箱不换工作流。

**2. 增量交付物作为恢复句柄**  
落点：plan / design / impl / review 结束只追加产物路径；恢复读最后完成 stage。  
最小实现：沿用 `_index.stage` + 产物列表，禁止另起状态机，也不恢复 token 账本。  
验收：中断后仅凭 `.ai_state` 能续下一 stage，不依赖对话记忆。

**3. 核验区分文字记录与环境终态**  
落点：`runtime-verify` 对 user VM 做终态探针（进程、端口、文件、容器是否真起来），证据写命令与退出码。  
最小实现：SSH 已达只核已声明层；daemon / 业务环境未验证则 fail-closed，禁止用日志冒充。  
验收：文字成功而探针失败 → 门禁 block。

**4. 用户 VM 能力分层声明**  
落点：索引记 OS / SSH / 二进制为已测；daemon、业务运行时标 `unverified`。  
最小实现：一张静态能力表加探针脚本，不预置云端 setup / 网络 / 缓存层。  
验收：引用未验证层即 block；docker 二进制存在不等于 daemon 可用。

**5. 按平台实能力挂载，禁止假对称**  
落点：PACE 热路径不变。xAI 受限 Python 只作本端辅助，不得登记为 user VM。  
最小实现：`platform_caps` 白名单，无能力则跳过；两端互不依赖对方工具。  
验收：拔掉厂商 code-execution 后，PACE 闭环与 VM 核验仍通。

### 三条应驳回的过度设计

**A. 为 VM 或云环境再做一套编排状态机。** 证据主张的是 harness 与 sandbox 解耦、用增量产物恢复，不是第二套 stage。再做会与 PACE 抢真相源。

**B. 把厂商容器 / 受限 Python 与用户 RHEL VM 收成统一 Environment。** Codex 云环境的 setup / 网络 / 缓存，与 xAI 受限解释器、已测 SSH VM 不是同类。混同后探针测错对象，全栈交付会假绿。

**C. 用全局跨模型审查或 token 遥测抬升复杂并行。** 并行质量应继续靠 worktree 隔离加一次独立 review。跨模型审查与 token 账本既已禁止，也不能证明环境终态。效率来自少一层编排，不是多一层评审或计量。

本版只做：身份分列、产物可恢复、终态探针、能力分层、按实能力增强。云端仿真与双状态机一律不做。

## 主agent采纳与修正

| 建议 | 处理 |
|---|---|
| 环境终态优先于文字成功、能力分层、产物恢复 | 采纳；对应 design AC5/6/9/10 |
| _index 新增 session_id、harness、sandbox_kind | 不原样采纳；优先已有指针与runtime-verify的环境记录，避免静态/派生信息挤入热索引 |
| worktree 当作 sandbox kind | 修正：worktree 是代码副本隔离，不是进程/网络/权限沙箱；runner能力单独判断 |
| 恢复只读最后完成stage | 修正：同时核对实际代码、未提交工件与证据有效性，防止从过期状态续跑 |
| 未验证VM层一律block / 无能力则跳过 | 修正：required 验收缺能力不放行；advisory能力缺失记录覆盖缺口，不阻塞无关任务 |
| 不统一所有Environment | 采纳能力不可假等价；保留统一的最小“输入→执行结果”证据合同，分别验证runner适用性 |

## 调用记录与局限

- 两次带联网工具的研究调用 stopReason=cancelled；它们只有中间计划，不计作研究完成，stderr为空。
- 第三次只要求基于已提供证据提出观点，不调用工具；stopReason=end_turn，num_turns=1。
- 未保存或引用模型内部推理字段；上文是CLI最终text。正式设计挑战另由非作者只读会话执行。

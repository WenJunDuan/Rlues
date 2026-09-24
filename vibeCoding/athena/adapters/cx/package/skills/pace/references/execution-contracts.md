# PACE · 恢复、审查绑定与整合合同（9.9.9）

本页消费 [stages.md](stages.md) 的阶段义务，复用现有 .ai_state 记录；不建立新状态机。当前主平台拥有整合与状态写入责任，CX-only 不依赖 CC 或 Grok。

## 最短恢复路径

`_index.md` → 当前 design/Done Contract 与必要 session-log → 实际 Git/worktree → 相关证据 → 下一未完成动作。
只跟当前指针；不默认扫描 archive/.runtime。上次模型说 PASS 不能代替现场核对。
索引保持 ≤12 KiB、route/current-state 各 ≤10 条、条目 ≤160 B；必要转换更新 stage/next_action，结论在收尾集中写。索引与溢出指针通过现有锁/原子更新机制保持一致，空更新不写。

## 一次独立审查的派发与接收

主 agent 使用本端 review-binding CLI 在现有 session-log 持久化下列事实，保留 review-manifest 校验；不手改绑定、不新增审查任务库：

| 字段 | 写者与来源 |
|---|---|
| review_run_id / mode | prepare 实际返回的本次唯一调用标识；design 或 implementation |
| reviewer_target | 工具返回的真实 target；返回前留未知，禁止从昵称猜 |
| packet_sha256 | 实际发送 packet 的内容摘要 |
| base_commit / input_manifest_sha256 | Git 基线及本次待审文件内容清单，包含未提交内容 |
| evidence_refs | 适用证据路径及校验值；纯设计声明不验证实现 |
| output / native_output_ref | 预期结果路径与可回读原生原文引用 |

reviewer 独立于作者，可在同一平台、同一模型的新上下文完成；模型遵从用户有效配置。优先当前可用原生 review，否则一个只读 reviewer/独立会话。无独立审查能力保持未完成。
仅真实异步调用设置 `next_action=await-review-result`；同步返回直接接收。异步按本端通知、等待或显式回读恢复，等待不重复派发，Stop 放行但不凭空启动新 turn。无法回读保持未知。
接收者重算实际输入，对照持久派发记录的 run、mode、packet、输入与证据引用；缺失、不符、不可读均不得接受为当前 PASS。晚到结果保存为 superseded，不覆盖当前 run。
原生输出缺元数据时，可从真实调用句柄/请求建立接收封装；保存原文，不声称 reviewer 返回了未提供字段。implementation 保留已有 commit/design/state 与 diff hash 检查；design 绑定所列文档内容，不伪造实现 commit。
最终结果写 `reviews/implementation-review.md`；原文可存 `reviews/_native/{review_run_id}.md`。现有 review-manifest 是绑定扩展，不能放松已有校验。审查后待审内容变化则更新绑定、针对性复核，保留旧结果。只有确认旧请求结束或失效后才重新派发。

### CX 原生绑定命令

本端入口为 [review-binding.py](../scripts/review-binding.py)，仅需 Python，不依赖 Node/CC。先运行 `--help`；以下路径和 run 均替换为现场真实值，不能按示例生成 receipt：

```bash
python3 ~/.agents/skills/pace/scripts/review-binding.py prepare --cwd /absolute/worktree --mode implementation
# 原生派发后，原样保存工具返回 JSON；run 来自上一步 review_run_id。
python3 ~/.agents/skills/pace/scripts/review-binding.py bind --cwd /absolute/worktree --run ACTUAL_RUN --receipt /absolute/dispatch-result.json
# 原生通知/等待/回读得到完成结果后，原样保存该工具返回 JSON。
python3 ~/.agents/skills/pace/scripts/review-binding.py accept --cwd /absolute/worktree --run ACTUAL_RUN --receipt /absolute/completion-result.json
# 仅当旧请求已结束或失效，且仍需新审查时执行。
python3 ~/.agents/skills/pace/scripts/review-binding.py supersede --cwd /absolute/worktree --run ACTUAL_RUN
```

design 审查用 `--mode design`，并以可重复的 `--input 相对worktree文档路径` 补充待审文档。prepare 采集基线、未提交输入和适用证据引用，等待期间不重复 prepare。
receipt 必须来自真实原生工具返回，保留完整 JSON；当前入口支持真实 ID 字段及 Desktop 的 task_name/agents 列表形状。缺 ID、未知状态或不支持的返回格式保持未验证，保留原文并报告，不能手造字段使其通过。
accept 持久化 PASS/CONCERNS/REWORK/FAIL；负结论留记录并返回返工动作，不算 PASS。输入过期或目标不匹配不能接受。supersede 不取消原生任务；复核创建新的独立目标，不复用同一 target 绑定新 run，以免接受晚到旧结果。

## writer 派工、恢复与整合

writer 先按 [orchestration.md#spawn-binding-handshake](orchestration.md#spawn-binding-handshake) 绑定真实 agent_id；只读 reviewer 不进入 generator assignment 链。
主 thread 先建立含实际待改内容的 worktree，派工内联基线、输入引用、绝对 worktree、允许写集、输出、验收命令和唯一整合者。agent 首条命令 `pwd`，每次 shell 显式 `workdir`；无 Codex `isolation: worktree` 参数假设。

| 时机 | session-log 保存的恢复事实 |
|---|---|
| 已绑定、放行前 | assignment 引用、真实 agent_id、任务/切片 slug、基线、绝对 worktree、写集、整合者 |
| 产物或中断 | 原生事件/消息引用、实际 commit 或受控增量工件/hash、未提交内容、已知失败、下一动作 |
| 整合前后 | 工件与顺序、冲突文件归属、整合后的内容标识、测试/审查引用 |

恢复时核对工作树和原生任务是否仍运行；不据摘要重复派工、终止 writer 或覆写文件。工件丢失/hash 不符保持未完成，未提交内容不得丢弃。
依赖复用 roadmap/items.yaml 的 blocked_by；并行 writer 写集互斥，共享文件一个写者。唯一整合者按依赖接收真实增量，在最终整合代码上验证；各工作树 PASS 不能相加成集成 PASS。

## 证据的有效范围

执行采集方记录被测代码内容、当前验收合同、实际非敏感环境摘要和输出引用；主 agent 补 covers 映射，不手造执行记录。秘密不进入摘要或 hash 输入。
业务测试可跨模型消费；原生 hook/平台协议按实际平台验证。相关代码、合同或环境变化使原证据失效；来源缺失或 Git/读取失败显式不可验证。仅因新增变更、失败或剩余风险扩大/重复验证；影响不明时保守复验。
中断或跨端交接复用相同摘要与证据，本端继续完成合法可用工作；外端失联不等于其任务完成。

## 真实全栈切片准入

biz-delivery-loop 开始真实垂直切片前在该切片 design 输入写选择记录：

- 真实仓库路径/远端、基线与允许改动范围；业务动作及目标验收。
- Convention Pack/runtime-env 路径与版本，FE 路由/API/DB 入口及现场探活。
- 已授权测试角色及权限差异；仅账户引用，不写凭证。
- 可重复种子、隔离数据与清理步骤；OS/服务 required 或 advisory。
- 正常、拒绝、越权、失败四类输入和预期 UI/API/DB/审计状态；允许执行的失败注入。

缺运行必需条件则相关切片未准入，继续独立可执行工作；不把 mock/文档算真实全栈通过。表设计与 DDL SQL 分开交付；涉及迁移才增加兼容/回滚验证。已有业务确认直接引用，不重复询问。
VM 配置存在、SSH 可达、项目场景 ready 分开判断；有 VM 不自动增加 required 验收，无 VM 时本地满足合同即可。runner 只清理本 run 资源，超时/未知/清理失败留下实际状态。

原生边界依据：[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Codex hooks](https://learn.chatgpt.com/docs/hooks)。文档与 capability probe 不能代替当前平台/版本/入口实测。

# PACE 审查绑定、writer 恢复与整合 (9.9.9)

扩展既有 review-manifest、subagent-assignments.jsonl 和 session-log；不新建任务库或 CODEX-TASK.md。原生消息给完整任务，持久文件只保留恢复事实。阶段义务见 [stages.md](stages.md)。

## 一次独立审查的派发与接受

主 agent 使用本端 Node CLI 在派发前生成并持久记录到 session-log（复用已有 review-manifest），不手改绑定记录：
- `review_run_id`、`mode`（design/implementation）、从实际发送内容计算的 `packet_sha256`。
- Git 实际 `base_commit`、覆盖未提交内容的 `input_manifest_sha256` 与输入清单引用。
- `evidence_refs`（路径与 hash）；纯设计声明不验证实现，可为空。
- 预期 `output` 和原始 `native_output_ref` 落点；取得工具真实 target 后补 `reviewer_target`，不得根据昵称猜测。

原生 review 可用优先；否则同端只读 reviewer/独立会话。设计作者不自审；无需另一厂商。只读 reviewer 不进入 generator assignment 链。
仅实际后台请求设置 `await-review-result`。通知、等待或显式回读按当前入口恢复；等待不重复派发、不让 Stop 无限续跑。前台返回直接接收。缺结果保持未完成。

接收者现场重算当前待审内容，对照持久记录，匹配 run、mode、packet、实际输入和证据。任一缺失/不符/不可读不接受当前 PASS；旧回调保留 superseded，不覆盖新 run。只有确认旧请求结束或失效且仍需审查时才重派。
CLI 从保存的真实原生结果读取身份和正文，保留原文；receipt 格式不支持或缺身份时保持未验证，不手造字段补齐。implementation 保留已有 commit/design/state 绑定校验；design 不伪造实现 commit。
审查后涉及待审内容的改动更新绑定并做针对性复核。相同原因新 P0 在第二次针对性复核仍出现则按现行终止规则交还用户。

## CC 本端审查 CLI

入口：[review-binding.cjs](../scripts/review-binding.cjs)，由 Node 执行，不调用 Python。安装后的最小顺序如下；路径和 run 均替换为实际值：

```bash
node ~/.claude/skills/pace/scripts/review-binding.cjs prepare --cwd /absolute/worktree --mode implementation
node ~/.claude/skills/pace/scripts/review-binding.cjs bind --cwd /absolute/worktree --run '<prepare 返回的 run>' --receipt /absolute/dispatch-tool-result.json
node ~/.claude/skills/pace/scripts/review-binding.cjs accept --cwd /absolute/worktree --run '<同一 run>' --receipt /absolute/completion-tool-result.json
```

prepare 从实际文件采集基线、packet、未提交输入和证据 hash；纯设计使用 `--mode design --input path/to/design.md`，多个输入重复 `--input`。取得 run 后只派发一次原生审查；派发返回 JSON 原样保存为 dispatch receipt，再 bind；真实完成工具返回 JSON 原样保存为 completion receipt，再 accept。保存工具响应不等于让模型补写一份“看起来完整”的响应。

支持的真实返回包含 agent_id/agentId/threadId/thread_id；本 Desktop 的 task_name 派发返回与 agents 完成列表也可直接保存，由 CLI 精确选取绑定目标。缺 ID、未知/未完成状态、格式不支持或输入漂移不能通过，不将任务昵称手工改成身份字段。
accept 要求完成状态及正文显式 VERDICT；PASS、CONCERNS、REWORK、FAIL 均保留原文与结果，只有 PASS 可作为交付通过证据，负结论进入返工。CLI 持久化原始 receipt 和接收结果，主 agent 不改写定级。

等待期间不重复 prepare。只有现场确认旧原生请求已结束或失效，才运行 `node ~/.claude/skills/pace/scripts/review-binding.cjs supersede --cwd /absolute/worktree --run '<旧 run>'`；该命令不取消原生任务。针对性复核准备新 run 并使用新的独立真实目标，不能复用旧 target 接收晚到结果。

## writer 交接与恢复

绑定执行细节见 [orchestration.md#spawn-binding-handshake](orchestration.md#spawn-binding-handshake)。放行写入前，在 session-log 保存：assignment 引用、真实 agent_id、任务/切片 slug、基线、绝对 worktree、允许写集、唯一整合者。
收到产物或中断后补：原生事件/消息引用、实际 commit 或受控增量工件与 hash、未提交内容、已知失败及下一动作。
恢复先核实 worktree 与原生任务是否仍运行；不能仅凭摘要重派、终止 writer 或覆盖文件。工件丢失/hash 不符保持未完成；没有 commit 不等于没有产物。

## 依赖与整合

复用 items.yaml 的 blocked_by；共享 schema、锁文件、索引和集成分支指定单一写者。两个互斥 writer 可以并行，已绑定后才放行。主 agent 是唯一整合者。
整合前后记录实际输入工件/顺序、冲突文件归属、整合内容标识与测试/review 引用。多个 worktree 各自 PASS 不能相加为集成 PASS；在最终代码上核对全局不变量并运行相关检查，再交独立 reviewer。
跨端/跨机器交接必须给可访问的基线、commit/受控增量、校验值和未提交文件；不假定原生工具继承私有会话或 worktree。

## 故障验收

覆盖晚到旧结果、错 run、缺结果、未提交改动、有效结果一次接收；覆盖收到一份 writer 产物后中断并恢复，识别共享文件冲突归属、保留增量、不重复派工、完成整合测试。

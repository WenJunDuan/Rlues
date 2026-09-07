# PACE · 门禁合同速查（9.9.9，CC/CX）

进入 impl、writer 派发、review、ship 时先查本页；阶段义务仍以 [stages.md](stages.md) 为准。正常执行无需预读 hook 源码；实际 block、版本不符或本页未覆盖的分支才沿文末源码定位。修改检查器时同步此页，避免记忆与发行包漂移。

下文 `S` = 当前 `.ai_state/sprints/{current_sprint_slug}/`；Feature+ = Feature/Refactor/System。文件名区分大小写；hash 均从实际文件字节计算，不能复制旧值。

## impl-entry 与 ship 查什么

| 时机 / 适用范围 | 文件与精确判据 |
|---|---|
| 所有入口 | `.ai_state/_index.md` 的 `path`、`stage`、`current_sprint_slug`；关联切片读 `current_roadmap_slug`。不得临时改路径或 skip 字段绕门禁。 |
| impl-entry · Feature+ | `S/design.md` 的 `## 验收标准` / `## Acceptance Criteria` / `## Done Contract` 下至少一条可观察验收；用 `- AC1: …` 或首列为 AC ID 的表格，拒绝 TODO/占位语句。spec 解析支持显式链接的 requirements，但 packet 仍要求 design 验收段含 AC ID。 |
| impl-entry · Feature+ packet | `S/review-packet.md` ≤80行；frontmatter `source_design_sha256` = design 文件 SHA-256；packet 的 AC ID 集合与 design 验收段相同，无遗漏/新增。按 AC 一一派生；源码按集合比较，不验证重复次数或语义等价，作者仍须保证语义。 |
| ship · 通用前置 | `design_changed_after_impl` 不为 true；design 与 implementation-review 均存在时，design mtime 不得更新于 review；工作树违规账本不得有未解除项。轻门禁是否适用由实际 diff 判定（≤60行且限允许类型），不能按“纯文档”自行豁免。 |
| ship · Feature+ 正常分支 | `S/subagent-events.jsonl` + `S/subagent-assignments.jsonl` 真实 generator 链（适用绿区 `skip_impl_subagent_check` 例外）；`S/checklist.yaml` 存在才验，每个 `- id` 对应 `status: completed`，不是 done/PASS；必须有 evidence 与当前 implementation review。 |
| ship · evidence | `S/evidence.yaml` 的 `collected_evidence` / `- tool_use_id` / `result: pass`；9.9.9 当前 sprint 还核对 `binding_status: current`、`source_sha256`、`design_sha256`、`environment_sha256`、`output_artifact`、`artifact_sha256`。至少一个可核验当前 PASS，无当前 FAIL；旧证据/unknown 不算通过。由采集器记录，主 agent 只补 `covers: [AC1, AC2]` 映射。 |
| ship · review | `S/reviews/implementation-review.md`：`verdict: PASS`、`review_run_id`、`native_output_ref`；9.9.9 核对 session-log 中真实 prepare/bind/accept 链、packet/输入/receipt 与结果 hash。CLI 生成 `schema_version`、`mode`、`reviewer_target`、`packet_sha256`、`input_manifest_sha256` 等封装，勿手写 PASS；声明 `reviewed_diff_sha256` 时还须匹配当前源码摘要。 |
| ship · Refactor/System | `S/runtime-verify.md` 含 `## 测试场景` 或 `## Test Scenarios`；`S/cleanup-pass.md` 含 PASS/completed/完成；适用 ≥5 文件变化时要求 `.ai_state/architecture/ARCHITECTURE.md` 存在且 architecture 有实际更新。runtime/architecture 按已有适用 skip 合同；不能假设 `skip_polish` 会免除 cleanup 检查。 |
| ship · 条件产物 | 有 roadmap 则核对 `roadmap/{slug}/items.yaml` 当前切片与依赖；Bugfix 要 `S/fix-note.md`。Hotfix/Quick 不自动进入 Feature+ 的 generator/manifest-TDD 审查链，但仍履行适用阶段义务。 |
| ship · manifest 存在才验 | `S/review-manifest.yaml` 全路径 opt-in，已声明不得为绕检删除。正常分支验证治理绑定；Feature+ 再启用 spec 复核、九字段 TDD、commit/design/state 绑定及每 AC PASS 映射。R/S 也不是默认必须新建 manifest。 |

manifest 精确键：`schema_version: 1`、`implementation_commit`（40位hex）、`index_governance_sha256`（64位hex）、`files:`（两空格缩进，hash 加引号）。files 至少 `design.md`；R/S 再含 `runtime-verify.md`；声明的额外文件也验。治理摘要绑定 version/path/current_sprint_slug、三个 skip_polish/runtime_verify/architecture_check、skip_impl_subagent_check、plan_critique_disabled/min_rounds，须由现有算法计算。
manifest 链的 review 正文还须有唯一的 `Reviewed design sha256:`、`Reviewed implementation commit:`、`Reviewed state manifest sha256:`；CLI accept 自动封装。源码或治理/合同漂移须更新输入并复核，不能只重算 hash 续用旧 PASS。

## tdd-evidence.yaml · 九字段

仅在适用 manifest 链需要此文件；行为实施仍按真实 red→green，纯文档不制造 RED。下列是字段槽位，非可提交证据：

```yaml
# S/tdd-evidence.yaml；每条以 - test_file 开始
- test_file: <实际测试文件>
  red_command: <实际失败命令>
  red_summary: <实际失败摘要>
  red_observed_at: <UTC ISO-8601>
  implementation_files: [<实际实现文件>]
  implementation_observed_at: <UTC ISO-8601>
  green_command: <实际成功命令>
  green_summary: <实际成功摘要>
  green_observed_at: <UTC ISO-8601>
```

九字段均非空；时间带 `Z` 或 `+00:00`，严格 `red < implementation < green`。先有真实观测再填，不按当前时间倒造顺序。

## writer · Start → assignment → Stop

派发前冻结其他未绑定 writer，记 raw 完整行边界 N 与已有 assignment IDs；任务内联完整写集、绝对工作目录、sprint、role、截止时间与等待绑定要求。仅匹配 N 后同 sprint **唯一未绑定 Start**，核对工具实际 ID；昵称/task_name 不能充当 ID。
raw schema 恰为 `schema_version,event,agent_id,agent_type,sprint_slug,timestamp`；assignment 恰为 `schema_version,agent_id,task_name,role,sprint_slug,timestamp`，均 schema_version=1。按 `agent_id+sprint_slug` 连接；`agent_type` 不是 role；实施用真实 `role: generator`，只读 reviewer 不填 generator。

- CC：`node ~/.claude/hooks/subagent-tracker.cjs assign --cwd <绝对目录> --agent-id <真实ID> --task-name <任务名> --role generator`，随后回读 assignment。
- CX：tracker 只记录原生事件，没有 assign 子命令；主 thread 在核对 Start 后向现有 assignment JSONL 追加 schema v1 一行，回读确认。
- 有消息工具：持久绑定后发送 `BOUND <真实ID>; proceed`。**无 SendMessage/等价工具**：仅在 writer 可后台执行、双方可读同一账本且 writer 能核对自身真实 ID 时，预先约定它只读、有界轮询该 assignment；看到唯一匹配自身 ID+sprint+task_name+role 的主 thread 记录才放行。只轮询已有账本，不创建旁路任务文件或猜 ID。
- 前台调用使主 thread 无法同时绑定时，先准备返回，再通过可用原生恢复入口继续同一真实 ID；无消息/恢复/安全轮询能力则保持未绑定。超时、重复或不一致停止写入；截止时间到达不是放行信号。
- 放行后才开下一个绑定窗口；完成须有真实 SubagentStop。gate 要 generator 唯一 Start、最终事件为 Stop、类型一致且 Stop 不早于 Start/assignment；Stop 本身不代表测试 PASS。详见 [握手合同](orchestration.md#spawn-binding-handshake)。

## review-binding · 四步顺序

命令前缀：CC = `node ~/.claude/skills/pace/scripts/review-binding.cjs`；CX = `python3 ~/.agents/skills/pace/scripts/review-binding.py`。下面只列子命令，路径/run 均替换为现场值：

1. **prepare**：`prepare --cwd <绝对目录> --mode implementation`（设计用 design，可重复 `--input <仓库相对文档>`）；保存返回的实际 review_run_id。待审输入必须已就绪。
2. **原生派发**：向一个独立 reviewer 发送实际 packet/输入与 run；原样保存工具返回 JSON 作 dispatch receipt。优先可用原生 review，否则本平台只读 reviewer。
3. **bind**：`bind --cwd <绝对目录> --run <实际run> --receipt <dispatch JSON绝对路径>`；完成真实 target 持久绑定。
4. **accept**：真实通知/等待/回读后，原样保存 completion JSON，再 `accept --cwd <绝对目录> --run <同一run> --receipt <completion JSON绝对路径>`。核对 completed/complete/succeeded、正文显式 VERDICT 与现场输入；只有 PASS 算通过，其他结论落盘返工。

同步完成也按 bind→accept；只有真实异步请求设 `next_action: await-review-result`。等待中不重复 prepare；旧请求已结束/失效才 `supersede --cwd … --run …`，它不取消任务，复核使用新独立 target。receipt 原文不能加工补 ID/状态；接口不支持则保留原文并报告。完整恢复见 [execution-contracts.md](execution-contracts.md)。

## 来源与维护边界

本页按9.9.9执行代码核对；门禁实际报错优先，定位对应函数修复文档或实现。Feature 新切片是否适用按实际范围分诊，不能为了少跑门禁把进行中的 System 降级；用户显式授权的局部 Hotfix 单独记录。

本端源码：[delivery-gate](https://github.com/WenJunDuan/Rlues/blob/main/vibeCoding/codex/9.9.9/.codex/hooks/delivery-gate.py)（impl/spec/packet、ship、TDD/manifest）、[subagent-tracker](https://github.com/WenJunDuan/Rlues/blob/main/vibeCoding/codex/9.9.9/.codex/hooks/subagent-tracker.py)（生命周期/assignment）、[review-binding](https://github.com/WenJunDuan/Rlues/blob/main/vibeCoding/codex/9.9.9/.codex/hooks/_review_binding.py)（prepare/bind/accept）。包内对应 `hooks/` 同名文件；安装态 CC = `~/.claude/hooks/`，CX = `~/.codex/hooks/`。

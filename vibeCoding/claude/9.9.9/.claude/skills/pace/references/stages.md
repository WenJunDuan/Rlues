# PACE References · Stages（9.9.9, Claude Code）

本页是本发行包阶段义务的唯一正文。其他 agent/skill/模板引用本页；恢复、review 绑定、证据与整合细则见 [execution-contracts.md](execution-contracts.md)。PACE 控制工作，.ai_state 保存合同与事实；CC-only 可完成适用全流程。

## brainstorm

触发：无法从现有输入写出可观察验收标准，或用户明确要求探索。
主 agent 先查可取得的上下文，再问影响下一动作的问题；足以进入 plan/roadmap/design 即收敛，不固定追加问题。
产出 `sprints/{slug}/brainstorm.md`，只存结论、理由与约束。具体方法见 [brainstorm](../../brainstorm/SKILL.md)。

## roadmap

触发：≥2 个可独立验收、可独立 ship 的切片，或用户明确要求拆分。模块数只定风险等级，不单独强制 roadmap。
主 agent 维护 `roadmap/{slug}/roadmap.md` 与 `items.yaml`，依赖使用 blocked_by；共享不变量不可独立交付时保留单 sprint。
ship 后核对当前 item，再推进可执行项。见 [roadmap](../../roadmap/SKILL.md)。

## plan

impl-entry、writer 派发、review 与 ship 的精确文件/字段先查 [门禁合同速查](gate-contracts.md)；正常执行无需预读 hook 源码，block、版本不符或未覆盖分支再定位源码。

1. 作者写 design.md：目标、决策、允许写集与可观察 Done Contract（验收标准）。
2. Feature+ 机械派生 review-packet.md：实际 design hash、完整 AC ID 双射、≤80 行。作者不自审或给设计打 VERDICT。
3. Feature 默认无固定设计审查；Refactor/System 或用户要求时，由非作者独立上下文按 packet 审查，允许本平台 reviewer。
4. impl-entry spec-gate 核验验收标准与 packet 一致；判据变化回 design 修订并更新派生材料。

Hotfix 可省略设计；Quick 采用简短计划和必要验收。不为纯文档或机械配置制造行为测试。

## design

System 在 plan 后补详细架构；可请求只读 architect 返回提案，由主 agent 落盘。独立设计挑战沿用 plan 的一次入口，不创建 critic/evaluator 链。

## impl

Done Contract 以 design.md 为唯一权威；generator 与 reviewer 使用相同验收。checklist.yaml 只在需要推进表时创建，存在才由主 agent 更新并在交付前验证全绿；不能另定义验收。

- 绿区：≤3 文件且合计 ≤150 行，或 Hotfix/Quick/Bugfix，主 thread 可直接实施。
- 黄区：单模块 Feature，调用 generator，worktree 可选。
- 红区：Refactor/System 或 ≥2 并行 writer。主 thread 先创建含实际待改内容的 worktree，再在任务消息给出绝对路径与互斥写集；agent 首条 shell `pwd`，以后每次 shell 指定 `workdir`。
- writer 先完成 [spawn binding handshake](orchestration.md#spawn-binding-handshake)，BOUND 后写入；共享文件单写者，最终验证由整合者负责。
- repo 外安装态目标不受 worktree 隔离：仅在授权范围内逐文件备份、单写者串行，并记录 `_index.harness_target_outside_repo: true`。
- 行为实现按 TDD red→green；验证命令由 evidence collector 留真实成功/失败记录。纯文档做解析、引用与一致性检查，不写镜像测试或伪造 RED。
- 路径证据变化时重走路由，默认只升不降并补足新路径义务。

## runtime-verify

Refactor/System 强制，Feature 按合同需要。impl 和单测后运行真实接口/CLI/UI 场景，失败返回 impl，修复后复验受影响范围。
环境由设计/runtime-env 决定：本机满足合同即可；VM 配置存在或 SSH 可达不代表项目 ready，也不自动增加 VM 门禁。required 环境不可用只阻塞相关验收。
原生 Goals 仅在用户显式要求或已有 Goal 时使用，不因进入阶段自动创建。用当前工具完成有界执行，不新建续跑循环。
产出 `runtime-verify.md`（含 `## 测试场景`）和实际执行证据；FE 用 [playwright](../../playwright/SKILL.md)，运行环境见 [athena-runtime-verify](../../athena-runtime-verify/SKILL.md)。
出口：Refactor/System → polish；其他路径 → review。

## polish

Refactor/System 在 runtime-verify 后、implementation review 前执行。polish_worker 沿用当前实现 worktree与明确写集；按 writer 握手绑定，主 agent 传入既有实现 worktree 绝对路径，不另开 isolation: worktree。
检查临时代码、注释、冗余、低效、过度设计；只清理实际问题。改变行为后运行受影响验证，产生新风险则返回 impl/runtime-verify。
主 agent 复核产物，落 cleanup-pass.md，按实际变化更新 architecture/与有价值的 compound。
清理完成 → review；skip_polish 不豁免 review。分支合并、推送及 worktree 清理在 ship 按已有授权处理，不在 polish 提前销毁待审工作树。
具体操作见 [polish](../../polish/SKILL.md)。

## review

发起一次独立多维 review：优先当前可用原生 `/code-review`，否则一个只读 reviewer/本平台独立会话。无需 CX/Grok 或不同模型家族。
检查 Spec coverage、Correctness、Security、Test risk、Over-engineering；R/S 加 Evidence。禁止 live 调度 critic/evaluator/spec-compliance。
派发前持久绑定实际 run、packet、输入与证据，按 [接收合同](execution-contracts.md#一次独立审查的派发与接收) 核验。同步结果直接接收；只有真实异步调用设置 `next_action=await-review-result`，Stop 放行不续跑，通知/回读恢复后清空。
结果保存 `reviews/implementation-review.md`，包含 verdict、review_run_id、native_output_ref、packet/diff 绑定和 findings；原生原文保留可回读引用。
VERDICT：PASS / CONCERNS / REWORK / FAIL。PASS → ship；其他结果按实际问题回 impl/design。审查输入变化须针对性复核；同因新 P0 第二次复核仍出现则保留证据并交还用户。未知/缺失/旧结果不能视为 PASS。

## ship

按已授权范围交付，由 delivery-gate 现场核验适用合同：

- Feature+ 的当前 implementation-review PASS 与 packet/diff/输入绑定有效，已有 review-manifest 的 commit/design/state 链不能被放松。
- generator 实施须有真实 Start→assignment→Stop；绿区例外按既有 skip_impl_subagent_check 规则。
- Refactor/System 已完成 runtime-verify、cleanup-pass 和适用 architecture 更新。
- design/待审代码变化后原 PASS 不直接复用；checklist 存在才验全绿。
- 执行证据引用真实来源，主 agent 只补 covers 映射；记账文件不人为触发无关复审。
- roadmap item 事实同步，仍有未完成项时不宣称全部完成。

完成当前必要检查后，只有新增变更、失败或未消除风险才扩大/重复验证；影响范围不明则保守复验。候选包、未满足验收与正式 ship 状态必须区分。

### 推送与小改动

pre-bash-guard 与 delivery-gate 是独立门禁：正常推送在 ship；已有 `ATHENA_ALLOW_PUSH=1` 仅用于授权的非当前 sprint 维护性推送，不靠伪切 stage 绕行。
≤60 行且满足轻门禁文件范围的纯文档/配置/依赖改动按实际 gate 判定；源码、hooks 与超预算仍走完整适用合同。门禁例外不意味着伪造审查/测试。

## 文书与状态预算

必要 stage/next_action 转换及时更新，收尾集中同步结论；不要逐工具复制日志。_index ≤12 KiB、route/current-state 各 ≤10 条、条目 ≤160 B；超量原文与指针由现有索引事务保留。
手写产物：design、派生 packet、implementation-review、Bugfix report/fix-note、R/S runtime-verify/cleanup-pass，以及按需 session-log；其他文件需真实消费者。design 目标 System ≤200 行/Feature ≤80 行，>300 行仅警告。
派工全部内联原生消息，禁止 CODEX-TASK.md 等第二任务书；最短恢复事实落 session-log。archive 与 .runtime 不默认读取，不恢复自建 token 遥测。

## 数据归属

| 位置 | 职责 |
|---|---|
| `_index.md` | 当前路由、阶段和权威指针 |
| `sprints/{slug}/design.md` / `review-packet.md` | 唯一验收与派生审查入口 |
| `runtime-verify.md` / `evidence.yaml` | 场景覆盖与执行来源 |
| `reviews/implementation-review.md` / `reviews/_native/` | 当前接收结果与原文 |
| `subagent-events.jsonl` / `subagent-assignments.jsonl` | 原生生命周期与真实身份绑定 |
| `session-log.md` | 中断、交接和整合的最短恢复事实 |
| `roadmap/{slug}/items.yaml` | 切片状态与 blocked_by |
| `requirements/` / `architecture/` / `compound/` | 耐久知识，旧决定不能覆盖新决定 |
| `sprints/archive/` / `.runtime/` | 冷历史与可重建运行信息；默认不扫 |

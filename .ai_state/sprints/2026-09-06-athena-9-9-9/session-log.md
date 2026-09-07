---
sprint_slug: "2026-09-06-athena-9-9-9"
target_release: "9.9.9"
scope: candidate-package-implementation
implementation_status: in-progress
---
# 本轮状态与恢复入口

## 2026-09-07 门禁速查与70轮 Hotfix（已安装；提交与推送以Git记录为准）

用户显式指定 Hotfix 并授权更新9.9.9与系统目录。范围：CC/CX PACE 速查、发现入口、无消息工具的现有账本握手；不改 gate 执行逻辑，不覆盖当前15个未提交 CC hook 修改。主 thread 单写者；安装态逐文件备份。验收：速查文件/字段对照当前源码，引用有效，两端技能校验与安装文件内容一致。当前 System/impl 与 rework_impl 保留为上层未完成工作；本 Hotfix 不代表整个发行 ship。
路由：显式 Hotfix（免审议），置信度1.0；对比继续 System 全流程会把文档修补混同发行验收，故此次采用用户指定局部 Hotfix。被新 route_history 条目替换的原末条：2026-09-07 System impl: user authorized local CC/CX 9.9.9 migration; external harness, retained sessions, safe-cache cleanup; conf=0.99。

- 追加授权：所有 agent 最大70轮；Hotfix 更新系统并推送。CC全部7角色 maxTurns=70，CX全部9角色 developer_instructions 声明最多70轮；官方配置与当前工具未提供CX同等硬限，未添加无效TOML键。到限保留进度，不自动续派绕限。参考：[CC](https://code.claude.com/docs/en/subagents#supported-frontmatter-fields)、[CX](https://learn.chatgpt.com/docs/config-file/config-reference)。
- 结果：CC/CX各新增70行 gate-contracts.md，入口从 PACE/stages 路由；九字段TDD、manifest条件、packet hash/AC集合、真实writer账本轮询与review四步顺序均对照9.9.9执行源码。保留 athena-review/SKILL.md（发现/派发）与 REVIEW.md（审查提示），职责不同，未删除。
- 验证：既有70轮配置检查先RED（缺maxTurns），修改后CC/CX副本均GREEN；9.9.9 validator 60 PASS / 0 FAIL；技能frontmatter、git diff --check通过。此结果只覆盖Hotfix与候选代码，不宣称父System全量验收完成。
- 安装：回读74个目标，62个有变化，零内容不符；~/.claude、~/.agents/skills及仍可发现的~/.codex/skills旧副本已同步。CC实际model/effort保留；其余受管角色正文更新到9.9.9合同。未改hooks、sessions或root config。
- 回退：66个既有文件逐文件备份在 /Users/mi_manchi/.athena/backups/athena-9.9.9-gate-turns-WLDntf；同目录manifest.json记录74个目标及8个新增文件。本地备份不推送。
- 推送范围：仅本Hotfix新增/修改的agent、skill、发行说明、校验与状态证据；启动前已有15个CC hook脏修改不纳入。父System/impl仍需rework；维护性Hotfix推送按用户明确授权使用已有ATHENA_ALLOW_PUSH入口，不伪切父sprint为ship。

### 追加：全部推送与安装态门禁补齐

用户再次明确“全部都推送”，取代上一段的排除范围：原有15个CC hook仓库边界修复一并提交。逐文件核对发现CC/CX delivery-gate仍为旧安装版本；其余hooks均一致。两端门禁已从9.9.9补齐，并保留CC安装态的impl状态修复放行逻辑、CX安装态的review使用repo root逻辑；两个旧文件已备份到同一回退目录的对应hooks路径。
CC状态修复回归先RED后GREEN：缺合同的impl允许修复.ai_state，源码写与Stop仍block；不放松实现门禁。源包与安装态门禁回读后再推送。SKILL.md与REVIEW.md继续保留。

最终安装回读：CC 21个、CX 17个hook全部与9.9.9源包一致；Hotfix相关技能/角色已核验。含新增状态修复回归的validator再次60 PASS / 0 FAIL。全部待提交变更按用户追加授权交付，父System的整体运行验收仍独立跟踪。

用户要求9.9.9迭代文档，三个目标均覆盖；以PACE/.ai_state为核心，单平台完整、多平台增强。当前只完成研究和文档工作，不代表发行实现或已安装升级。
基线：aa0ae23864a217002ab10610c93a3d9c22f01ecb。设计工作树：/Users/mi_manchi/workspace/Rlues-worktrees/athena-9.9.9-design，分支 codex/athena-9.9.9-design。主工作区已有的配置事件和上轮 brainstorm 改动需保留。

## 文件入口与事实

- design.md：架构、目录、迁移和14项实施验收；vm-design.md：用户VM的边界和输入/运行协议。
- execution-contracts.md：审查绑定、writer恢复、业务准入；eval-plan.md：6任务矩阵及预注册判定。
- ../../roadmap/athena-9-9-9/：6个切片，全部 pending；research.md：实际旧版冲突与一手出处。
- grok-research.md：grok-4.6 最终独立观点；两次联网调用中断，第三次基于所供证据 end_turn。只保存最终文本与必要元数据。
- VM只读观察：注册配置0600，key认证，SSH严格主机校验退出0；RHEL10.2/x86_64，docker/python3/node/git二进制存在。未做daemon或项目验证，不记录连接秘密。

## 独立设计审查

首轮run athena999_design_review，由实际 target /root/athena999_design_review 返回 REWORK：4项P1、1项P2。原文在 reviews/_native/athena999_design_review.md；当时packet在 reviews/_native/review-packet-initial.md，hash cfcfcf5e3514caa3acf85ffecbce75ba8413d1e3c9f183332aaafda9f82c6207。
修订依次补齐：VM受控输入及远端校验、审查持久绑定、writer恢复事实、预注册效率规则、全栈项目准入。复用既有状态文件，无新增执行状态机。

针对性复核已派发：

| 项 | 实际值 |
|---|---|
| review_run_id / mode | athena999_design_review_followup / design |
| reviewer_target | /root/athena999_design_review |
| packet_sha256 | 2c667b047f9ef549634ad35b5d284843efd364b60039d83cfa4e1fdaf74555a4 |
| base_commit | aa0ae23864a217002ab10610c93a3d9c22f01ecb |
| input binding | review-packet.md.input_sha256 的8项文档；packet hash 同时绑定此清单 |
| evidence scope | 纯设计与已列研究/观察；不验证9.9.9实现 |
| expected raw output | reviews/_native/athena999_design_review_followup.md |
| current result | PASS；原始返回与8项输入在接收时再次核对一致 |

## 文档核验

已通过 YAML 解析、8项输入hash、14项AC双射、6个pending切片的无环依赖检查；主设计167行、packet56行，处于既有预算内。没有运行未实现的9.9.9 validator 或把文档检查当运行时验收。
独立复核已完成，5项发现全部解决。已将完成文档合入主工作区 .ai_state 并窄幅更新索引，旧 brainstorm 以 superseded 保留。后续实现从切片1及旧版基线测量开始，本轮不自动进入实现。

最终回读通过：主目录8项输入与独立PASS所审hash一致，原生结果hash可核对，YAML/AC双射/切片依赖/索引预算和指针均有效，git diff --check通过。主目录索引10153字节，保留9.9.8运行schema；历史已入index-overflow，配置事件原有改动保留。未改发行或安装态文件，未提交或推送。

## 2026-09-06 后续用户授权

用户原话：直接把cc和cx的9.9.9版本输出出来，之后由Claude fable5.1查看。该授权取代设计时“本轮仅文档”的执行范围，当前进入发行候选实现；不代表安装态更新、推送或未测AC已完成。保留已审设计内容哈希；当前范围与进度以本追加记录及索引为准。

- writer binding: athena999_cc_package -> 01a0764d-ed7b-72d0-aaa6-af47b5b7a5c5; worktree /Users/mi_manchi/workspace/Rlues-worktrees/athena-9.9.9-design; baseline aa0ae23; write CC 9.9.9 prompt/config docs excluding hooks and installer/VM dirs; integrator main.

- writer binding: athena999_cc_writer -> 01a0764f-836c-7251-aa28-eb097e3bfa46; CC scoped docs ownership; same worktree/base; prior configured generator had no file tools and made no changes.

- writer binding: athena999_cc_native -> 01a07650-a17f-7d10-b03b-9e5d4fb0930f; CC scoped docs ownership, native default role; same worktree/base; prior worker exposed no tools, no changes.

- writer binding: athena999_cx_native -> 01a07651-b2d0-7f32-9be1-a2d124d3320d; CX scoped docs ownership; same worktree/base; main integrates.

- writer binding: athena999_state_hooks -> 01a07652-d928-79a0-b44e-b4fbc5822452; CC/CX9.9.9 hooks + pace/scripts + dedicated state/review tests; same worktree/base; main integrates.

- writer binding: athena999_vm_install -> 01a07653-9db0-7b50-a63c-7dde51848e09; both packages setup/init/migrate/vm/runtime-verify skills + dedicated tests; same worktree/base; main integrates.

## 2026-09-07 Grok 核对（未安装 9.9.9）

本机已装 Athena 9.9.8（`~/.claude` + `~/.codex`）。按用户要求：不安装 9.9.9；已装机器删除安装器备份；保留会话。已删除 `~/.athena/backups/athena-9.9.8-redeploy-*`，保留 `~/.athena/vm.json` 与 CC/CX 会话目录。

候选包核对与补全：
- Agent 去掉 `maxTurns`；stub 恢复 `disable-model-invocation`。
- `REVIEW.md` 从 `.claude/` 根目录移到 `skills/athena-review/REVIEW.md`（CC skill 目录约定）。
- 被截短的 skill 从 9.9.8 全文恢复并叠 9.9.9 增量；CX 补 `fullstack-contract`/`state-contract`。
- VM 包内自带 `templates/vm.json.example` + `references/vm.schema.json`。
- 新增 opt-in `/llm-as-a-verifier`（默认关，logprobs 排序，不是 ship 门禁）。
- 安装器永不覆盖 sessions/history；已装成功后剪除更早安装器备份。

`python3 vibeCoding/scripts/validate-athena-9.9.9.py`：56 PASS / 0 FAIL。未改安装态 9.9.8。用户要 Claude 审核后再决定安装。

## 2026-09-07 合入 Codex 核查缺陷（仍未安装）

按 completeness-audit 顺序修确定缺陷，未安装 9.9.9：
- review accept 核对原生 frontmatter 的 run/mode/packet；错声明拒绝，正文引用不误伤。
- init 探测结束后用共享锁合并最新 index，不覆盖并发 stage/正文。
- cleanup-pass 不再要求 polish 阶段删 worktree。
- Pre/Post 验证命令共用同一分类器（含 Gradle）。
- CX 安装示例改为 `--only cx`；quantum playbook 去掉退役角色与错误 adapter。
- LaaV 缺有效 logprobs / 全员无法评分时 skip，不退回离散分、不标 ranked。
- 补 `configure-vm.py` 与 SSH alias。

`python3 -B vibeCoding/scripts/validate-athena-9.9.9.py`：58 PASS / 0 FAIL。仍未跑 E1–E3 与原生 CLI 全链路。

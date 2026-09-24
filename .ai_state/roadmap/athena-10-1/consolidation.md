# 散落规划合并表 · Athena 10.1

> 2026-09-24。把 Rlues 与 quantum-agent 中所有未结的规划、提案、坑、记账逐条归入 10.1 切片（S0–S9）或明确关闭/延后。
> 去向写法：`S2` = 该切片实现；`S2·A3` = design.md 对应条目；`关闭` = 已修或被设计消解；`延后` = 不在 10.1；`只记` = 不改文件。
> 每个 S 切片的 sprint design 须引用本表中指向它的行，ship 时逐行勾掉。

## 来源清单

| 代号 | 文件 | 未结条目 |
|---|---|---|
| NV | Rlues `.ai_state/sprints/2026-09-06-athena-next-version/proposals.md` | 51 |
| BS | 同目录 `brainstorm.md`（已 superseded） | 4 个方向 |
| R999 | `roadmap/athena-9-9-9/`（status proposed，6 项 pending） | 6 |
| Q12 | `roadmap/q12-batch2-production-gaps/`（切片 5/6/9 + 记账） | 15 |
| P | `.ai_state/proposals.md` | 11 |
| HP | `.ai_state/harness-patches.md` | 1 类 |
| BR | `architecture/blockers-and-roadmap.md` | 3 |
| EX | `compound/2026-08-27-explore-athena-9-9-8-post-ship-directions.md` | 12 |
| CV | `compound/2026-07-25-explore-prompt-harness-convergence.md` | 4 |
| PI | `sprints/2026-09-13-pi-agent-9-10/`（Feature，未 ship） | 1 |
| QO | quantum-agent `.ai_state/proposals.md`「仍开表格行」 | 17 |
| QP | quantum-agent `.ai_state/proposals.md`「门禁坑」 | 11 |
| QA | quantum-agent `docs/2026-09-23-q12-acceptance/README.md` 未生效/部分 | 11 |
| NEW | 2026-09-24 本次调研与实测（refs/） | 20 |

## NV · 下版本提案（51）

| id | 一句话 | 去向 |
|---|---|---|
| NV-A1 | session-log 电报体硬预算 | S4（log.md ≤20 行） |
| NV-A2 | review 存储单源 | S3（review.json） |
| NV-A3 | ship 收口自动归档 | S4 |
| NV-A4 | 记账提交合并 | S4 + S5（宪法/pace 规则） |
| NV-A5 | 诊断样本只进 roadmap notes | S4（issues 行 + 指针） |
| NV-B1 | 路由简报漏 path，`_index.path` 与 slug 一致性 | S4（`athena sprint start` 自动写 path，消解） |
| NV-B2 | 外部写者 Bugfix 缺三件套 | S4 + S5（Bugfix 三段式 design 取代三件套；grok-exec 简报） |
| NV-B3 | packet 验收标题只认五个字面，报错不列合法集 | S2（解析器报错列出全部合法形态） |
| NV-B4 | pre-bash-guard 误拦跨仓 push | S0·AC1 |
| NV-B5 | `cat` alias heredoc 写出 0 字节 | S5（rules 一行）+ S2·H5 warn |
| NV-B6 | compose 缺省 tag 删后须显式传镜像变量 | S5（athena-vm） |
| NV-B7 | 子 agent 署名按子会话规则 | S5（派工模板） |
| NV-C1 | bind 拒绝无逐文件归因 | S3·AC2 |
| NV-C2 | review 窗口内并行写者（含文档）导致 bind 恒拒 | S3（绑定源码树 sha，冲突即显式重审）+ S5（宪法：review 窗口内并行写者用隔离工作区） |
| NV-C3 | Bugfix 分诊同步三件套路径 | S4 + S5（三段式） |
| NV-C4 | grok 把 tdd-evidence 写到仓库根 | S5（grok-exec）；S2 证据改主仓 `.runtime` 后消解 |
| NV-C5 | grok 402 余额耗尽即停派 | S5 |
| NV-C6 | grok 模型核名用 `grok models` | S5 |
| NV-C7 | `--output-format json` 取最后一个顶层对象 | S5 |
| NV-C8 | 外部写者接回顺序（建 sprint → cherry-pick → 复跑） | S5 + S4 |
| NV-C9 | 派工不带 `model:` | S5 |
| NV-C10 | reviewer 模板删 run id / frontmatter | S3·AC3 |
| NV-C11 | 禁占位时戳 | S3（CLI 盖时戳） |
| NV-C12 | accept 自动落盘，SKILL 仍写「转录」 | S3 |
| NV-C13 | `design_changed_after_impl` 在同轮 design+impl 误触发 | S0·AC2 |
| NV-C14 | `features_count` 误计 | S4（删 counts） |
| NV-C15 | 承诺闭合句式误报 | S0·AC3（10.1 降为 S2·A4） |
| NV-C16 | 转录类事实断言须带核对出处 | S5（宪法「转述写出处」）+ S3（packet `transcribed_claims`） |
| NV-C17 | stage 切 ship 必须是最后一次写入 | S4（CLI 原子迁移）+ S5（stages.yaml order_note） |
| NV-C18 | 无 pipefail 记 unknown | 关闭（`athena run`） |
| NV-C19 | packet 标题/frontmatter 重绑/AC 锚定 | 只记（S2 保留 AC 锚定并在模板示例写明） |
| NV-C20 | `cat`→`bat` alias；macOS 无 `timeout` | S5（rules） |
| NV-C21 | `_index` 键归属不清 | S4（v2：CLI 唯一写者） |
| NV-D1 | 单一现行队列 queue.md | S4 |
| NV-D2 | ship 自动归档带保留窗 | S4 |
| NV-D3 | 归档前运行时读取检查 | S4·AC3 |
| NV-D4 | gitignored 证据随归档 | S4 + S2（证据改 `.runtime`） |
| NV-D5 | 台账清账即移出 | S4（issues 月结） |
| NV-D6 | 取代双向标注 | S4（decision 模板）+ S2·A6 |
| NV-D7 | pointer/锚点存在性校验 | S2·A6 |
| NV-D8 | 梳理触发阈值 | S2·A7 + S4·AC5 |
| NV-D9 | counts 口径 | S4（删） |
| NV-D10 | 历史不批量 sed | S4（迁移规则） |
| NV-D11 | deps-check 全组件清单 | S5 |
| NV-D12 | 依赖来源标注 | S5 |
| NV-D13 | TS7 工具 API 面 | 只记 |
| NV-D14 | SDK 升级私有契约复核清单 | S5（deps-check） |
| NV-D15 | 卸 Node 后 hook 全失效 | S6（`/usr/bin/env node` + doctor） |
| NV-D16 | `!` 前缀无 TTY、sudo 读不到密码 | S5（rules） |
| NV-D17 | 厂商 apt 源优先级 | S5（athena-vm doctor） |
| NV-D18 | 本机 Node/Python 单一版本铁令 | S5（deps-check 末步） |

## BS · brainstorm（superseded）

| id | 方向 | 去向 |
|---|---|---|
| BS-A | 共源与平台适配、可重建发行 | S1 + S6 |
| BS-B | 复杂任务依赖、写集、整合、跨端恢复 | S4（items `depends_on`/`write_set`）+ S3/S7（CC workflow 波次） |
| BS-C | 全栈垂直切片 | 延后（10.1 发布后在 quantum 真实需求上做） |
| BS-D | 代表性行为评测 | S8 |

## R999 · 9.9.9 roadmap（6 项 pending）

| id | 切片（AC） | 去向 |
|---|---|---|
| R999-1 | pace-contract-convergence（AC3/7） | S1·AC5（stages.yaml 单一真相）+ S5 |
| R999-2 | state-recovery-and-evidence（AC4/5/6） | S2·AC5（tree-sha 证据有效性）+ S4 |
| R999-3 | single-platform-and-parallel（AC1/2/5/8/14） | S2（三端适配器各自完整）+ S4（写集）+ S7（能力探测） |
| R999-4 | vm-runtime-contract（AC9/10） | 延后（athena-vm 维持；issue `env` 类跟踪） |
| R999-5 | fullstack-business-slice（AC11） | 延后（同 BS-C） |
| R999-6 | migration-and-behavior-evals（AC12/13/14） | S6 + S8 |

## Q12 · 批二剩余与记账

| id | 条目 | 去向 |
|---|---|---|
| Q12-5 | 切片 5 writer-provenance | 代码已合入 main（`08d7400..68b26f9`）；S2·AC7 以 A1 提示保留，S2 review 覆盖 |
| Q12-6 | 切片 6 ship 会话退出与架构已审范围（#11/#17） | S2（只读 Stop 放行；A3 基线锚定） |
| Q12-9 | 切片 9 平台适用性同步与发行回归 | S1 + S6 |
| Q12-N1 | `_shell-lex` 不在 `REQUIRED_ASSETS` | S6·AC4 |
| Q12-N2 | ship 架构检查变更集失真（P17） | S2·A3 |
| Q12-N3 | CC/CX guard 危险清单差异 | S2·H5（三端取并集） |
| Q12-N4 | guard 两端 401/406 行超规模 | S2·AC8 |
| Q12-N5 | Pi runtime-verify playbook 悬空引用 | S5 |
| Q12-N6 | CX evidence-collector 独有脱敏正则 | S2（§8 合并） |
| Q12-N7 | `init-platforms.py` 用 `'.claude' in parts` 判端 | S0·AC5 |
| Q12-N8 | 切片 7 复核：引号包裹 shape、设计措辞 | S2（fixture） |
| Q12-N9 | 反引号 AC 标签静默剔除 | S2（解析诊断） |
| Q12-N10 | packet 有小节 0 条目诊断不对称 | S3 |
| Q12-N11 | 熔断 reason_sha1 含可变数据不升级 | S2（§5.6 归一化） |
| Q12-N12 | 切片 3 遗留：导出 `tryRepoRoot/findAiState`，消除 governance 解析复写 | S2（`lib/context`） |

## P · Rlues proposals

| id | 条目 | 去向 |
|---|---|---|
| P1–P4 | token-usage 白名单、generator 生命周期、cwd 解析、polish 隔离 | 关闭（2026-07-25 已修） |
| P8 | 截断导致 SubagentStop 缺失 | 关闭（D1：写者链降为提示） |
| P9 | 红区 + 仓库外改动 worktree 死锁 | S2·§5.5（带过期豁免 `harness_target_outside_repo`） |
| P10 | critic 轮次字面计数 | S2（删除该检查） |
| P11 | 机器契约双写 | S1·AC5 |
| P12 | 派工时序无机械强制 | S3（CC workflow 固化顺序）；不做硬门 |
| P13a | 台账补写触发 review 漂移 | S3（树 sha 排除 `.ai_state`）+ S6（台账退役） |
| P13b | 破坏性清理命令被执行器拒绝 | S2·H5 复核危险表（平台行为，只记原因） |
| P14 | 审「未提交增量」的 reviewer 被 worktree 检查拦 | S2·H4（写面声明豁免） |
| P15/P16 | spill 竞态、零溢出空写 | 关闭（Q12 切片 1） |
| P17 | ship 架构检查看不见已提交改动 | S2·A3 |

## HP · harness-patches 台账

| id | 条目 | 去向 |
|---|---|---|
| HP-* | W1–W40 安装态补丁与复核命令 | 内容已在 9.9.9 源；S6 以 manifest + doctor 取代台账；S9 归档 |

## BR · blockers-and-roadmap

| id | 条目 | 去向 |
|---|---|---|
| BR-P5 | frontmatter 解析共享库 | S2（`lib/frontmatter`） |
| BR-skip | `skip_impl_subagent_check` sprint 级粒度 | S2（豁免 + 过期） |
| BR-P4 | G4 门禁产物级校验 | 关闭（quantum-codegen 自校验承担） |

## EX · 9.9.8 post-ship 方向

| id | 条目 | 去向 |
|---|---|---|
| EX-1 | role-labeled telemetry | 关闭（已作废） |
| EX-2 | 证据引用存在性校验 | S2·A6 |
| EX-3 | CX git 失败空树哈希（F9） | 关闭（S2 删除 py 实现；JS 核 git 失败 fail-closed） |
| EX-4 | hook 松紧数据化 | S8·AC4（issues 中 gate 行统计） |
| EX-5 | 产物回读率观察 | 关闭（改为直接把 sprint 文件从 15 降到 4） |
| EX-6 | rules 疤痕退役机制 | S5·AC2（溯源表 + Kirby） |
| EX-7 | 轻路径仪式归零 | S2 + S4（Hotfix 只剩 H2 与 git；Quick 最小 design） |
| EX-8 | 自建遥测整体拆除 | S2·AC9（确认 token-usage-collector 不再分发） |
| EX-9 | 三家族分工可选门禁字段 | S2·A10 + S3（`reviewer.family`） |
| EX-10 | harness eval 套件 | S8 |
| EX-11 | Bugfix 复现测试保护 | S2·A9（flag，提示级） |
| EX-12 | spill 竞态 / 零溢出写 | 关闭（Q12 切片 1） |

## CV · prompt harness convergence

| id | 条目 | 去向 |
|---|---|---|
| CV-1 | 共享契约 + CC/CX 适配器 | S1 + S2 |
| CV-2 | skill catalog ≤6,500 字符 | S5·AC3 |
| CV-3 | `_index` ≤4 KiB | S4（≤3 KB） |
| CV-4 | prompt A/B 评测 | S8 |

## PI · Pi 9.10 Feature

| id | 条目 | 去向 |
|---|---|---|
| PI-1 | Pi 端全结构迁移（未 ship，README 路径漂移） | S0·AC4（路径）+ S7（0.87 适配）；原 sprint S9 归档 |

## QO · quantum 仍开表格行（17）

| id | 日期 · 条目 | 去向 |
|---|---|---|
| QO-1 | 09-08 CC 跨 sprint 绑定拒收（tracker 归属） | S2·A1（D1） |
| QO-2 | 09-08 collector tool result 形状 / workdir | 关闭（Q12 批一生效；`athena run` 取代） |
| QO-3 | 09-08 worktree Start 误报 | S2·H4 |
| QO-4 | 09-09 guard 误拦 quoted heredoc | S0·AC1 + S2·H5 |
| QO-5 | 09-09 worktree audit 误报合法 linked worktree | S2·H4（校验 git-dir 与 common-dir） |
| QO-6 | 09-10 delivery-gate 主模块 exports 缺失 | 关闭（S2 重写为模块化） |
| QO-7 | 09-10 spill 指针丢 sprint 路径 | 关闭（Q12 #9 生效） |
| QO-8 | 09-11 worktree 写者被主仓 `_index` 误判 | S2（`lib/context`：状态以主仓为准，worktree 写入按主仓 sprint 判定；fixture） |
| QO-9 | 09-11 证据随 worktree 回收丢失 | S2·§8（写主仓 `.runtime`） |
| QO-10 | 09-11 ship 阶段纯注释 Quick 被拦 Edit | 关闭（S2：ship 检查只在 stop/`athena ship` 触发） |
| QO-11 | 09-12 runtime-run 秘密正则误排 | 关闭（Q12 #12 生效） |
| QO-12 | 09-12 index-updater 只扫 sprints 计数归零 | S4（删 counts） |
| QO-13 | 09-13 继承 ship stage 拦只读会话 Stop | S2（Q12 #17） |
| QO-14 | 09-13 凭据分类器拒绝时挂起 | 只记（CC 平台行为） |
| QO-15 | 09-14 review-binding 绑 cleanup-pass 为 evidence_docs | S3（树 sha 排除 `.ai_state`） |
| QO-16 | 09-15 tdd-evidence 形状校验空转 | S2（删除该校验；证据并入 evidence） |
| QO-17 | 09-15 prepare 把 session-log 列为输入必然自毁 | S3（无输入清单） |

## QP · quantum 门禁坑（11）

| id | 条目 | 去向 |
|---|---|---|
| QP-1 | 改完 findings 后 bind 恒拒 | S3（无 bind） |
| QP-2 | dispatch/result 回执 schema 不同 | S3（无回执） |
| QP-3 | 采集器只认特定命令形态 | S2·§8（`athena run`） |
| QP-5 | 每个 run 要全新 reviewer | S3（不再机械要求） |
| QP-6 | tracker assign 要求新 SubagentStart | S2（D1） |
| QP-7 | 老 System sprint 别走 ship | S4（暂停/归档语义） |
| QP-8 | bind 只收 UUID | S3（`--run latest`） |
| QP-9 | result.json 必含三字段 | S3（CLI 生成） |
| QP-10 | 90 轮上限续派不入账 | S2（D1）+ S5（续派用 SendMessage，不影响门禁） |
| QP-11 | AC 行首锚定口径 | S2（保留）+ S5（模板示例） |
| QP-cat | `cat` alias heredoc 0 字节 | 同 NV-B5 |

## QA · Q12 验收未生效/部分（11）

| id | 条目 | 去向 |
|---|---|---|
| QA-7 / QA-21 | 外部写者回执、tracker 跨 sprint 归属 | 已合入 main；S2·A1 |
| QA-17 | R/S 架构检查看已审范围 | S2·A3 |
| QA-20 | 归档计数语义 | S4（删 counts） |
| QA-22 | 只读会话 Stop | S2 |
| QA-25 | stages.md 写明记账先于 review | S5（`stages.yaml` order_note） |
| QA-26 | 转录断言带核对出处 | S5 + S3 |
| QA-27 | 承诺闭合调参 | S0·AC3 |
| QA-29 | 跨仓推送 / heredoc 推送字样误拦 | S0·AC1 |
| QA-30 | design_changed_after_impl 误触发 | S0·AC2 |
| QA-31 | features_count 误计 | S4（删 counts） |

## NEW · 本次调研与实测（20）

| id | 条目 | 去向 |
|---|---|---|
| NEW-1 | 5 个未注册死 hook（pace-continuator×2、compact-snapshot×2、subagent-retry.py） | S2·AC9 |
| NEW-2 | 宪法「CC 无原生 `/goal`」与 CC 2.1.269+ 冲突 | S0·AC4 |
| NEW-3 | CC 2.1.277 读 AGENTS.md | S1（三端同源宪法；仍生成 CLAUDE.md） |
| NEW-4 | CC `omitClaudeMd` | S5·AC4 |
| NEW-5 | CC 动态 workflow / Tasks | S3·AC5、S7（flag） |
| NEW-6 | CC `claude plugin eval` | S8（插件化分发为 COULD，探测后定） |
| NEW-7 | CX 0.156 worktree 默认开启 | S7·AC2 |
| NEW-8 | Pi 0.87 `turn_end`/`agent_before_settle` 可续跑、`shouldStopAfterTurn` 删除 | S7·AC1 |
| NEW-9 | Pi 包名迁 `@earendil-works`，peer `*` | S0·AC4 |
| NEW-10 | Grok Build 声称 AGENTS.md/skills/hooks 兼容 | S7·AC2（探测）/ D6 |
| NEW-11 | Opus 5.5 / GPT-6 提示词指南（删思考指令、情境化、完成标准驱动） | S5·AC2 |
| NEW-12 | `.snapshots/config-events.jsonl` 每会话改动且入库 | S4·AC6 |
| NEW-13 | Rlues `.runtime` 35 MB（q12 输入包 3×12 MB） | S9·步 3（删除需确认） |
| NEW-14 | 两仓 `_index` 平台版本过期且不一致 | S2/S4（`.runtime/probe.json`） |
| NEW-15 | quantum `harness_target_outside_repo: true` 自 09-10 常开 | S2·§5.5 + S9·步 6 |
| NEW-16 | quantum 冷层 21.9 MB 入库 | S4（月度打包） |
| NEW-17 | 每 sprint ~15 过程文件 | S4 |
| NEW-18 | 只改 `.ai_state` 的提交 46.5%（quantum）/ 62%（Rlues） | S4 + S5 |
| NEW-19 | Cowork 设备 VM Python 3.10 与 `datetime.UTC` 不兼容；测试缺 git 身份 | roadmap §5；S2 删除 py hooks 后消失 |
| NEW-20 | harness-iteration skill 过于保守 | v2.0 提案卡（用户保存）；S5 引用 |

## 统计（脚本计数）

共 166 条。一条可指向多个切片，按出现次数计。

| 去向 | 次数 |
|---|---|
| S0 | 11 |
| S1 | 6 |
| S2 | 56 |
| S3 | 21 |
| S4 | 34 |
| S5 | 34 |
| S6 | 7 |
| S7 | 7 |
| S8 | 6 |
| S9 | 4 |
| 关闭 | 14 |
| 延后 | 3 |
| 只记 | 4 |

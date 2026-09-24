---
mode: completeness-audit
checked_commit: aeb1da6a821d313c0e23d877cf69f848f932004c
date: 2026-09-07
result: gaps-found
host_installation: not-performed
formal_release_acceptance: incomplete
---
# Grok 更新后 9.9.9 完整性核查

结论：两端发行资产能独立首装，但当前合同和承重代码仍有确定缺陷，不能宣称完整验收完成。此次只检查，未修改发行源码、安装真实HOME、删除备份或再次push。远端main已核对与上述commit一致。旧工作树不作为覆盖主分支的来源。

## 已直接验证

| 检查 | 结果 | 边界 |
|---|---|---|
| 当前整包validator | 56 PASS / 0 FAIL | 内含17+18+4=39个行为测试；不覆盖下列新增反例 |
| CC独立发行包首装 | 成功 | 临时HOME、仅复制CC包、无9.9.8源码；143个hooks/agents/skills/rules文件内容一致 |
| CX独立发行包首装 | 成功 | 临时HOME、仅复制CX包、无9.9.8源码；145个hooks/agents/skills/standards文件内容一致 |
| 已安装路径上的init | 两端成功 | 仅选本端，未用另一端发行资产补齐 |
| SessionStart/面包屑 | 两端实际脚本成功 | 使用各自配置中的真实入口；不是完整CLI模型会话验收 |
| 历史保护 | 两端模拟历史均保留 | 测试fixture包含history、projects和sessions；没有触及真实会话 |
| 27项skill/REVIEW/VM资产 | 存在 | CC REVIEW已在athena-review目录；schema/example与LaaV脚本已入包 |
| agent轮数配置 | 未发现maxTurns/max_turns/max-turns | 仍有文档层面的固定轮数残留，见下 |

这些检查支持“包内资产可独立安装”。它们不证明完整CC-only/CX-only模型任务、原生review/Stop/worktree、真实业务或效率已通过。

## 应先修正的确定问题

| 优先级 | 触发与影响 | 当前源码位置（相对仓库根） |
|---|---|---|
| P1 | 原生结果明确声明错误run/mode/packet仍被accept包装成当前PASS；错误审查范围可成为通过依据 | `vibeCoding/codex/9.9.9/.codex/hooks/_review_binding.py:153`；CC对应`_review-binding.cjs:105` |
| P1 | init探测CLI期间另一写者更新stage，初始化随后用旧全文覆盖，使review退回impl并丢掉新增正文 | 两端`skills/athena-init/scripts/init-platforms.py:98`至109 |
| P1 | polish模板要求merge/PR/丢弃及删除worktree，再把finishing作为PASS条件，发生在最终review之前 | 两端`skills/pace/templates/sprints/cleanup-pass.md:36`、59；还引用旧pass文件 |
| P2 | Pre/Post验证命令分类不一致，Gradle等已支持验证被记为unverifiable | CC`hooks/_input-binding.cjs:8`及两端collector对应分类 |
| P2 | CX首装两条示例硬写`--only cc`，照抄会装错端或找不到CC包 | CX`skills/athena-setup/SKILL.md:14` |
| P2 | DB/unit读取不存在的quantum-backend-adapter.md；实际是db/test两个adapter | 两端`skills/quantum-codegen/references/{db,unit}-playbook.md:31` |
| P2 | page/e2e/db仍调spec-compliance，security仍调evaluator；已退役角色重新成为流程消费者 | 两端quantum-codegen对应playbook第57/58行 |
| P2 | init旧正文无条件探测另一端；CX polish仍要求CC机制；CC hook文档仍公开固定critique轮数 | 两端init playbook第26/32行；CX polish playbook第13行；CC pace/references/hooks.md第41/46行 |
| P2 | LaaV缺少有效候选logprob分布时退回离散整数；全部候选都不可评分仍返回ranked | 两端`skills/llm-as-a-verifier/scripts/rank.py:97`、173至188 |

前三个旧代码问题中的review/init/classifier修复及回归曾留在旧工作树，未进入当前main。此次没有直接复制修复，而是将既有反例定向到当前main执行：3个测试方法、24个失败子例、0个执行错误。24是失败输入分支数，不是24个独立缺陷。
LaaV另做了纯离线复现，无API调用：没有top_logprobs时返回12.0；20拆成两个token时退回20.0；两个候选都无有效分数时仍是`status: ranked`且scores均为null。校准前还应先解决这些确定性问题。

## 对 Grok 优化建议的核对

1. **AC13未执行：属实。** eval-plan.md仍为not-run。E1–E3每端3组旧/新配对，共18次；双端共36次运行。先固定输入和条件，修复已知质量问题，再投入这些比较，不宣称已省token。
2. **热路径要测：赞成，已做第一轮字节测量。** 完整包不意味着每轮全读；这符合CC/CX的按需加载机制。实际数据见下表。
3. **双端最小共享：合理，排在当前缺陷之后。** 先用同一行为预期约束两个原生实现，再考虑纯schema/合同/安装事务的最小共享；不因去重让CC日常hook依赖CX运行时，也不做全量编译框架。
4. **候选push与正式ship：应明确区分。** 将用户明确授权、目标分支、候选文件和待推commit绑定到既有授权机制；不泛化为stage=impl任意push，不用Python绕过hook。未完成的发行验收保持未完成。
5. **AC14缺实际平台链路：属实。** 此次执行了hook脚本和首装，并未把它们冒充当前CLI原生review/隔离/等待闭环。
6. **VM“只有SSH通”需修正。** 昨天local与RHEL的HTTP+SQLite四步及清理均已成功，证据留在旧工作树，当前两端runner hash与该证据绑定完全一致。当前doctor也已经有checked_at（runtime-run.py:450）。缺口主要是证据未整合、注册产品体验与完整项目验收；这些smoke不能替代FE/BE/DB真实业务。
7. **LaaV应默认关闭且先校准：赞成。** 当前还需先修评分计算。上游采用A–T字母刻度处理token logprob，当前整数实现不是无差别移植；缺后端能力保持skip，校准前仅观察，不能承接交付门禁。

## 热路径实测（单独发行包、全新项目fixture）

| UTF-8字节 | CC | CX |
|---|---:|---:|
| 初始化后的完整_index文件 | 6449 | 7518 |
| SessionStart实际注入context | 1384 | 1347 |
| System/impl面包屑实际context | 214 | 150 |
| pace/SKILL.md完整文件 | 5548 | 5721 |
| compound/SKILL.md完整文件 | 4468 | 4468 |

两端pace和compound均超过既有4KiB skill热路径目标。这里测的是文件与实际hook输出字节；不把三者简单相加当作每轮必然开销，也不冒充模型token或性能结论。不同stage/项目须另测；详细playbook仍按需读取。

## 验证与后续入口

- 当前包检查：`python3 -B vibeCoding/scripts/validate-athena-9.9.9.py`；本轮日志`/tmp/athena999-grok-audit-validator.log`。
- 首装/实际hook测量：`/tmp/audit_grok999_fresh.py`；结果`/tmp/athena999-grok-fresh-results.json`。
- 三项漏合入缺陷：`/tmp/audit_grok999_regressions.py`；结果`/tmp/athena999-grok-missing-regressions.log`。该脚本复用旧工作树的反例，但被测代码显式指向当前main。
- LaaV离线结果：`/tmp/athena999-grok-laav-offline.json`；没有网络请求或真实API key。
- VM历史证据：旧工作树`/Users/mi_manchi/workspace/Rlues-worktrees/athena-9.9.9-design/.ai_state/sprints/2026-09-06-athena-9-9-9/runtime-results/`；runner SHA256为`d4f39b8997be7cdb58728182eee4b13ce1aac16782aa3e109452549d582dce29`。
- 文档/完整性另由只读原生agent `/root/audit_grok999_completeness`检查；最终列出的具体缺陷已归并于上表。

建议保持9.9.9：先合入最小可靠性修复并清除旧流程正文，再做针对性review；然后冻结E1–E3及平台原生任务，并将可复用VM证据整合进当前sprint。安装继续等待用户指定的Claude审核。

依据：[CC supporting files](https://code.claude.com/docs/en/skills#add-supporting-files)、[Codex skill按需加载](https://learn.chatgpt.com/docs/build-skills)、[LaaV上游实现](https://github.com/llm-as-a-verifier/llm-as-a-verifier)。

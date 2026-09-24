---
doc_type: explore
slug: "athena-9-9-8-post-ship-directions"
created: "2026-08-27"
sprint_slug: "2026-08-27-athena-9-9-8"
status: "open"
topic: "9.9.8 ship 后整体复盘：后续 hotfix / 9.9.9+ 的方向要点"
researcher: "主 agent (claude-fable-5) 复盘 + 用户四问 (ai_state 啰嗦? hooks 严? 提示词重? 流程可优化?)"
---

# Explore: athena-9-9-8-post-ship-directions

## 问题 (question)

9.9.8 (Thin PACE Control Plane) 已 ship。用户计划在其上推多个 hotfix/后续版本，需要一份可回读的方向清单：哪些残留要修、哪些结构性方向值得投入、判断依据是什么。

## 方法 (method)

- Read: design.md rev2 全文、review 链 (design-review CONCERNS → impl CONCERNS F1–F8 → rework PASS)、cleanup-pass、runtime-verify、eval-ac11、architecture/athena-9.9.8.md、CHANGELOG、两个 ship commit 的 diff stat
- 对照用户四个反问逐项评估；结论按优先级排序

## 发现 (findings)

**主轴判断：9.9.8 把"删仪式"走到了合理终点，再删会伤边界。下一阶段的杠杆是从"每版手工审计驱动"切换到"自家数据驱动"——ledger/telemetry 基础设施本版已铺好，但标签精度与回读统计还不足以支撑决策。**

按优先级：

1. ~~role-labeled telemetry~~ **已作废** (2026-08-27 用户拍板本地遥测整体退役, 见 decision `retire-local-telemetry-collection`)。度量工具改为代表性任务 eval 套件 + CC `/usage` per-loop 读数，见第 10 条。
2. **证据引用存在性校验**: F10 (packet 引的首次备份路径已不在) 暴露"被引用证据无人校验存在性"。gate 已对 native_output_ref 校验，应推广到 backup ref / baseline / evidence 路径。**更正 (2026-08-27 tidy 复核)**: baseline-9.9.6-tokens.json 实测存在且 inventory 4/4 sha256 匹配，早前"已消失"系误读；但其 4 个 path 因 sprint 归档现需 `sprints/archive/2026/` 前缀才可解析——冻结文件不改，校验器应做归档路径宽容，这正是本条要治的类别。
3. **F9 双端 fail-closed 不对称**: CX `list_source_files` 在 git 失败时返回 `[]` → 哈希出空树 e3b0c442… 而非像 CC 返回 "" fail-close。ship 时 git 故障会产生"合法但错误"的 diff hash。hotfix 级，改动一行语义。
4. **hook 松紧数据化**: 9.9.8 已做完红黄绿收敛，剩余问题不是"严"而是 parser 军备竞赛 (``rm -rf `echo /` `` 双端拦不住已是承认极限) 与维护税。stop-failures.jsonl / gate block 率 ledger 已在——用实测 block 率与误报率决定 parser 收缩到"红区清单+窄白名单"还是维持，不再凭感觉加减规则。
5. **产物回读率观察窗 (回应"ai_state 啰嗦?")**: 索引层已有界不啰嗦；啰嗦在 sprint 产物层——9.9.8 sprint 落 15 个文件，但没有任何一类产物的"被后续会话回读次数"统计。给产物记回读率，2–3 个 sprint 零回读的 (候选: session-log、deployment、version-pin) 降为可选。9.9.3 的观察窗思路扩展到产物文件。
6. **rules 疤痕退役机制 (回应"提示词重?")**: 常驻面 9.9.6 已压到位；现在最重的是 rules/ 五件套里持续累积的踩坑疤痕条目 (backfill 记法、量化 AC 记法、可达性检索式)。铁律有溯源表+候选评估，rules 没有——同一机制扩展过去：N 个 sprint 未再命中其防的失败类别 → 降级 references 冷路径。
7. **轻路径仪式归零**: Quick/Bugfix/Hotfix 理想态只剩 gate + git，不留文件税。依赖 5 的回读数据授权。
8. **自建遥测整体拆除 (从"降级"升格, 用户拍板)**: 双端 token-usage-collector (~950 行) 与 tool-trace 写入注册整体退役，PostToolUse 记账面随之收窄；`.gitignore` 遥测段与 `.runtime/` retention 简化。AC 不得再写依赖自建账本的量化门槛。见 decision `retire-local-telemetry-collection`。
9. **三家族分工升级为可选门禁字段**: 本 sprint 实测 Grok 主刀 / Codex 修订 / Claude 独立挑战链条有效 (CONCERNS→定向返工→PASS，抓出 untracked 树对 gate 隐形的真洞)。"reviewer 与 author 不同家族"目前只是偏好，可做成 `_index` 可选字段供 gate 校验。

以下两条借自 Anthropic AI-native SDLC playbook (2026-08-27 对照评估，设计 rev2 已引用该文):

10. **harness eval 套件 (playbook "CI 持续 evals" play, 替代遥测度量)**: 10–20 个真实历史任务 + 可接受结果判据，CLAUDE.md/skill/hook/模型变更时重跑；每次 gate 逃逸/回归沉淀为永久 fixture (现有 validator fixture 实践的显式化)。这是遥测退役后唯一的质量回归度量工具，也补上 9.9.6 起"无 A/B eval"的已知缺口。
11. **Bugfix 复现测试保护 hook (playbook "先自验" play)**: Bugfix 路径先提交失败复现测试，hook 禁止修复会话再改该测试文件——"修复前就存在、且智能体无法改写的测试，才是修复证据"。确定性、改动面小、堵真实漏洞 (改测试凑绿)，与 tdd-evidence 互补。

12. **2026-08-27 tidy/复核现场实测的新 hotfix 候选**: (a) `_index-bounds` 溢出搬运竞态——spill 文件不在 `_index-io` 锁内，rh-0..3 全文曾静默丢失 (已从 git 历史修复)；(b) `flush()` 零溢出也无条件写，sprint 为空时在 .ai_state 根反复重建空 stub；(c) `subagent-worktree-check` 对"写面仅 .ai_state 的 reviewer"一刀切要求 worktree，而 worktree 检出 HEAD 看不到待审的未提交增量——fallback reviewer 路径在 System path 下结构性死锁，需类比 `harness_target_outside_repo` 的豁免；(d) 9.9.8 发行模板漂移: templates/_index 仍标 version 9.9.6、next_action 注释缺 await-review-result、缺 harness_target_outside_repo 字段。

## 证据 (evidence)

- 残留 F9/F10: `sprints/2026-08-27-athena-9-9-8/reviews/implementation-review.md` (rework PASS, P2×2)
- AC11 标签残留: `sprints/2026-08-27-athena-9-9-8/eval-ac11.md` Verdict 节 ("mixed opus turns … stay non-control")
- baseline 存续更正: tidy 复核 `.runtime/baseline/baseline-9.9.6-tokens.json` 存在、4/4 sha256 匹配；4 个 inventory path 因归档需 archive/2026/ 前缀 (路径漂移, 非丢失)
- parser 极限: 9.9.6 CHANGELOG "已知共有限制"；红黄绿收敛见 design.md "Hook 严格度" 节
- 产物计数: 9.9.8 sprint 目录 15 文件 (ls 实测)
- 遥测降级依据: design.md rev2 F8 (CC 2.1.243 /usage per-loop、OTEL)

## 建议 (recommendation)

- hotfix 排序 (2026-08-27 修订): 先 3 (F9, 一行级) 与 11 (测试保护 hook, 小而确定)；再 8 (遥测拆除, 删代码为主) 与 2 的 gate 扩展 (引用存在性)；10 (eval 套件) 在 8 之前或同批落地，避免出现无度量窗口期。
- 4/5/6 不急于改规则本身，先让 ledger/回读统计跑 2–3 个 sprint 攒数据，再按数据裁剪——避免重蹈"用更多 prompt 治理 prompt"。
- 9 可与任一 hotfix 顺路落地 (加字段+gate 读取，改动面小)。
- SDLC playbook 其余 play (managed settings / CI/CD claude -p / Claude Tag / 生产 σ 监控) 对单人本地 harness 不适用，显式不采纳，防止长成第二控制面。

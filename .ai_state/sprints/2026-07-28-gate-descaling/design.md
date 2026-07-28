# Gate Descaling — 反文书化改造 (2026-07-28)

> System 级 harness 改动。用户拍板"直接修改, 避免纸面操作, 文档保存齐全"。
> R1+R2 合并单文档 (harness-iteration v1.1 规模分级; 反驳痕迹见 §4)。
> 执行方: Cowork 会话 (repo 外编辑, 不经本 harness 门禁)。

## 1. 病灶 (实测, 非推断)

- tool-trace 实测: 9.9.6 主 sprint 写入操作 `.ai_state` 记账 102 次 vs 代码 15 次 (**8.4%**); 记账写入 > 全部交付写入之和 (70)
- proposals.md P1-P13 中 **9 条是门禁误伤合法工作的死锁台账** (P1/P2/P3/P4/P9×2/P12/P13/P6); 每次解锁靠用户拍板豁免 (route_history ≥4 次)
- 结构病根: 摩擦梯度倒挂 (写代码过 subagent+worktree+lifecycle 链; 写 .ai_state 零门槛) + 门禁验文档存在性而非代码行为

## 2. 原则

门禁从「文档存在」转向「行为证据」; 摩擦梯度反转 (写代码 ≤ 写文档)。
**判定链一条不砍**: VERDICT PASS / TDD red→green / design_changed_after_impl / spec-gate AC 全保留。砍的是文档的数量、体积、必钉集。

## 3. 改动清单 (MUST, 全部已实施)

| # | 改动 | 文件 (CC ‖ CX) |
|---|---|---|
| M1 | 绿区扩容: 单文件≤30行 → **≤3 文件且合计≤150行, 或 Hotfix/Quick/Bugfix** 主 agent 直做 | CLAUDE.md 铁律[零写入] ‖ AGENTS.md; pace SKILL + stages |
| M2 | **P9 根治**: `_index.harness_target_outside_repo: true` → worktree 强制豁免 (repo 外零隔离效果), stderr 提示备份纪律 | subagent-worktree-check.cjs ‖ subagent-worktree-audit.py |
| M3 | manifest 必钉集收缩: core `[design]`; R/S 另加 `runtime-verify.md` (原 6 项)。声明即验语义不变 | delivery-gate.cjs ‖ .py `MANIFEST_REQUIRED_*` |
| M4 | checklist.yaml 可选 (存在才验全绿); done_contract 并入 design.md `## Done Contract` | delivery-gate ×2; stages.md ×2 |
| M5 | **P10 修复**: critic 轮数计数锚定 `^#{2,3}\s.*Critic Findings` 标题行, 正文提及不计数 | delivery-gate ×2 `validateCriticRounds` |
| M6 | critic min 轮数默认全路径 1 (原 R/S=2); `plan_critique_min_rounds` 可调高 | 同上 |
| M7 | 文书预算警告 (不 block): design.md >300 行 stderr 提示 (目标 System ≤200 / Feature ≤80) | 同上 |
| M8 | **P13 修复**: `.ai_state/harness-patches.md` + `proposals.md` 入 post-review drift 白名单 (过程台账非被审对象); light-ship 护栏不动 | delivery-gate ×2 `allowedExact` |
| M9 | 铁律[Hook 是进化器] 降频: 仅门禁 block 或用户纠偏时写 proposals, 不逐 Stop 反思 | CLAUDE.md ‖ AGENTS.md |
| M10 | 文书白名单 + route-note 降可选 (并入 route_history 一行) + critic/passN 产物格式极简 (禁评分表/散文/复述) | stages.md ×2; critic.md ‖ critic.toml |
| M11 | 副本同步: CC `hooks/delivery-gate.cjs` (曾落后 .claude 版) 与 CX `.codex/hooks/delivery-gate.py` (曾落后 root 版) 均以编辑后 canonical 覆盖, 消除 P5 类漂移 | 2 文件 |

## 4. 反驳痕迹 (R2, 逐条挂反例后保留/修形)

| 提案 | 反驳 | 处置 |
|---|---|---|
| design.md 行数硬 block | 会当场卡死现有 52KB design, 复刻 P 系列死锁 | 改 warn-only (M7) |
| evidence.yaml 移出必钉 = 证据弱化? | 否 — evidence 仍被 validateEvidence + AC mapping 强制消费; 只是不钉哈希 (P1: 钉 hook 持续改写的文件 = 结构性漂移) | 保留 M3 |
| checklist 可选 = 进度失控? | done_contract 在 design.md 由 spec-gate 验 AC; checklist 是双写 | 保留 M4, 超大 sprint 仍可建 |
| P9 用 prompt 内容自动判 repo 外? | 判定面脆弱易伪造; 显式 _index 字段可审计可 grep, 与 proposals P9 建议一致 | 显式字段 (M2) |
| critic min R/S 2→1 弱化审议? | max_rounds 仍 4; 下限只保证"被独立批过一次"; 两轮强制在 9.9.6 sprint 实测产出的是轮次凑数不是质量 (P10 即证) | 保留 M6 |
| 砍 route-note 丢审议痕迹? | route_history 已双写同信息; 复杂 re-route 仍可单立 | 降可选 (M10) |
| 全砍 (R1 曾含): cleanup-pass 移出独立检查 / 铁律1 重写 / index-updater 改动 | 超授权范围; cleanup 是 R/S 行为产物非纯文书; 宪法大改需单独刀 | **砍, 不做** |

## 5. 验证记录 (本会话实跑)

- 语法: `node --check` ×2 cjs, `py_compile` ×2 py — 全 PASS
- 行为冒烟 (fixture 实跑):
  - Feature ship **无 checklist.yaml** → exit 0 (旧版必 block) ✅
  - design 正文含 "Critic Findings" 字样 → 计 1 轮不计 2 (P10) ✅; `min_rounds=2` 时正确 block ✅
  - Refactor + 写文件 subagent 无 worktree → exit 2; 加 `harness_target_outside_repo: true` → exit 0 + EXEMPT 提示 (P9) ✅
  - CX py gate 同场景 Feature ship 无 checklist → exit 0 ✅
- 未验 (留给用户 dogfood): 安装态同步后的真实 sprint 全流程; CX spawn 链路上的 audit 豁免实跑

## 6. Dogfood 验收标准 (下一个真实 sprint 采数)

- AC1: tool-trace 代码写入占比 8.4% → **≥40%** (harness-gate sprint 已证 43% 可达)
- AC2: sprint 手写 md 字节数 ≤ 代码 diff 字节数
- AC3: 零次"用户拍板豁免门禁" (P9 类死锁不再发生)
- AC4: proposals.md 新增条目数下降 (门禁误伤减少的代理指标)

## 7. 回滚

单 commit revert 即可 (所有改动一次提交); hook 层各改动点均有 `2026-07-28 gate-descaling` / `P9 fix` / `P10 fix` / `P13 fix` 注释锚点, 可逐项 revert。安装态 (~/.claude, ~/.codex) 尚未同步 — 用户按 harness-patches.md 流程 diff 回补, 同步前先备份。

## 8. Out of Scope (本刀不做)

- P11 (契约单源生成) / P12 (派工时序机械化 B-m1) — 待第二消费者/下刀
- 铁律1 门禁清单重写; index-updater re-route 阈值随绿区扩容联动 (Quick>3 文件上限与新绿区≤3 文件一致, 暂无冲突, 观察)
- 版本号不动 (9.9.6 内 patch 批次, 铁律[不版本通胀]); 台账见 harness-patches.md

## 9. 下刀批次 (2026-07-28 · W21-W24)

| # | 改动 | 验证 |
|---|---|---|
| W21/A2 | token-usage-collector 双端: Stop 全量 transcript 聚合只在 stage=ship 跑 (SubagentStop 保留); 消除每 turn 重读整个 transcript + 重写 758KB yaml 的固定税 | 冒烟: impl Stop 跳过 / ship Stop 写入 ✅ |
| W22/A3 | index-updater 双端按写入面分流: 写 .ai_state → 只重扫 counts/pointers; 写实现文件 → 只查 re-route; 无变化不写 (减 mtime churn); payload 缺失回退旧全量 (fail-open) | 冒烟: 代码写 counts 不动+re-route 触发; state 写 counts 刷新+不触发 ✅ |
| W23/B1 | delivery-gate 双端 lite-admissible: hook 自动记录 (command/timestamp/result) + agent 补一行 ac_id/covers 即 admissible; 十字段手写 artifact 契约降为可选严格路径 | 单测 4/4 双端: lite 放行 / 未映射 block / fail block / 坏时间戳 block ✅ |
| C1/C2 | update-plan F2 基线刷新 (回归期望以 W10-W24 为准); F6 A/B eval 砍, 换 dogfood 三指标 | 文本 diff |

**A1 撤回 (反驳自己的 finding)**: pre-bash-guard「重造已有能力」不成立 — CX 端 `approval_policy=never` + `danger-full-access` 无原生权限引擎兜底, parser 是唯一护栏, 且 9.9.6 升级正因平坦正则被实测绕过 (`rm -rf /*` 等样本在 guard 头注列明); CC 原生 deny 为精确匹配, 不覆盖归一化变体。**两端 guard 均不动**。教训: 判"重复造轮子"前先核对该轮子在最弱平台上的替代物是否存在。

**取舍声明 (W23)**: lite 路径弱化了 sha256/artifact 链 — 但该链同为 agent 手造, 防伪性本为剧场; 真实防线是 evidence-collector 只对白名单验证命令 (pytest/npm test/cargo test 等) 自动落 result, agent 伪造需手写整条记录, 与旧契约的伪造成本相同。

## 10. 路由刀 (2026-07-28 · W25-W27, fable5 + 模型路由)

| # | 改动 | 依据 |
|---|---|---|
| W25/R1 | CC settings.json `effortLevel: xhigh → high`; plan/design 靠 ultrathink 关键词显式升档 (32K) | 全局 xhigh = 每个平庸 turn 付顶格推理税; **CX 端本就是 high + plan_mode xhigh** — 本改动同时修复双端 effort 路由不对称 |
| W26/R2 | evaluator `model: opus → fable` (effort xhigh 不变), 加 Fable 不可用显式重试注记 (对齐 architect/critic 措辞) | VERDICT 是门禁判决点, 判定型角色配判断力最强模型; 判定/产出角色分型: Fable=architect/critic/evaluator (判定), Opus=generator/reviewer/spec-compliance/polish (产出)。**覆盖 07-25 角色矩阵决策, 用户 2026-07-28 批准** |
| W27/R3 | 按消费模型重写 prompt: critic.md 7 维度铺陈 45 行 → 判据清单表 (138→101 行); evaluator.md 砍 4 维 X.X 评分表 (判定由 VERDICT 决策规则表机械承载, 打分是剧场) | Fable 消费的 prompt 少脚手架多判据; Opus 消费的 (generator/reviewer) 保留结构化脚手架**不动**; 宪法 CLAUDE.md/AGENTS.md 已在行数预算内且承重, 本刀不动 |
| 漂移修 | evaluator (CC md + CX toml) 判据源 `checklist.yaml done_contract` → `design.md ## Done Contract` (M4 批次漏网); Evidence Cross-Check 对照面改为 checklist 存在才逐 task, 否则逐 Done Contract 条目 | batch1 一致性收口 |

architect.md 已精简 (24 行) 无需动。CX 端模型路由不对称项 (无 Fable) 按铁律[四原语]只对齐语义不伪造对称, evaluator.toml 仅修漂移不换模型。

## 11. 收尾刀 (2026-07-28 · W28-W30)

| # | 改动 | 验证 |
|---|---|---|
| W28/B3 | compact-restore 白名单化: CC 抽 `_index-render.cjs` 共享模块 (session-start 复用同源, 消双写), 注入 4KB→523B 实测且带告警; CX 内联同构 | 冒烟: fixture 注入 523B 含 design_changed 告警 ✅; session-start 回归输出正常 ✅ |
| W29/A5 | pace-continuator 双端砍 ## 历史 写入 (B5 空条目一并消灭), hook 变纯读; 模板段废除 | node --check / py_compile ✅ |
| W30/C3 | roadmap 编号收敛为 items.yaml slug 单源 + F↔item 映射 + 计划外批次补录 (items 10→12, gate 的 endsWith 匹配校验兼容) | 文本 diff; item slug 与 sprint slug 后缀匹配 ✅ |

## 12. 实测归因刀 (2026-07-28 · W31-W34)

下午 dogfood (sensory-retirement, Refactor) 实测: 代码 7%、ship 同因 block×4 熔断、CX 每消息全扫、533KB 遥测照写、CODEX-TASK 自造。归因→改动:

| 病根 | 改动 | 验证 |
|---|---|---|
| R/S 完整契约 (manifest→binding→tdd) 是 ship 空转与 review/cleanup/ship 文书劳役主源 | W31: manifest 全路径 opt-in; Cross-Check 段 gate 检查砍; R/S 底线=runtime-verify+cleanup+PASS | R/S ship 无 manifest 双端 exit 0 ✅ |
| CX 布线: index-updater 挂 UserPromptSubmit+PostToolUse(Bash|MCP), 无路径事件 fail-open 全扫 | W32: 无写入路径 no-op | Bash/UPS 事件 _index 零写入 ✅ |
| CX token-usage 事件名对不上 "Stop" → W21 失效 | W33: payload 形状判定 | impl 跳过 ✅ |
| 宪法「阶段转换前同步」= architecture 层 5 文档更新的合法性来源; 握手「任务文件」= CODEX-TASK 诱因; 铁律3 route-note 措辞 | W34: 宪法两处改写 + 握手内联化 + stages 派工禁落盘 | 文本 diff; 宪法 21/23 行预算内 ✅ |

**残余已知项**: evaluator/passN 产物约定仍要求 Cross-Check 段 (prompt 层, gate 不验 — 判定价值保留, 成本一段表格); design.md 体积仍 warn-only。下轮 dogfood 若 AC1 (代码占比≥40%) 仍不达标, 候选下一刀: design 体积 block (新 sprint 生效) + polish/cleanup 并入 review。

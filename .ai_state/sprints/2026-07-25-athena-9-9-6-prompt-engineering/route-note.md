# Route Note — 2026-07-25-athena-9-9-6-prompt-engineering

> 可审计路由摘要；不记录私有思维链。

- **输入**: 调研近期 CC/CX 与外部 prompt/agent 工程，形成 Athena 9.9.6 双端架构、roadmap 和更新计划。
- **候选**: A=直接 System plan；B=System+roadmap。A 较快但把 CC/CX、skills/PACE/state/config/release 压进单 sprint；B 符合“先调研”和 ≥3 模块地板。
- **权衡**: 爆炸半径=跨平台跨模块；可逆性=文档高、后续配置/hook 中；紧急度=建设性升级；不确定性=中。
- **决策**: **System + roadmap**；用户已在 2026-07-25 明确授权从 9.9.3 构建 9.9.6 底稿，现进入 plan/design critic 门禁；置信度 **0.97**。
- **事实**: 官方确认 Claude Code 2.1.219 / Opus 5；Codex resolver=`gpt-5.6-sol`，当前 stable=`0.144.4`。
- **边界**: 允许写本 sprint/roadmap，并在独立 worktree 新建 9.9.6 双端底稿和根 `.gitignore` 精确修复；禁止改 9.9.3 package、用户 HOME 和主工作树已有改动；不 commit/push/release。
- **编排**: architect raw Start event 在有界窗口内缺失，无法绑定 agent id；已 fail-closed 停止，agent 回执确认未读写/联网，本轮不再 spawn。
- **廉价退出**: 未获 official exact-version 或 local eval 证明的模型矩阵/hook 行为保持候选；底稿只落无争议平台迁移，不硬编码未证实字段。
- **产物**: `roadmap/athena-9-9-6-prompt-engineering/` + 本 sprint v3.1 `design.md`/`checklist.yaml`；正式 critic PASS 后由 generator 在隔离 worktree 生成底稿。

## 2026-07-25 · Claude review repair route

- **输入**: 用户授权修复 `REVIEW-9.9.6.md` 中经复核成立的问题。
- **候选**: A=按 Quick 在主树逐项修；B=沿用当前 System/impl，在隔离 worktree 由 generator 修复。跨 CC/CX、hooks、validator 与合同文档，A 低于变更面地板。
- **决策**: 选择 **B**，沿用当前 sprint，不降级、不新建第二状态；置信度 **0.98**。
- **边界**: 修复成立或部分成立 finding；对未证实的“所有网关必现”等外推改为风险与 dogfood 断言；不实现无设计依据的 CC CHANGELOG 对称要求，不 commit/push/release。
- **退出点**: 若 exact 0.145 hook fixture 否定源码合同，回 design 重审 CX spawn gate；若缺少可恢复的 9.9.6 validator 源码，以 9.9.3 行为覆盖为基线重建，不按函数数量伪造 parity。
- **用户隔离例外**: 用户随后明确要求“不使用 worktree，直接在原本上修改”。已删除尚未放行、无文件写入的临时 worktree/branch；保留 System 路径和 generator 单写者，允许写集收窄到当前 checkout 的 9.9.6 双端与本地 validator。

## 2026-07-28 · 范围扩张: gate 契约可见性与派工时序 (非 re-route)

- **输入**: 2026-07-27 撰写的独立 hotfix design (gate 契约可见性与派工时序, A–F 六条)，起因是消费侧 `quantum-cowork` 当天 `ledger-debt-batch` sprint 的八条实测失败，其中两个 worktree 写者整轮撞墙、约 21 万 token 花在被阻断的运行上。
- **候选**: A=另立 Feature sprint (原 design 的建议值)；B=并入当前 System sprint 作追加范围；C=先收完 9.9.6 的 F1-F6 再单独做。
- **权衡**: 三案改的是**同一批 9.9.6 发行件** (`vibeCoding/{claude,codex}/9.9.6/` 的模板/references/rules)，A 会让同一批文件在两个 sprint 的契约下各被审一次；C 让消费侧继续踩隐藏考纲。B 的代价是 System 路径地板 (critic ×2、manifest 强制、逐 AC 绑定) 覆盖到新增范围，成本更高但审查覆盖一次到位。
- **决策**: **B, 用户 2026-07-28 明确拍板**；path 维持 **System** (原 design 建议的 Feature 作废)，不新建 sprint、不新建第二状态；置信度 **0.95**。
- **一手事实 (本轮亲验, 非转述)**:
  - 本 sprint `design.md` 原 AC11/AC12 是业务 AC 却占用 harness 保留元标号 → `validateAcMapping` 把这两个标号排除在 per-AC 绑定之外，"本地测试树全覆盖" 与 "A/B eval N≥3 Pareto" ship 时静默免检。已重编号为 AC17/AC18。
  - 撰写重编号说明时**当场复现同一失败**: 在 AC17 条目正文写 "(原 AC11)" 会被 `validateAcMapping` 的 `matchAll(/(AC\d+)/g)` 从条目正文重新抽出保留标号，使重编号失效。映射改写进节表头注 (非条目行, 不被采集)，并在 design 内留下禁写注释。
  - `AC16` (Stop 熔断) 此前无任何 checklist 任务承载；实现已落 `fe3296d` 且两端安装态可见，但逐项 fixture 证据未留档 → 补 H1 任务。
  - ship 契约缺口: `evidence.yaml` 2 条记录 / 绑定字段命中 0；`review-manifest.yaml`、`tdd-evidence.yaml`、`cleanup-pass.md`、`reviews/` 全缺；活动 worktree = 1。
- **边界**: 只改文档面 —— 两端 `skills/pace/templates|references/`、`rules|standards/`，以及安装态 `~/.claude`、`~/.codex` 的对应文件。**两端 `delivery-gate.cjs`/`.py`、evidence-collector 与任何 hook 一行不动**；batch/debt 路径 (F 条) 未拍板前零实施 (AC26 反向断言看住)。
- **隔离决策**: **不用 worktree**。依 `stages.md` 先例与 `2026-07-25-harness-gate-p1-p4`：改动对象含项目 repo 之外的安装态，worktree 对 repo 外路径零隔离效果却照样阻断写入；隔离手段改为单写者串行 + 改动前备份 + `harness-patches.md` 逐条复核命令。
- **退出点**: 若 A1 模板注记块在 /tmp fixture 红绿对照中无法同时满足"合规骨架不 block"与"原失败形态被 block"，说明契约理解有误，回 design 重审而非放宽门槛；若 critic R6 判定新增范围与 §1-§11 存在冲突，按 critic 结论收窄而非扩面。
- **产物**: `design.md` §12 + §13 的 AC17-AC28、`checklist.yaml` G1-G6 与 H1、`annex-2026-07-27-gate-contract.md` (原独立 design 全文保全)。

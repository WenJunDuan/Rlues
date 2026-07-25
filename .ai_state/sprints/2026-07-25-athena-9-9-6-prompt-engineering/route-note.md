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

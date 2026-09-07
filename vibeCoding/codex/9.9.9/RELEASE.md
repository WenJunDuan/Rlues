# Athena Codex 9.9.9

Status: **candidate — not shipped**. Baseline: immutable 9.9.8.

本包供独立审查，包括用户指定的 Claude fable5.1 审查；该审查选择不是 CX-only 运行依赖。9.9.9 以 PACE + .ai_state 为核心，本端独立闭环、多平台按需增强。

候选变更：design 单一 Done Contract/checklist 可选；runtime-verify → polish → 一次独立 review；按真实异步入口等待；主 thread 创建绝对 worktree；恢复/审查输入绑定/并行整合/真实全栈准入下沉 PACE references；新模板默认 ["cx"]，兼容读取旧 ["both"]；角色模型继承有效用户配置；移除默认本地用量采集指引。Agent 每次任务最多70轮（CX为指令约束，当前无原生轮次硬限）；到限返回进度，不自动续派绕限。审查提示在 `skills/athena-review/REVIEW.md`。包内自带 VM schema/example。`/llm-as-a-verifier` 为 opt-in 排序，默认关，不是 ship 门禁。安装保留 sessions；已装机器成功后可删更早安装器备份。

已运行候选检查：隔离的cc/cx/both首装、迁移回滚回归、state/review故障案例、实际Codex配置加载，以及本机/SSH的HTTP+SQLite运行与清理。精确结果见当前sprint审查入口。这些证据不代表 AC1–AC14 或正式发行全部通过。正式 ship 仍需目标平台入口、单端闭环、迁移/回滚、关键 hook/review/worktree、真实运行/全栈、基线评测及最终独立审查证据。缺少所需结果时明确保持未完成，不宣称效率改进已测得。

结构限制（不宣称已关闭）：stage=ship 时 PreToolUse 可在 Stop/delivery-gate 之前放行 `git push`；CX Stop 在三次 block 后按平台设计 fail-open。原生 review receipt 是 agent 落盘的 JSON，不是厂商证明。`author_target` 在子进程缺少 `CODEX_THREAD_ID`/`CLAUDE_SESSION_ID` 时为空。AC14 原生 hook/review/worktree 入口待装机实测。`~/.athena/backups/` 中的用户配置备份可能含密钥且永不自动删除。VM 对已退出 session leader 仍 `killpg`，以便回收 prepare 残留子进程；pid 复用仍是残余竞态。

当前审查导航：[变更记录](CHANGELOG.md)、[迁移说明](AI-MIGRATION-GUIDE.md)、[阶段义务](.codex/skills/pace/references/stages.md)、[执行合同](.codex/skills/pace/references/execution-contracts.md)、[平台边界](.codex/skills/pace/references/platform-contracts.md)。安装态更新与推送不由本候选包生成动作自动授权。

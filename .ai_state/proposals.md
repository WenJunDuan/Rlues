# Athena Harness 进化提案 (铁律[Hook 是进化器])

> 📍 **归属说明 (用户 2026-07-25 指示)**: harness (hooks/rules/skills) 的**改动记录与补丁台账归 harness 自己的项目** —
> `/Users/mi_manchi/workspace/Rlues/.ai_state/harness-patches.md` (8 条补丁, 含逐条可执行复核命令; 源码入库 `vibeCoding/{claude,codex}/9.9.6/`)。
> **本文件只保留"在本项目实测发现"的提案记录**(发现过程是本项目的一手事实), 今后 harness 的修复 sprint 一律在 Rlues 立。

> **2026-07-25 状态**: 用户拍板修 P1-P4。分诊亲验后扩为 **P1-P7** — sprint `2026-07-25-harness-gate-p1-p4` design 已落盘 (7 条修法 + 三组 dry-run 验证方案), 处置见各条尾部与该 design。
> ⚠️ **P1 是回归**: 9.9.3 期已按用户拍板修好的白名单被 **9.9.6 升级覆盖** (`rg 'token-usage.yaml' delivery-gate.cjs` 现 0 命中) → 催生 P5 (patch 台账)。
> 新增: **P5** 升级覆盖本地 hook 修复无台账 · **P6** tdd-evidence 八字段必填 vs backfill 无 red 阶段的现实冲突 (9.9.6 加严所致, 2026-07-25 dry-run 实测当前 main = block) · **P7** 量化 AC 必先核基线 (批次3 REWORK 根因固化)。
>
> **P8 (2026-07-25, critic F1 分出)**: 截断/瞬断导致 `SubagentStop` 事件根本没被写入 (batch1 role=generator `ac31263f6412` = 8 Start/**0 Stop**, 亲验) — 这不是 gate 判据问题而是**事件采集缺口**, 指向 `subagent-tracker.cjs` 与平台生命周期钩子。本 sprint 的 W2 只放行"有 Stop 的 resume"(4/2/末次Stop), 截断场景继续走 `skip_impl_subagent_check` 显式释放 (不推翻 compound/2026-07-22 决策)。**待修**。
>
> **P9 (2026-07-25, 实测撞上)**: `subagent-worktree-check.cjs:107` 对 Refactor/System + 写文件 subagent **无条件**要求 `isolation: worktree`, **无任何豁免出口** (亲验全文 135 行, 不读 _index 任何字段)。但当改动对象在项目 repo **之外**时 (如 `~/.claude` harness 自身), worktree 既无隔离效果 (不覆盖 repo 外文件) 又**禁止**写入这些路径 → 合法任务被死锁。本次处置: 用户显式批准把 harness sprint 降为 Feature 路径 (记 `route_history`)。**建议修复**: 加 `_index` 字段 (如 `harness_target_outside_repo: true`) 或识别 "改动清单全在 repo 外" 时放行并要求备份证据。**待修** (鸡生蛋: 修它需写 hook, 写 hook 又被它拦 → 需主 agent 直做那一步)。

## P1 · delivery-gate 与 token-usage hook 的文件名/易变性错位 (2026-07-24, batch1 ship 实测死结)

- **现象**: delivery-gate.cjs 的 post-review 白名单只认 `sprints/{slug}/token-usage.jsonl` (delivery-gate.cjs:409), 但 token-usage hook 实际写 `token-usage.yaml`, 且**每次 Stop 都先于 gate 改写** (updated_at + totals 累计)。
- **后果**: 全契约 ship 结构性死锁 — 把 token-usage.yaml 钉进 review-manifest → Stop 时 hook 先写后验, 哈希必落后一拍 (`review-manifest hash mismatch: token-usage.yaml`, 2026-07-24 实测); 不钉 → working drift 不在白名单, 同样 block。任一状态均无解。
- **同类隐患**: evidence.yaml 被 manifest 强制钉住, 但 PostToolUse hook 会因 ship 阶段的验证命令 (如 merge 后复跑 bun test) 继续追加 → 同样的钉住-即-失效。
- **建议修复** (二选一): (a) 白名单加 `token-usage.yaml` 且把 token-usage/evidence 这类 hook 持续维护的记账文件从 manifest 必钉集合中排除 (它们是过程记账, 不是被审对象); (b) token-usage hook 改写 `.jsonl` 对齐 gate。
- **本次处置**: 档案全部诚实落盘 (review-manifest/tdd-evidence/binding/ARCHITECTURE), 死结经用户拍板走 idle 释放 (先例: compound/2026-07-21-decision-e3-2-3-idle-release.md)。


> ✅ **2026-07-25 已修复** (sprint 2026-07-25-harness-gate-p1-p4): 见 `.ai_state/harness-patches.md` 第 1 条 (含可执行复核命令) · 源已入 Rlues `vibeCoding/{claude,codex}/9.9.6/` (commit b4f45eb) 防升级再蒸发 · G1-G5 dry-run 实跑证据见该 sprint `tdd-evidence.yaml`。

## P2 · generator 生命周期 "恰一次 Start/Stop" 与断点续跑不兼容 (2026-07-24, batch1 实测)

- **现象**: validateGeneratorChain 要求 generator agent_id 恰一次 SubagentStart/Stop; API 瞬断 (本会话 7 次) 后 SendMessage 断点续跑, 同一 agent_id 产生 19 Start/6 Stop — 真实工作痕迹反而不合规。
- **建议**: 放宽为 "≥1 Start 且末次事件为 Stop 且 assignment 时间戳落在首 Start 之后"; 或续跑事件带 resume 标记。
- **2026-07-24 batch2 复发**: 瞬断 2 次 SendMessage 续跑 → 同 agent_id 多次 Start/Stop; 且 assignments 握手因 generator 写入被 worktree 硬隔离 (见 P4) 根本无法写进主仓共享 JSONL — 恰一次契约在 worktree 隔离模式下结构性不可满足, 修复优先级建议提升。
- **本次处置**: skip_impl_subagent_check=true 诚实豁免 (证据链完整留档: assignments + events + 10 worktree commits), 先例 compound/2026-07-22-decision-e3-4-generator-truncation-subagent-check.md。


> ✅ **2026-07-25 已修复** (sprint 2026-07-25-harness-gate-p1-p4): 见 `.ai_state/harness-patches.md` 第 2 条 (含可执行复核命令) · 源已入 Rlues `vibeCoding/{claude,codex}/9.9.6/` (commit b4f45eb) 防升级再蒸发 · G1-G5 dry-run 实跑证据见该 sprint `tdd-evidence.yaml`。

## P3 · delivery-gate 按 shell cwd 解析 .ai_state, worktree 内误拦 (2026-07-24, batch2 实测)

- **现象**: 主 agent Bash `cd` 进 subagent worktree 查进度后 cwd 持久化; Stop 时 delivery-gate 以 cwd 为根解析 `.ai_state`, 在 worktree 里找 batch1 的 `evidence.yaml` (gitignore 白名单文件, worktree 检出必然不存在) 而 block。polish subagent 也复现: 对 /tmp 的无关 Write 都触发同一 complaint。
- **建议**: gate 解析项目根用 `git rev-parse --git-common-dir` 归一到主仓, 而非 process.cwd(); 或检测 cwd 在 `.claude/worktrees/` 下时跳过 ship 验证 (worktree 不是 ship 面)。
- **本次处置**: cd 回主仓即解; 工作纪律改为查 worktree 一律 `git -C <path>`。


> ✅ **2026-07-25 已修复** (sprint 2026-07-25-harness-gate-p1-p4): 见 `.ai_state/harness-patches.md` 第 3 条 (含可执行复核命令) · 源已入 Rlues `vibeCoding/{claude,codex}/9.9.6/` (commit b4f45eb) 防升级再蒸发 · G1-G5 dry-run 实跑证据见该 sprint `tdd-evidence.yaml`。

## P4 · polish_worker 的 Edit/Write 被硬隔离在自有 worktree, 无法履行"唯一写者"职责 (2026-07-24, batch2 实测)

- **现象**: polish-worker 带 worktree 隔离 spawn 后, 对主仓 .ai_state 与目标 generator worktree 的写入均被拒 (`This agent is isolated in the worktree ...`); 它被迫把目标分支 merge 进自己的 worktree 作业, 产物靠"再合并回 main"传递。可行但多一跳分支, 且 architecture/cleanup-pass 等主仓档案更新被间接化。
- **建议**: polish 阶段 spawn polish-worker 时**不加 isolation** (它本就是串行唯一写者, 无并行写冲突面), 或平台支持指定"作业于既有 worktree"; skill/stages 文档同步注明。
- **本次处置**: 分支合并传递成功 (979e004 → merge 2a3949e), 无产物丢失。


> 🟡 **2026-07-25 重定界并部分处置**: 平台 isolation 语义 hook 改不了 → 改的是编排知识: `skills/pace/references/stages.md` polish 段已注明 polish_worker 不加 isolation、改动对象在 repo 外时同理不用 worktree (harness-patches 第 8 条)。**衍生出 P9** (worktree 强制检查无豁免出口) 仍待修。

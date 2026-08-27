# _index overflow — 2026-08-27-athena-9-9-8

Full items moved off `_index.md` (AC9). Do not delete.

## st-0

### archived-0
`2026-07-25`: **用户最终确认 CC 角色矩阵**：main `model=best`；无全局 subagent override；architect/critic=Fable，evaluator 与其余四个实现/审查角色=Opus；effort 保持 3×xhigh + 4×high。

### archived-1
`2026-07-25`: **9.9.6 reviewable bottom draft 已收敛到当前 Rlues/main 工作目录**（uncommitted；临时 worktree/branch 已删除）。CC 117 / CX 115 文件，26 skills/端；Codex 0.145.0 实际加载配置成功；9.9.3 零 diff；本地 tests/evals 尚未创建，F1-F7 保持 pending。证据见当前 sprint `bottom-draft-evidence.md`。

## st-1

2026-08-27 design：Grok/Codex 已完善 `Thin PACE Control Plane`：一次原生 review、hook 红黄绿（现场复现无害 `rg` parser 误判）、final-diff hash、有界 `_index`。双端 `athena-vm` 已具 setup/doctor，当前未配置；LaaV 仅作 logprob best-of-N/进度实验，不替代 VM/test/review/ship。packet 52 行并绑定最新 design hash；下一步仍是独立 Claude 复盘，通过前不授权实现。

## st-2

2026-07-29 ship：hotfix2 已完成提交并推送 `main`（`19dd8d5`）；delivery-gate exit 0，工作树干净，当前 sprint/roadmap 项均 completed。AC9 A/B N≥3 仍按范围锁定为下一 sprint，不影响本轮交付完成。

## st-3

2026-07-29 W35-W40 hotfix2：canonical 双端包已同步 ~/.claude 与 ~/.codex（30 个目标，逐文件事务备份）；历史/会话/SQLite 保留，缓存清理完成，_to_delete 内容可恢复隔离。validator 66/0/0、W35-W40 台账、真实 sprint `verdict_ac2=PASS`（git 度量代理）、review/evaluator PASS；AC9 A/B N≥3 明确 deferred 到下一 sprint。

## st-4

2026-07-28 W31-W34 安装态部署已完成：12 个源条目、10 个唯一目标，9 个过期目标更新；两端哈希、语法、历史与 SQLite 校验通过。会话、历史、配置、认证、插件、项目态和数据库保留；两个仓库 _to_delete_* 目录移入保留备份隔离区并从仓库移除。记录见 sprints/2026-07-28-installation-sync-w31-w34/deployment.md。

## st-5

2026-07-28 用户主动关闭 9.9.6 prompt-engineering / gate-descaling 方向：原本的改动反复且叙述冗长，后续不再考虑同类扩展。活动 sprint、roadmap 与续跑动作已清空；已完成实现、同步、验证和历史记录保留，未执行项标为 superseded，不伪称 release 已完成。决策档案见 compound/2026-07-28-decision-close-prompt-engineering-direction.md。

## st-6

`2026-07-28`: **10bd534 gate-descaling 本地 draft 已同步到当前系统端点**：CC 128 / CX 33 / shared skills 97，管理哈希 257/257；历史 JSONL 2 份共 545 行、SQLite 9 个 quick-check=ok；只清理两端 `.DS_Store` 与 `__pycache__`（1,116 文件 / 16,467,927 字节），未触碰历史、会话、插件、数据库、认证或活动缓存。静态验证 `66 PASS / 0 FAIL / 0 SKIP`。仍为 `impl` / `reviewable draft`，未标记 release complete。详见 `sprints/2026-07-25-athena-9-9-6-prompt-engineering/deployments/20260728T061441Z-gate-descaling-sync.md`。

## st-7

`2026-07-28`: **hotfix gate-contract 并入本 sprint 作追加范围**（用户拍板，不另立 sprint）。核出现场踩雷：本 sprint `design.md:316-317` 的 AC11/AC12 是**业务 AC 却占了 harness 保留元标号** —— `delivery-gate.cjs:813` 把 AC11/AC12 排除在 per-AC 证据绑定之外，即"本地测试树全覆盖"与"A/B eval N≥3 Pareto"两条 ship 时静默免检；`validateMetaAcceptance` 反而据标号额外要求 evaluator PASS + cleanup 完成 + 活动 worktree=1（碰巧与 System 真义务重合，未炸）。这正是 hotfix design §一 失败 #3 的现场复现。ship 契约缺口实测：`evidence.yaml` 2 条记录 / 绑定字段命中 **0**，`review-manifest.yaml`、`tdd-evidence.yaml`、`cleanup-pass.md`、`reviews/` 全缺；critic 字面轮次 5（System 地板 2，已过，但新增范围需再加一轮）；活动 worktree=1。新 design 的 AC 段已实测可被 spec-gate 解析（/tmp fixture 喂 PreToolUse，exit 0）。

## st-8

`2026-07-25`: **Claude review 成立项已修复，仍处 impl**：P0 provider/background/spawn gate、validator、hook/docs/security drift 收口；local-only validator 63 PASS / 0 FAIL / 0 SKIP（含 fresh setup、exact Codex 0.145 config.load、F-series、worktree gate fixtures）。用户明确要求直接在 main checkout 修改；三种 subagent 角色均因无 shell/编辑工具零写入失败，主 thread 接管。完整 F1-F6/runtime-verify/正式 2+1 review 仍 pending，未 commit/push/release。证据见 `review-repair-evidence.md`。

## st-9

### archived-0
`2026-07-25`: **Claude review 成立项已修复，仍处 impl**：P0 provider/background/spawn gate、validator、hook/docs/security  →index-overflow.md#st-8

### archived-1
older 当前状态 →index-overflow.md#st-0

## st-10

### archived-0
`2026-07-28`: **hotfix gate-contract 并入本 sprint 作追加范围**（用户拍板，不另立 sprint）。核出现场踩雷： →index-overflow.md#st-7

### archived-1
older 当前状态 →index-overflow.md#st-9

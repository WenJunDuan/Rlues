---
sprint_slug: "2026-07-29-athena-9-9-6-hotfix2"
path: "System"
stage: "runtime-verify"
status: "completed"
verified_at: "2026-07-29T14:24:00Z"
base_ref: "6bcd16c"
head_ref: "77b64bb"
---

# Runtime Verify — hotfix2 W35-W40

## 完成条件与停止条件

- readiness checker：`python3 vibeCoding/scripts/validate-athena-9.9.6.py` 必须 `66 PASS / 0 FAIL / 0 SKIP`。
- W35-W40 台账命令在 canonical 源与两个安装态均 PASS；安装态 gate 必须包含 W38，Codex config 不得含 `openai_base_url`、`model_context_window` 或 `model_auto_compact_token_limit`。
- 新仪器必须直接输出 `verdict_ac2=PASS`；这里是 git 单源度量代理，不替代设计 AC2 的只读/worktree 行为判据。三类场景、边界、失败/安全和环境检查均完成后停止，不再生成普通 telemetry。

## 测试场景

| 类别 | 场景与命令 | 结果 |
|---|---|---|
| 正常 | validator；W35-W40 ledger source + installed；`python3 vibeCoding/scripts/athena-metrics.py . 2026-07-29-athena-9-9-6-hotfix2 6bcd16c` | PASS；`66/0/0`；度量代理 `verdict_ac2=PASS`，code=5605，sprint md=177，state=416，commits=1 |
| 边界 | 安装态 `subagent-worktree-audit.py`：只读 `explorer` 无 worktree；`generator` 在 System 无 worktree | PASS；explorer exit 0 且无违规行；generator exit 2 且写入 1 条 blocked-before-start 证据 |
| 失败/安全 | evidence `redact()` 输入 provider key、Bearer、AWS/assignment、CLI flag、DATABASE/URL userinfo 与普通命令；停止布线检查 | PASS；敏感值均 `[REDACTED]`；两端 Stop 只剩 delivery-gate，PreCompact/continuator/token collector 未注册 |
| 环境 | 4 个 CC `node --check`、6 个 CX `ast.parse`、settings/hooks/config 解析、9 个 Codex SQLite `PRAGMA quick_check` | PASS；9/9 `ok` |

## 自测自改记录

1. 首次 validator 报告为 hook 文档未标注三项已停产资产；更新双端 `skills/pace/references/hooks.md`，明确 `pace-continuator`、`token-usage-collector`、`compact-snapshot` 为未注册历史资产。
2. validator 自身加载 gate 时会产生 transient `__pycache__`，导致自检把自己的缓存判成 junk；在 local-only validator 设置 `sys.dont_write_bytecode = True`，清理既有 `.pyc`/`.DS_Store` 后以用户原命令复跑。
3. 安装态写入前逐文件备份，配置采用 release-owned 字段合并；会话、历史、插件、项目与数据库未进入写入清单。Codex 当前活动 session/log 在验证期间自然增长，未被删除或回滚。

## AC coverage（本轮证据边界）

| 设计项 | 本轮结论 | 证据边界 |
|---|---|---|
| AC1 | PASS（已运行时验证） | validator `66 PASS / 0 FAIL / 0 SKIP`、双端 config/registry 解析 |
| AC2 | PASS（行为夹具） | 安装态 read-only explorer exit 0；System writer 缺 worktree exit 2；度量命令的 `verdict_ac2` 仅为代理量 |
| AC3–AC8 | PASS（实现/安装面） | W35-W40 台账、双端源码/安装 parity、文档与语法/SQLite 检查；未把普通动作记账恢复为证据 |
| AC9 | DEFERRED | 下一 sprint 做三类 A/B、每类 N≥3；本轮不宣称 PASS，数据用于 10.0 架构收缩裁决 |
| AC10 | PASS（交付面） | 单次实现提交 + 安装同步事务备份；未创建 stage-only/progress-only commit |

## Reflect

- 这轮数据使用 git 单源仪器，不再依赖每个动作的 raw tool/subagent/token 账本；命令直接打印 `verdict_ac2=PASS`，但设计 AC2 仍以行为夹具为准。
- 过时且无消费者的 `_hf2_sync` 镜像已删除；canonical release 是唯一安装源，避免旧 gate 回灌。
- `_to_delete_hf2_out`（30 文件）与 `_to_delete_git_debris`（4 个空锁残骸）已从仓库路径移入同一事务备份的 `deleted-to-delete/`，恢复路径保留。

## VERDICT

**PASS（本轮范围）— runtime-verify 完成；AC9 明确留给下一 sprint，不在本轮伪报完成。**

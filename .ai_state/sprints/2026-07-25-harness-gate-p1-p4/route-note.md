# Route Note · harness-gate-p1-p4 (2026-07-25)

- **来源**: 用户 2026-07-25 拍板 "修 harness P1-P4" (四条已连续三个 sprint 逼出契约豁免/绕行, 是当前最大流程摩擦)。原始记录: `.ai_state/proposals.md` P1-P4 (批次 1/2 实测写入)。
- **对象**: `~/.claude/hooks/delivery-gate.cjs` (969 行, 门禁中枢) + 可能的 skill 文档 + proposals 勾销。**注意: 对象在项目 repo 之外。**

## 亲验现状 (2026-07-25, 主 agent 逐条核实 — 不照旧档动手, 批次2/3 幻影计数教训同型)

⚠️ **harness 已从 9.9.3 升级到 9.9.6** (rules/_index.md version: 9.9.6), 四条必须按当前代码重新定界:

| 条目 | 9.9.3 记录 | 2026-07-25 当前代码亲验 | 结论 |
|---|---|---|---|
| **P1** token-usage 白名单错位 | gate 只认 `.jsonl`, hook 写 `.yaml` | delivery-gate.cjs:409 白名单仅 `token-usage.jsonl`; **`rg 'token-usage.yaml'` 全文 0 命中**; token-usage-collector.cjs:397 确认仍写 `token-usage.yaml`; stop-failure-recorder.cjs 写 `stop-failures.jsonl` 亦不在白名单 | **回归!** 9.9.3 期用户拍板的本地修复 (本会话早先在旧 gate 见过带 "2026-07-24 P1 fix (用户拍板)" 注释的白名单行) 被 9.9.6 升级覆盖 → 需重修 + 防再丢 |
| **P2** generator 恰一次 Start/Stop | 断点续跑必然违规 | delivery-gate.cjs:175-176 `starts.length !== 1` / `stops.length !== 1` 硬判 | **仍存在**, 需放宽 |
| **P3** gate 按 cwd 解析 .ai_state | worktree 内误拦 | :386 与 :789 均 `git rev-parse --show-toplevel` 以传入 cwd 为基; :942 `payload.cwd \|\| process.cwd()` | **仍存在**, 需归一到主仓 |
| **P4** subagent 写入被 worktree 硬隔离 | polish-worker 写不了主仓 | 平台行为 (Claude Code isolation 语义), **hook 代码无法修** | **重定界**: 可修面 = 流程/文档 (spawn polish-worker 不加 isolation) + 本 sprint 自身即第一个应用 |
| **P5 (新)** 升级覆盖本地 hook 修复 | — | `~/.claude` **不是 git repo** (亲验 `rev-parse` 失败), 无版本/回滚; `~/.claude/backups` 目录存在但非 patch 层 | **新增条目**: P1 回归的根因, 不解决则本 sprint 修复同样会被下次升级冲掉 |
| **P6 (新)** tdd-evidence 八字段必填 vs backfill 现实 | — | :429 要求 8 字段全非空 (`red_command` 在内); 批次 3 有 6 条 backfill 记录如实省略 `red_command` (无独立 red 阶段, red_summary 已说明) → **dry-run 实测当前 main = block** (`tdd-evidence record is missing red/implementation/green fields`) | **新增条目**: 9.9.6 加严所致 (上轮 Stop 放行时 harness 尚为 9.9.3, 两轮之间被升级); 需 gate 承认 backfill 形态或档案补显式 N/A |

## 数字更正 (2026-07-25, critic F9 抓出 + 主 agent 亲验)

- 本档原写"批次3 10 Start/8 Stop"**有误**: 实测 batch3 events 全 agent 合计 **20 Start / 11 Stop**; 而 P2 真正的对象是**单个 role=generator agent** —— batch1 `ac31263f6412` = **8 Start / 0 Stop / 末次=Start** (截断未收尾), `a248c4aee453`/`a5a5bdc3bb04` = **2 Start / 1 Stop / 末次=Stop** (合法 resume, 才是 W2 要放行的形态)。测量命令见 design Round 2 AC12 风格。
- 教训: 本档自身犯了 W7 要防的错 (引用未测量的数字), 已按同一规则更正。

## dry-run 基线 (2026-07-25 实测)

`echo '{"cwd":"<主仓>","hook_event_name":"Stop"}' | node ~/.claude/hooks/delivery-gate.cjs` → **block**: `tdd-evidence record is missing red/implementation/green fields` (即 P6)。此路径即本 sprint 的验证手段, 已确认可用 (输出 stdout JSON `decision:block`, 放行则无输出)。

## P3 修法实测 (2026-07-25, 主 agent 亲验 git 行为)

| 位置 | `--show-toplevel` (现用) | `--git-common-dir` | `--path-format=absolute --git-common-dir` |
|---|---|---|---|
| 主仓 | 主仓根 ✓ | `.git` (**相对!**) | `<主仓>/.git` ✓ |
| worktree 内 | **worktree 路径 ✗ (P3 根因)** | `<主仓>/.git` ✓ | `<主仓>/.git` ✓ |

→ 修法定案: `path.dirname(gitText(cwd, ["rev-parse","--path-format=absolute","--git-common-dir"]))`。`--path-format` 需 git ≥2.31 (本机 2.54.0 ✓, 文档: https://git-scm.com/docs/git-rev-parse#Documentation/git-rev-parse.txt---path-formatabsoluterelative)。

## 路由决策

- **候选 (a)** 红区 System + generator + `isolation: worktree` (按铁律[零写入]红区默认): **否决** — P4 实测证明带 isolation 的 subagent 写不了项目外路径, 而 `~/.claude` 根本不在项目 repo 内, worktree 对它**零隔离效果**且直接阻断作业。
- **候选 (b, 本路)** path=**Refactor**, 写者 = generator subagent **不加 isolation** (黄区形态), 隔离手段改为 **手工备份 + 单写者串行**: 改前 `cp delivery-gate.cjs ~/.claude/backups/delivery-gate.cjs.pre-p1p4-<ts>`; 无并行写者。护栏因"改动对象是门禁自身 + 无 git 回滚"上调: critic ≥2 轮 + **可执行 dry-run 验证强制** (见下)。
- **候选 (c)** 主 agent 直做: 否决 — 改动跨 4 条问题 ~20-30 行代码 + 文档, 超绿区 30 行/单文件线。

## 可测性 (design 必须落实)

gate 是 Stop hook, 读 stdin JSON payload。**可控验证路径**: `echo '<payload>' | node ~/.claude/hooks/delivery-gate.cjs` 直接跑, 用**批次 3 真实档案**作 fixture。三组必测:
1. **旧被拦场景应放行**: batch3 sprint (token-usage.yaml 有 working drift) → 修复后不再 block
2. **真违规仍应拦** (防修成筛子): 篡改 manifest 哈希 / 缺 cleanup-pass / VERDICT 非 PASS → 仍 block
3. **P2 放宽后**: 多 Start/Stop (batch3 真实 events, 10 Start/8 Stop) 放行, 但"只有 Start 无 Stop"仍 block

- **置信度**: 0.8 (四条现状全亲验; 不确定性在 P2 放宽的判据边界与 P5 机制解法的克制度 — 交 design+critic; 门禁改坏的风险由备份 + 三组 dry-run 兜底)。

# Harness Patches 台账 (本项目 = Athena harness 源仓库)

> **归属**: 用户 2026-07-25 明确 —— harness (hooks/rules/skills) 的改动记录属于**本项目**, 不占用消费侧项目 (quantum-cowork) 的 `.ai_state`。
> 本次修复的完整设计与验证证据历史地留在消费侧 (发现与实测都在那里发生): `quantum-cowork/.ai_state/sprints/2026-07-25-harness-gate-p1-p4/`
> (`design.md` 3 轮 / `tdd-evidence.yaml` G1-G5 实跑 / `proposals.md` P1-P9)。**今后 harness 改动一律在本项目立 sprint。**
>
> ⚠️ **W8 护栏的语义**: `delivery-gate` 的 light-ship 豁免检测的是**文件名** `harness-patches.md` (与仓库无关) —— 台账搬到本项目后, 在**本项目**改 harness 时护栏照样生效 (diff 含本文件即不走 light-ship)。

> **为什么有这份文件**: `~/.claude` 与 `~/.codex` 都不是 git repo, 对它们的本地修复没有版本
> 也没有回滚路径。9.9.3 期用户拍板的 delivery-gate 白名单修复就是这样在升级到 9.9.6 时被
> 安装包静默覆盖的 (= proposals P1 回归), 而且没有任何人能机械发现。
>
> **怎么用**: 每次 harness 升级后逐条跑"复核命令"; 命中"已被覆盖"就从 Rlues 对应路径 diff 回补。
>
> **机械消费者**: `delivery-gate` 的 `isLightShipFile` / `is_light_ship_file` 已加分支 —— 只要某
> 次 ship 的 diff 里含本文件, 该 ship 就不再走 light 路径, 必须走全契约 (见下方 P-W8)。这让台账
> 不是"写死的文档", 而是有门禁消费者的机制。
>
> 相关档案: `sprints/2026-07-25-harness-gate-p1-p4/design.md` (Round 3 为权威) ·
> 同目录 `tdd-evidence.yaml` (G1-G5 实跑证据) · `proposals.md` (P1-P9)。

## 备份 (唯一回滚路径)

改动前逐字节副本, 2026-07-25T15:39:39Z:

- `~/.claude/backups/delivery-gate.cjs.pre-p1p8-20260725T153939Z`
- `~/.claude/backups/delivery-gate.py.pre-p1p8-20260725T153939Z`

复核命令:

```sh
ls -l ~/.claude/backups/delivery-gate.cjs.pre-p1p8-* ~/.claude/backups/delivery-gate.py.pre-p1p8-*
diff ~/.claude/backups/delivery-gate.cjs.pre-p1p8-20260725T153939Z ~/.claude/hooks/delivery-gate.cjs | head -40
```

备份与安装态 `diff` **必须非空** (非空 = 修复还在; 变空 = 修复被升级冲掉了)。

---

## 1. `~/.claude/hooks/delivery-gate.cjs` · P1 白名单 (W1)

- **理由**: `token-usage-collector.cjs` 每次 Stop 改写 `token-usage.yaml`, `stop-failure-recorder.cjs`
  每次 block 追加 `stop-failures.jsonl`。两者都是 hook 自己维护的过程记账, 不是被审对象, 却不在
  `allowedExact` 里 → 被判未授权 `.ai_state` drift。而且是死结: recorder 因 block 写的档案就是下一次
  block 的理由。**不加 `proposals.md`** (没有任何 hook 写它, 加进去是实质放宽)。
- **复核命令**:

```sh
rg -n '\$\{sprintRel\}/(token-usage\.yaml|stop-failures\.jsonl)' ~/.claude/hooks/delivery-gate.cjs
```

  期望 **2 行命中**。0 命中 = 已被覆盖。

- **Rlues 对应路径**: `vibeCoding/claude/9.9.6/hooks/delivery-gate.cjs` (commit b4f45eb)

## 2. `~/.claude/hooks/delivery-gate.cjs` · P2 generator 生命周期收束语义 (W2)

- **理由**: 原判据 `starts.length !== 1` / `stops.length !== 1` 要求 generator 物理只跑一次, 而 API 瞬断
  后用 SendMessage 续跑会给同一 `agent_id` 追加第二对 Start/Stop → 合法续跑结构性不可 ship。改为
  "已收束": ≥1 Start + ≥1 Stop + **末次事件须为 Stop**; 同秒 tie 用文件行号稳定排序; `agent_type`
  改为该 agent_id 全部事件唯一。真截断 (有 Start 无 Stop / Stop 只在中间) **仍拦**, 继续走
  `skip_impl_subagent_check` 显式释放。
- **复核命令**:

```sh
rg -n 'starts\.length !== 1|stops\.length !== 1' ~/.claude/hooks/delivery-gate.cjs   # 期望 0 命中
rg -n 'must end with SubagentStop' ~/.claude/hooks/delivery-gate.cjs                 # 期望 1 命中
rg -n 'a\.lineNumber - b\.lineNumber' ~/.claude/hooks/delivery-gate.cjs              # 期望 1 命中 (稳定排序)
```

- **Rlues 对应路径**: 同上

## 3. `~/.claude/hooks/delivery-gate.cjs` · P3 项目根归一 (W3)

- **理由**: linked worktree 内 `rev-parse --show-toplevel` 返回 worktree 路径, gate 于是拿一个新检出去
  解析 `.ai_state` —— 而 `.gitignore:28` 让 `evidence.yaml` 这类档案在新检出必然缺失 → worktree 内任何
  Stop 都被误拦。改为 `--path-format=absolute --git-common-dir` (worktree 内也返回主仓 `.git`), 并让
  `root` 与 `findAiState` **同源**, 避免 `sprintRel` 变成 `../wt-x/...` 的混框。submodule 与 bare
  (basename 不是 `.git`) 回退 `--show-toplevel`; 非 git / git 不可用返回 `null` 退化为原 cwd 语义。
  早退 (`findAiState(cwd)` 为空即静默返回) **保持在 try 之前**, 保证非 git 目录的 PreToolUse 不崩栈也不多跑 git。
- **复核命令**:

```sh
rg -n 'function tryRepoRoot' ~/.claude/hooks/delivery-gate.cjs                        # 期望 1 命中
rg -n 'path-format=absolute' ~/.claude/hooks/delivery-gate.cjs                        # 期望 1 命中
rg -n 'validateShip\(aiState, fm, root \|\| cwd\)' ~/.claude/hooks/delivery-gate.cjs  # 期望 1 命中
# 行为面 (G4): 非 git 目录的 PreToolUse 必须静默 no-op 且不崩栈
echo '{"cwd":"/tmp","hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"/tmp/x.txt"}}' \
  | node ~/.claude/hooks/delivery-gate.cjs; echo "exit=$?"    # 期望: 无输出, exit 0
```

- **Rlues 对应路径**: 同上

## 4. `~/.claude/hooks/delivery-gate.cjs` · W8 台账进 light-ship 护栏

- **理由**: `isLightShipFile` 的 `hooks/` 护栏只认仓内路径, 而 harness 改动落在 `~/.claude`,
  对 gate 天然不可见 → 改门禁自身的 sprint 只要仓内净 diff ≤60 行且都是文档态就被判 light ship,
  manifest / tdd-evidence / review 契约整段跳过, **门禁改动零机械复核**。本文件是这类改动唯一的
  仓内痕迹, 故让它出现在 diff 里就取消 light 资格。
- **复核命令**:

```sh
rg -n 'harness-patches' ~/.claude/hooks/delivery-gate.cjs ~/.codex/hooks/delivery-gate.py
```

  期望 **两端各 1 命中**。

- **Rlues 对应路径**: `vibeCoding/claude/9.9.6/hooks/delivery-gate.cjs` +
  `vibeCoding/codex/9.9.6/hooks/delivery-gate.py`

## 5. `~/.codex/hooks/delivery-gate.py` · P1 + P3 + W8 对称修复 (W9)

- **理由**: codex 端同型缺陷 (白名单只有 `token-usage.jsonl`; `git_root` 用 `--show-toplevel`;
  `is_light_ship_file` 同样有 light-ship 洞)。codex 端**没有 P2** (无 exactly-one Start/Stop 判定),
  故不做 W2 对称改动。`git_root` 复用既有 `git_lines` (本就吞 OSError 与非零退出), 天然非抛。
- **复核命令**:

```sh
rg -n '\{sprint_rel\}/(token-usage\.yaml|stop-failures\.jsonl)' ~/.codex/hooks/delivery-gate.py  # 期望 2 行
rg -n 'path-format=absolute' ~/.codex/hooks/delivery-gate.py                                     # 期望 1 行
rg -n 'ai_state = find_ai_state\(root\) or ai_state' ~/.codex/hooks/delivery-gate.py             # 期望 1 行
python3 -m py_compile ~/.codex/hooks/delivery-gate.py && echo "py syntax OK"
```

- **Rlues 对应路径**: `vibeCoding/codex/9.9.6/hooks/delivery-gate.py` (commit b4f45eb)

## 6. `~/.claude/rules/doc-style.md` · tdd-evidence backfill 记法 (W4)

- **理由**: gate 要求 tdd-evidence 八字段全非空, 而给既有正确实现补测试 (backfill) 没有独立 red
  阶段 —— 合法工程形态与门禁冲突。**不放宽 gate** (那会给"没做 TDD 却声称做了"开真口子), 改为落规范:
  `red_command` 写显式 backfill 声明, `red_summary` 必须给真实缺口证据, `red_observed_at` 语义为
  缺口核实时刻。规范正文禁写会被 `PLACEHOLDER_PHRASES` 命中的缩写。
- **复核命令**:

```sh
rg -n 'tdd-evidence backfill 记法' ~/.claude/rules/doc-style.md          # 期望 1 命中
rg -in 'n/a' ~/.claude/rules/doc-style.md; echo "want-no-match exit=$?"  # 期望无命中 (exit 1)
```

- **Rlues 对应路径**: `vibeCoding/claude/9.9.6/rules/doc-style.md`

## 7. `~/.claude/rules/coding-standards.md` · 量化验收标准必先核基线 (W7)

- **理由**: 批次 3 一次 REWORK 的根因 —— design 写下 "所有改动文件 ≤300 行" 时没核
  `storage/workflows.ts` 基线已 341 行, 门槛在落笔时即不可达。属规范缺失, 固化成规则。
- **复核命令**:

```sh
rg -n '量化验收标准必先核基线' ~/.claude/rules/coding-standards.md   # 期望 1 命中
```

- **Rlues 对应路径**: `vibeCoding/claude/9.9.6/rules/coding-standards.md`

## 8. `~/.claude/skills/pace/references/stages.md` · spawn 决策注记 (W5)

- **理由**: P4 是平台语义 (Claude Code isolation), hook 改不了; 可修面是编排知识。带
  `isolation: worktree` 的 subagent 写不了主仓 `.ai_state/` 与 `architecture/`; 而改动对象在项目
  repo 之外时 (如本 sprint 改 `~/.claude`), worktree 对它零隔离效果却照样阻断写入。
- **复核命令**:

```sh
rg -n '不加 `isolation: worktree`' ~/.claude/skills/pace/references/stages.md   # 期望 1 命中
```

- **Rlues 对应路径**: `vibeCoding/claude/9.9.6/skills/pace/references/stages.md`

---

## 9. G1-G5 · gate 契约可见性与派工时序 (W10, 2026-07-28)

- **理由**: 门禁的机器判据 (标题白名单 / 仅列表项 / 保留元标号 11-12 / critic 字面计数 / per-AC
  evidence 绑定) 从不出现在它所约束的模板里 = 隐藏考纲。消费侧一次 Refactor sprint 因此三个写者
  整轮撞墙。设计见 sprint `2026-07-25-athena-9-9-6-prompt-engineering` design §12 + annex。
  **纯文档面, 零 hook 改动。**
- **改了什么** (安装态 10 文件, 与 Rlues 发行件逐字节同步):

  | 落点 | 改动 |
  |---|---|
  | `~/.{claude,codex}/skills/pace/templates/sprints/design.md` | 加 ≤20 行「⚙ 机器契约」注记块; **清除模板自带的幻影 critic 轮次段头** |
  | `~/.{claude,codex}/skills/pace/references/stages.md` | ship 段加 per-AC 绑定义务 + admissible 三形态; impl 加 step 0 派工时序 |
  | `~/.{claude,codex}/skills/pace/templates/sprints/route-note.md` | 加「已验证基线」表 + 两句硬边界 |
  | `~/.claude/rules/coding-standards.md` · `~/.codex/standards/coding-standards.md` | 加 P1 类型不可见依赖检索清单 |
  | `~/.claude/rules/doc-style.md` · `~/.codex/standards/doc-style.md` | 加量化 AC 记法 (禁 `≥`) |

- **备份 (唯一回滚路径)**: `~/.claude/backups/*.pre-g1g5-20260728T024943Z` (6) +
  `~/.codex/backups/*.pre-g1g5-20260728T024943Z` (6)。
- **复核命令** (每条锚定到被改的那一处, 不用全文件计数 —— 见下方 2026-07-28 复核记录的判据沉淀):

```sh
# 注记块五锚点 (每份模板各 ≥1)
for f in ~/.claude/skills/pace/templates/sprints/design.md ~/.codex/skills/pace/templates/sprints/design.md; do
  for t in ACCEPTANCE_HEAD isPlaceholderCriterion validateCriticRounds validateMetaAcceptance validateAcMapping; do
    printf '%s %s=%s\n' "$f" "$t" "$(grep -c "$t" "$f")"; done; done
# 幻影 critic 轮次已清除 (两份均须 = 0)
grep -c 'Critic Findings' ~/.claude/skills/pace/templates/sprints/design.md \
                          ~/.codex/skills/pace/templates/sprints/design.md
# stages: 绑定义务 + 派工 step0 + 禁正则复刻 (各 ≥1)
rg -c 'ac_id\|covers' ~/.claude/skills/pace/references/stages.md ~/.codex/skills/pace/references/stages.md
rg -c '派工时序' ~/.claude/skills/pace/references/stages.md ~/.codex/skills/pace/references/stages.md
rg -c '禁止.*手搓正则复刻' ~/.claude/skills/pace/references/stages.md ~/.codex/skills/pace/references/stages.md
# route-note 基线节边界句 (各 1)
rg -c '不得退化为采信不复核' ~/.claude/skills/pace/templates/sprints/route-note.md \
                              ~/.codex/skills/pace/templates/sprints/route-note.md
# rules 两条 (各 1)
rg -c '必须能抓住该 AC 自己要防的那类失败' ~/.claude/rules/coding-standards.md ~/.codex/standards/coding-standards.md
rg -c '量化 AC 记法' ~/.claude/rules/doc-style.md ~/.codex/standards/doc-style.md
```

- **行为面复核 (最强的一条, AC20)**: 红绿对照产物
  `sprints/2026-07-25-athena-9-9-6-prompt-engineering/ac20-red-green.txt`
  (sha256 `1a5c0627f1acb2e9d174493525c6483c330bf18eb525e35d7c2dd06c7c5e9479`) ——
  改后模板骨架不被 spec-gate 拦; CJK 序号 + 表格形态仍被 fail-closed 拦且 reason 正确。
- **Rlues 对应路径**: `vibeCoding/claude/9.9.6/.claude/{skills/pace/{templates/sprints,references},rules}/` +
  `vibeCoding/codex/9.9.6/.codex/{skills/pace/{templates/sprints,references},standards}/` (10 文件)。
- **已知不对称 (登记, 非缺陷)**: CX `route-note.md` 安装态版本行仍写 v9.9.3 (发行件 v9.9.6);
  CX `doc-style.md` 无 CC 的「tdd-evidence backfill 记法」段。二者均为本刀之前的既存差异, 未顺手改。

## 复核记录

### 2026-07-28 · 全量逐条复跑 (8/8 存活)

备份两份均在 (`delivery-gate.{cjs,py}.pre-p1p8-20260725T153939Z`)。八条补丁全部命中, 无一被升级覆盖。

**但三条的"期望命中数"已失真, 需在 G6/AC28 一并修正** —— 台账的判据是"0 命中 = 已被覆盖",
命中数偏大不代表补丁失效, 但写着"期望 1"却实测 2 会让下一个复核者误判, 削弱机制本身:

| 条 | 复核命令 | 台账写的期望 | 2026-07-28 实测 | 原因 |
|---|---|---|---|---|
| W3 | `rg -c 'path-format=absolute' delivery-gate.cjs` | 1 | **2** | 2026-07-27 治理哈希/熔断修复新增了第二处调用 |
| W9 | 同上, `delivery-gate.py` | 1 | **2** | 同上, CX 侧对称 |
| W8 | `rg -c 'harness-patches' <两端>` | 两端各 1 | **cjs 4 / py 3** | 期望值只算了 `isLightShipFile` 那一处, 未计 P2/P3/P1 修复的注释引用 |

**修正方向** (不在本次改, 留给 G6): W8 的复核命令应收窄到护栏本身
(`rg -c 'harness-patches\.md\$' ...` 或直接匹配 `isLightShipFile` 内那行), 而不是全文件计数;
W3/W9 改为 `≥1` 或同样锚定到 `tryRepoRoot` / `git_root` 函数体内。
**判据沉淀: 复核命令必须锚定到被修的那一处, 全文件计数会随无关改动漂移。**

## 已知验证缺口 / 观察 (不在本 sprint 修)

- **Rlues `vibeCoding/scripts/test-delivery-gate.py:14-15` 硬编码指向 9.9.0 老副本**: 跑绿与安装态这份
  gate 无关, 故本 sprint **不拿它当回归基线** (design Round 3 F14), 全部以 G1-G5 为准。未改它。
- **`.gitignore:28` 把 `.ai_state/**/evidence.yaml` 排除在版本控制之外**, 而 `review-manifest.yaml`
  会声明它的 sha256 → 任何新检出 (worktree / clone) 都必然 `review-manifest target missing:
  evidence.yaml`。批次 3 存档即如此 (manifest 声明了哈希, 文件从未进 git)。P3 修复让 gate 改用主仓
  解析, 症状被绕开, 但"契约声明了一个 git 不携带的文件"这条**结构性矛盾仍在**, 建议后续 sprint 处理。


## 2026-07-29 · hotfix2 实现批次 (W35-W40, Codex Sol 设计 × Fable 实现)

> 设计: `sprints/2026-07-29-athena-9-9-6-hotfix2/design.md` (含 Round 2 Fable critic F1-F8)。用户授权直接实现。

| 条 | 内容 | 复核命令 (0 命中 = 已被覆盖) |
|---|---|---|
| W35 | 双端 evidence 脱敏 (redact command) + tool-trace 停产 + CX result 归一 (F8 解析死锁) + .gitignore 遥测退出。**supersede W21/W33**: token-usage 已从默认 lifecycle 整体退出 (settings/hooks.json 布线删除), 旧复核命令失效属预期 | `rg -c 'W35' evidence-collector.cjs evidence-collector.py` (各 ≥1) · `rg -c redact evidence-collector.py` ≥2 |
| W36 | re-route 数据源 tool-trace → git 三探针 (diff/cached/untracked), **supersede W18** 数据源部分 | `rg -c 'W36' index-updater.cjs index-updater.py` (各 1) |
| W37 | breadcrumb 去 next_action + 预算 240B (双端); next_action 枚举告警 (index-updater 双端) + 模板注释 | `rg -c 'W37' stage-breadcrumb.cjs user-prompt-submit.py` (各 1) |
| W38 | AC11/12 保留标号豁免 + meta-acceptance 双端删除; 模板 annex 契约刷 opt-in (P0-3) | `rg -c 'W38' delivery-gate.cjs delivery-gate.py` (各 ≥2) |
| W39 | CX SessionStart 移植未消解 GateEscalated 告警 (与 CC 对齐, 冒烟实证) | `rg -c 'W39' session-start.py` ≥1 |
| W40 | binding 握手只绑 writer/generator (orchestration ×2); P0-1 CX 只读角色豁免 (READONLY_ROLES); config.toml 清 openai_base_url/context_window/auto_compact; roadmap 地板 ≥3模块 → ≥2 独立切片 (宪法/SKILL/athena-dev/stages 六处); Stop 只留 gate、PreCompact 删除 (双端布线) | `rg -c 'W40' orchestration.md` ×2 · `rg -c READONLY_ROLES subagent-worktree-audit.py` · `rg -c openai_base_url config.toml` (=0) |

- 官方合同实证: CX Stop 仅 additionalContext **不续轮** (需 decision:block) — continuator 删除安全; codex config 默认值文档截断, 保持待验证。
- 新仪器: `vibeCoding/scripts/athena-metrics.py` (git 单源, AC2/AC9 口径)。
- 安装态需同步本批 (~20 文件); 同步后在安装态复跑 W10-W40 复核命令 + validator。

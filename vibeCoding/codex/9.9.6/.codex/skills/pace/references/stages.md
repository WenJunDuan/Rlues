# PACE References · Stages (v9.9.6, Codex)

> 从 pace/SKILL.md 下沉的 stage 详解. 进入某 stage 前 Read 对应段即可, 不必全读.

## brainstorm (借 CodeStable + Superpowers)

**触发**: 用户描述模糊 / 显式说 "想法不清楚" / 无法直接写出可验收标准
**职责**: 多轮对话理清楚, 不评估不约束
**产出**: `sprints/{date}-{slug}/brainstorm.md`
**路由**: → plan (清晰) / → roadmap (大需求) / → design (System 路径需求清晰)
**详**: `~/.agents/skills/brainstorm/SKILL.md`

## roadmap (借 CodeStable)

**触发**: ≥3 模块需求 / 显式 "拆分" / brainstorm 收敛后大需求
**职责**: 拆 feature 序列, 产出 items.yaml + roadmap.md
**调度**: delivery-gate 与主 agent 在 ship 后核对 roadmap, 不依赖某个 shell 输出自动推进
**详**: `~/.agents/skills/roadmap/SKILL.md`

## plan (强制 critique 多轮)

**进入条件**: brainstorm/roadmap 完成, 或需求清晰直接进 (入口审议已落盘 route-note, 见 pace SKILL)
**工作流**:
1. Codex `plan_mode_reasoning_effort = "xhigh"` 已在 config.toml 生效;
   `_index.plan_model: opus` 为 CC 端专属 (Opus 5 审议); CX 端使用 xhigh reasoning effort
2. 用 xhigh 写 `design.md` `## Round 1` 段
3. `spawn_agent` 启动 critic (独立 context)
4. critic 返回 `## Round N · Critic Findings`; 主 agent 追加到 design.md
5. NEEDS_REVISION → 主 agent 再 xhigh 修订, 写 `## Round N+1`, 再 critic
6. **最多 `_index.plan_critique_max_rounds` 轮** (默认 4, 可调 2-6); **最少轮数 (2026-07-28 gate-descaling)**: 全路径默认 ≥1 轮 (`plan_critique_min_rounds` 可覆写调高; delivery-gate 在 ship 机械验 design.md 的 Critic Findings **标题行**数 — 正文提及不计数, P10 修复)。critic 只输出反例清单 (P0/P1 findings + VERDICT), 不写评分表不写散文
7. PASS → 进 impl (单模块) 或 design (System 路径)

**例外**: `_index.plan_critique_disabled = true` 关闭多轮 (用户自负责)

## design (System 路径)

System 路径专用, plan 通过后进 design 出详细架构. 可 `spawn_agent` 启动只读 architect; 主 agent 把返回提案写入 design.md.

## impl (铁律[零写入] 按区路由)

**工作流**:
0. **派工时序 (2026-07-28, 实测驱动)** — 三条, 违反会让在飞写者整轮撞墙:
   - **翻 stage 先于派工**: `stage` 进 impl (含 `current_sprint_slug` 切换) 必须在**首次 `spawn_agent` 之前**完成。
     delivery-gate 挂 PreToolUse 写入类工具, 且从**主 checkout** 解析 `_index.md` ——
     worktree 里的写者同样受主仓 stage 支配, 门禁从翻转那一刻起对所有在飞写者即时生效。
   - **派工前自检 AC 段可被 gate 解析**: 合成一个 PreToolUse payload 喂**安装态 gate 本体**,
     期待无 block 决策。**禁止**手搓正则复刻 gate 判据 —— 复刻品与 gate 双写必漂, 是新的隐藏考纲。
     ```sh
     printf '{"cwd":"%s","hook_event_name":"PreToolUse","tool_name":"Write",
       "tool_input":{"file_path":"%s/src/__gate_probe__"}}' "$PWD" "$PWD" \
       | python3 ~/.codex/hooks/delivery-gate.py; echo "exit=$?"   # 期望: 无输出, exit 0
     ```
   - **在飞写者存在时禁改 stage**: `active_worktrees` 非空, 或 subagent-events 有未配对 Start 时,
     不得修改 `_index` 的 `stage` / `current_sprint_slug`。
1. **done_contract 写进 design.md 的 `## Done Contract` 段** (2026-07-28 gate-descaling: 不再单立 checklist.yaml, 消灭双写):
   逐条把验收标准写成**可机械判定**的完成条件 (命令 + 期望输出 / 文件 + 断言)。
   铁律: generator 与 evaluator 判的是**同一份 done_contract**; evaluator 不得在 review 时另造判据,
   generator 也不得自行放宽。判据要改 → 回 design 改, 不在 impl 里私改。
   checklist.yaml 降为**可选** (超大 sprint 需要任务推进表时才建; 存在则 delivery-gate 照旧验全绿)
2. 绿区任务 (≤3 文件且合计 ≤150 行, 或 Hotfix/Quick/Bugfix): 主 thread 直接做, 不强制 spawn_agent
3. 黄区: `spawn_agent` 启动 generator (TDD: 测试先, 代码后); Feature+ 必须留下 generator 的 **Stop 完成记录**, 仅 Start 记录不算完成
4. 红区 (Refactor/System): 主 thread 先 `git worktree add`, 再把 worktree 绝对路径与互斥写集写进 `spawn_agent.message`; agent 首个命令 `pwd`, 后续 shell 显式 `workdir`
5. 并行多 generator (大改): 也强制 worktree
6. 超大规模 (≥5 独立同构子任务): 评估 multi-agent v2 fan-out, 见 `references/orchestration.md`
7. hooks 记录其实际收到的工具调用; 未观察到的写入由主 agent 用 `git diff --stat` / `git diff` 补证
8. v9.9.0: index-updater 检测改动文件数超路径上限 (Quick>3/Feature>10) → next_action=re-route,
   主 agent 停当前 task 重走路由审议 (只升不降, 补新路径欠的 stage)

## runtime-verify (v9.8.0, System/Refactor 强制 · Feature 可选)

impl 写完代码 + 单测后, 不直接进 review, 先做运行时自测自改:
- 用 `/goal` 承载 (**双端**: Codex goals 自 rust-v0.133.0 起 default-on 且不再 experimental —
  不自造循环, 铁律[不抱金饭碗讨饭]): 实跑接口 + 模拟数据 (正常/边界/异常) + 不同环境 →
  测出问题自己改 → 复跑到完成条件满足
- v9.9.0: `_index.tools_available.vm_available=true` → 环境矩阵加**远程 VM 实跑** (`ssh athena-vm-{name} '...'`, 见 /athena-vm)
- 前端/E2E 用 `$playwright` skill 写可复跑测试; browser + computer-use plugin 仅作探索/人工式冒烟; 后端用 curl/真实调用; CLI 用实际命令 + 退出码断言
- ⚠️ 完成判定只看对话里展示的: 完成条件写成"把实跑命令 + 输出晒进对话"
- 出口 reflect: 对照 design + 实跑发现, 列"还有哪里没完善" → 回 impl 补 或 进 review
- 详见 skill: `/athena-runtime-verify`
- 产出: `sprints/{slug}/runtime-verify.md` (delivery-gate.py 在 ship 时验存在 + 含 `## 测试场景` 段)

## review (6 维度)

**两步执行**:
1. 并行 `spawn_agent`: reviewer (代码 findings) + spec-compliance (MISSING/EXTRA/DEVIATED); 两者只返回结果
2. 主 agent 串行合并 `reviews/passN.md`, 再 `spawn_agent` 跑 evaluator; evaluator 只返回 VERDICT, 主 agent 追加并更新 `_index.next_action`

**passN.md 产物约定 (2026-07-28 gate-descaling)**: 只写 P0/P1 findings + Spec Compliance 表 + Evidence Cross-Check (R/S) + 绑定行 + VERDICT。禁复述实现、禁逐文件叙事; P2/INFO 一行带过。目标 ≤120 行 — review 的价值在判定, 不在散文。

VERDICT 四象限: **PASS | CONCERNS | REWORK | FAIL**
- PASS (Refactor/System) → polish
- PASS (其他) → ship
- CONCERNS / REWORK / FAIL → 回 impl 或修复/defer 后生成新 passN；不得直接 polish/ship

> 注: review stage 不靠 Stop hook 同步；主 agent 用原生 wait 收齐两个返回，并且只有主 agent 写 review 产物。
> spec-compliance 完整性由 delivery-gate 在 **ship** stage 检查 (此时产物已落盘).

## polish (Refactor/System 强制)

`spawn_agent` 启动 polish worker:
- 5 检查项 (临时代码 / 注释 / 冗余 / 低效 / 过度设计)
- finishing-a-development-branch (借 Superpowers): 跑测试 + 提示 merge/PR/继续/丢弃 + 清理 worktree
- 产出 `cleanup-pass.md`
- 触发 architecture/ 更新 (≥5 文件改动)

## ship

主 agent commit + push. delivery-gate 检查:
- Refactor/System: 必须有 cleanup-pass.md
- Refactor/System (≥5 文件): 必须更新 architecture/ (铁律[门禁]); 文件数优先用 git diff 现场计算, evidence.yaml 为辅
- design_changed_after_impl=true: block 直到重新 review
- Feature/Refactor/System: pass1.md 必须含 `## Spec Compliance` 段
- v9.9.0: Refactor/System 的 pass1.md 必须含 `## Evidence Cross-Check` 段 (U3)
- v9.9.0 (U1): Feature+ 的 subagent-log.md 必须含 generator 记录 (逃生: skip_impl_subagent_check)
- design.md 的 Critic Findings **标题行** ≥ min 轮 (默认全路径 1; plan_critique_min_rounds 覆写); design.md >300 行 stderr 警告
- review-manifest 必钉集: 全路径 design.md; R/S 另加 runtime-verify.md (checklist/evidence/cleanup/architecture 改为声明即验, 不强制钉)
- checklist.yaml 存在才验; 记账文件 (token-usage/tool-trace/stop-failures/harness-patches/proposals) 不受 post-review drift 拦截
- AC 证据记法 (2026-07-28 W23): 跑真实验证命令后 evidence-collector 已自动落记录, agent 在该记录**补一行 `covers: [ACn]`** 即 admissible; 十字段手写 artifact 记录仅当命令证据不适用 (source: artifact/review) 时用
- v9.9.0: design.md mtime 晚于 pass1.md → block 重新 review (CC=兜底 / CX=主检测)
- current_roadmap_slug 非空: 提示主 agent 继续下个 item
- 长任务建议: ship 前核对 Goals 完成条件, 承载铁律[门禁] Sisyphus 语义 (见 references/orchestration.md)

**per-AC 证据绑定义务 (2026-07-28 新增, review PASS 后、翻 ship 前做)**

`validate_ac_mapping` 要求 design.md 里**每条业务 ACn** 在 `evidence.yaml` 有一条 admissible 的绑定记录。
触发条件: 该校验**仅在 `review-manifest.yaml` 存在时执行**, 而 Refactor/System 的 manifest 是强制的
→ **红区必踩**; 其余路径不带 manifest 时业务 AC 完全不绑定 (同一份 AC 强制力差一整级, 别误以为通用)。

⚠️ **hook 自动采集的 evidence 记录不含 `ac_id` / `covers` 两个字段, 一条都不构成绑定**;
写者交的 `tdd-evidence.yaml` 走另一条校验, **不参与 AC 绑定**。
绑定必须是**有意为之的断言** —— 谁声称这条命令/审查覆盖了 ACn, 谁签名 (铁律[证据与出处])。

admissible 三形态速查:

| source | 要求 |
|---|---|
| `command` | `output_artifact` 在 sprint 目录内 + `artifact_sha256` 对得上 + `exit_code: 0` + `implementation_commit` = reviewed commit; 产物内容须含该命令、`exit_code: 0` 行与 summary |
| `artifact` | `command_or_artifact` 指向 sprint 目录内一个真实存在的文件 |
| `review` | **最低成本形态**: 指向最新 passN.md, 前提是该档含 `## Spec Compliance` + `## Evidence Cross-Check` + 逐 AC SATISFIED 行 + 最终 VERDICT PASS |

最低成本路径: review 档写全逐 AC SATISFIED 表 → 每条 ACn 追加一条 `source: review` 记录指向它。
公共字段 (`result: pass` / `source` / `command_or_artifact` / `observed_at` UTC ISO-8601 / `summary`) 缺一即不算。


### 推送门禁 (pre-bash-guard) 与合法放行

两道独立门禁, 合法推送均无需伪造产物:

- **pre-bash-guard** (Bash 前置) 拦 `git push`: 当前项目 stage 非 ship 且非空 (idle) → BLOCK。放行 = 走到 ship 再推, 或 `ATHENA_ALLOW_PUSH=1 git push …` (命令含此标即放行)。后者用于**推非当前 sprint 的维护性改动** (Athena 源仓自身 / 跨仓同步 / sprint 未 ship 但需推的记账 commit) —— **取代"切 stage=ship→推→回 plan"绕行**, 该绕行会连带触发下面的 ship 契约、制造记账噪声。
- **delivery-gate 轻门禁 (v9.9.6)**: ship 时若净 diff (对 upstream) ≤60 行且仅触及文档 / 配置 / 依赖 / `.ai_state` / 测试 (排除 hooks/settings/源码逻辑) → 只校验 roadmap 一致性, 跳过 review-manifest / tdd-evidence / 三件套; 源码 / harness / 超预算仍走完整契约 (fail-closed)。让纯文档 / 依赖类 ship 不再被迫产出机械改动无法诚实给出的 red→green。

## evidence 平台差异 (诚实降级, 铁律[证据与出处] CX 语义)

Codex hooks 可覆盖 shell、`apply_patch` 与部分 MCP 调用, 但是否触发取决于当前工具映射和 matcher; 不把 hook 当完整审计或安全边界.
因此 evidence 链分两层:
1. **过程证据** — evidence-collector.py 采集实际收到的 test/lint/build 调用; 无法确定退出状态时记录 unknown, 不得默认 pass
2. **文件证据** — delivery-gate.py 门禁时用 `git diff --stat` 现场计算变更面

官方说明: https://learn.chatgpt.com/docs/hooks

对等的是**门禁强度**, 不是逐字段照抄 CC.

## 文书预算 (2026-07-28 gate-descaling — 反"程序员变文员")

实测病灶: 9.9.6 主 sprint 写入操作里 `.ai_state` 记账 102 次 vs 代码 15 次 (8.4%)。规则:

- **手写文档白名单**: sprint 目录里 agent 手写的 md 只允许 design.md / reviews/passN.md / (Bugfix) issue-report+fix-note / (R/S) runtime-verify.md + cleanup-pass.md。route-note **并入 `_index.route_history` 一行**, 不再单立文件; *-evidence.md / verification-inventory / session-log 等自造散文**禁止** — 证据走 hook 自动的 evidence.yaml/tool-trace, 不走手写复述
- **体积预算**: design.md 目标 ≤200 行 (System) / ≤80 行 (Feature); 超 300 行 delivery-gate 在 ship 时 stderr 警告 (不 block, 防死锁)。critic 轮次追加不计入
- **判据**: 一个 sprint 内 agent 手写 md 字节数不应超过代码 diff 字节数; 超了 = 文书跑赢了产出, 停下反省而不是继续写

## 新数据目录 (v9.6.4 起)

```
.ai_state/
├── _index.md                          # 项目状态 + frontmatter
├── sprints/
│   └── YYYY-MM-DD-{slug}/             # 一个 sprint 一目录
│       ├── route-note.md              # (可选, 2026-07-28 起) 默认并入 _index.route_history 一行; 仅复杂 re-route 才单立
│       ├── brainstorm.md              # (可选) brainstorm 产出
│       ├── design.md                  # 含 ## Round N · Critic Findings 段
│       ├── checklist.yaml             # (可选, 2026-07-28 起) 超大 sprint 才建; 存在则验全绿
│       ├── issue-report.md            # v9.8.0 Bugfix: 可复现报告 (athena-issue)
│       ├── fix-note.md                # v9.8.0 Bugfix: 修复记录+验证 (delivery-gate 验)
│       ├── runtime-verify.md           # v9.8.0 运行时自测自改 (delivery-gate 验)
│       ├── reviews/pass1.md           # 含 ## Spec Compliance 段
│       ├── cleanup-pass.md            # polish 产出
│       ├── subagent-log.md            # hook 自动写
│       ├── worktrees.yaml             # 主 agent / hooks 记录 worktree 生命周期
│       ├── evidence.yaml              # 可观察工具调用的过程证据
│       └── tool-trace.jsonl           # 可观察工具调用轨迹
├── roadmap/
│   └── {slug}/
│       ├── roadmap.md
│       └── items.yaml
├── architecture/
│   ├── ARCHITECTURE.md
│   └── {type}-{slug}.md
├── requirements/                     # v9.8.0 长效需求档 (WHY, 逃生通道)
│   └── {slug}.md
├── compound/
│   ├── YYYY-MM-DD-learning-{slug}.md
│   ├── YYYY-MM-DD-trick-{slug}.md
│   ├── YYYY-MM-DD-decision-{slug}.md
│   └── YYYY-MM-DD-explore-{slug}.md
└── .snapshots/                        # PreCompact 快照 (CX 0.129+)
```

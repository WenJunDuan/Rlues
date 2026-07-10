# PACE References · Stages (v9.9.1)

> 从 pace/SKILL.md 下沉的 stage 详解. 进入某 stage 前 Read 对应段即可, 不必全读.

## brainstorm (借 CodeStable + Superpowers)

**触发**: 用户描述模糊 / 显式说 "想法不清楚" / 无法直接写出可验收标准
**职责**: 多轮对话理清楚, 不评估不约束
**产出**: `sprints/{date}-{slug}/brainstorm.md`
**路由**: → plan (清晰) / → roadmap (大需求) / → design (System 路径需求清晰)
**详**: `~/.claude/skills/brainstorm/SKILL.md`

## roadmap (借 CodeStable)

**触发**: ≥3 模块需求 / 显式 "拆分" / brainstorm 收敛后大需求
**职责**: 拆 feature 序列, 产出 items.yaml + roadmap.md
**调度**: delivery-gate 与主 agent 在 ship 后核对并推进下一 item
**详**: `~/.claude/skills/roadmap/SKILL.md`

## plan (强制 critique 多轮)

**进入条件**: brainstorm/roadmap 完成, 或需求清晰直接进 (入口审议已落盘 route-note, 见 pace SKILL)
**工作流**:
1. 主 agent 在第一条 message 加 "**ultrathink**" 关键词 (CC v2.1.68+ 触发 32K thinking);
   System/Refactor 且 `_index.plan_model: fable` → 本 stage 用 `/model fable` 切 claude-fable-5 审议
   (Mythos 级, $10/$50 每 Mtok — 只在最贵的决策上花最贵的思考, 用完切回)
2. 用 ultrathink 写 `design.md` `## Round 1` 段
3. 用 CC 当前 subagent 机制调用 read-only critic
4. critic 返回 `## Round N · Critic Findings`; 主 agent 追加到 design.md
5. NEEDS_REVISION → 主 agent 再 ultrathink 修订, 写 `## Round N+1`, 再 critic
6. **最多 `_index.plan_critique_max_rounds` 轮** (默认 4, 可调 2-6); **最少轮数 (v9.9.0 U2)**: Refactor/System ≥2 轮, 其余 ≥1 轮 (`plan_critique_min_rounds` 可覆写, delivery-gate 在 ship 机械验 design.md 的 Critic Findings 数)
7. PASS → 进 impl (单模块) 或 design (System 路径)

**例外**: `_index.plan_critique_disabled = true` 关闭多轮 (用户自负责)

## design (System 路径)

System 路径专用, plan 通过后进 design 出详细架构. 可 spawn `architect` subagent.

## impl (铁律[零写入] 按区路由)

**工作流**:
1. 主 agent 写 `checklist.yaml` (tasks 列表, design_ref 引用)
2. 绿区任务 (单文件 ≤30 行, Hotfix/Quick): 主 agent 直接做, 不强制 subagent
3. 黄区: 调用 generator subagent (TDD: 测试先, 代码后); Feature+ 必须留下 generator 的 Stop 完成记录, 仅 Start 不算完成
4. 红区 (Refactor/System): generator **必须 `isolation: worktree`**
5. 并行多 generator (大改): 也强制 worktree
6. 超大规模 (≥5 独立同构子任务): 评估 ultracode, 见 `references/orchestration.md`
7. PostToolUse hook 自动写 evidence.yaml + tool-trace.jsonl
8. v9.9.0: index-updater 检测改动文件数超路径上限 (Quick>3/Feature>10) → next_action=re-route,
   主 agent 停当前 task 重走路由审议 (只升不降, 补新路径欠的 stage)

## runtime-verify (v9.8.0, System/Refactor 强制 · Feature 可选)

impl 写完代码 + 单测后, 不直接进 review, 先做运行时自测自改:
- 用 `/goal`(CC) 承载: 实跑接口 + 模拟数据 (正常/边界/异常) + 不同环境 → 测出问题自己改 → 复跑到完成条件满足
- v9.9.0: `_index.tools_available.vm_available=true` → 环境矩阵加**远程 VM 实跑** (`ssh athena-vm-{name} '...'`, 见 /athena-vm)
- 前端/E2E 用 `$playwright` skill / 官方 playwright-skill; 后端用 curl/真实调用; CLI 用实际命令 + 退出码断言
- ⚠️ /goal supervisor 只读 transcript: 完成条件写成"把实跑命令 + 输出晒进对话"
- 出口 reflect: 对照 design + 实跑发现, 列"还有哪里没完善" → 回 impl 补 或 进 review
- 详见 skill: `/athena-runtime-verify`
- 产出: `sprints/{slug}/runtime-verify.md` (delivery-gate 在 ship 时验存在 + 含 `## 测试场景` 段)

## review (6 维度)

**两步执行**:
1. 并行运行 reviewer + spec-compliance; 两者只返回结果
2. 主 agent 合并 `reviews/passN.md`, 再运行 evaluator; evaluator 只返回 VERDICT, 主 agent 追加并更新 `_index.next_action`

VERDICT 四象限: **PASS | CONCERNS | REWORK | FAIL**
- PASS / CONCERNS (Refactor/System) → polish
- PASS / CONCERNS (其他) → ship
- REWORK / FAIL → 回 impl

> 注: review stage 本身不设同步 Stop 门禁 (后台 review agent 异步写产物, 同步等待会死锁).
> spec-compliance 完整性由 delivery-gate 在 **ship** stage 检查 (此时产物已落盘).

## polish (Refactor/System 强制)

spawn `polish_worker` subagent:
- 5 检查项 (临时代码 / 注释 / 冗余 / 低效 / 过度设计)
- finishing-a-development-branch (借 Superpowers): 跑测试 + 提示 merge/PR/继续/丢弃 + 清理 worktree
- 产出 `cleanup-pass.md`
- 触发 architecture/ 更新 (≥5 文件改动)

## ship

主 agent commit + push. delivery-gate 检查:
- Refactor/System: 必须有 cleanup-pass.md
- Refactor/System (≥5 文件): 必须更新 architecture/ (铁律[架构])
- design_changed_after_impl=true: block 直到重新 review
- Feature/Refactor/System: pass1.md 必须含 `## Spec Compliance` 段
- v9.9.0: Refactor/System 的 pass1.md 必须含 `## Evidence Cross-Check` 段 (U3)
- v9.9.0 (U1): Feature+ 的 subagent-log.md 必须含 generator 记录 (逃生: skip_impl_subagent_check)
- v9.9.0 (U2): design.md 的 Critic Findings ≥ min 轮 (Refactor/System=2, 其余=1; plan_critique_min_rounds 覆写)
- v9.9.0: design.md mtime 晚于 pass1.md → block 重新 review (CC=兜底 / CX=主检测)
- current_roadmap_slug 非空: 提示主 agent 继续下个 item
- 长任务建议: ship 前用 `/goal` 设完成条件, 承载铁律[Sisyphus] (见 references/orchestration.md)

## 新数据目录 (v9.6.4 起)

```
.ai_state/
├── _index.md                          # 项目状态 + frontmatter
├── sprints/
│   └── YYYY-MM-DD-{slug}/             # 一个 sprint 一目录
│       ├── route-note.md              # v9.9.0 路由审议落盘 (候选/权衡/置信度/Re-route)
│       ├── brainstorm.md              # (可选) brainstorm 产出
│       ├── design.md                  # 含 ## Round N · Critic Findings 段
│       ├── checklist.yaml             # impl 推进清单
│       ├── issue-report.md            # v9.8.0 Bugfix: 可复现报告 (athena-issue)
│       ├── fix-note.md                # v9.8.0 Bugfix: 修复记录+验证 (delivery-gate 验)
│       ├── runtime-verify.md           # v9.8.0 运行时自测自改 (delivery-gate 验)
│       ├── reviews/pass1.md           # 含 ## Spec Compliance 段
│       ├── cleanup-pass.md            # polish 产出
│       ├── subagent-log.md            # SubagentStop hook 自动写
│       ├── worktrees.yaml             # WorktreeCreate/Remove hook 自动写
│       ├── evidence.yaml              # PostToolUse 收集 tool_use ID
│       └── tool-trace.jsonl           # 每个 tool call 一行
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
└── .snapshots/                        # PreCompact 快照
```

# PACE References · Stages (v9.8.0)

> 从 pace/SKILL.md 下沉的 stage 详解. 进入某 stage 前 Read 对应段即可, 不必全读.

## brainstorm (借 CodeStable + Superpowers)

**触发**: 用户描述模糊 / 显式说 "想法不清楚" / 单词级模糊 (≤8 词无具体动词)
**职责**: 多轮对话理清楚, 不评估不约束
**产出**: `sprints/{date}-{slug}/brainstorm.md`
**路由**: → plan (清晰) / → roadmap (大需求) / → design (System 路径需求清晰)
**详**: `~/.claude/skills/brainstorm/SKILL.md`

## roadmap (借 CodeStable)

**触发**: ≥3 模块需求 / 显式 "拆分" / brainstorm 收敛后大需求
**职责**: 拆 feature 序列, 产出 items.yaml + roadmap.md
**调度**: SubagentStop hook 自动推进下一 item
**详**: `~/.claude/skills/roadmap/SKILL.md`

## plan (强制 critique 多轮)

**进入条件**: brainstorm/roadmap 完成, 或需求清晰直接进
**工作流**:
1. 主 agent 在第一条 message 加 "**ultrathink**" 关键词 (CC v2.1.68+ 触发 32K thinking)
2. 用 ultrathink 写 `design.md` `## Round 1` 段
3. Task tool 调用 `critic` subagent (独立 context, 防自我锚定 — 借 OMO Metis 思路)
4. critic 追加 `## Round N · Critic Findings` 段, VERDICT: PASS | NEEDS_REVISION
5. NEEDS_REVISION → 主 agent 再 ultrathink 修订, 写 `## Round N+1`, 再 critic
6. **最多 `_index.plan_critique_max_rounds` 轮** (默认 4, 可调 2-6)
7. PASS → 进 impl (单模块) 或 design (System 路径)

**例外**: `_index.plan_critique_disabled = true` 关闭多轮 (用户自负责)

## design (System 路径)

System 路径专用, plan 通过后进 design 出详细架构. 可 spawn `architect` subagent.

## impl (铁律[零写入] 按区路由)

**工作流**:
1. 主 agent 写 `checklist.yaml` (tasks 列表, design_ref 引用)
2. 绿区任务 (单文件 ≤30 行, Hotfix/Quick): 主 agent 直接做, 不强制 subagent
3. 黄区: Task tool 调用 `generator` subagent (TDD: 测试先, 代码后)
4. 红区 (Refactor/System): generator **必须 `isolation: worktree`**
5. 并行多 generator (大改): 也强制 worktree
6. 超大规模 (≥5 独立同构子任务): 评估 ultracode, 见 `references/orchestration.md`
7. PostToolUse hook 自动写 evidence.yaml + tool-trace.jsonl

## runtime-verify (v9.8.0, System/Refactor 强制 · Feature 可选)

impl 写完代码 + 单测后, 不直接进 review, 先做运行时自测自改:
- 用 `/goal`(CC) 承载: 实跑接口 + 模拟数据 (正常/边界/异常) + 不同环境 → 测出问题自己改 → 复跑到完成条件满足
- 前端/E2E 用 `$playwright` skill / 官方 playwright-skill; 后端用 curl/真实调用; CLI 用实际命令 + 退出码断言
- ⚠️ /goal supervisor 只读 transcript: 完成条件写成"把实跑命令 + 输出晒进对话"
- 出口 reflect: 对照 design + 实跑发现, 列"还有哪里没完善" → 回 impl 补 或 进 review
- 详见 skill: `/athena-runtime-verify`
- 产出: `sprints/{slug}/runtime-verify.md` (delivery-gate 在 ship 时验存在 + 含 `## 测试场景` 段)

## review (6 维度)

**并行 spawn 3 个 subagent**:
1. `reviewer` (代码层 findings: bug/security/test/quality)
2. `spec-compliance` (design ↔ git diff: MISSING/EXTRA/DEVIATED, 借 CodeStable cs-feat-accept + OpenSpec /opsx:verify)
3. `evaluator` (后跑, 综合 VERDICT, 写 `_index.next_action`)

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
- current_roadmap_slug 非空: 提示主 agent 继续下个 item
- 长任务建议: ship 前用 `/goal` 设完成条件, 承载铁律[Sisyphus] (见 references/orchestration.md)

## 新数据目录 (v9.6.4 起)

```
.ai_state/
├── _index.md                          # 项目状态 + frontmatter
├── sprints/
│   └── YYYY-MM-DD-{slug}/             # 一个 sprint 一目录
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

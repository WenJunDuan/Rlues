---
name: pace
description: |
  PACE 路由 + 8 stage 状态机. Athena 项目的中枢. 主 agent 进入任何 sprint 前必读.
  v9.6.4 升级: 新增 brainstorm + roadmap stage, sprints/ 替代 details/, compound/ 颗粒化, 接入 ultrathink/critic, spec-compliance 等.
effort: high
---

# PACE — Router & State Machine (v9.6.4)

## 6 路径

主 agent 收到用户输入后, 按改动量 + 紧急度判定路径:

| 路径 | 触发 | stage 流程 | 强制 review? | 强制 polish? | 强制 worktree? |
|---|---|---|---|---|---|
| **Hotfix** | 生产事故, 几分钟修 | impl → ship | ❌ | ❌ | ❌ |
| **Bugfix** | 已知 bug, 单文件 | plan → impl → review → ship | ✅ 单维 | ❌ | ❌ |
| **Quick** | 小改动, ≤3 文件 | plan → impl → review → ship | ✅ 单维 | ❌ | ❌ |
| **Feature** | 新功能, 单模块 | plan → impl → review → ship | ✅ 单维 | ❌ | ❌ (可选) |
| **Refactor** | 改架构, ≥5 文件 | plan → impl → review → polish → ship | ✅ 三维度 | ✅ | ✅ 强制 |
| **System** | 跨模块, 系统级 | plan → design → impl → review → polish → ship | ✅ 三维度 | ✅ | ✅ 强制 |

## 8 Stage 状态机

```
                          (大需求或描述模糊时)
                                ↓
[brainstorm] ──→ [roadmap] ──→ plan ──→ [design] ──→ impl ──→ review ──→ [polish] ──→ ship
   (新)           (新)          ↑           (System)              (3 维度)         (Refactor/System)
                                ultrathink + critic 多轮
```

### brainstorm (新, 借 CodeStable + Superpowers)

**触发**: 用户描述模糊 / 显式说 "想法不清楚" / 单词级模糊 (≤8 词无具体动词)
**职责**: 多轮对话理清楚, 不评估不约束
**产出**: `sprints/{date}-{slug}/brainstorm.md`
**路由**: → plan (清晰) / → roadmap (大需求) / → design (System 路径需求清晰)
**详**: `~/.agents/skills/_athena/brainstorm/SKILL.md`

### roadmap (新, 借 CodeStable)

**触发**: ≥3 模块需求 / 显式 "拆分" / brainstorm 收敛后大需求
**职责**: 拆 feature 序列, 产出 items.yaml + roadmap.md
**调度**: SubagentStop hook 自动推进下一 item
**详**: `~/.agents/skills/_athena/roadmap/SKILL.md`

### plan (强制 critique 多轮, v9.6.4 升级)

**进入条件**: brainstorm/roadmap 完成, 或需求清晰直接进
**工作流**:
1. 主 agent 在第一条 message 加 "**ultrathink**" 关键词 (Codex plan_mode_reasoning_effort = "xhigh")
2. 用 ultrathink 写 `design.md` `## Round 1` 段
3. spawn_agent `critic` subagent (独立 context, 防自我锚定 — 借 OMO Metis 思路)
4. critic 追加 `## Round N · Critic Findings` 段, VERDICT: PASS | NEEDS_REVISION
5. NEEDS_REVISION → 主 agent 再 ultrathink 修订, 写 `## Round N+1`, 再 critic
6. **最多 `_index.plan_critique_max_rounds` 轮** (默认 4, 可调 2-6)
7. PASS → 进 impl (单模块) 或 design (System 路径)

**例外**: `_index.plan_critique_disabled = true` 关闭多轮 (用户自负责)

### design (System 路径)

System 路径专用, plan 通过后进 design 出详细架构. 可 spawn `architect` subagent.

### impl (subagent 始终用, 铁律 12)

**工作流**:
1. 主 agent 写 `checklist.yaml` (tasks 列表, design_ref 引用)
2. spawn_agent `generator` subagent (TDD: 测试先, 代码后)
3. Refactor/System: generator **必须 `主 thread `git worktree add` + spawn_agent --cwd`** (铁律 12)
4. 并行多 generator (大改): 也强制 worktree
5. PostToolUse hook 自动写 evidence.yaml + tool-trace.jsonl

### review (6 维度, v9.6.4 升级)

**并行 spawn 3 个 subagent**:
1. `reviewer` (代码层 findings: bug/security/test/quality)
2. `spec-compliance` (design ↔ git diff: MISSING/EXTRA/DEVIATED, 借 CodeStable cs-feat-accept + OpenSpec /opsx:verify)
3. `evaluator` (后跑, 综合 VERDICT, 写 `_index.next_action`)

VERDICT 四象限: **PASS | CONCERNS | REWORK | FAIL**
- PASS / CONCERNS (Refactor/System) → polish
- PASS / CONCERNS (其他) → ship
- REWORK / FAIL → 回 impl

**Stop hook prompt 类型** (官方 2026-03+) 自动检查 `## Spec Compliance` 段存在, 不存在 block.

### polish (Refactor/System 强制)

spawn `polish_worker` subagent:
- 5 检查项 (临时代码 / 注释 / 冗余 / 低效 / 过度设计)
- finishing-a-development-branch (借 Superpowers): 跑测试 + 提示 merge/PR/继续/丢弃 + 清理 worktree
- 产出 `cleanup-pass.md`
- 触发 architecture/ 更新 (≥5 文件改动)

### ship

主 agent commit + push. delivery-gate 检查:
- Refactor/System: 必须有 cleanup-pass.md (沿用 v9.6.2)
- Refactor/System (≥5 文件): 必须更新 architecture/ (铁律 15)
- design_changed_after_impl=true: block 直到重新 review
- current_roadmap_slug 非空: 提示主 agent 继续下个 item

## 新数据目录 (v9.6.4)

```
.ai_state/
├── _index.md                          # 项目状态 + frontmatter
├── sprints/                           # 🆕 替代 details/
│   └── YYYY-MM-DD-{slug}/             # 一个 sprint 一目录
│       ├── brainstorm.md              # (可选) brainstorm 产出
│       ├── design.md                  # 含 ## Round N · Critic Findings 段
│       ├── checklist.yaml             # impl 推进清单
│       ├── reviews/pass1.md           # 含 ## Spec Compliance 段
│       ├── cleanup-pass.md            # polish 产出
│       ├── subagent-log.md            # SubagentStop hook 自动写
│       ├── worktrees.yaml             # WorktreeCreate/Remove hook 自动写
│       ├── evidence.yaml              # PostToolUse 收集 tool_use ID
│       └── tool-trace.jsonl           # 每个 tool call 一行
├── roadmap/                           # 🆕 大需求拆分
│   └── {slug}/
│       ├── roadmap.md
│       └── items.yaml
├── architecture/                      # 🆕 长效架构档
│   ├── ARCHITECTURE.md
│   └── {type}-{slug}.md
├── compound/                          # 🆕 替代 lessons.md (颗粒化)
│   ├── YYYY-MM-DD-learning-{slug}.md
│   ├── YYYY-MM-DD-trick-{slug}.md
│   ├── YYYY-MM-DD-decision-{slug}.md
│   └── YYYY-MM-DD-explore-{slug}.md
└── .snapshots/                        # (沿用) PreCompact 快照
```

## 路由判断 (在 athena-dev 入口)

```python
def route(user_input, ai_state):
    # 1. 显式信号
    if explicit_kws(["想法不清楚", "先 brainstorm", "讨论"]):
        return "brainstorm"
    if explicit_kws(["路线图", "分步推进", "拆分"]):
        return "roadmap"
    if explicit_kws(["bug", "修复"]):
        return "Bugfix"
    if explicit_kws(["重构", "refactor"]):
        return "Refactor"

    # 2. 隐式: 单词级模糊 → brainstorm (铁律 14)
    if len(user_input.split()) < 8 and not has_concrete_verb(user_input):
        return "brainstorm"

    # 3. ≥ 3 模块需求 → roadmap (铁律 14)
    if mentions_modules(user_input) >= 3:
        return "roadmap"

    # 4. 默认: 按改动量分 Feature/Quick/Hotfix
    return classify_by_scope(user_input)
```

## Hook 联动

| Hook 事件 | 文件 | 职责 |
|---|---|---|
| SessionStart | session-start.cjs | 注入 _index.md + stage-specific 操作提示 |
| PreToolUse(Bash) | pre-bash-guard.cjs | 灾难命令拦截 |
| PreToolUse(Task) | subagent-worktree-check.cjs | 铁律 12 强制 (大功能 → worktree) |
| PostToolUse(Edit/Write/MultiEdit) | index-updater + evidence-collector + design-change-detector | 状态同步 / 证据收集 / design 变更标记 |
| PostToolUse(Bash) | evidence-collector | 命令证据 |
| PostToolUse(Task) | subagent-retry | 失败重试建议 |
| SubagentStop | subagent-tracker.cjs | 写 subagent-log + roadmap 自动推进 |
| WorktreeCreate / WorktreeRemove | worktree-tracker.cjs | worktrees.yaml + active_worktrees |
| Stop | prompt 类型 + delivery-gate.cjs + pace-continuator.cjs | 智能 stage 推进 + 交付门 |
| PreCompact / PostCompact | compact-snapshot/restore.cjs | 跨 compact 状态恢复 |

## compound 联动 (铁律 13)

- plan stage 开始: 主 agent 读 `_index.pointers.latest_decisions` 列出的 5 个 `decision-*.md`
- design stage: grep 关键词读相关 `learning-*.md` + `trick-*.md`
- polish stage 完成: 触发 `/compound add learning` 提示
- review 发现 P0: reviewer 触发 `/compound add learning`

详: `~/.agents/skills/_athena/compound/SKILL.md`

## 项目级例外 (用户可调)

- `_index.skip_polish = true`: 跳过 polish (用户自负责)
- `_index.skip_architecture_check = true`: 跳过 architecture mtime 检查
- `_index.plan_critique_disabled = true`: 关闭多轮 critique
- `_index.plan_critique_max_rounds = N`: 调整最大轮数 (2-6)

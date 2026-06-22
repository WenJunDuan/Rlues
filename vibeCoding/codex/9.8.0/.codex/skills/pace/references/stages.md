# PACE References · Stages (v9.8.0, Codex)

> 从 pace/SKILL.md 下沉的 stage 详解. 进入某 stage 前 Read 对应段即可, 不必全读.

## brainstorm (借 CodeStable + Superpowers)

**触发**: 用户描述模糊 / 显式说 "想法不清楚" / 单词级模糊 (≤8 词无具体动词)
**职责**: 多轮对话理清楚, 不评估不约束
**产出**: `sprints/{date}-{slug}/brainstorm.md`
**路由**: → plan (清晰) / → roadmap (大需求) / → design (System 路径需求清晰)
**详**: `~/.codex/skills/brainstorm/SKILL.md`

## roadmap (借 CodeStable)

**触发**: ≥3 模块需求 / 显式 "拆分" / brainstorm 收敛后大需求
**职责**: 拆 feature 序列, 产出 items.yaml + roadmap.md
**调度**: subagent-retry hook (PostToolUse Bash) 检测 ship 完成自动推进下一 item
**详**: `~/.codex/skills/roadmap/SKILL.md`

## plan (强制 critique 多轮)

**进入条件**: brainstorm/roadmap 完成, 或需求清晰直接进
**工作流**:
1. Codex `plan_mode_reasoning_effort = "xhigh"` 已在 config.toml 生效
2. 用 xhigh 写 `design.md` `## Round 1` 段
3. spawn_agent `critic` subagent (独立 context, 防自我锚定 — 借 OMO Metis 思路)
4. critic 追加 `## Round N · Critic Findings` 段, VERDICT: PASS | NEEDS_REVISION
5. NEEDS_REVISION → 主 agent 再 xhigh 修订, 写 `## Round N+1`, 再 critic
6. **最多 `_index.plan_critique_max_rounds` 轮** (默认 4, 可调 2-6)
7. PASS → 进 impl (单模块) 或 design (System 路径)

**例外**: `_index.plan_critique_disabled = true` 关闭多轮 (用户自负责)

## design (System 路径)

System 路径专用, plan 通过后进 design 出详细架构. 可 spawn `architect` subagent.

## impl (铁律[零写入] 按区路由)

**工作流**:
1. 主 agent 写 `checklist.yaml` (tasks 列表, design_ref 引用)
2. 绿区任务 (单文件 ≤30 行, Hotfix/Quick): 主 thread 直接做, 不强制 spawn_agent
3. 黄区: spawn_agent `generator` subagent (TDD: 测试先, 代码后)
4. 红区 (Refactor/System): 主 thread 先 `git worktree add` 再 `spawn_agent --cwd <wt-path>` **强制** (pre-bash-guard 机械检查)
5. 并行多 generator (大改): 也强制 worktree
6. 超大规模 (≥5 独立同构子任务): 评估 multi-agent v2 fan-out, 见 `references/orchestration.md`
7. PostToolUse(Bash) hook 自动写 evidence.yaml (过程证据) + tool-trace.jsonl

## runtime-verify (v9.8.0, System/Refactor 强制 · Feature 可选)

impl 写完代码 + 单测后, 不直接进 review, 先做运行时自测自改:
- 用 Codex Goals 承载: 实跑接口 + 模拟数据 (正常/边界/异常) + 不同环境 → 测出问题自己改 → 复跑到完成条件满足
- 前端/E2E 用 browser + computer-use plugin (config.toml openai-bundled); 后端用 curl/真实调用; CLI 用实际命令 + 退出码断言
- ⚠️ 完成判定只看对话里展示的: 完成条件写成"把实跑命令 + 输出晒进对话"
- 出口 reflect: 对照 design + 实跑发现, 列"还有哪里没完善" → 回 impl 补 或 进 review
- 详见 skill: `/athena-runtime-verify`
- 产出: `sprints/{slug}/runtime-verify.md` (delivery-gate.py 在 ship 时验存在 + 含 `## 测试场景` 段)

## review (6 维度)

**并行 spawn 3 个 subagent**:
1. `reviewer.toml` (代码层 findings: bug/security/test/quality)
2. `spec-compliance.toml` (design ↔ git diff: MISSING/EXTRA/DEVIATED, 借 CodeStable cs-feat-accept + OpenSpec /opsx:verify)
3. `evaluator.toml` (后跑, 综合 VERDICT, 写 `_index.next_action`)

VERDICT 四象限: **PASS | CONCERNS | REWORK | FAIL**
- PASS / CONCERNS (Refactor/System) → polish
- PASS / CONCERNS (其他) → ship
- REWORK / FAIL → 回 impl

> 注: review stage 本身不设同步 Stop 门禁 (后台 review agent 异步写产物, 同步等待会死锁).
> spec-compliance 完整性由 delivery-gate 在 **ship** stage 检查 (此时产物已落盘).

## polish (Refactor/System 强制)

spawn_agent `polish_worker.toml`:
- 5 检查项 (临时代码 / 注释 / 冗余 / 低效 / 过度设计)
- finishing-a-development-branch (借 Superpowers): 跑测试 + 提示 merge/PR/继续/丢弃 + 清理 worktree
- 产出 `cleanup-pass.md`
- 触发 architecture/ 更新 (≥5 文件改动)

## ship

主 agent commit + push. delivery-gate 检查:
- Refactor/System: 必须有 cleanup-pass.md
- Refactor/System (≥5 文件): 必须更新 architecture/ (铁律[架构]); 文件数优先用 git diff 现场计算, evidence.yaml 为辅
- design_changed_after_impl=true: block 直到重新 review
- Feature/Refactor/System: pass1.md 必须含 `## Spec Compliance` 段
- current_roadmap_slug 非空: 提示主 agent 继续下个 item
- 长任务建议: ship 前核对 Goals 完成条件, 承载铁律[Sisyphus] (见 references/orchestration.md)

## evidence 平台差异 (诚实降级, 铁律[证据] CX 语义)

CX 的 PreToolUse/PostToolUse 实质只拦 shell 工具; apply_patch / 文件写 / MCP 工具不触发 hook [官方 developers.openai.com/codex/hooks: 非 shell、非 MCP 工具调用不被拦截].
因此 CX 的 evidence 链分两层:
1. **过程证据** — evidence-collector.py 挂 PostToolUse(Bash), 采集 test/lint/build 命令与结果摘要
2. **文件证据** — delivery-gate.py 门禁时用 `git diff --stat` 现场计算变更面

对等的是**门禁强度**, 不是逐字段照抄 CC.

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
│       ├── subagent-log.md            # hook 自动写
│       ├── worktrees.yaml             # pre-bash-guard 监听 git worktree 命令写
│       ├── evidence.yaml              # PostToolUse(Bash) 过程证据
│       └── tool-trace.jsonl           # 每个 Bash tool call 一行
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

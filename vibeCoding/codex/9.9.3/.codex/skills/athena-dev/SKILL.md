---
name: athena-dev
description: |
  Athena 主入口 skill (Codex). 接收用户任务, 做 PACE 路由分诊 (brainstorm/roadmap/plan/...), 启动对应 stage.
  v9.7.0: 由 deprecated prompts/ 迁为 skill; 修 CC 残留 (session-start.cjs→py); 铁律引用名称化.
  v9.9.1: 路由输出可审计决策摘要 (候选、证据、权衡、决策、置信度), 不要求暴露私有思维链; re-route 只升不降.
---

# /athena-dev — Athena 主入口 (Codex, v9.9.3)

## 触发

用户进任意项目, 说 "开始", "做个 X", "帮我 Y" 等. 主 agent 进入路由分诊.

## 路由审议 (铁律[分诊] · v9.9.1 决策摘要)

**前置**: 无 `.ai_state/` → 提示先跑 /athena-init, 停. 用户显式声明生产事故/hotfix → 直接进 plan(Hotfix) (唯一免审议).

路由是 triage, 不是查表. 主 agent 基于证据决策; 对用户只展示结论性摘要, 不展示私有思维链:

### Step 0 · 检查上下文
- `_index.md`: 当前 stage / path / route_history (上次路由错在哪) / counts (项目成熟度)
- `git log --oneline -10`: 最近在动哪些模块
- 输入中的显式信号: "重构" / "bug" / "讨论" 等关键词是**强证据**, 计入权衡但不短路直判 — "重构一下这个函数"不该触发 Refactor 全套流程

### Step 1 · 候选
提出 ≥2 个候选 (路径或 stage), 各列支持/反对证据.

### Step 2 · 四维权衡

| 维度 | 问自己 |
|---|---|
| 爆炸半径 | 波及几个文件/模块? 碰 CI / 数据 / 外部接口吗? |
| 可逆性 | 做错了 revert 一个 commit 能回来吗? |
| 紧急度 | 用户在救火还是在建设? |
| 需求不确定性 | 能直接写出验收标准吗? 写不出 = 模糊 → brainstorm |

### Step 3 · 决策 + 置信度
- **≥0.8**: 直接进路径
- **0.5–0.8**: 带假设进 — route-note 写明假设 + 廉价退出点 (什么信号出现就 re-route)
- **<0.5**: 停. 问用户 1-2 个决定性问题 (能砍掉一半候选的那种), 或进 brainstorm

### Step 4 · 护栏校验 (地板, 不可击穿)
≥3 模块 → 至少 roadmap; 跨模块 / 预估 ≥5 文件 → 至少 Refactor. 审议结果低于地板 → 取地板.

### Step 5 · 落盘
`sprints/{slug}/route-note.md` 记录候选、证据、关键权衡、决策、置信度与退出点; 更新 `_index.route_confidence`. 不写逐步思维过程.

## 路由决定后的动作

### → brainstorm

```bash
# 创建 sprint 目录
slug="$(date +%Y-%m-%d)-$(slugify '$user_topic')"
mkdir -p ".ai_state/sprints/${slug}"
cp ~/.agents/skills/pace/templates/sprints/brainstorm.md ".ai_state/sprints/${slug}/"

# 更新 _index.md
update_field stage "brainstorm"
update_field current_sprint_slug "${slug}"

# 进 brainstorm skill
read ~/.agents/skills/brainstorm/SKILL.md
# 多轮对话
```

### → roadmap

```bash
slug="$(slugify '$user_topic')"
mkdir -p ".ai_state/roadmap/${slug}/drafts"
cp ~/.agents/skills/pace/templates/roadmap/{roadmap.md,items.yaml} ".ai_state/roadmap/${slug}/"

update_field stage "roadmap"
update_field current_roadmap_slug "${slug}"

read ~/.agents/skills/roadmap/SKILL.md
```

### → plan / design (需求清晰)

```bash
slug="$(date +%Y-%m-%d)-$(slugify '$task_name')"
mkdir -p ".ai_state/sprints/${slug}/reviews"
cp ~/.agents/skills/pace/templates/sprints/{design.md,checklist.yaml,route-note.md} ".ai_state/sprints/${slug}/"

update_field path "${path_type}"
update_field route_confidence "${confidence}"   # v9.9.1 路由决策摘要
update_field stage "plan"
update_field current_sprint_slug "${slug}"

# Codex plan_mode_reasoning_effort = "xhigh" 已生效 (config.toml)
# 进 pace skill
```

## next_action 处理

主 agent 进 athena-dev 时, 先读 `_index.next_action`:

| next_action 值 | 动作 |
|---|---|
| `""` (空) | 正常路由 |
| `next_roadmap_item:{slug}` | 自动进 plan stage 处理新 item, 跳过路由 |
| `roadmap_complete` | 提示用户庆祝 + 触发 `/compound add learning` |
| `polish` | 自动进 polish stage |
| `ship` | 自动进 ship stage |
| `runtime-verify` | 调 /athena-runtime-verify (impl 完成后, System/Refactor 运行时自测自改) |
| `rework_impl` | 回 impl stage, 提示 review findings |
| `re-route` | v9.9.0: 停当前 task, 重走路由审议 (只升不降), route-note 追加 `## Re-route`, 补新路径欠的 stage |

## 推理力度提示

plan/design stage 由 config.toml `plan_mode_reasoning_effort = "xhigh"` 保证最大推理预算. SessionStart hook (session-start.py) 在 stage_hints 中自动提示.

## 与其他 skill 联动

| 用户意图 | 进哪个 skill |
|---|---|
| 开始任务 | athena-dev (这个) |
| 想法不清楚 | brainstorm |
| 拆大需求 | roadmap |
| 全流程开发 | pace |
| 完成总结 | athena-status |
| 跨版本迁移 | athena-migrate |
| 项目初始化 | athena-init |
| 沉淀知识 | compound |
| 维护架构档 | architect-doc |
| review 复杂改动 | athena-review |
| 记录原始需求 (新能力·逃生通道) | athena-requirements |
| 报告/分析/修复 bug | athena-issue |

## 例外

- 用户直接说 "直接做:" 或 `--skip-brainstorm` → 跳过 brainstorm
- 用户显式说 "我自己拆 roadmap" → 跳过 roadmap, 直接 plan
- Hotfix 路径: 跳过所有分诊, 直接进 plan (生产事故无时间分诊)

## 主 agent 行为约束

- ✅ 必须先读 `_index.md` 确定当前状态
- ✅ 路由判断必须基于实际输入 + ai_state, 不能"我觉得"
- ✅ 审议结论必须落盘 route-note (置信度 + 假设 + 廉价退出点), 不留痕的路由不算路由
- ✅ 收到 next_action=re-route 或自查触发 → 只升不降, 降级必须用户显式批准
- ✅ 模糊时优先 brainstorm, 不要直接猜想用户意图
- ❌ 不允许跳过分诊直接进 plan (铁律[分诊])
- ❌ 写入不按红黄绿区路由 (铁律[零写入]: 绿区主 thread 直做, 黄/红区 spawn_agent)

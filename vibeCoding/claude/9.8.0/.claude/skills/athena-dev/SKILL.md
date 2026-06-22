---
name: athena-dev
description: |
  Athena 主入口 skill. 接收用户任务, 做 PACE 路由分诊 (brainstorm/roadmap/plan/...), 启动对应 stage.
  v9.7.0: 铁律引用名称化 (CC/CX 编号非对称, 引用一律用 铁律[名称]).
effort: medium
---

# /athena-dev — Athena 主入口 (v9.8.0)

## 触发

用户进任意项目, 说 "开始", "做个 X", "帮我 Y" 等. 主 agent 进入路由分诊.

## 路由分诊 (铁律[分诊])

```python
def route(user_input, ai_state):
    # 0. 检查是否在 Athena 项目中
    if not has_ai_state_dir():
        suggest("先跑 /athena-init 初始化项目")
        return None

    # 1. 显式信号优先 (用户直接说)
    if explicit_kws(["想法不清楚", "先 brainstorm", "讨论", "聊聊"]):
        return start_stage("brainstorm")
    if explicit_kws(["路线图", "拆分", "分步推进"]):
        return start_stage("roadmap")
    if explicit_kws(["生产事故", "线上故障", "hotfix"]):
        return start_stage("plan", path="Hotfix")
    if explicit_kws(["bug", "缺陷", "修复"]):
        return start_stage("plan", path="Bugfix")
    if explicit_kws(["重构", "refactor"]):
        return start_stage("plan", path="Refactor")
    if explicit_kws(["系统级", "跨模块", "架构"]):
        return start_stage("plan", path="System")

    # 2. 隐式判断 (铁律[分诊])
    if len(user_input.split()) < 8 and not has_concrete_verb(user_input):
        # 单词级模糊 → brainstorm
        return start_stage("brainstorm")

    if mentions_modules(user_input) >= 3:
        # ≥3 模块 → roadmap
        return start_stage("roadmap")

    # 3. 默认: 按改动量分类
    estimated = estimate_scope(user_input)
    if estimated == "tiny":
        return start_stage("plan", path="Quick")  # ≤3 文件
    if estimated == "single_module":
        return start_stage("plan", path="Feature")
    if estimated == "multi_module":
        return start_stage("plan", path="System")

    return start_stage("plan", path="Feature")  # fallback
```

## 路由决定后的动作

### → brainstorm

```bash
# 创建 sprint 目录
slug="$(date +%Y-%m-%d)-$(slugify '$user_topic')"
mkdir -p ".ai_state/sprints/${slug}"
cp ~/.claude/skills/pace/templates/sprints/brainstorm.md ".ai_state/sprints/${slug}/"

# 更新 _index.md
update_field stage "brainstorm"
update_field current_sprint_slug "${slug}"

# 进 brainstorm skill
read ~/.claude/skills/brainstorm/SKILL.md
# 多轮对话
```

### → roadmap

```bash
slug="$(slugify '$user_topic')"
mkdir -p ".ai_state/roadmap/${slug}/drafts"
cp ~/.claude/skills/pace/templates/roadmap/{roadmap.md,items.yaml} ".ai_state/roadmap/${slug}/"

update_field stage "roadmap"
update_field current_roadmap_slug "${slug}"

read ~/.claude/skills/roadmap/SKILL.md
```

### → plan / design (需求清晰)

```bash
slug="$(date +%Y-%m-%d)-$(slugify '$task_name')"
mkdir -p ".ai_state/sprints/${slug}/reviews"
cp ~/.claude/skills/pace/templates/sprints/{design.md,checklist.yaml} ".ai_state/sprints/${slug}/"

update_field path "${path_type}"
update_field stage "plan"
update_field current_sprint_slug "${slug}"

# 主 agent 在第一条 message 加 "ultrathink"
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

## ultrathink 提示自动注入

进 plan/design stage 时, athena-dev 必须在主 agent 第一条 message 加 "ultrathink" 关键词. 这由 SessionStart hook (session-start.cjs) 通过 stage_hints 自动提示.

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
- ✅ 模糊时优先 brainstorm, 不要直接猜想用户意图
- ❌ 不允许跳过分诊直接进 plan (铁律[分诊])
- ❌ 写入不按红黄绿区路由 (铁律[零写入]: 绿区主 agent 直做, 黄/红区 subagent)

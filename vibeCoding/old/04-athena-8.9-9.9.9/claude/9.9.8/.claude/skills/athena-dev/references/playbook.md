# athena-dev · playbook

> 从 SKILL.md 下沉的完整正文 (v9.9.6 渐进披露拆分)。热路径只留触发与判据。

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
cp ~/.claude/skills/pace/templates/sprints/{design.md,checklist.yaml,route-note.md} ".ai_state/sprints/${slug}/"

update_field path "${path_type}"
update_field route_confidence "${confidence}"   # v9.9.1 路由决策摘要
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
| `re-route` | v9.9.0: 停当前 task, 重走路由审议 (只升不降), route-note 追加 `## Re-route`, 补新路径欠的 stage |

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

## 主 agent 行为约束

- ✅ 必须先读 `_index.md` 确定当前状态
- ✅ 路由判断必须基于实际输入 + ai_state, 不能"我觉得"
- ✅ 审议结论必须落盘 route-note (置信度 + 假设 + 廉价退出点), 不留痕的路由不算路由
- ✅ 收到 next_action=re-route 或自查触发 → 只升不降, 降级必须用户显式批准
- ✅ 模糊时优先 brainstorm, 不要直接猜想用户意图
- ❌ 不允许跳过分诊直接进 plan (铁律[分诊])
- ❌ 写入不按红黄绿区路由 (铁律[零写入]: 绿区主 agent 直做, 黄/红区 subagent)

---
name: brainstorm
description: |
  PACE 可选最早 stage. 用户想法模糊时通过对话理清楚.
  AI 角色: 思考伙伴, 挖用户真正想解决的问题, 必要时提出更好的替代方案.
  完成后产出 sprints/{date}-{slug}/brainstorm.md 并路由到 plan / roadmap / direct design.
effort: medium
---

# /brainstorm — PACE 分诊层 (v9.6.4 新)

## 触发

| 信号 | 来源 | 是否进 brainstorm |
|---|---|---|
| 用户显式 "想法不清楚" / "先 brainstorm" / "功能方向还在摇摆" | 用户 | ✅ |
| 主 agent 判断输入信号低 (单词级模糊, ≤ 8 词且无具体动词) | 自动 | ✅ |
| 用户带方案但说 "听听别的意见" | 用户 | ✅ |
| 用户显式 `--skip-brainstorm` | 用户 | ❌ |
| 输入开头 "直接做:" | 用户 | ❌ |
| 显式 bug / 重构描述 | 自动 | ❌ (走 Bugfix/Refactor 路径) |
| ≥ 3 模块的大需求 | 自动 | ❌ (直接进 roadmap) |
| 想法清晰 + 单模块 | 自动 | ❌ (直接 plan) |

## 工作流

### Step 1: 创建 sprint 目录

```bash
slug=$(date +%Y-%m-%d)-$(echo "$user_topic" | slugify)
mkdir -p .ai_state/sprints/$slug
cp ~/.agents/skills/_athena/pace/templates/sprints/brainstorm.md .ai_state/sprints/$slug/
```

### Step 2: 更新 _index.md

```yaml
stage: "brainstorm"
current_sprint_slug: "{date}-{slug}"
pointers:
  latest_brainstorm: "sprints/{date}-{slug}/brainstorm.md"
```

### Step 3: 多轮对话

每轮在 brainstorm.md 追加 `## 第 N 轮 · {主题}` 段:
- **第 1 轮**: 追问真问题 (借 Superpowers brainstorming: refines rough ideas through questions)
- **第 2 轮**: 评估方案 + 主动提出替代
- **第 N 轮**: 继续聚焦或换方向

### Step 4: 收敛 + 路由

收敛时在 brainstorm.md 写 `## 收敛` 段, 选下一步:

```python
def route_after_brainstorm(brainstorm_doc):
    if brainstorm_doc.shows_single_clear_feature:
        return "plan"
    if brainstorm_doc.requires_3_or_more_modules:
        return "roadmap"
    if brainstorm_doc.is_system_level_clear:
        return "design"  # System 路径直接进 design
    return "plan"  # 默认
```

## AI 角色 (思考伙伴, 不是审计员)

- **挖用户真正想解决的问题**, 不停在第一个脱口而出的方案
- 用户带方案来时, **主动评估它**, 必要时提出更好的替代
- 探索 / 质疑 / 改变主意 / 聊着聊着发现真正想做的是另一件事 — 都正常
- 不评估 (没有 VERDICT), 不约束 (rules 不注入), 不调研

## 哲学 (借 CodeStable + Superpowers)

> brainstorm 是**创意空间, 不是审计关卡**. 约束和落地细节留给 design stage.

## 与其他 stage 联动

| stage | 何时与 brainstorm 衔接 |
|---|---|
| plan | brainstorm 收敛 = 单 feature 清晰 → 进 plan |
| roadmap | brainstorm 收敛 = 大需求 → 进 roadmap 拆分 |
| design | brainstorm 收敛 = System 路径需求清晰 → 直接 design |
| compound | brainstorm 产生 insight → 触发 `/compound add explore` 提示 |

## 约束

- 不读 compound (避免污染创意空间)
- 不调用其他 subagent (主 agent 与用户对话)
- 不写代码 (铁律 12: 主分支零写入)
- ≤ 5 轮 (若 5 轮还没收敛, 提示用户该有方向了)

## 例外

- 用户在 brainstorm 中明确说 "去查 X 的资料" → 主 agent 可调度 docs_researcher / WebSearch (这是显式调研, 不是创意污染)
- 用户在 brainstorm 中说 "看下我们之前怎么决定 Y" → 主 agent 可读 compound/decision-*.md

## 写入 _index.md (收敛后)

```yaml
stage: "{plan | roadmap | design}"  # 下个 stage
current_sprint_slug: "..."  # 保留
pointers:
  latest_brainstorm: "sprints/{date}-{slug}/brainstorm.md"  # 保留
```

brainstorm.md 文件不删除, 留作后续 plan/design 的输入参考.

## 模板

见 `~/.agents/skills/_athena/pace/templates/sprints/brainstorm.md`

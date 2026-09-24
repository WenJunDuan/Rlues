# roadmap · playbook

> 从 SKILL.md 下沉的完整正文 (v9.9.6 渐进披露拆分)。热路径只留触发与判据。

## items.yaml schema

```yaml
roadmap_slug: auth-system
created: 2026-05-25
total_items: 5
items:
  - slug: jwt-basic
    title: "JWT 基础发行 + 验证"
    status: pending             # pending / in_progress / completed / blocked
    sprint_slug: ""             # 进入 plan 时填 sprints/ 下对应 slug
    blocked_by: []              # 依赖前置 item slug
    estimated_complexity: M     # S/M/L/XL
    notes: ""
  - slug: rbac-policy
    title: "RBAC 策略引擎"
    status: pending
    blocked_by: [jwt-basic]
    estimated_complexity: L
  ...
```

## 工作流

### Step 1: 创建 roadmap 目录

```bash
slug=$(slugify "$user_topic")
mkdir -p .ai_state/roadmap/$slug/drafts
cp ~/.agents/skills/pace/templates/roadmap/roadmap.md .ai_state/roadmap/$slug/
cp ~/.agents/skills/pace/templates/roadmap/items.yaml .ai_state/roadmap/$slug/
```

### Step 2: 调用 architect 调研

主 agent 用 `spawn_agent` 启动 read-only architect:
- 探索代码库
- 返回 roadmap.md 草稿 (背景 / 总体方案 / 阶段拆分)
- 返回 items.yaml 初稿 (子 feature 列表 + 依赖关系)

主 agent 审阅后串行落盘. 只读 architect 不写 roadmap 文件.

### Step 3: 用户确认

主 agent 把 items.yaml 给用户看, 用户可以:
- 增删 item
- 调整 estimated_complexity
- 调整 blocked_by 依赖关系
- 重排顺序

### Step 4: 拓扑排序选第一个可执行 item

```python
def select_next_item(items):
    completed = {it.slug for it in items if it.status == "completed"}
    for it in items:
        if it.status == "pending" and set(it.blocked_by).issubset(completed):
            return it
    return None
```

### Step 5: 该 item 进 plan stage

更新 `_index.md`:
```yaml
stage: "plan"
current_sprint_slug: "{date}-{item.slug}"
current_roadmap_slug: "{roadmap.slug}"  # 保持
```

走完整 PACE 循环 (plan → ... → ship).

### Step 6: ship 后回 roadmap, 选下一个

ship 完成时 (由主 agent 在 delivery-gate 通过后执行):
1. items.yaml 回写: 当前 item.status = "completed", sprint_slug = "{date}-{slug}"
2. 检查是否还有 pending → 是, 选下一个, `_index.next_action = "next_roadmap_item:{slug}"`
3. 全部 completed → roadmap 完成, `_index.current_roadmap_slug = ""`
4. 主 agent 提示用户 "roadmap {slug} 完成"

## delivery-gate 联动

- `_index.current_roadmap_slug` 非空 + items.yaml 还有 pending → ship hook 阻止 "全部完成" 宣称
- 主 agent 必须在 ship 后回查 items.yaml

## 与 brainstorm 关系

```
brainstorm (想法不清晰) → roadmap (方向清晰但量太大) → plan (单 feature) → ...
```

两者可串联. brainstorm 收敛后若属大需求, 进 roadmap.

## compound 联动

- roadmap 拆分时, 主 agent 读 `compound/decision-*.md` 看是否有相关历史决策
- roadmap 完成后, 触发 `/compound add learning` 沉淀整个 roadmap 的经验

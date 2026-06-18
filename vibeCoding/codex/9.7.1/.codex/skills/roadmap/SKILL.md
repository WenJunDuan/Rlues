---
name: roadmap
description: |
  PACE 可选 stage. 大需求 (跨 ≥3 模块) 拆成子 feature 序列.
  产出 .ai_state/roadmap/{slug}/items.yaml + roadmap.md.
  每个子 item 完成后回写 status, 主 agent 自动进入下一个 item 的 plan stage.
effort: high
---

# /roadmap — 大需求拆分 (v9.6.4 新)

## 触发条件

```python
def needs_roadmap(user_input, brainstorm_output=None):
    if explicit_kws(["路线图", "拆分", "roadmap", "分步推进", "分阶段"]):
        return True
    if mentions_modules(user_input) >= 3:
        return True
    if brainstorm_output and brainstorm_output.recommends_roadmap:
        return True
    return False
```

## 数据结构

```
.ai_state/roadmap/{slug}/
├── roadmap.md          # 主文档: 背景 / 拆解 / 排期
├── items.yaml          # 机器可读子 feature 清单
└── drafts/             # 可选: 调研笔记 / 备选方案
```

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
cp ~/.codex/skills/pace/templates/roadmap/roadmap.md .ai_state/roadmap/$slug/
cp ~/.codex/skills/pace/templates/roadmap/items.yaml .ai_state/roadmap/$slug/
```

### Step 2: spawn architect 调研 (worktree 隔离)

主 agent 用 spawn_agent `architect.toml` (read-only, ultrathink):
- 探索代码库
- 输出 roadmap.md 草稿 (背景 / 总体方案 / 阶段拆分)
- 输出 items.yaml 初稿 (子 feature 列表 + 依赖关系)

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

ship 完成时 (由 SubagentStop hook 触发):
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

## 路径限制

roadmap 只对 Feature / Refactor / System 路径有意义.
Hotfix / Bugfix / Quick **不进 roadmap** (本就是小改动).

## 例外

- `_index.skip_roadmap = true`: 大需求也不强制 roadmap (主 agent 一次性处理, 风险自担)
- 用户显式 "我自己拆": 不进 roadmap stage, 用户直接说"先做 X 再做 Y"

## 不要做 (借 OMO 教训)

- 不引入 milestone / epic / story 三层 (太重, 不是 PMS)
- 不引入跨 roadmap 依赖 (一次只跑一个 roadmap)
- 不引入自动调度算法 (主 agent + 用户决定顺序)
- 不允许 roadmap 中途插队新 item (除非用户显式说 "插队")

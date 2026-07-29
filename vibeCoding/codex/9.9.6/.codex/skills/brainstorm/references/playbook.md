# brainstorm · playbook

> 从 SKILL.md 下沉的完整正文 (v9.9.6 渐进披露拆分)。热路径只留触发与判据。

## 提问透镜 (混用, 不报菜名)

第一性原理 / 意图与赢的定义 / 约束挖掘 (不可谈判项) / 隐含假设 ("X 成立需要什么为真") / 次优备选 (说不出备选 = 没真正选择) / pre-mortem ("12 个月后失败了, 为什么") / 边界测试 (不做什么比做什么更定义项目) / 可逆性 (单向门 vs 双向门) / 五 whys。对话保持自然, 结构藏在水下。

## 工作流

### Step 1: 创建 sprint 目录

```bash
slug=$(date +%Y-%m-%d)-$(echo "$user_topic" | slugify)
mkdir -p .ai_state/sprints/$slug
cp ~/.agents/skills/pace/templates/sprints/brainstorm.md .ai_state/sprints/$slug/
```

### Step 2: 更新 _index.md

```yaml
stage: "brainstorm"
current_sprint_slug: "{date}-{slug}"
pointers:
  latest_brainstorm: "sprints/{date}-{slug}/brainstorm.md"
```

### Step 3: 提问循环 (核心循环 1-7)

对话过程**不逐轮落盘** — 问答是过程, 不是产物。中途 compact 风险高时可先写半成品 log (标 converged: false)。

### Step 4: 收敛 + 落盘 distilled log + 路由

**终止条件**: 下一个具体动作 (写 plan / 拆 roadmap / 进 design) 已经可能 — 且仅在此时。
落盘 brainstorm.md (distilled log 模板): 存结论与理由, 不存问答记录; 空段删除, 不留 TBD。

路由判定 (同 v9.7.0):
- 单 feature 清晰 → plan
- ≥2 个可独立验收、可独立 ship 的切片 → roadmap
- System 路径需求清晰 → direct design

## AI 角色

- **面试官, 不是提案人**: 默认不吐整版方案; 用户被追问出的意图 > AI 猜出的意图
- 用户带方案来时, 先问到理解它的 why, 再评估与替代
- 不评估 (没有 VERDICT), 不约束 (rules 不注入)
- 探索中改变主意 / 发现真正想做的是另一件事 — 都正常

## 约束

- 不读 compound (避免污染创意空间; 例外见下)
- 不调用其他 subagent (主 agent 与用户对话; 查库用自己的 Read/Grep)
- 不写代码 (铁律[零写入]: brainstorm 无任何代码写入)
- 不设固定轮数上限; 但用户表现出不耐烦或明说 "够了" → 立即收敛落盘

## 与其他 stage 联动

| stage | 衔接 |
|---|---|
| plan | 收敛 = 单 feature 清晰 → 进 plan |
| roadmap | 收敛 = 大需求 → 进 roadmap 拆分 |
| design | 收敛 = System 路径需求清晰 → 直接 design |
| compound | 产生 insight → 触发 `/compound add explore` 提示 |

## 写入 _index.md (收敛后)

```yaml
stage: "{plan | roadmap | design}"
current_sprint_slug: "..."
pointers:
  latest_brainstorm: "sprints/{date}-{slug}/brainstorm.md"
```

brainstorm.md 是后续 plan/design 的输入; Intent/Constraints 段是 design.md 验收标准的直接原料。

## 模板

见 `~/.agents/skills/pace/templates/sprints/brainstorm.md` (v9.9.6 distilled-log 格式)

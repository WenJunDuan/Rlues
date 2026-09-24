---
name: brainstorm
description: |
  PACE 可选最早 stage. 用户想法模糊时通过提问理清楚.
  v9.9.3 grill-me 化 (借 Matt Pocock grill-me, MIT): 一次一问 + strawman 推荐答 + 先查库再问人.
  AI 角色: 相不是生成提案让用户审, 而是用问题把用户的真实意图、约束、隐含假设挖到台面上.
  完成后产出 sprints/{date}-{slug}/brainstorm.md (distilled log) 并路由到 plan / roadmap / direct design.
---

# /brainstorm — PACE 分诊层 (v9.9.3 · grill-me 化)

## 触发

| 信号 | 来源 | 是否进 brainstorm |
|---|---|---|
| 用户显式 "想法不清楚" / "先 brainstorm" / "帮我想清楚" | 用户 | ✅ |
| 语义模糊: 主 agent 无法从输入直接写出可观测验收标准 (铁律[分诊]) | 自动 | ✅ |
| 用户带方案但说 "听听别的意见" / "pressure-test 一下" | 用户 | ✅ |
| 用户显式 `--skip-brainstorm` / 输入开头 "直接做:" | 用户 | ❌ |
| 显式 bug / 重构描述 | 自动 | ❌ (走 Bugfix/Refactor 路径) |
| ≥ 3 模块的大需求且方向已清晰 | 自动 | ❌ (直接进 roadmap) |
| 想法清晰 + 单模块 | 自动 | ❌ (直接 plan) |

## 核心循环 (grill-me)

1. **一次只问一个问题**, 并附上你的**推荐答案** — 用户对草案说 "对/不对/改成X" 远比面对空白提问轻松 (选择题, 不是作文题)
2. **追刚拿到的答案, 再横向换题** — 提前收口都是因为换题太快; 深度来自把一条线问到底
3. **能自己查的不问用户**: 答案在代码/.ai_state/architecture/compound 里 → Grep/Read 自行确认, 连续解决掉的问题只汇报一句
4. **顶住模糊回答**: "以后再说" / "大概X吧" / "都行" = 继续钻的信号, 不是过关信号; 允许指出矛盾与含糊, 礼貌但不接受雾
5. **半答案给 strawman**: 用户说 "不知道, 可能X" → 给一个可反对的完整草案 "这样定, 哪里不对?" — 反对比发明容易
6. **觉得问够了, 再问三个** — "已经够了"的感觉是水面, 不是水底
7. **禁止用总结推进**: "所以你的意思是X/Y/Z" 是收口不是推进; 综合留给最后的 log

## 提问透镜 (混用, 不报菜名)

第一性原理 / 意图与赢的定义 / 约束挖掘 (不可谈判项) / 隐含假设 ("X 成立需要什么为真") / 次优备选 (说不出备选 = 没真正选择) / pre-mortem ("12 个月后失败了, 为什么") / 边界测试 (不做什么比做什么更定义项目) / 可逆性 (单向门 vs 双向门) / 五 whys。对话保持自然, 结构藏在水下。

## 工作流

### Step 1: 创建 sprint 目录

```bash
slug=$(date +%Y-%m-%d)-$(echo "$user_topic" | slugify)
mkdir -p .ai_state/sprints/$slug
cp ~/.claude/skills/pace/templates/sprints/brainstorm.md .ai_state/sprints/$slug/
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
- ≥3 模块 → roadmap
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

## 例外

- 用户明确说 "去查 X 的资料" → 主 agent 可调度 docs_researcher / WebSearch (显式调研)
- 用户说 "看下我们之前怎么决定 Y" → 主 agent 可读 compound/decision-*.md

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

见 `~/.claude/skills/pace/templates/sprints/brainstorm.md` (v9.9.3 distilled-log 格式)

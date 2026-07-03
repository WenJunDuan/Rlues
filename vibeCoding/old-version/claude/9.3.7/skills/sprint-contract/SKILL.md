---
effort: high
---
# Sprint Contract — 开工前的验收合同

## 为什么需要合同

GSD 有计划但没有验收协商。Superpowers 有 brainstorm 但没有约束力。
Sprint Contract 解决的问题是: **Generator 做什么、Evaluator 验什么, 动手前谈清楚。**

没有合同的后果:
- Generator 做完了, Evaluator 说 "我觉得还差 XX" → 返工
- Evaluator 验的标准和 Generator 理解的不一样 → 扯皮
- 边界条件没人提 → 上线后才发现

有合同的效果:
- Generator 读合同就知道做到什么程度算完
- Evaluator 按合同逐条验, 不凭感觉打分
- feature_list.json 的 acceptance_steps 直接从合同展开, hooks 程序化验证

## 触发时机

**D 阶段** (design.md 完成后, 进 P 之前)

## 角色

| 谁 | 做什么 |
|:---|:---|
| Planner (主 Agent) | 草拟合同: 范围 + 验收标准 + 排除项 |
| @evaluator | 审核合同: 可测吗? 遗漏了什么? 标准够不够? |

---

## Step 1: Planner 草拟

基于 design.md, 为每个 Sprint 草拟合同, 内容必须包括:

### 合同模板

```markdown
# Sprint {N} 验收合同

## 范围
[本 Sprint 要实现的功能, 1-3 句话概括]

## Features (对应 feature_list.json)

### F{NNN}: [功能名]
- 描述: [一句话]
- 验收步骤:
  1. [具体操作, 不是 "功能正常"]
  2. [可观测的结果, 如 "页面显示成功消息"]
  3. [边界条件, 如 "空输入时显示错误提示"]
- 验证方式: [playwright/单元测试/curl/手动]
- 优先级: P0(必须) / P1(应该) / P2(可以)

### F{NNN}: [下一个功能]
...

## 边界条件 (必须覆盖)
- 空输入/null: [预期行为]
- 超长输入: [预期行为]
- 并发操作: [预期行为]
- 权限不足: [预期行为]
- 网络超时: [预期行为]

## 不在范围 (明确排除)
- [不做的事情, 防止 Generator 过度工程]
- [下个 Sprint 做的事情]

## 技术约束
- 性能: [如有要求, 如 "响应时间 <500ms"]
- 兼容性: [如有要求]
- 安全: [如有要求, 如 "密码必须 hash"]

## 预估
- 时间: [X 小时]
- 主要风险: [1-2 个]
- 降级方案: [如果风险发生怎么办]
```

### 草拟要点

- **验收步骤必须可操作**: "用户能登录" ❌ → "输入邮箱密码, 点击登录, 跳转到 dashboard, 显示用户名" ✅
- **每个 Feature 必须有验证方式**: Playwright 能自动验的标 playwright, 需要人工看的标手动
- **边界条件不是可选的**: 至少覆盖 3 种异常场景
- **不在范围比在范围更重要**: 明确说 "不做 XX" 防止范围蔓延

---

## Step 2: @evaluator 审核

Planner 草拟完后, 调度 @evaluator 审核:

```
@evaluator 审核 Sprint {N} 合同:
读 .ai_state/contract-{N}.md
按以下 5 条审核, 每条给 ✅ 或 ❌ + 理由
```

### 审核清单

| # | 问题 | ❌ 的典型原因 |
|:---|:---|:---|
| 1 | 每个 Feature 的验收步骤能用 playwright 或测试框架自动验证吗? | "功能正常" 不是可测标准 |
| 2 | 边界条件覆盖了至少 3 种异常场景吗? | 只写了 happy path |
| 3 | 不在范围是否足够明确? Generator 会不会多做? | "不在范围" 为空 |
| 4 | 验收步骤和 design.md 的接口定义一致吗? | 合同说返回 200, design 说返回 201 |
| 5 | 时间预估合理吗? 1 个 Sprint ≤ 1 天? | Sprint 太大, 应该拆 |

### 审核输出格式

```
Sprint {N} 合同审核:
[1] 验收可测性:   ✅
[2] 边界覆盖:     ❌ 缺少并发场景
[3] 范围明确性:   ✅
[4] 与 design 一致: ✅
[5] 时间合理性:   ❌ 预估 3 天, 应拆为 2 个 Sprint

建议:
- F003 增加并发注册的验收步骤
- 拆分为 Sprint 1 (注册) + Sprint 2 (登录+重置)
```

---

## Step 3: 协商

- @evaluator 有 ❌ → Planner 修改合同 → @evaluator 重新审核
- **最多 2 轮协商**, 超过 → cunzhi 让用户拍板
- 双方全 ✅ → 合同锁定

---

## Step 4: 生成 feature_list.json

合同锁定后, 从合同的 Features 展开生成 feature_list.json:

```
合同 Feature            →  feature_list.json entry
─────────────────────────────────────────────────
F001: 邮箱注册           →  {"id":"F001","sprint":1,
  验收步骤:                   "description":"邮箱注册",
  1. 打开注册页                "acceptance_steps":[
  2. 输入邮箱密码               "打开注册页",
  3. 点击注册                   "输入邮箱密码",
  4. 验证跳转                   "点击注册",
  5. 空邮箱报错                  "验证跳转到欢迎页",
                               "空邮箱时显示错误提示"
                             ],
                             "passes":false}
```

**铁律: feature_list.json 生成后, description 和 acceptance_steps 禁止修改。**
这就是合同的约束力 — 写进 JSON, hooks 保护, 不能口头改。

---

## Step 5: 合同怎么被使用

合同生成后, 在后续阶段被三个角色引用:

| 阶段 | 谁 | 怎么用合同 |
|:---|:---|:---|
| E 执行 | @generator | 读 contract-{N}.md 知道做什么、做到什么程度 |
| T 审查 | @evaluator | 按 feature_list.json 逐条验 (从合同展开的) |
| T 判定 | @evaluator | Spec Compliance 维度 = 合同的验收标准通过率 |
| V 归档 | delivery-gate hook | 读 feature_list.json passes 计数, 不全通过→阻断 |

---

## 输出

1. `.ai_state/contract-{N}.md` — 锁定的合同
2. `.ai_state/feature_list.json` — 从合同展开的 JSON (hooks 验证)
3. `.ai_state/state.json` — 更新 total_sprints, features_total

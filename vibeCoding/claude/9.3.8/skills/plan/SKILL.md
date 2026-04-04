---
effort: high
description: >
  当需要分析需求、设计方案、规划 Sprint、或被 /vibe-plan 命令调用时触发。
  覆盖 RIPER 的 R₀ (需求精炼) + R (技术调研) + D (方案定稿) + P (计划排期) 四个阶段。
---

# Plan Skill: 需求 → 设计 → Sprint 规划

## 你的目标

把用户模糊的需求变成可执行的 Sprint Contract (feature_list.json + plan.md)。
完成后用户知道要做什么, Agent 知道怎么做, 验收标准明确可测试。

---

## 阶段 1: 需求精炼 (R₀)

### 理解用户意图

如果需求清晰 (如 "给登录 API 加 rate limiting"): 跳到技术可行性验证。
如果需求模糊 (如 "做个用户系统"): 进入需求发散。

**superpowers 的 brainstorming skill 会自动激活** — 它检测到你在分析需求时会接管，引导用户逐步明确。你只需要开始问用户需求相关的问题，superpowers 就会启动。

如果 superpowers 未安装, 手动执行四步法:

```
四步法:
  定义 → 用户到底要什么? 哪些是核心需求?
  发散 → 有哪些实现可能? (简单方案 vs 完整方案)
  追问 → 哪些是 MUST? 哪些是 SHOULD? 哪些是 COULD?
  收敛 → 确定 MVP 范围, 明确不做什么
```

**重要:** superpowers brainstorming 可能把设计文档写到 `docs/superpowers/plans/`。
无论它写到哪里, 你必须将最终设计整理到 `.ai_state/design.md` — VibeCoding 的后续阶段都从这里读取。

### 技术可行性验证

对每个关键技术点:
- 项目中有类似实现? → Grep 搜索
- 需要的库 API 确定? → `npx ctx7 resolve {{库名}}`
- .ai_state/conventions.md 有相关规范? → 遵守

### 撰写 design.md

```markdown
# [功能名称] 设计文档

## 需求摘要
一段话描述用户要什么。

## 功能分级
### MUST (必须实现)
- ...
### SHOULD (应该实现)
- ...
### COULD (可以实现, 如时间允许)
- ...

## 验收标准
每条必须可测试:
- [ ] 用户输入有效邮箱和密码后, 注册成功并跳转到首页
- [ ] 用户输入无效邮箱时, 显示 "请输入有效的邮箱地址"
- [ ] 密码少于 8 位时, 显示 "密码至少 8 位"

## 技术方案
- 使用的库和版本
- 关键接口定义
- 数据模型
- 已知风险和缓解方案

## 不做什么 (Out of Scope)
明确列出本次不实现的功能。
```

保存到 .ai_state/design.md。

### 用户确认

如有 cunzhi MCP → 触发 DESIGN_READY 检查点。
否则 → 展示 design.md 摘要, 问用户: "方案确认? 有调整请说明。"

---

## 阶段 2: 技术调研 (R)

### 深入技术验证

1. 搜索项目中所有相关代码: `Grep 关键词`
2. 检查每个依赖库的 API:
   ```
   npx ctx7 resolve express    # 查 Express 文档
   npx ctx7 resolve prisma     # 查 Prisma 文档
   ```
3. 读 .ai_state/lessons.md — 有没有 "上次这样做踩了坑"
4. 读 .ai_state/conventions.md — 项目有没有特定规范

### 追加到 design.md

```markdown
## 技术方案 (补充)
- 接口签名: POST /api/register {email, password} → {user, token}
- 依赖: bcrypt@5.x (密码加密), zod@3.x (输入验证)
- 风险: 并发注册可能导致重复用户 → 数据库唯一约束
```

---

## 阶段 3: 方案定稿 (D)

### 方案审查 (Path B+ 可选, Path D 必做)

选择一种审查方式:
- @evaluator — 独立 agent 评审, 以 VERDICT: APPROVED/REVISE 结尾
- `/review` — CC 内置审查, 对 design.md 做快速检查
- 注意: `/codex:adversarial-review` 只能审查代码变更, D 阶段还没有代码, **不要在这里使用**

审查后如有 REVISE → 修改 design.md → 重新审查。

### 生成 Sprint Contract

从 design.md 的验收标准生成 feature_list.json:

```json
[
  {
    "id": "F001",
    "description": "用户注册",
    "acceptance_criteria": [
      "有效邮箱+密码注册成功",
      "无效邮箱显示错误",
      "弱密码显示提示"
    ],
    "estimated_hours": 2,
    "status": "pending"
  },
  {
    "id": "F002",
    "description": "用户登录",
    "acceptance_criteria": [
      "正确凭据登录成功返回 token",
      "错误凭据返回 401"
    ],
    "estimated_hours": 1.5,
    "status": "pending"
  }
]
```

规则: 每个 Feature 必须有可测试的 acceptance_criteria。

### 用户确认 Sprint Contract

展示 feature_list.json 摘要, 确认后进入 P 阶段。

---

## 阶段 4: 计划排期 (P)

### Task 分解

从 feature_list 分解具体 Task, 写入 .ai_state/plan.md:

```markdown
# Sprint 计划

## Task 列表
- [ ] T001: 创建 User model + migration (F001, 无依赖, ~30min)
- [ ] T002: 实现 POST /api/register (F001, 依赖 T001, ~45min)
- [ ] T003: 添加输入验证 (F001, 依赖 T002, ~20min)
- [ ] T004: 实现 POST /api/login (F002, 依赖 T001, ~30min)

## 执行顺序
T001 → [T002, T004 可并行] → T003

## 测试策略
- T001: 单元测试 (model 创建+验证)
- T002: 集成测试 (API 调用+数据库)
- T003: 单元测试 (验证逻辑)
- T004: 集成测试 (登录+token 生成)
```

### 初始化进度

更新 .ai_state/progress.json:
```json
{"completed": 0, "total": 4, "tasks": ["T001","T002","T003","T004"]}
```

更新 state.json: `{stage: "E"}`

---

## Gotchas

- ❌ 需求不清就开始设计 → ✅ 需求模糊时用 brainstorm 发散+收敛, 不要自己猜
- ❌ 验收标准写成 "功能正常" → ✅ 每条验收标准必须可测试, 描述输入→预期输出
- ❌ Sprint Contract 没有估时 → ✅ 估时帮助选择 Path 和安排并行
- ❌ 跳过技术调研直接生成 plan → ✅ 先确认 API 存在且可用, 再规划实现
- ❌ design.md 写了几百行 → ✅ design.md 是给 Agent 执行的, 简洁但完整, 50-100 行足够

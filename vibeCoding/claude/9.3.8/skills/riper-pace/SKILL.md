---
effort: high
description: >
  当收到新任务、不确定从哪开始、需要评估任务复杂度、或被 /vibe-dev 命令调用时触发。
  这是 VibeCoding 的核心工作流引擎: 先路由复杂度, 再按阶段编排执行。
---

# RIPER-PACE 工作流引擎

## 概述

RIPER-PACE = PACE 复杂度路由 + RIPER 阶段编排。
收到任务后: **先用 PACE 选路径, 再用 RIPER 按路径执行对应阶段。**

---

## 前置检查 (每次触发时)

1. **.ai_state/ 目录存在?**
   - 不存在 → 先创建 .ai_state/ 目录 + 从 templates/ai-state/ 复制模板文件初始化
   - 或者调 @scaffolder 做完整初始化 (推荐)
2. **conventions.md 有 Gotchas?** → 读取, 后续阶段注意避开

---

## PACE 路由器: 选择执行路径

### 五维评估

对任务做以下 5 个维度的评估, 取最高匹配路径:

| 维度 | A (快速) | B (标准) | C (复杂) | D (系统) |
|------|---------|---------|---------|---------|
| 文件影响 | 1-3 个文件 | 4-10 个文件 | 10+ 个文件 | 跨服务/仓库 |
| 预估时间 | < 30 分钟 | 30分钟 - 4小时 | 4小时 - 2天 | > 2天 |
| 架构影响 | 无 | 局部模块 | 跨模块 | 系统级 |
| 测试复杂度 | 单元测试 | 单元+集成 | 含 E2E | 全链路 |
| 风险等级 | 低 (可回滚) | 中 | 高 (不可逆) | 极高 |

### 路径决策

```
任一维度达到某 Path → 取最高 Path。
例: 文件影响 = B, 风险等级 = C → 选 Path C。
```

用户可覆盖: "这个用 Path A 就行" → 尊重用户判断, 但如果明显不合理需提醒。

### 路径 → 阶段映射

```
Path A (快速):  ─────────────────── E ──→ T
Path B (标准):  R₀ → R → D → P → E → T → V
Path C (复杂):  R₀ → R → D → P → E (并行 @generator) → T (含对抗审查) → V
Path D (系统):  R₀ → R → D (含设计评审) → P → E (并行) → T (全套审查) → V
```

### 路由完成后

1. 更新 .ai_state/state.json: `{path: "B", stage: "R0", sprint: 1}`
2. 告知用户: "任务评估为 Path B (标准), 将按 R₀→R→D→P→E→T→V 执行。"
3. 进入第一个阶段。

---

## RIPER 阶段编排

### 每阶段进入前 (通用检查)

在进入任何阶段前, 先做以下检查:
1. 当前项目里有没有类似实现? → Grep 搜索相关代码
2. 用到的库 API 确定吗? → 不确定就用 context7: `npx ctx7 resolve {{库名}}`
3. .ai_state/conventions.md 有相关 Gotchas 吗? → 有就注意避开
4. .ai_state/lessons.md 有相关教训吗? → 有就参考

---

### R₀ 需求精炼 (Path B+)

**目标:** 把模糊需求变成可验收的 Spec。

**步骤:**
1. 理解用户意图 — 如果需求不清晰, 进入需求发散 (superpowers brainstorming skill 会自动激活):
   - 定义: 用户到底要什么?
   - 发散: 有哪些可能的实现方式?
   - 追问: 哪些是必须的? 哪些是可选的?
   - 收敛: 确定 MUST / SHOULD / COULD 分级
2. 技术可行性验证 — 用 context7 查关键库的 API, 确认方案可行
3. 撰写 design.md — 包含:
   - 需求摘要
   - MUST / SHOULD / COULD 功能分级
   - 验收标准 (每条必须可测试, 如 "用户输入无效邮箱时显示错误提示")
   - 技术约束和假设
4. 用户确认 — 如果有 cunzhi MCP, 触发 DESIGN_READY 检查点; 否则直接问用户

**产出:** .ai_state/design.md
**门控:** 用户确认后, 更新 state.json stage → "R"
**详细指引:** → plan/SKILL.md 阶段 1 (需求精炼)

---

### R 技术调研 (Path B+)

**目标:** 验证技术方案可行, 排除关键风险。

**步骤:**
1. 搜索项目中类似实现 — Grep 相关关键词, Read 相关文件
2. 查库文档 — context7: `npx ctx7 resolve {{库名}}`
3. 查历史经验 — 读 .ai_state/lessons.md 和 conventions.md
4. 追加技术方案到 design.md — 包含:
   - 关键接口定义 (输入/输出/错误码)
   - 依赖库及版本
   - 已知风险和缓解方案 (如 "并发量大时需要加锁")

**产出:** design.md 追加技术方案段
**门控:** 技术方案段非空, 进入 D
**详细指引:** → plan/SKILL.md 阶段 2 (技术调研)

---

### D 方案定稿 (Path B+)

**目标:** 锁定方案, 生成 Sprint Contract。

**步骤:**
1. 方案审查 — 可选:
   - @evaluator 独立评审方案 (以 VERDICT: APPROVED/REVISE 结尾)
   - `/review` (CC 内置) 对 design.md 做快速审查
   - 注意: `/codex:adversarial-review` 只能审查代码变更, D 阶段无代码, 不要用
   - Path D 必须做设计评审; Path B/C 可选
2. 生成 feature_list.json — Sprint Contract:
   ```json
   [
     {
       "id": "F001",
       "description": "用户注册功能",
       "acceptance_criteria": ["邮箱格式验证", "密码强度检查", "注册成功跳转"],
       "estimated_hours": 2,
       "status": "pending"
     }
   ]
   ```
3. 每个 Feature 必须有: ID, 描述, 验收标准 (可测试), 估时, 状态

**产出:** .ai_state/feature_list.json
**门控:** 用户确认 Sprint Contract 后, 更新 state.json stage → "P"
**详细指引:** → plan/SKILL.md 阶段 3 (方案定稿)

---

### P 计划排期 (Path B+)

**目标:** 确定执行顺序和依赖关系。

**步骤:**
1. 从 feature_list.json 分解 Task — 每个 Feature 可能有多个 Task
2. 确定依赖关系 — 哪些 Task 必须先完成
3. 确定执行顺序 — 考虑依赖和并行可能
4. 为每个 Task 规划测试策略
5. 写入 .ai_state/plan.md:
   ```markdown
   ## Task 列表
   - [ ] T001: 创建 User model (F001, 无依赖)
   - [ ] T002: 实现注册 API (F001, 依赖 T001)
   - [ ] T003: 添加邮箱验证 (F001, 依赖 T002)
   
   ## 执行顺序
   T001 → T002 → T003
   ```

**产出:** .ai_state/plan.md
**门控:** plan.md 非空, 每个 Task 有明确完成定义, 进入 E
**详细指引:** → plan/SKILL.md 阶段 4 (计划排期)
**注意:** 使用 VibeCoding 的 plan.md 格式 (Task ID + Feature 映射 + 依赖 + checkbox)。
如果 superpowers writing-plans skill 自动激活并生成了不同格式的 plan, 以 VibeCoding 格式为准。

---

### E 执行 (所有 Path)

**目标:** 逐个完成 Task, 写代码 + 测试。

**三级委托策略** (按顺序尝试, 详见 execute skill):

```
┌─────────────────────────────────────────────────┐
│ Level 1 (首选): /codex:rescue <task 描述>        │
│   Codex 在后台执行, 你审查结果                     │
│   适合: 独立、明确的实现任务                        │
│   后台管理: /codex:status → /codex:result          │
├─────────────────────────────────────────────────┤
│ Level 2 (次选): @generator subagent                   │
│   CC subagent 在独立 worktree 中执行                    │
│   适合: 需要 CC 工具链的任务                        │
├─────────────────────────────────────────────────┤
│ Level 3 (兜底): 手动 TDD                          │
│   你自己写: 先测试 → 后实现 → 运行验证              │
│   适合: 简单任务或前两级不可用时                     │
└─────────────────────────────────────────────────┘
```

**每个 Task 的执行循环:**
1. 选取下一个 pending Task → 更新 feature_list.json status → "doing"
2. 按三级委托策略实现
3. 运行测试, 确认通过
4. 执行 reflexion skill → 自我审查 (铁律 #4)
5. 更新 feature_list.json status → "done"
6. 更新 progress.json
7. 重复直到所有 Task 完成 (Sisyphus 铁律 #3)

**Path C/D 并行:** 可同时委托多个无依赖的 Task 给 @generator 或 /codex:rescue --background

**产出:** 代码 + 测试 + progress.json
**门控:** plan.md 所有 Task done 或 blocked (Sisyphus), 进入 T
**详细指引:** → execute/SKILL.md (三级委托 + TDD + Task 循环)

---

### T 测试验证 (所有 Path)

**目标:** 独立验证代码质量, 生成综合评分。

**审查工具编排** (详见 review skill):

| Path | 必做 | 可选 |
|------|------|------|
| A | /review (CC 内置) 或 /codex:review | — |
| B | /codex:review + @evaluator 评分 | /codex:adversarial-review |
| C | /codex:review + /codex:adversarial-review + @evaluator + ECC scan | playwright E2E |
| D | 全部 | 全部 |

**评分:** @evaluator 按 4 维度评分 → 更新 .ai_state/quality.json → VERDICT

**门控:**
- PASS (均分 ≥ 4.0) → 进 V
- CONCERNS (3.0-3.9) → 修复问题后重新评分
- REWORK (2.0-2.9) → 回 E 阶段重做
- FAIL (< 2.0) → 回 D 阶段重新设计

**详细指引:** → review/SKILL.md (多工具审查编排 + 评分)

---

### V 归档 (Path B+)

**目标:** 更新项目知识库, 为下次迭代积累经验。

**步骤:**
1. 更新 conventions.md — 新发现的 Gotchas (❌ 错误做法 → ✅ 正确做法)
2. 更新 lessons.md — 本次开发的关键教训
3. 重置状态 — state.json: `{path: "", stage: "", sprint: sprint+1}`
4. 告知用户: "Sprint N 完成, 交付了 X 个 Feature。"

**产出:** conventions.md + lessons.md 更新, state.json 重置
**门控:** 无 (最终阶段)

---

## 阶段转换规则

1. **前进:** 满足当前阶段门控条件后, 更新 state.json stage 并进入下一阶段
2. **后退:** T 阶段 REWORK → 回 E; FAIL → 回 D。state.json 同步更新
3. **跳过:** Path A 跳过 R₀/R/D/P/V, 只做 E→T
4. **中断恢复:** 如果 session 断开, context-loader hook 会读 state.json 恢复到当前阶段
5. **用户覆盖:** 用户可随时说 "跳到 E 阶段" 或 "回到设计阶段", 尊重但提醒后果

## Gotchas

- ❌ 收到任务直接写代码 → ✅ 先走 PACE 路由, 确定 Path 再开始
- ❌ Path B 任务当 Path A 做 → ✅ 如果任务涉及 4+ 文件或架构变更, 至少用 Path B
- ❌ D 阶段用 /codex:adversarial-review → ✅ 该命令审查代码变更, D 阶段无代码, 用 @evaluator 或 `/review`
- ❌ E 阶段完成一半就进 T → ✅ Sisyphus: 所有 Task 完成才能进 T
- ❌ T 阶段 CONCERNS 就交付 → ✅ 修复 CONCERNS 指出的问题后重新评分再交付
- ❌ 跳过 V 阶段直接结束 → ✅ V 阶段积累的经验是下次迭代的关键输入

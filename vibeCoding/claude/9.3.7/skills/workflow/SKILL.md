---
effort: high
---
# VibeCoding Workflow Engine — PACE 路由 + RIPER-7 编排

> 收到需求 → PACE 评估 Path → 按 Path 执行 RIPER-7 → 每阶段调插件

---

## Step 0: PACE 复杂度路由

### 5 维判定

| 维度 | A (快速) | B (标准) | C (复杂) | D (系统) |
|:---|:---|:---|:---|:---|
| 文件数 | 1-2 | 3-10 | 10-50 | 50+ |
| 预估时间 | ≤30min | 6-12h | 1-3天 | 1周+ |
| 架构影响 | 无 | 局部 | 跨模块 | 全局 |
| 依赖变更 | 无 | 1-2个 | 多个 | 技术栈级 |
| 测试需求 | 功能验证 | 单元+集成 | +E2E | +安全+性能 |

**规则**: 默认 A, 任意 2 维达 B→升 B, 依此类推
**用户说 "简单改一下"** → 保持 A
**不确定** → cunzhi 问用户

### 评估后输出
```
📊 PACE → Path [X]
插件: [本 Path 加载的插件]
阶段: [本 Path 执行的 RIPER-7 阶段]
```

### 写 state.json
```json
{"path": "B", "current_phase": "R0", ...}
```

---

## Path A: 快速修复 (≤30min)

**执行者**: 主 Agent 直接执行, 不 spawn subagent

### A-1. 调研 (轻量)
- `augment-context-engine` search "[关键词]" — 搜索相关代码
- 已知方案 → 跳过, 直接写

### A-2. 执行
优先:
```
/gsd:quick "[需求描述]"
```
GSD quick 模式: 跳过重规划, fresh subagent 直接执行

降级: `/codex:rescue "[需求]"` → `superpowers execute-plan` → 手动写

### A-3. 交付
- CC 原生 `git add` + `git commit` (或 commit-commands 插件增强)
- delivery-gate hook 宽松模式 (不检查 feature_list / quality)
- cunzhi [DELIVERY_CONFIRMED]

**新手示例**: "修个 typo" → `/gsd:quick "修复README中的typo"`

---

## Path B/C/D: 完整 RIPER-7

### 角色分工

| 角色 | 谁 | CC 机制 | 何时 |
|:---|:---|:---|:---|
| Planner | 主 Agent (你) | 直接执行 | R₀/R/D/P/V |
| Generator | `@generator` | subagent (worktree) | E |
| Evaluator | `@evaluator` | subagent (只读) | T, D(审合同) |

---

### R₀ 预研

**执行者**: 主 Agent (Planner)

**判断项目类型**: `.git/` 存在 → 已有项目; 否则 → 新项目

**新项目**:
1. `/gsd:discuss-phase` — GSD 结构化访谈
   GSD 会问: 目标用户? 核心功能? 技术约束? 非功能需求?
   用户不确定怎么答 → GSD 给选项

**已有项目**:
1. `/gsd:map-codebase` — 生成代码结构地图
2. `augment-context-engine` search "[需求关键词]" — 搜索已有代码

**两者共同**:
3. `superpowers brainstorm "[需求]"` — 2-3 个方案对比
4. 读 `.ai_state/knowledge.md` — 历史经验
5. 需求仍模糊 → cunzhi [DIRECTION] 确认方向

**输出**: 明确的需求描述 (含边界 + 非功能)

---

### R 调研

**执行者**: 主 Agent (Planner)

1. `augment-context-engine` search — 深入搜索代码架构
2. `context7 "[库名] [API]"` — 查外部库文档
3. WebSearch — 最新官方文档/changelog
4. 评估技术风险 + 依赖兼容性

**输出**: `.ai_state/design.md`

---

### D 定稿

**执行者**: 主 Agent (Planner) + `@evaluator` 审合同

1. 完善 design.md (接口/数据结构/模块划分/错误处理)
2. `superpowers plan-review` — 方案评审
3. 将实现拆分为 Sprints (每 Sprint ≤ 1 天)
4. sprint-contract skill — 草拟每 Sprint 验收合同
5. `@evaluator` 审核合同:
   ```
   @evaluator 审核 Sprint {N} 合同:
   - 验收标准可测吗? 能用 playwright/测试框架验证?
   - 遗漏边界条件?
   - acceptance_steps 完整?
   ```
6. **生成 feature_list.json** (从 contracts 展开):
   ```json
   [{"id":"F001","sprint":1,"category":"functional",
     "description":"用户可通过邮箱注册",
     "acceptance_steps":["打开注册页","填写邮箱密码","点击注册","验证跳转"],
     "passes":false,"_verified_by":""}]
   ```
   **铁律**: 生成后 description/acceptance_steps 禁止修改
7. 更新 state.json: total_sprints, features_total
8. cunzhi [DESIGN_READY] — 用户确认

**输出**: design.md + contract-{N}.md + feature_list.json + state.json

---

### P 规划

**执行者**: 主 Agent (Planner)

1. `/gsd:plan-phase` — GSD 生成原子计划
   每计划 2-3 tasks, 控制在 50% context
   独立 tasks 自动分 waves (并行)
2. `superpowers plan-review` — 检查合理性
3. 也可以用 CC 原生 `Shift+Tab` 进入 Plan Mode 让 Claude 只分析不写
4. cunzhi [PLAN_CONFIRMED] — 用户确认
4. 更新 state.json: current_sprint, current_phase="P"

**输出**: plan.md

---

### E 执行

**执行者**: `@generator` subagent

**主 Agent 调度**:
```
@generator 执行 Sprint {N}:
- 读 plan.md Sprint {N} 的 Tasks
- 读 contract-{N}.md 验收标准
- 读 feature_list.json sprint={N} 的 features
- 按三级策略执行, 每 Task 后 reflexion
```

**三级策略**:

| 优先级 | 插件 | 命令 | 降级条件 |
|:---|:---|:---|:---|
| 1 | GSD | `/gsd:execute` | GSD 未装 / plan-phase 未跑 |
| 2 | Codex | `/codex:rescue "实现 [Task], 标准: [contract]"` | 未装 / 超时 / 报错 |
| 3 | superpowers | `superpowers execute-plan` | 不可用 |
| 4 | 手动 | TDD: 测试→实现→重构 | — |

**Path C 并行**: GSD waves 自动并行独立 tasks
**codex 后台**: `/codex:rescue --background "..."` → `/codex:status` → `/codex:result`

**每 Task 后**:
- GSD execute 模式 → GSD 自带验证, 跳过 reflexion (GSD subagent 看不到我们的 skills)
- codex / superpowers / 手动 → 执行 reflexion skill 自检 (7 条)

**GSD 与 VibeCoding 状态同步**:
GSD 有自己的状态文件 (SPEC.md / PLAN files), VibeCoding 有 .ai_state/。
每次 GSD 阶段完成后, 同步关键结果到 .ai_state/:
- GSD execute 完成 → 更新 doing.md + state.json (current_phase="E")
- GSD verify-work 完成 → 结果反映到 feature_list.json

**更新**: doing.md + state.json (current_phase="E")

---

### T 测试/审查

**执行者**: `@evaluator` subagent

**主 Agent 调度**:
```
@evaluator 审查 Sprint {N}:
- 读 state.json 确认当前 Path (决定调哪些插件)
- 调 code-review + codex:adversarial + playwright
- Path C/D 额外调 ECC
- 综合 → quality.json
- 更新 feature_list.json passes
```

**@evaluator 按 evaluator.md 执行**, 核心步骤:

| Step | 工具 | 做什么 | 所有 Path | Path C/D |
|:---|:---|:---|:---|:---|
| 0 | /diff | CC 原生: 先看变更全貌 | ✅ | ✅ |
| 1 | /review | CC 原生: 内置代码审查 | ✅ | ✅ |
| 2 | codex:adversarial-review | GPT-5.4 对抗质疑 | ✅ | ✅ |
| 3 | playwright-skill | E2E + 截图 | ✅ | ✅ |
| 4 | ECC AgentShield | 安全扫描 | — | ✅ |
| 5 | GSD verify-work | 手动测试引导 | ✅ | ✅ |

**综合 → quality.json** (1-5 标度, PASS/CONCERNS/REWORK/FAIL)

**判定后**:
- **PASS** → 进 V 或下一个 Sprint
- **CONCERNS** → cunzhi 让用户决定: 放行还是修?
- **REWORK** → 主 Agent 再调 `@generator` 修复
- **FAIL** → 回到 D 重新设计
- **E↔T 循环 ≤3 轮**, 超过 → FAIL + 人工介入

---

### V 归档

**执行者**: 主 Agent (Planner)

1. CC 原生 git commit (或 `commit-commands` 插件增强格式)
2. kaizen skill → knowledge.md 经验沉淀
3. ECC `instinct-export` → 导出模式 (如有)
4. 写 progress.json 会话摘要:
   ```json
   {"timestamp":"ISO","sprint":"1/3",
    "completed_features":["F001","F002"],
    "next_steps":"开始 Sprint 2",
    "git_commit":"abc1234","known_issues":""}
   ```
5. 更新 state.json
6. cunzhi [DELIVERY_CONFIRMED]

**Context Reset (Path C/D)**:
还有下一个 Sprint?
→ 写完 progress.json 后, 建议:
  "退出当前 session, 用 `/vibe-resume` 恢复。
   GSD 和 .ai_state/ 会保留完整状态, 下个 session 从 progress.json 接上。"
→ state.json.context_resets += 1

---

## 新手指引

| 你说 | 我做 |
|:---|:---|
| "修个 typo" | Path A → `/gsd:quick "修复typo"` |
| "加个登录功能" | Path B → 完整 R₀→R→D→P→E↔T→V |
| "重构认证模块" | Path C → + GSD waves 并行 |
| "从零搭微服务" | Path D → + ECC 安全深度扫描 |
| "不确定" | cunzhi 问你, 你说了算 |

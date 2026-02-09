# RIPER-7 工作流编排

唯一权威调度表。每个阶段: 加载什么 skill、调用什么 plugin、用什么 MCP。

---

## 启动检查 (每次进入 RIPER-7 前)

```
1. 读 .ai_state/session.md → 确认项目+当前 Path+riper_phase
2. 读 .ai_state/doing.md → 有未完成? → 恢复该阶段
3. 无 session.md → 提示 vibe-init
```

---

## 阶段总调度

| 阶段 | VibeCoding Skill | 官方 Plugin | MCP | Superpowers Skill |
|:---|:---|:---|:---|:---|
| **R** | brainstorm | — | sou, deepwiki | brainstorming |
| **D** | brainstorm | — | sou, deepwiki, cunzhi | brainstorming |
| **P** | — | feature-dev (自动) | cunzhi | writing-plans |
| **C** | cunzhi | — | cunzhi | — |
| **E** | tdd, worktrees† | commit-commands (每次提交), hookify†, frontend-design† | sou | subagent-driven-dev |
| **V** | verification | — | — | verification-before-completion |
| **Rev** | code-quality, knowledge | code-review (/review), security-guidance (自动), pr-review-toolkit† (/pr-review) | cunzhi | requesting-code-review |

† = Path C/D 或按项目类型，非必须

---

## R — Require (需求理解)

**目标**: 搞清楚做什么 / 不做什么

```
工具编排:
  1. → skill/brainstorm (R 阶段增强)
     a. sou.search("任务关键词")     ← MCP: 搜索现有代码
     b. 读 .ai_state/conventions.md   ← 避免已知坑
     c. 读 .knowledge/experience/     ← 避免重复犯错
  2. deepwiki.query("技术领域")       ← MCP: 领域知识 (按需)
  3. → Superpowers brainstorming       ← 苏格拉底式提问 (5-8 问)
     降级: SP 未安装 → 直接提问 (范围/约束/验收)
  4. 输出: 需求理解摘要

→ 更新 session.md: riper_phase: R
```

禁止修改代码。

---

## D — Discuss (方案讨论)

**目标**: 2-3 备选方案 + 推荐

```
工具编排:
  1. → skill/brainstorm (D 阶段增强)
     a. deepwiki.query("方案技术")    ← MCP: 技术调研
     b. sou.search("现有实现模式")    ← MCP: 搜索已有代码
  2. → Superpowers brainstorming       ← 方案对比段
     降级: SP 未安装 → 直接列出 2-3 方案 + trade-off
  3. → .ai_state/decisions.md          ← skill/brainstorm 写入 ADR
  4. cunzhi [DESIGN_READY]             ← MCP: 寸止确认

→ 更新 session.md: riper_phase: D
```

禁止修改代码。必须呈现多个备选。

---

## P — Plan (任务拆解)

**目标**: 微任务列表 (每个 2-5 分钟)

```
工具编排:
  1. → Superpowers writing-plans       ← 结构化拆解
     降级: SP 未安装 → 直接拆解微任务
  2. → 官方 feature-dev plugin         ← 自动: 功能开发规范
  3. Path B/C/D: TDD 任务交替 (先 RED 后 GREEN)
  4. 每个任务含: 文件路径 + 验证步骤
  5. → .ai_state/plan.md + todo.md

  6. cunzhi [PLAN_READY]

→ 更新 session.md: riper_phase: P
```

---

## C — Confirm (逐项确认)

**目标**: 寸止确认验收标准

```
工具编排:
  1. → skill/cunzhi 逐项确认
     - 验收标准
     - 范围边界 (做/不做)
     - 技术细节 (数据结构/API)
  2. 用户可修改/补充
  3. → 更新 todo.md (添加 acceptance criteria)
  4. cunzhi [CONFIRMED]

→ 更新 session.md: riper_phase: C
```

---

## E — Execute (编码实现)

**目标**: TDD 循环 + 写代码

```
工具编排:
  0. Path C/D: → skill/worktrees 创建隔离分支
     Path C: git worktree add → 单分支隔离
     Path D: Lead 主分支 + Teammate 子分支
  1. → skill/tdd                       ← RED-GREEN-REFACTOR 循环
     内部调用:
       Superpowers tdd                  ← TDD 方法论
       降级: SP 未安装 → 直接 RED-GREEN-REFACTOR
       Superpowers subagent-driven-dev  ← 子任务并行
       降级: SP 未安装 → 顺序执行
  2. sou.search("参考实现")             ← MCP: 搜索相关代码
  3. 按项目类型按需:
     → 官方 hookify plugin              ← React Hooks 项目 (自动)
     → 官方 frontend-design plugin      ← 前端 UI 项目 (自动)
     → skill/context7                   ← 需要查库文档时
  4. 提交策略 (官方 commit-commands plugin):
     Path A: 改完直接 commit
     Path B: 每个 TASK 完成后 commit
     Path C/D: 每个 GREEN 后 commit (小步提交)
  5. todo.md → doing.md → done.md

→ 更新 session.md: riper_phase: E, current_task: TASK-N

Path D: 加载 skill/agent-teams → Lead 分配 → Teammates 并行。
```

---

## V — Verify (验证)

**目标**: 自检交付物完整性

```
工具编排:
  1. → skill/verification              ← 验证循环 (按 Path 分级清单)
     内部调用:
       Superpowers verification-before-completion
       降级: SP 未安装 → 直接执行清单
  2. 通过 → done.md (verified: true)
  3. 失败 → 修复重试 (max 3)
     2 次: 加载 skill/debugging
     3 次: cunzhi [VERIFY_FAIL] 人工介入

→ 更新 session.md: riper_phase: V
```

---

## Rev — Review (审查 + 学习)

**目标**: Linus 审查 + 经验提取

```
工具编排:
  1. → skill/code-quality              ← 六维审查
     内部调用:
       官方 code-review plugin          ← /review 触发
       官方 security-guidance plugin    ← 自动: 扫描安全问题
       官方 pr-review-toolkit plugin    ← /pr-review (Path C/D)
       Superpowers requesting-code-review
       降级: SP 未安装 → 直接六维审查
  2. → skill/knowledge                  ← 经验提取
     → .knowledge/experience/
  3. 严重问题 → 回到 E
  4. 上下文 >500K → 加载 skill/archive → 归档已完成阶段
  5. cunzhi [TASK_DONE]
  6. → .ai_state/archive.md

→ 更新 session.md: riper_phase: done
```

---

## 阶段转换规则

```
启动   : 检查 session.md → 恢复或开始
R → D  : 能回答"做什么/不做什么"
D → P  : cunzhi DESIGN_READY 通过
P → C  : cunzhi PLAN_READY 通过
C → E  : cunzhi CONFIRMED 通过
E → V  : todo.md 清空
V → Rev: done.md 全部 verified: true
Rev → ✓: cunzhi TASK_DONE
```

每次转换更新 session.md 的 riper_phase 字段。
中断恢复: vibe-resume 读 session.md → 跳到对应阶段。

---

## Path 裁剪

| Path | 阶段 | 跳过 |
|:---|:---|:---|
| A | R → E → V | D, P, C, Rev |
| B | R → D → P → C → E → V → Rev | 无 |
| C | 同 B + 九步展开 + 每步寸止 | 无 |
| D | Lead(R→D→P→C) → Teams(E) → Lead(V→Rev) | 无 |

### Path C 九步展开

| Step | RIPER | 系统动作 | 寸止 |
|:---|:---|:---|:---|
| 1 | R | 苏格拉底提问 | — |
| 2 | R | 需求确认 | REQ_READY |
| 3 | D | 方案探索 | — |
| 4 | D | 方案对比+推荐 | DESIGN_READY |
| 5 | P+C | 微任务拆解+确认 | CONFIRMED |
| 6 | E | TDD 开发 (worktree) | PHASE_DONE |
| 7 | E | TDD 开发 | — |
| 8 | V | 自检验证 | VERIFIED |
| 9 | Rev | 审查+学习+归档 | TASK_DONE |

---
effort: high
description: >
  当进入代码实现阶段、需要执行 Task 写代码、或被 /vibe-work 命令调用时触发。
  管理三级委托策略、TDD 流程、和 Task 执行循环。
---

# Execute Skill: 代码实现

## 你的目标

逐个完成 plan.md 中的 Task, 写出通过测试的代码。
使用三级委托策略: 优先委托给 Codex/subagent, 兜底自己写。

---

## 前置检查

开始执行前, 确认:
1. .ai_state/state.json 存在 → 读取当前 Path
2. **Path B+:** plan.md 存在且有 Task 列表 (没有 → 先走 plan skill)
3. **Path B+:** feature_list.json 已初始化 (没有 → 先走 plan skill)
4. **Path A:** 不需要 plan.md 和 feature_list.json — 直接根据用户描述执行修复
5. .ai_state/state.json stage = "E" (不是 → 更新为 "E")
6. .ai_state/conventions.md 的 Gotchas — 注意避开已知坑

---

## 三级委托策略

### Level 1: /codex:rescue (首选)

适用场景: 独立、明确的实现任务。Codex 在后台执行, 你审查结果。

```
/codex:rescue 实现 T001: 创建 User model，参照 .ai_state/design.md 的数据模型定义，使用 Prisma schema，包含 email(unique), passwordHash, createdAt 字段
```

管理后台任务:
```
/codex:status          # 查看进度
/codex:result          # 任务完成后取结果
/codex:cancel          # 取消任务
```

长任务推荐后台:
```
/codex:rescue --background 实现 T002: POST /api/register API
```

可指定模型和 effort:
```
/codex:rescue --model gpt-5.4-mini --effort medium 简单的输入验证
```

收到结果后: 审查代码 → 应用到项目 → 运行测试验证。

**降级触发:** Codex 不可用、超时、或结果质量不满意 → 降到 Level 2。

### Level 2: @generator subagent (次选)

适用场景: Codex 不可用或超时时, 使用 CC 自带的 subagent 在独立 worktree 中执行。

**调用方式:** 委托给 @generator:
```
@generator 实现 T001: 创建 User model, 参照 .ai_state/design.md 数据模型定义
```

@generator 在独立 worktree 中工作:
1. 读取 Task 描述 + 验收标准
2. 先写测试, 再写实现
3. 运行测试确认通过
4. 输出变更摘要

完成后: 你审查 @generator 的输出 → 应用到项目 → 运行测试验证。

**降级触发:** @generator 超时或失败 → 降到 Level 3。

### Level 3: 手动 TDD (兜底)

适用场景: 简单任务, 或 Level 1/2 都不可用时。

严格 TDD 流程:
1. **先写测试** — 从 acceptance_criteria 创建测试用例
   ```typescript
   // __tests__/register.test.ts
   describe('POST /api/register', () => {
     it('should register with valid email and password', async () => {
       // ... 测试代码
     });
     it('should reject invalid email', async () => {
       // ... 测试代码
     });
   });
   ```
2. **运行测试** — 确认测试失败 (红)
3. **写实现** — 写最少的代码让测试通过
4. **运行测试** — 确认测试通过 (绿)
5. **重构** — 优化代码, 确认测试仍通过

---

## Path A 快速执行

Path A (修 bug / 改配置) 不需要 plan.md, 直接执行:

1. 理解用户描述的问题
2. 定位相关代码 (Grep/Read)
3. 按 Level 3 手动 TDD 修复: 写测试 → 修代码 → 运行测试
4. reflexion 自查
5. 完成 → 进入 T 阶段

---

## Task 执行循环 (Path B+)

对 plan.md 中的每个 Task, 重复以下流程:

```
┌──→ 1. 选取下一个 pending Task
│    2. feature_list.json 对应 Feature status → "doing"
│    3. 按三级委托策略实现
│    4. 运行测试, 确认全部通过
│    5. 执行 reflexion skill (铁律 #4)
│        → 发现问题? 立即修复, 回到步骤 4
│        → 无问题? 继续
│    6. feature_list.json status → "done"
│    7. progress.json 更新 completed 计数
│    8. plan.md 中勾选 [x]
└──← 9. 还有 pending Task? → 回到步骤 1
     10. 所有 Task done 或 blocked → E 阶段完成
```

### Path C/D 并行执行

当有多个无依赖的 Task 时, 可并行委托:
```
/codex:rescue --background 实现 T002: POST /api/register
/codex:rescue --background 实现 T004: POST /api/login
/codex:status  # 两个任务并行进行
```

或使用 @generator subagent (独立 worktree):
```
委托 @generator 实现 T002, 参照 design.md 验收标准
```

并行完成后逐个审查 + reflexion。

---

## 遇到阻塞

如果某个 Task 无法完成 (如依赖不可用、需求不明确):
1. feature_list.json 对应项 status → "blocked"
2. 在 plan.md 中标注: `- [blocked] T003: 原因 — 等待第三方 API 开放`
3. 通知用户: "T003 被阻塞, 原因是... 需要你的决定。"
4. 继续执行其他非阻塞的 Task

---

## Gotchas

- ❌ 跳过测试直接写实现 → ✅ TDD: 先写测试再写实现, 这是铁律 #2
- ❌ Level 1 结果不审查就应用 → ✅ 所有委托结果必须审查: 读代码 + 运行测试
- ❌ 一个 Task 没完成就开始下一个 → ✅ 完成当前 Task (含 reflexion) 后再继续
- ❌ 测试失败就跳过 → ✅ 测试必须通过。修不好就标 blocked, 不要跳过
- ❌ 忘记更新 feature_list.json → ✅ 每个 Task 完成/阻塞时同步更新状态文件
- ❌ 用 Level 3 写完不做 reflexion → ✅ 无论哪个 Level, reflexion 都是必须的

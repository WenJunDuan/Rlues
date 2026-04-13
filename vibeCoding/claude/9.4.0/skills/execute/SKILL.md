---
name: execute
effort: high
context: fork
description: >
  代码实现。Task 执行、TDD、三级委托、自审链路。当进入 E 阶段时触发。
allowed-tools: Bash, Read, Write, Edit, MultiEdit, Grep, Glob, Task
---

# Execute Skill: 代码实现

## 当前状态
!`cat .ai_state/project.json 2>/dev/null | head -5`

## 待办任务
!`grep -c "\[ \]" .ai_state/tasks.md 2>/dev/null`

## 项目注意事项
!`cat .ai_state/project.json 2>/dev/null`

---

## 前置检查

- **Path A:** 不需要 tasks.md — 直接修复, 跳到 "Path A 快速执行"
- **Path B+:** tasks.md 必须有待办 Task
- project.json stage 更新为 "E"

---

## 三级委托

### Level 1: /codex:rescue (首选)

**委托前必须:** 生成 .ai_state/handoff.md (design 摘要 + Task 描述 + conventions + gotchas)

```
/codex:rescue --background 实现 [Task]: [描述], 参照 .ai_state/handoff.md
/codex:status        → 轮询进度
/codex:result        → 取回结果
```

**取回后 Claude 必须审查** (谁写的代码谁先自审不适用于 Codex — Claude 作为 PM 审查):
1. 读 Codex 产出的代码
2. 对照 Task 验收标准逐条检查
3. 检查边界情况和错误处理
4. 满意 → 应用到项目 → 运行测试
5. 不满意 → 修改后应用 或 降级到 Level 2/3 重写

### Level 2: @generator (次选)

```
@generator 实现 [Task]: [描述], 参照 .ai_state/design.md
```

取回后同样 Claude 审查 → 应用 → 测试

### Level 3: 手动 TDD (兜底)

Claude 自己写。严格 TDD:
1. 写测试 (红) → 运行确认失败
2. 写实现 (绿) → 运行确认通过
3. 重构 → 确认仍通过

**Claude 写完后必须自审:**
- 验收标准逐条对照
- 边界情况 (空值/超大/并发/权限)
- 代码质量 (命名/结构/重复)

---

## Path A 快速执行

1. 理解问题 → Grep/Read 定位
2. Level 3 手动 TDD 修复
3. 自审 → 进入 T 阶段

---

## Task 执行循环 (Path B+)

对每个待办 Task:

```
1. 生成 handoff.md
2. 按三级委托实现
3. 运行测试
   └─ 失败? → /debug 分析 → 修复 → 重测 (循环直到通过)
4. 自审 (无论哪个 Level 委托, Claude 都要审查一遍)
5. tasks.md: 移到 "完成" 段 (- [x])
6. 下一个 Task
```

**Path C/D 并行:** `/batch 按 tasks.md 中独立 Task 并行执行`

**所有 Task 完成后:**
1. 运行 `/simplify` 清理代码
2. 更新 project.json: stage="T"
3. 进入 T 阶段 (review skill)

---

## 遇到阻塞

1. tasks.md: 移到 "阻塞" 段, 注明原因
2. 通知用户
3. 继续其他非阻塞 Task

## Gotchas

- ❌ 跳过测试 → ✅ TDD 铁律
- ❌ 委托结果不审查就应用 → ✅ 所有结果必须 Claude 审查
- ❌ 忘记更新 tasks.md → ✅ 每个 Task 完成立即更新
- ❌ 不生成 handoff.md → ✅ codex:rescue 前必须生成
- ❌ 测试失败跳过 → ✅ 修不好标 blocked, 不要跳过
- ❌ 不自审 → ✅ 无论谁写的, Claude 都要审一遍

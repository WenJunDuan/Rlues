---
name: execute
effort: high
context: fork
description: >
  代码实现。Task 执行、TDD、三级委托。当进入 E 阶段或调用 /vibe-work 时触发。
allowed-tools: Bash, Read, Write, Edit, MultiEdit, Grep, Glob, Task
---

# Execute Skill: 代码实现

## 当前状态
!`cat .ai_state/project.json 2>/dev/null | head -5`

## 待办任务
!`grep "^\- \[ \]" .ai_state/tasks.md 2>/dev/null || echo '(无待办 Task)'`

## 项目注意事项
!`cat .ai_state/project.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'⚠️ {g}') for g in d.get('gotchas',[])]" 2>/dev/null || true`

---

## 前置检查

- **Path A:** 不需要 tasks.md — 直接根据用户描述修复
- **Path B+:** tasks.md 必须存在且有待办 Task (没有 → 先走 plan skill)
- project.json stage 更新为 "E"

---

## 三级委托

按顺序尝试, 失败则降级:

### Level 1: /codex:rescue (首选)

委托前生成交接上下文:
```
将 design.md 摘要 + 当前 Task 描述 + conventions + gotchas 写入 .ai_state/handoff.md
```

```
/codex:rescue --background 实现 [Task ID]: [描述], 参照 .ai_state/handoff.md
/codex:status        # 查进度
/codex:result        # 取结果
```

取回结果 → 审查代码 → 应用到项目 → 运行测试

**降级条件:** Codex 不可用 / 超时 / 结果不满意

### Level 2: @generator (次选)

```
@generator 实现 [Task ID]: [描述], 参照 .ai_state/design.md
```

@generator 在独立 worktree 中: 读 Task → 先写测试 → 再写实现 → 运行测试

**降级条件:** @generator 失败

### Level 3: 手动 TDD (兜底)

严格 TDD: 写测试 (红) → 写实现 (绿) → 重构 → 确认测试通过

---

## Path A 快速执行

Path A 不走 Task 循环, 直接:
1. 理解问题 → Grep/Read 定位代码
2. Level 3 手动 TDD 修复
3. 自查 → 进入 T 阶段

---

## Task 执行循环 (Path B+)

```
对每个待办 Task:
  1. 按三级委托实现
  2. 运行测试 (npm test / pytest / 项目测试命令)
  3. 自查: 代码是否满足 Task 验收标准? 有无遗漏?
  4. tasks.md: 移到 "完成" 段 (- [x])
  5. 重复直到无待办 Task
```

**Path C/D 并行:** 有多个独立 Task → `/batch 按 tasks.md 并行执行`

**所有 Task 完成后:** 运行 `/simplify` 清理代码 → 进入 T 阶段

---

## 遇到阻塞

1. tasks.md: 移到 "阻塞" 段, 注明原因
2. 通知用户
3. 继续执行其他非阻塞 Task

## Gotchas

- ❌ 跳过测试直接写实现 → ✅ TDD: 先测试后实现
- ❌ Level 1 结果不审查就应用 → ✅ 所有委托结果必须审查
- ❌ 忘记更新 tasks.md → ✅ 每个 Task 完成/阻塞时同步更新
- ❌ 不生成 handoff.md 就委托 → ✅ codex:rescue 前必须生成交接上下文

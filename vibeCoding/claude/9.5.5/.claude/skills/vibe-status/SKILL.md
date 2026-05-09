---
name: vibe-status
effort: xhigh
disable-model-invocation: true
description: >
  VibeCoding 状态面板。显示当前 PACE 状态、最近 hook 触发、项目 lessons 数量、plugin 健康。
---

# /vibe-status (v9.5)

实时聚合 VibeCoding 运行状态。无副作用, 只读。

## 收集顺序

### 1. PACE 状态
读 `.ai_state/project.json` → Path/Stage/Sprint/test_cmd/conventions/gotchas

### 2. Sprint 进度
读 `.ai_state/tasks.md` → 计算: done / pending / blocked

### 3. Hook 触发记录
读 `.ai_state/hook-trace.jsonl` (最近 50 条) → 按 hook 名分组统计:
- delivery-gate: 触发 N 次, 阻断 M 次, soft warn K 次
- bash-guard: 拦截 N 次
- subagent-retry: 注入提示 N 次
- session-start / post-compact: 注入次数
- (v9.5) output-evidence-augmentor: mutate 次数 (启用时)
- (v9.5) session-end-reminder / task-created-advisor: 触发次数

### 4. Lessons 统计 (v9.5: 仅项目级)
读 `.ai_state/lessons.md` → 行数 + 最新 1 条标题
全局级已删除（Hermes 不做跨项目记忆）

### 5. Plugin 健康
- codex: `which codex` + `/codex:setup` 状态行
- superpowers: 检查 `~/.claude/plugins/cache/superpowers/` 存在
- claude-mem: 检查 `~/.claude/plugins/` 是否含 claude-mem
- context7: `npx ctx7 --version 2>&1 | head -1`

### 6. Effort 状态 (v9.5)
读 `$CLAUDE_EFFORT` → 当前 effort level（xhigh / max / high / medium / low）

## 输出格式

```
=== VibeCoding Hermes v9.5 Status ===

[PACE]    Path: Feature  Stage: impl  Sprint: 3  Effort: xhigh
[Tasks]   3 done · 2 pending · 0 blocked
          Next: Task 4 — auth middleware

[Hooks]   最近 50 次触发:
  delivery-gate     ✓ 12 (阻断 2, soft 1)
  bash-guard        ✓ 0 拦截
  subagent-retry    ⚠ 3 注入
  output-augmentor  ⚪ disabled (设置 settings 启用)
  session-end       ⏰ 2

[Lessons] 项目: 4 条 (最新: "JWT refresh secret 分离")
          [全局已删除, 跨项目记忆装 claude-mem]

[Plugins] codex@1.0.4         ✓ ready
          superpowers@5.x     ✓ loaded
          claude-mem          ⚪ 未装 (推荐)
          context7            ✓ available
          ctx7 CLI            ✓ npx ctx7 v2.x

[Lints]   test_cmd: npm test
          lint_cmd: npm run lint
```

## 实现方式

无外部依赖, 用 Bash + jq + ls 读已有文件聚合。失败的项 → 显示 "✗ 不可用"。
不写新文件, 不改状态。

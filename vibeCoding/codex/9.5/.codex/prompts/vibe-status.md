# /vibe-status — VibeCoding 状态面板 (Codex 端)

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
- lesson-drafter: 起草 N 个 draft
- session-start / user-prompt-submit: 注入次数

### 4. Lessons 统计
- 项目级: `.ai_state/lessons.md` 行数 + 最新 1 条标题
- 全局级: `ls ~/.codex/lessons/*.md` 计数 (排除 draft- 和 archive)
- Drafts: `ls ~/.codex/lessons/draft-*.md` 列表 (含创建日期, > 7 天提示用户应该归档/确认)

### 5. Codex 平台健康
- `codex --version`
- `grep "codex_hooks = true" ~/.codex/config.toml`
- 当前 model + profile
- `npx ctx7 --version 2>&1 | head -1`

## 输出格式

```
=== VibeCoding Hermes v9.4.5 (Codex) Status ===

[PACE]   Path: Feature  Stage: impl  Sprint: 3
[Tasks]  3 done · 2 pending · 0 blocked
         Next: Task 4 — auth middleware

[Hooks]  最近 50 次触发:
  session-start      ✓ 5 注入
  user-prompt-submit ✓ 28 注入 (智能触发, 18 命中关键词)
  delivery-gate      ✓ 12 (阻断 2, soft 1)
  bash-guard         ✓ 0 拦截
  subagent-retry     ⚠ 3 注入压力
  lesson-drafter     📝 1 draft

[Lessons]
  项目: 4 条 (最新: "JWT refresh secret 分离")
  全局: 8 条
  Drafts: 1 个待审 (draft-2026-04-28-spawn-agent-fail.md, 0 天)

[Codex]
  version       ✓ codex-cli 0.124.0
  codex_hooks   ✓ stable
  model         gpt-5.5 (default)
  ctx7 CLI      ✓ npx ctx7 v2.x

[Lints]
  test_cmd: npm test
  lint_cmd: npm run lint
```

## 实现方式

无外部依赖, 用 Bash + jq + ls 读已有文件聚合。失败的项 → 显示 "✗ 不可用"。

不写新文件, 不改状态。

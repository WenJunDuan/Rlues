# athena-checkpoint · playbook

> 从 SKILL.md 下沉的完整正文 (v9.9.6 渐进披露拆分)。热路径只留触发与判据。

## 工作流

### Step 1 · 写前快照 (防覆盖)

```bash
ts=$(date +%Y-%m-%d-%H%M%S)
cp .ai_state/_index.md ".ai_state/.snapshots/pre-checkpoint-${ts}.md"
```
与 compact-snapshot.py hook 同机制的手动版.

### Step 2 · 主 thread 总结本会话增量

回顾**本会话** (非整个项目史), 提炼三块:
1. **做了什么**: stage 推进 / 改了哪些文件 / 拍了哪些决策 / 跑了哪些验证
2. **当前状态**: stage / path / next_action / current_sprint_slug / 卡在哪
3. **下次接续点**: 下次从哪继续 (具体到动作)

### Step 3 · 写入两处（索引经现有锁/原子更新机制）

1. **`_index.md` frontmatter**: 校正 stage/path/next_action/current_sprint_slug、`pointers.latest_{design,review,cleanup,requirement}`；≤12 KiB，route_history/current-state 各最多 10 条、条目 ≤160 B，溢出原文与指针一起保留；空更新不写
2. **`sprints/{slug}/session-log.md`**: 按 [执行合同](../../pace/references/execution-contracts.md) 保存实际基线、未提交增量、任务真实 ID/工件引用、唯一整合者、已知失败与下一动作

### Step 4 · 回显结果（已有授权不重复确认）

```
✓ checkpoint 已存 ({ts})
  stage: impl  path: System  sprint: 2026-06-22-xxx
  next_action: runtime-verify
  下次接续: 跑 /athena-runtime-verify 验 /api/refresh 并发场景
  快照: .snapshots/pre-checkpoint-{ts}.md
```

## session-log.md 格式

```markdown
# Session Log — {slug}

## 2026-06-22 14:30 (checkpoint)
- 做了: 独立设计挑战完成 → impl T1-T6 写完单测过; runtime-verify T4 并发卡住
- 状态: stage=impl, next_action=runtime-verify
- 决策: 并发刷新用乐观锁 (compound/...-decision-refresh-lock.md)
- 下次接续: /athena-runtime-verify 复跑并发用例
- blocker: 无
```

## 与 compact hook / compound 分工

| | compact-snapshot.py hook | /checkpoint (本) | /compound |
|---|---|---|---|
| 触发 | PreCompact 自动 | 手动 | 踩坑/决策时 |
| 写什么 | 原样快照 _index | _index 校正 + session-log + 接续点 | 跨 sprint 经验 |
| 性质 | 防丢保险 | 主动留交接 (本会话状态) | 长期复利知识 |

checkpoint 是"我做到哪了", compound 是"我学到啥". 不混.

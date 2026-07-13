---
name: athena-checkpoint
description: |
  会话记忆固化 skill (v9.8.0 新, Codex). 会话结束/中途, 主 thread 自己总结本会话增量写进 .ai_state
  (_index.md 当前状态 + sprints/{slug}/session-log.md), 免去用户每次手动描述一堆让它存.
  手动 /checkpoint 触发. 与 compact-snapshot.py hook (0.129+) 互补.
---

# /athena-checkpoint — 会话记忆固化 (v9.8.0, Codex)

## 痛点 (你的反馈)

每次会话要结束, 你都得手动描述 "现在做到哪、下次接着干啥" 让 Athena 存进 .ai_state.
本 skill 做成一键: **主 thread 自己回顾本会话、提炼增量、落进工程**, 你只需确认.

## 触发

- **手动**: `/athena-checkpoint` / "存一下进展" / "记录到 ai_state" / "收尾"
- **建议时机** (主 thread 可提醒, 不自动): 会话结束前 · 长任务阶段切换 · 重要决策后 · context 快满

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

### Step 3 · 写入两处 (apply_patch)

1. **`_index.md` frontmatter**: 校正 stage/path/next_action/current_sprint_slug/last_critic_round 等
2. **`sprints/{slug}/session-log.md`**: 追加本会话日志段

### Step 4 · 回显关键字段 (让你确认)

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
- 做了: plan 4 轮 critic PASS → impl T1-T6 写完单测过; runtime-verify T4 并发卡住
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

## 不做

- ❌ 不自动频繁 checkpoint (token 浪费; 手动/建议)
- ❌ 不替代 compact hook (兜底保险)
- ❌ 不写 compound (跨 sprint 沉淀)
- ❌ 不总结整个项目史 (只本会话增量)

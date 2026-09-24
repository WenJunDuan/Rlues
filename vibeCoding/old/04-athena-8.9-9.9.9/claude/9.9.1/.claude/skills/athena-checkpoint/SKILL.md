---
name: athena-checkpoint
description: |
  会话记忆固化 skill (v9.8.0 新). 会话结束/中途, agent 自己总结本会话增量写进 .ai_state
  (_index.md 当前状态 + sprints/{slug}/session-log.md), 免去用户每次手动描述一堆让它存.
  手动 /checkpoint 触发. 与 compact-snapshot hook 互补 (hook 机械兜底, skill 做需推理的总结).
---

# /athena-checkpoint — 会话记忆固化 (v9.8.0)

## 痛点 (你的反馈)

每次会话要结束, 你都得手动描述一堆 "现在做到哪、下次接着干啥", 让 Athena 存进 .ai_state.
本 skill 把这个动作做成一键: **agent 自己回顾本会话、提炼增量、落进工程**, 你只需确认。

## 触发

- **手动**: 用户说 `/athena-checkpoint` / "存一下进展" / "记录到 ai_state" / "收尾"
- **建议时机** (主 agent 可主动提醒, 但不自动执行): 会话结束前 · 长任务阶段切换 · 重要决策后 · context 快满时

## 工作流

### Step 1 · 写前快照 (防覆盖)

```bash
ts=$(date +%Y-%m-%d-%H%M%S)
cp .ai_state/_index.md ".ai_state/.snapshots/pre-checkpoint-${ts}.md"
```
与 compact-snapshot hook 同机制的手动版. 改坏了能回滚。

### Step 2 · agent 总结本会话增量

主 agent 回顾**本会话** (不是整个项目历史), 提炼三块:

1. **做了什么**: stage 推进 (如 plan→impl) / 改了哪些文件 / 拍了哪些决策 / 跑了哪些验证
2. **当前状态**: stage / path / next_action / current_sprint_slug / 卡在哪 (若有 blocker)
3. **下次接续点**: 下一 turn / 下次会话该从哪继续 (具体到动作, 不是"继续开发")

### Step 3 · 写入两处

1. **`_index.md` frontmatter**: 校正 stage / path / next_action / current_sprint_slug / last_critic_round 等字段, 确保与实际一致 (hook 自动维护的字段也复核一遍)
2. **`sprints/{slug}/session-log.md`**: 追加本会话日志段 (见格式)

### Step 4 · 回显关键字段 (让你确认记对了)

向用户回显:
```
✓ checkpoint 已存 ({ts})
  stage: impl  path: System  sprint: 2026-06-22-xxx
  next_action: runtime-verify (T4-T6 单测已过, 待实跑)
  下次接续: 跑 /athena-runtime-verify 验 /api/refresh 的并发场景
  快照: .snapshots/pre-checkpoint-{ts}.md
```
你扫一眼确认, 不对当场说, agent 改。

## session-log.md 格式

```markdown
# Session Log — {slug}

## 2026-06-22 14:30 (checkpoint)
- 做了: plan 4 轮 critic PASS → impl T1-T6 写完, 单测过; runtime-verify T4 并发场景卡住
- 状态: stage=impl, next_action=runtime-verify
- 决策: 并发刷新用乐观锁 (见 compound/2026-06-22-decision-refresh-lock.md)
- 下次接续: /athena-runtime-verify 复跑并发用例, 过了进 review
- blocker: 无

## 2026-06-21 ...
[更早的会话, 倒序追加]
```

## 与 compact-snapshot hook 的分工 (互补不重复)

| | compact-snapshot hook | athena-checkpoint skill (本) |
|---|---|---|
| 触发 | PreCompact 自动 | 用户手动 /checkpoint |
| 能力 | 机械复制 _index.md → .snapshots/ | **agent 推理总结本会话增量** |
| 写什么 | 原样快照 | _index 校正 + session-log 日志 + 接续点 |
| 场景 | compact 兜底 (防丢) | 会话结束主动固化 (给下次用) |

hook 是"防丢的保险", skill 是"主动留交接". hook 触发不了需要推理的总结 — 那是本 skill 的活。

## 与 /compound 的分工

| | /checkpoint (本) | /compound |
|---|---|---|
| 存什么 | **本会话状态 + 接续点** (短期, 给下次接续) | 跨 sprint 经验 (长期, learning/trick/decision) |
| 范围 | 当前 sprint 进展 | 项目级复利知识 |
| 频率 | 每次会话收尾 | 踩坑/优雅模式/决策时 |

checkpoint 是"我做到哪了", compound 是"我学到了啥". 不混。

## 不做

- ❌ 不自动频繁 checkpoint (token 浪费; 手动或建议, 不强制)
- ❌ 不替代 compact hook (hook 是兜底保险)
- ❌ 不写 compound (那是跨 sprint 沉淀; checkpoint 是本会话状态)
- ❌ 不总结整个项目史 (只本会话增量; 项目史看 git log + sprints/)

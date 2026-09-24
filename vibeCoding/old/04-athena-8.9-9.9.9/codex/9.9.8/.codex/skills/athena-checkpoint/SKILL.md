---
name: athena-checkpoint
description: 把本会话增量固化进 .ai_state。长任务收尾、context 将满或关键决策后触发。
---

# /athena-checkpoint — 会话记忆固化 (v9.9.6, Codex)

Memory contract: **Tier1 working memory** only supplies the current-turn delta; **Tier2 persistent memory** receives authoritative state; **_index.md retrieval router** keeps stage/next_action/current sprint, authoritative pointers, route_history≤10 and current-state log≤10. Detailed history belongs in `session-log.md`; hooks are fallback only.

## 痛点 (你的反馈)

每次会话要结束, 你都得手动描述 "现在做到哪、下次接着干啥" 让 Athena 存进 .ai_state.
本 skill 做成一键: **主 thread 自己回顾本会话、提炼增量、落进工程**, 你只需确认.

## 触发

- **手动**: `/athena-checkpoint` / "存一下进展" / "记录到 ai_state" / "收尾"
- **建议时机** (主 thread 可提醒, 不自动): 会话结束前 · 长任务阶段切换 · 重要决策后 · context 快满

## 不做

- ❌ 不自动频繁 checkpoint (token 浪费; 手动/建议)
- ❌ 不替代 compact hook (兜底保险)
- ❌ 不写 compound (跨 sprint 沉淀)
- ❌ 不总结整个项目史 (只本会话增量)

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。

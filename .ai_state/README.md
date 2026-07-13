# .ai_state — Athena PACE 项目状态 (导航)

> 本目录是 Athena 的 **Tier2 持久记忆**(数据平面)。续作先读 `_index.md`(当前状态) + 本 README。

## 当前状态 (2026-07-13)
- 版本: **Athena 9.9.2** 双端 (CC+CX), 位于 `../vibeCoding/{claude,codex}/9.9.2`。
- 当前 sprint: `sprints/2026-07-13-athena-9-9-2-architecture-review` (System)。
- 进度: 实现 + codex(gpt5.6) 2+1 review `pass1=REWORK` → **rework 已修**(见 sprint/`rework-notes.md`); 本沙盒 CC harness 83/0/2。**待 codex pass2 复审 + py3.11 validator 实跑**。

## 目录结构
| 路径 | 内容 |
|---|---|
| `_index.md` | 状态入口 (path/stage/next_action/pointers/counts) — **续作先读** |
| `README.md` | 本导航 |
| `sprints/{date}-{slug}/` | route-note · design · checklist · evidence.yaml · reviews/ · runtime-verify · cleanup-pass · rework-notes |
| `roadmap/{slug}/` | 大需求拆分 (roadmap.md + items.yaml) |
| `architecture/` | 系统架构真相 (ARCHITECTURE.md 入口 + athena-9.9.2.md 现状) |
| `requirements/` | 长效需求档 (WHY) |
| `compound/` | 跨 sprint 复利: learning / trick / decision / explore |
| `.snapshots/` | compaction 快照 |

## 如何续作 (下次持续优化)
1. 读 `_index.md` → 看 `stage` / `next_action` / `pointers`。
2. 读当前 sprint `design.md`(合同 AC1–13) + `checklist.yaml`(I0–I8 进度) + `reviews/pass1.md`(评审) + `rework-notes.md`(修复台账)。
3. 9.9.2 未竟项集中在 `rework-notes.md` 的"待外部"段: py3.11 validator + codex pass2。
4. 架构现状看 `architecture/athena-9.9.2.md`; 决策看 `compound/2026-07-13-decision-*.md`。

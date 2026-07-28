# .ai_state — Athena PACE 项目状态 (导航)

> 本目录是 Athena 的 **Tier2 持久记忆**(数据平面)。续作先读 `_index.md`(当前状态) + 本 README。

## 当前状态 (2026-07-28)

> 权威值以 `_index.md` frontmatter 为准; 本节只给人读的概览, 不作机械消费。

- 版本: **Athena 9.9.6** 双端 (CC+CX), 位于 `../vibeCoding/{claude,codex}/9.9.6` (已入 git)。9.9.3 为不可变基线。
- 当前 sprint: `sprints/2026-07-25-athena-9-9-6-prompt-engineering` (System, stage=impl)。
- 进度: 底稿收敛 + Claude review 成立项已修 (local validator 63/0/0); §10.1 Stop 熔断已落 `fe3296d`。
  2026-07-28 并入 gate 契约可见性与派工时序 (design §12 / AC19-AC28 / checklist G1-G6), 待 R6 critic。
- 未竟: F1-F6 本地 runtime/eval、H1 (AC16 fixtures)、G1-G6、runtime-verify、正式 2+1 review、polish。
  ship 契约缺口: `review-manifest.yaml` / `tdd-evidence.yaml` / `cleanup-pass.md` / `reviews/` 均待产出,
  `evidence.yaml` 尚无 per-AC 绑定记录。

## 目录结构
| 路径 | 内容 |
|---|---|
| `_index.md` | 状态入口 (path/stage/next_action/pointers/counts) — **续作先读** |
| `README.md` | 本导航 |
| `harness-patches.md` | **安装态补丁台账** — `~/.claude` / `~/.codex` 不是 git 仓, 本文件是那些改动唯一的仓内痕迹, 每条带可执行复核命令。⚠️ 有机械消费者: 两端 delivery-gate 的 `isLightShipFile` 按**文件名**匹配, diff 含它即取消 light-ship 资格、强制走全契约。**勿改名、勿挪出 `.ai_state/` 顶层** |
| `proposals.md` | **harness 进化提案** (铁律[Hook 是进化器]) — 在本项目实测发现的 P1-P9。无 hook 写它, 由主 agent 在 Stop 反思时手写; gate 白名单**故意不含**它 (加进去等于实质放宽) |
| `sprints/{date}-{slug}/` | route-note · design · checklist · evidence.yaml · reviews/ · runtime-verify · cleanup-pass · rework-notes |
| `roadmap/{slug}/` | 大需求拆分 (roadmap.md + items.yaml) |
| `architecture/` | 系统架构真相 (ARCHITECTURE.md 入口 + athena-9.9.6.md 现状) |
| `requirements/` | 长效需求档 (WHY) |
| `compound/` | 跨 sprint 复利: learning / trick / decision / explore |
| `.snapshots/` | compaction 快照 |

## 如何续作 (下次持续优化)
1. 读 `_index.md` → 看 `stage` / `next_action` / `pointers`。
2. 读当前 sprint `design.md` (§13 = 合同 AC1–AC28, 注意 **编号 11/12 是 harness 保留元标号, 业务 AC 必须避开**)
   + `checklist.yaml` (R/H/F/G 四组任务与 `ac_refs` 映射) + `route-note.md` (分诊与范围扩张记录)。
3. 当前 sprint 的 §12 追加范围出自 `annex-2026-07-27-gate-contract.md` (原独立 hotfix design 全文), 论证细节以 annex 为准。
4. 架构现状看 `architecture/athena-9.9.6.md`; 决策与教训看 `compound/`; harness 本地补丁的复核命令看 `harness-patches.md`。

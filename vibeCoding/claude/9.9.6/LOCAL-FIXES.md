# 9.9.6 本地修复入库 (2026-07-25)

> **为什么这个目录突然有代码**: 9.3+ 起本仓各版本目录只存文档 (RELEASE/CHANGELOG/REVIEW/MIGRATION), 代码只活在安装态 `~/.claude` 与 `~/.codex`。
> 后果实测: 9.9.3 期已按用户拍板修好的 delivery-gate 白名单补丁, 被 9.9.6 升级**直接覆盖蒸发** —— 全仓 `rg -l 'token-usage.yaml' --glob '*.cjs'` 曾 0 命中即铁证。
> 因此本次修复**同时入库**: 源在 git 里, 下次升级至少能 diff 出"我们改过什么", 不再无声丢失。

## 入库范围 (只入本次被改的文件, 非全量镜像)

| 仓内路径 | 安装态对应 | 本次改动 |
|---|---|---|
| `claude/9.9.6/hooks/delivery-gate.cjs` | `~/.claude/hooks/delivery-gate.cjs` | P1 白名单两项 · P3 tryRepoRoot + root/aiState 同源 · P2 generator 收束语义 · P8-guard light-ship 认 harness-patches |
| `codex/9.9.6/hooks/delivery-gate.py` | `~/.codex/hooks/delivery-gate.py` | 同上三件事对称 (P1 白名单 / root 与 find_ai_state 同源 + basename 兜底 / is_light_ship_file 分支) |
| `claude/9.9.6/rules/doc-style.md` | `~/.claude/rules/doc-style.md` | 新增 "tdd-evidence backfill 记法" (P6) |
| `claude/9.9.6/rules/coding-standards.md` | `~/.claude/rules/coding-standards.md` | 新增 "P1 · 量化验收标准必先核基线" (P7) |
| `claude/9.9.6/skills/pace/references/stages.md` | `~/.claude/skills/pace/references/stages.md` | polish 段 spawn 决策注记 (P4: 不加 isolation) |

## 升级后怎么用它

1. 升级完先跑项目内 `.ai_state/harness-patches.md` 的逐条复核命令
2. 任一条报"未命中" = 该修复被覆盖 → `diff <本目录对应文件> <安装态文件>` 找回改动重新 apply
3. 若新版本已官方修好同一问题, 在台账里标注"上游已修, 本地补丁可弃"

## 完整设计与验证证据

项目档案: `quantum-cowork/.ai_state/sprints/2026-07-25-harness-gate-p1-p4/`
- `design.md` — 3 轮 (critic 2 轮 / 17 findings / 4 P0), Round 3 为权威
- `tdd-evidence.yaml` — G1-G5 五组 dry-run 实跑证据 (放行面 / 拦截面防筛子 / P2 四边界 / root 解析四情形 / light-ship 两端)
- `.ai_state/proposals.md` — P1-P9 原始记录与处置

# 9.9.6 本地修复入库 (2026-07-25)

> 起因: 9.3 起本仓 `<version>/` 只存文档, 不存代码。9.9.3 期用户拍板的 delivery-gate 白名单
> 修复因此从未进过 git —— `rg -l 'token-usage.yaml' --glob '*.cjs'` 全仓 0 命中 —— 升级到
> 9.9.6 时被安装包直接覆盖 (P1 回归)。本目录只收录**本次实际改动过的文件**, 不做全量镜像
> (全量镜像是另一个决策, 需用户拍板)。

## 本次入库文件 (与安装态逐字节一致, `diff` 已验空)

| 入库路径 | 安装态路径 | 本次改动 |
|---|---|---|
| `claude/9.9.6/hooks/delivery-gate.cjs` | `~/.claude/hooks/delivery-gate.cjs` | P1 白名单 / P2 generator 收束语义 / P3 root 归一 / W8 台账护栏 |
| `claude/9.9.6/rules/doc-style.md` | `~/.claude/rules/doc-style.md` | tdd-evidence backfill 三字段记法 |
| `claude/9.9.6/rules/coding-standards.md` | `~/.claude/rules/coding-standards.md` | 量化验收标准必先核基线 |
| `claude/9.9.6/skills/pace/references/stages.md` | `~/.claude/skills/pace/references/stages.md` | polish 段 spawn 决策 (不加 isolation / repo 外对象不用 worktree) |
| `codex/9.9.6/hooks/delivery-gate.py` | `~/.codex/hooks/delivery-gate.py` | P1 白名单 / P3 root 归一 / W8 台账护栏 (codex 无 P2) |

## 升级后怎么用

逐条跑消费侧项目 `.ai_state/harness-patches.md` 里的复核命令; 命中"已被覆盖"的, 从本目录
对应文件 `diff` 回补。改动动机、G1-G5 实跑证据与备份路径都记在那份台账里。

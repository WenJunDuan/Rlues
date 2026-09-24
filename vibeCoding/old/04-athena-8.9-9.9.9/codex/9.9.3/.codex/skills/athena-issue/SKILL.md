---
name: athena-issue
description: |
  Bugfix 路径的结构化问题流程: report → analyze → fix-note 三件套档案, 落在 sprints/{slug}/, Codex.
  把"偏轻"的 Bugfix 升级成可复现 / 可追溯 / 可复盘. 借 CodeStable issue 实体, 适配 agent-in-loop.
---

# /athena-issue — 结构化问题流程 (v9.8.0 新, Codex)

## 为什么存在 (痛点)

原 Bugfix 路径 plan → impl → review → ship **偏轻**: 无 design.md、无根因记录、修完即忘。
同一个坑反复踩, 因为没有可检索的 report / analysis / fix-note。delivery-gate 当前**完全不拦 Bugfix**, ship 零问责。
本 skill 给 Bugfix 配三件套档案 (借 CodeStable issue 流程), 落在 `sprints/{slug}/`, 并补一道最小 ship 门禁。

## 三阶段 (report → analyze → fix-note)

| 阶段 | 产出 (sprints/{slug}/) | 干什么 |
|---|---|---|
| **report** | `issue-report.md` | 把脑子里的问题落成**可复现**: 现象 / 复现步骤 / 期望 vs 实际 / 环境 |
| **analyze** | `issue-analysis.md` (根因不显然才写) | 定位根因 / 评估修复风险 / 给方案。自己查代码定位, 不猜 |
| **fix-note** | `fix-note.md` | 修复记录: 改了什么 / 为什么 / **验证命令 + 输出**。delivery-gate 验它 |

## 与 PACE Bugfix 路径

```
Bugfix: report → (analyze) → impl(fix) → review → ship
```
- **report 先行**: 没有可复现的 report 不准动手
- **analyze 可选**: 根因显然 (typo / 拼错字段) 跳过; 不显然 (竞态 / 状态污染 / 边界) **必写**
- **fix-note 必写**: 修完写, 含验证证据 (改前复现 fail → 改后复跑 pass)

## delivery-gate 联动 (v9.8.0 新增门禁)

`Bugfix + stage=ship` → delivery-gate.py 检查 `sprints/{slug}/fix-note.md` 存在。缺 → block。
> Bugfix 路径**第一道 ship 门禁** —— 原本完全不拦, 现在至少要求"修了什么、怎么验证的"落盘。

## 与 runtime-verify 的关系

Bugfix 默认跳过 runtime-verify。但若 bug 涉及**接口 / 状态 / 并发**, 在 fix-note 里附实跑验证 (借 runtime-verify 的"晒命令 + 输出"纪律)。

## 工作流

1. 用户报 bug → 主 thread 起 `issue-report.md` (复现步骤是硬要求, apply_patch 写)
2. 根因不显然 → 写 `issue-analysis.md` (查代码定位, 列候选根因 + 证据)
3. 定点修 (绿区主 thread 直做 / 黄区用 `spawn_agent` 启动 generator)
4. 写 `fix-note.md`: 改动 + 根因 + 验证命令&输出
5. review (Bugfix 仅跑 reviewer) → ship (delivery-gate 验 fix-note)
6. 反复踩的坑 → 触发 `/compound add learning`

## 不做

- ❌ 不给每个 typo 走三件套 (绿区小 bug: 直接修 + 一行 fix-note)
- ❌ analyze 不强制 (根因显然就跳 —— 铁律[反过度工程])
- ❌ 不替代 compound (单次修复写 fix-note; 有普适教训才进 compound/learning)
- ❌ report 不写猜测根因 (那是 analyze 的事; report 只记客观现象 + 复现)

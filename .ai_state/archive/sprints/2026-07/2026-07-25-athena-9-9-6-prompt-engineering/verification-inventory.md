---
sprint: "2026-07-25-athena-9-9-6-prompt-engineering"
item: "Item 3 · Opus 5 行为迁移"
created: "2026-07-25"
scope: "vibeCoding/{claude,codex}/9.9.6 全仓 (hook 源码除外)"
---

# Verification 指令 inventory 与三分类

## 官方依据

> "It also verifies its own work without being told to, so **remove verification instructions carried over from earlier models** ('include a final verification step,' 'use a subagent to verify'); **they cause over-verification on Claude Opus 5**."
> — Opus 5 官方行为说明

> "it … verifies its work more often than smaller models … **reminders to test or check are usually unnecessary**"
> — Claude Code model-config，Fable 5 段（同向，且 Athena 的 architect/critic 正是跑 fable）

## 分类判据

| 类 | 判据 | 处置 |
|---|---|---|
| **a** | 平台已自动做 | **删** |
| **b** | Athena 必须强制 | 移到 hook/gate 机械判定，prompt 不复述；主 agent 的**落盘与所有权**职责保留 |
| **c** | 需要判断 | 留 skill |

## 扫描式

```
再次(检查|验证|确认) | double-check | re-verify | 最终验证 | final verification
| 用 subagent 验证 | 证明完成 | 自跑(命令|测试) | 附(命令输出|diff) | 复核
```

范围：`claude/9.9.6/.claude` + `codex/9.9.6/.codex`，排除 `*.cjs` / `*.py`（hook 源码里的字符串是实现，不是给模型的指令）。

## a 类 — 已删除（2 处语义，双端共 4 个文件）

| 位置 | 原文 | 处置 |
|---|---|---|
| `CLAUDE.md` / `AGENTS.md` 第 6 行 | 自跑命令/测试并读取输出证明完成; 同一路径工具失败三次后附 stderr… | **删前半句**。Opus 5 / Fable 5 已自发验证，这句在新模型上直接导致过度验证。后半句（失败三次后附 stderr 再报阻塞）是**失败上报协议**，保留 |
| 双端铁律 5 | 报"完成"附可复核命令输出/diff (不足时 delivery-gate 现场核验); API/配置/协议必引官方文档或源码 URL | **改写**为「完成度由 delivery-gate 现场核验，不在对话里复述验证过程; API/配置/协议必引官方文档或源码 URL」。判定权从 prompt 移到 gate，出处要求保留 |

**a 类清零。** 由 `validate-athena-9.9.6.py` 的「宪法无 legacy verification 劝导」断言持续守住。

## b 类 — 保留（6 处，全部是所有权约定，不是自我验证劝导）

| 位置 | 要点 | 为什么不删 |
|---|---|---|
| `CC/CX skills/pace/SKILL.md` | spec-gate impl-entry：进 impl 前先验 design.md 有机器可识别验收标准 | 这是 **gate 的前置条件描述**；实际判定在 delivery-gate，prompt 只是告知入口 |
| `CC/CX skills/polish/SKILL.md` | `.ai_state` 产物由主 agent 根据实际 diff 与返回结果复核后落盘 | 铁律[零写入]：read-only worker 不落盘，主 agent 负责合并 —— **多写者所有权模型** |
| `CX agents/polish_worker.toml` | 主 agent 复核 diff、运行测试并写 cleanup-pass 后转 ship | 同上 |
| `CX skills/pace/references/orchestration.md` | 主 thread 用 `git -C <worktree> status --short` 与 diff 复核边界 | worktree 边界核验是**机制**，平台无替代 |

判据：这 6 处的主语都是**主 agent 对 subagent 产物的合并 / 落盘 / 边界核验**。删掉会破坏铁律[零写入]与红黄绿区的写者约定，与"让模型再检查一遍自己的工作"是两回事。

## c 类 — 0 处

未发现需要保留在 skill 里的判断型验证指令。

## 显式不属于本次清理范围

以下**不是** verification coaxing，而是由 hook 与 gate 机械核验的产物合同，本版一条未删：

- TDD red → green（generator 强制）
- 真实测试而非 mock 一切求绿
- evidence.yaml / tool-trace.jsonl 证据链
- runtime-verify 实跑要求（System/Refactor 强制）
- delivery-gate 的 Evidence Cross-Check（`done_without_evidence ≥ 1` → VERDICT 上限 CONCERNS）

原计划文档曾把这些与 a 类混为一谈，本 inventory 明确区分：**a 类是"劝模型自查"，这些是"机器验产物"。**

## Opus 5 另两条行为变化的处置

| 官方变化 | 冲突面 | 9.9.6 处置 | 状态 |
|---|---|---|---|
| "In multi-agent frameworks, it **delegates to subagents more readily**" | 铁律[零写入] 绿区主 agent 直做 | prompt 侧未加对抗话术；改由 **sprint contract**（done_contract 约束交付面）+ **worktree gate**（红区/并行强制隔离）兜底 | 绿区过度委派的 eval 场景**未做** |
| "In agentic sessions, the model **narrates its progress more often**" | 宪法「输出结果优先，最少结构」 | 宪法该句保留 —— 它是**格式约定**不是验证劝导，删了会失去唯一的输出形态约束 | 无效进度汇报计数场景**未做** |

两条的 eval 场景都需要 runtime 验证（真机跑完整 PACE 并计数），属独立门，列在 RELEASE.md 的未验证风险面第 4 条。

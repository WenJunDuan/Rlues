---
name: athena-dev
description: Athena 主入口。收到新任务需要 PACE 路由分诊时触发。
---

# /athena-dev — Athena 主入口 (Codex, v9.9.6)

## 触发

用户进任意项目, 说 "开始", "做个 X", "帮我 Y" 等. 主 agent 进入路由分诊.

## 路由审议 (铁律[分诊] · v9.9.1 决策摘要)

**前置**: 无 `.ai_state/` → 提示先跑 /athena-init, 停. 用户显式声明生产事故/hotfix → 直接进 plan(Hotfix) (唯一免审议).

路由是 triage, 不是查表. 主 agent 基于证据决策; 对用户只展示结论性摘要, 不展示私有思维链:

### Step 0 · 检查上下文
- `_index.md`: 当前 stage / path / route_history (上次路由错在哪) / counts (项目成熟度)
- `git log --oneline -10`: 最近在动哪些模块
- 输入中的显式信号: "重构" / "bug" / "讨论" 等关键词是**强证据**, 计入权衡但不短路直判 — "重构一下这个函数"不该触发 Refactor 全套流程

### Step 1 · 候选
提出 ≥2 个候选 (路径或 stage), 各列支持/反对证据.

### Step 2 · 四维权衡

| 维度 | 问自己 |
|---|---|
| 爆炸半径 | 波及几个文件/模块? 碰 CI / 数据 / 外部接口吗? |
| 可逆性 | 做错了 revert 一个 commit 能回来吗? |
| 紧急度 | 用户在救火还是在建设? |
| 需求不确定性 | 能直接写出验收标准吗? 写不出 = 模糊 → brainstorm |

### Step 3 · 决策 + 置信度
- **≥0.8**: 直接进路径
- **0.5–0.8**: 带假设进 — route-note 写明假设 + 廉价退出点 (什么信号出现就 re-route)
- **<0.5**: 停. 问用户 1-2 个决定性问题 (能砍掉一半候选的那种), 或进 brainstorm

### Step 4 · 护栏校验 (地板, 不可击穿)
≥2 个可独立验收交付的切片 → 至少 roadmap (模块数只定风险等级); 跨模块 / 预估 ≥5 文件 → 至少 Refactor. 审议结果低于地板 → 取地板.

### Step 5 · 落盘 (2026-07-28 gate-descaling)
默认: `_index.route_history` 记一行 (路径+一句话依据+置信度) + 更新 `_index.route_confidence`; **不再单立 route-note.md**。
仅复杂场景 (置信度 0.5-0.8 带假设进 / 发生 re-route) 才落 `sprints/{slug}/route-note.md` 写明假设与廉价退出点。不写逐步思维过程.

## 例外

- 用户直接说 "直接做:" 或 `--skip-brainstorm` → 跳过 brainstorm
- 用户显式说 "我自己拆 roadmap" → 跳过 roadmap, 直接 plan
- Hotfix 路径: 跳过所有分诊, 直接进 plan (生产事故无时间分诊)

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。

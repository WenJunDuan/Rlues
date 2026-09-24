---
name: athena-runtime-verify
description: impl 之后的运行时验证环。System/Refactor 强制；需要实跑接口而非只跑单测时触发。
---

# /athena-runtime-verify — 运行时验证环 (v9.9.9)

阶段义务唯一正文为 `../pace/references/stages.md`。本 skill 负责运行场景与证据。

真实执行入口是 `../athena-vm/scripts/runtime-run.py` 的 snapshot/doctor/run，协议见 `athena-vm/references/playbook.md` 与本 skill `references/playbook.md`。

## 为什么存在

PACE 到 impl 为止, review + 单测只验证 **"我们想的问题实现没 / 单测过没"**, 不验证 **实际运行**.
代码单测全绿 ≠ 真实接口跑得通 / 边界数据不炸 / 换个环境不挂.

## 触发 (按 PACE 级别)

| 路径 | runtime-verify | /goal 承载范围 |
|---|---|---|
| Hotfix | 跳过 (救火无时间) | — |
| Bugfix / Quick | 跳过 (改动小, 单测够) | — |
| Feature | **可选** (碰外部接口 / 有状态 / 多环境 → 做) | 用户显式要求或已有 Goal 时 |
| Refactor | **强制** | 可选增强，不是唯一通道 |
| System | **强制 + 完整 Sprint** | 可选增强 |

> 不在小改动上强制 (铁律[反过度工程]).

普通本平台 workflow 可完成验证。VM 和另一模型平台均是可选能力，required 环境不足只阻塞相应验收。不可把 unknown、未运行或 SSH 可达当场景通过。

可选：测试已绿且 ≥2 合格候选、`laav_enabled` 时，在进入 review 前跑 `/llm-as-a-verifier`。

## VERDICT: PASS | REWORK(回 impl)

## 不做

- ❌ 不自造 loop 引擎；无 `/goal` 时用 runtime-run.py + 本会话继续
- ❌ 不替代单测 (单测在 impl; 这里是运行时实跑)
- ❌ 不把 SSH 可达、配置存在、未运行标成通过
- ❌ Hotfix/Bugfix/Quick 不强制

## 例外

- 项目无可运行环境 (纯库 / 纯算法): 降级为"用真实数据跑示例 + 边界"
- `_index.skip_runtime_verify = true`: 跳过 (用户自负责, 不推荐 System/Refactor 跳)

## 详细 playbook

完整工作流见 `references/playbook.md`。

---
name: athena-runtime-verify
description: impl 之后的运行时验证环。System/Refactor 强制；需要实跑接口而非只跑单测时触发。
---

# /athena-runtime-verify — 运行时验证环 (v9.9.6)

## 为什么存在 (痛点)

PACE 到 impl 为止, review 三件套 + 单测只验证 **"我们想的问题实现没 / 单测过没"**, 不验证 **实际运行**.
代码单测全绿 ≠ 真实接口跑得通 / 边界数据不炸 / 换个环境不挂.
本 skill 在 impl 与 review 之间插一个 **运行时验证环**: 写完 → 实跑 → 自测自改 → 直到真能跑.

把"人盯着跑测试、贴日志、让它改"这件事, 换成 **系统自己跑、自己发现、自己改** (Loop Engineering).

## 触发 (按 PACE 级别)

| 路径 | runtime-verify | /goal 承载范围 |
|---|---|---|
| Hotfix | 跳过 (救火无时间) | — |
| Bugfix / Quick | 跳过 (改动小, 单测够) | — |
| Feature | **可选** (主 agent 判断: 碰外部接口 / 有状态 / 多环境 → 做) | impl+runtime (可选) |
| Refactor | **强制** | impl+runtime |
| System | **强制 + 完整 Sprint** | 全程 PACE |

> 不在小改动上强制 (铁律[反过度工程]). 单测能覆盖的别上 /goal, 杀鸡用牛刀。

## VERDICT: PASS | REWORK(回 impl)

## 不做

- ❌ 不自造 loop 引擎 (用官方 /goal)
- ❌ 不替代单测 (单测在 impl; 这里是运行时实跑)
- ❌ 不无限循环 (/goal turn 上限护栏必写, 撞上限停下来报告)
- ❌ Hotfix/Bugfix/Quick 不强制 (小改动过度工程)
- ❌ reflect 不发散成新需求 (那是项目级 brainstorm; 这里只查本 sprint 落地完整性)

## 例外

- 项目无可运行环境 (纯库 / 纯算法, 无接口无 UI): 降级为"用真实数据跑示例 + 边界", 不强求起服务
- `_index.skip_runtime_verify = true`: 跳过 (用户自负责, 不推荐 System/Refactor 跳)

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。

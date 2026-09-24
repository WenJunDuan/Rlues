---
name: roadmap
description: PACE 可选 stage。存在 ≥2 个可独立验收交付的切片，或用户明确要求拆分时触发。
---

# /roadmap — 大需求拆分 (v9.6.4 新)

## 触发条件

```python
def needs_roadmap(user_input, brainstorm_output=None):
    if explicit_kws(["路线图", "拆分", "roadmap", "分步推进", "分阶段"]):
        return True
    if independently_acceptable_and_shippable_slices(user_input) >= 2:
        return True
    if brainstorm_output and brainstorm_output.recommends_roadmap:
        return True
    return False
```

模块数只辅助风险路由，不单独强制拆分；共享跨模块不变量无法独立交付时保留一个 sprint。依赖、写集与整合按 [PACE 执行合同](../pace/references/execution-contracts.md#writer-派工恢复与整合)。

## 数据结构

```
.ai_state/roadmap/{slug}/
├── roadmap.md          # 主文档: 背景 / 拆解 / 排期
├── items.yaml          # 机器可读子 feature 清单
└── drafts/             # 可选: 调研笔记 / 备选方案
```

## 路径限制

roadmap 只对 Feature / Refactor / System 路径有意义.
Hotfix / Bugfix / Quick **不进 roadmap** (本就是小改动).

## 例外

- `_index.skip_roadmap = true`: 大需求也不强制 roadmap (主 agent 一次性处理, 风险自担)
- 用户显式 "我自己拆": 不进 roadmap stage, 用户直接说"先做 X 再做 Y"

## 不要做 (借 OMO 教训)

- 不引入 milestone / epic / story 三层 (太重, 不是 PMS)
- 不引入跨 roadmap 依赖 (一次只跑一个 roadmap)
- 不引入自动调度算法 (主 agent + 用户决定顺序)
- 不允许 roadmap 中途插队新 item (除非用户显式说 "插队")

## 详细 playbook

完整工作流、模板、schema 与联动细节见 `references/playbook.md` —— 按需 Read, 不进热路径。

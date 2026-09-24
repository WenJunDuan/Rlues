---
name: architect-doc
description: 维护 .ai_state/architecture/ 当前架构档；System 完成、Refactor 改动 ≥5 文件、新增子系统或用户要求更新架构档时用。
---

# architect-doc — 架构现状档

## 何时

| 时机 | 要求 |
|---|---|
| System，ship 前 | 必须更新（A3 提示；豁免 `skip_architecture_check`） |
| Refactor 改动 ≥5 文件，ship 前 | 必须更新 |
| Feature 新增 endpoint / 数据模型 | 酌情 |
| 首次在项目里用 | 建 `ARCHITECTURE.md` 初版 |

## 步骤

1. 读当前 sprint design.md 与 `git diff <base_commit>`，列出涉及的子系统。
2. 可选：派只读 `architect` 子 agent 生成修改提案（沿用用户模型设置）；主 agent 审后写入。
3. 更新 `architecture/ARCHITECTURE.md`（总入口 + 索引）和对应 `{type}-{slug}.md`。
4. 新子系统：type ∈ api db auth cache frontend backend infra messaging monitoring cli lib；从模板建档，并加进 ARCHITECTURE.md 索引。
5. 首次建档：有 README / docs 架构说明就从中提取；没有就问用户 DB、API 风格、部署方式三问，写最简版。

模板：`{{athena:SKILLS_DIR}}/pace/templates/architecture/`。

## 写什么、不写什么

- 写：现在长什么样——组件、边界、数据流、外部依赖、约束。
- 不写：演进历史（git log、decisions/）、实现细节（源码）、本次 sprint 计划（design.md）、未实现设想（roadmap）。
- design（这次改什么）→ architecture（现在是什么）→ decisions（为什么这样选），三者不重复。
- `architecture/` 不归档，永远是现状。

完成条件：改动涉及的每个子系统档都反映 ship 后的现状，A3 不再提示。

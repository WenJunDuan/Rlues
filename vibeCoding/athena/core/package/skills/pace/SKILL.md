---
name: pace
description: PACE 路径、阶段、门禁与 athena CLI 的全景；分诊后要确定下一步、被门禁拦下、或恢复中断任务时读。
---

# PACE（Athena 10.1）

新任务先按 [athena-dev](../athena-dev/SKILL.md) 分诊。阶段义务与硬门只看 [stages.md](references/stages.md)（由 stages.yaml 生成）。

## 路径

| 路径 | 何时 | 阶段 |
|---|---|---|
| Hotfix | 用户点名，或紧急有界恢复 | impl → ship |
| Bugfix | 已知缺陷局部修 | design（三段式）→ impl → review → ship |
| Quick | 只读诊断，或 ≤3 文件小改 | design → impl → ship |
| Feature | 单模块新能力 | design → impl → [runtime-verify] → review → ship |
| Refactor | 改结构，≥5 文件 | design → impl → runtime-verify → polish → review → ship |
| System | 跨模块 | design → impl → runtime-verify → polish → review → ship |

护栏是地板：≥2 个可独立验收切片 → roadmap；跨模块或 ≥5 文件 → Refactor/System。同任务只升不降，降级要用户明示。

## 一个 sprint 的最短循环

1. `athena sprint start <roadmap>/<item> [--path P]`，或 `athena sprint start --req <file> --path P --slug S`：建 `sprints/<slug>/`（design.md + log.md），切 `_index`。
2. 写 design.md 的 `- ACn:` 行（H1：没有非占位 AC，仓库内写入被拦）。
3. 实现。按区写入（[execution.md](references/execution.md)）。
4. `athena run --covers AC1,AC2 -- <命令>`：证据绑定当前源码树（H2）。
5. R/S：runtime-verify → polish（跳过要豁免 `skip_runtime_verify` / `skip_polish`）。
6. `athena review prepare` → 独立 reviewer → `athena review accept`（H3，见 athena-review）。
7. 记账全部写完 → `athena ship`（H2/H3 复核、归档、items done、`_index` 归零）→ 与代码同一提交。

`athena sprint stage <id>` 切阶段；`pause --resume-when` / `resume` / `drop --reason` 管中断。ship 必须是最后一次写入：之后再改源码，证据与 review 作废。

## 被拦时

| 信息 | 动作 |
|---|---|
| H1 | 补 design.md 的 `- ACn:` 行 |
| H2 | `athena run` 在当前树上重跑检查；unprovable 按 reason 改写命令 |
| H3 | 重新 `review prepare` → reviewer → accept |
| H4 | 写者子 agent 用隔离 worktree；repo 外目标用豁免 `harness_target_outside_repo` |
| H5 | 危险命令换安全写法；推送等 ship |
| 认为误拦 | `athena issue add --type gate --text "<一句话>"`，请用户放行；同一拦截连续 3 次自动熔断并记 G 行 |

豁免：`_index.exemptions` 里 `{key, until, reason}`，≤14 天；H2/H3 没有豁免。细节 [gates.md](references/gates.md)。

## References

| 场景 | Read |
|---|---|
| 阶段、硬门、提示项 | references/stages.md |
| 门禁细节、豁免、熔断 | references/gates.md |
| 派工、隔离、外部写者、整合 | references/execution.md |
| 状态文件、恢复、梳理 | references/state.md |
| 平台差异（CC / CX / Pi） | references/platform.md |
| 决策记录（ADR） | references/decisions.md |
| 全栈切片准入 | references/fullstack-contract.md |
| 插件、MCP | references/plugins.md |

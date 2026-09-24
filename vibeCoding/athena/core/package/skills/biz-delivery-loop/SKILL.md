---
name: biz-delivery-loop
description: 业务需求走全栈 PACE 闭环的编排入口。只编排现有 skill 与证据，不写代码、不建第二状态机。
---

# biz-delivery-loop

业务全栈交付编排 skill。职责是把需求清单纳入 PACE，把前端、数据库、后端、测试、安全、E2E 和交付报告
串成带 checkpoint 的 loop。本 skill **系统无关**：项目知识只从 Convention Pack、Capability Manifest
或 `runtime-env` 声明读取；状态唯一权威是 `.ai_state/_index.md`。

## 何时使用

- 一个业务功能需要 FE/BE/DB/测试/安全/E2E 多环节协同交付。
- 用户要求 checkpoint、回滚、需求完成度和完整交付报告。
- 需要调度 `quantum-codegen` (mode=page/module/db/unit/security/e2e) 与 `quantum-data` 等 skill。

## 何时不使用

- 单文件 hotfix、局部 bugfix 或无需全栈 loop 的小改动。
- 需求无法写出验收标准；先进入 brainstorm 或 requirements。
- 想跳过 PACE 自建状态机；本 skill 只编排，不拥有独立状态。

## 输入

1. 原始需求清单、验收标准和优先级。
2. Convention Pack：FE、BE、DB、测试、安全、E2E、交付报告约定。
3. `runtime-env`：FE/BE/DB 命令、端口、探活 URL、teardown。
4. 可选 Capability Manifest：运行期只读数据能力。
5. `references/` 下的 checkpoint、报告 schema 和 runtime-env contract。

## 工作流

1. 读 `references/orchestration-contract.md`，运行 `python3 scripts/check_delivery_loop_contract.py <biz-delivery-loop-skill-dir>` 核对合同与报告结构。
2. 按 [PACE 全栈准入](../pace/references/fullstack-contract.md) 在 design 记录真实仓库、角色、环境、测试种子与正常/拒绝/越权/失败断言。缺所需环境保持该切片未完成，继续独立工作。
3. 将可独立验收业务动作拆为 roadmap 切片；复用 blocked_by。先明确规则、API、schema 与适用 checkpoint，已确认内容引用原证据。
4. 按依赖调度 FE page、DB design + DDL、BE module。mock demo 可用于效果确认，不能替代真实 FE/BE/DB 验收；有收益再并行互斥写集，由主 agent 整合。
5. 集成后通过 unit、e2e、security 模式真实运行并核对 UI/API/DB/权限/审计。quantum-data 仅在 manifest 声明范围内只读。
6. 后续阶段只按 [PACE stages](../pace/references/stages.md)：R/S 为 runtime-verify → polish → review；一次独立多维 review 的结果是 reviews/implementation-review.md。
7. 报告复用需求→产物→证据→状态/遗留；保留可空用量兼容字段，缺原生来源为 unavailable，不阻塞功能交付。CP1/CP3/CP5 仅在当前 design/用户要求且尚未确认时请求确认；按有效授权进入 ship。

## 输出

- 每个 PACE stage 的产物路径、命令、证据和 checkpoint 结果。
- 按 `references/delivery-report-schema.md` 生成的交付报告。
- 回滚记录、loop 次数、blocked 原因和人工确认清单。

## 铁律

- 不建平行状态机；只读写 PACE 认可的 stage、hook、evidence 和报告产物。
- checkpoint 验证证据，不验证日志里的某个字符串。
- 同一 checkpoint 同因连续三次失败记录 stderr、已试方案和 issue；只阻塞相关依赖，继续独立授权工作。
- 不猜环境；全栈运行只依据 `runtime-env`。
- 本 skill 只编排，不直接写业务代码；代码生成交给对应 skill。

## PACE 集成

- requirements/roadmap/design：组织需求、切片、契约和人工 checkpoint。
- impl：调度各生成 skill，收集产物路径。
- runtime-verify：调度单测、集成、E2E、安全测试并归档证据。
- review/polish/ship：复用 PACE 门禁，最终交付报告作为 ship 输入。

## References

- `references/checkpoint-protocol.md`
- `references/delivery-report-schema.md`
- `references/orchestration-contract.md`
- `references/runtime-env-contract.md`
- `scripts/check_delivery_loop_contract.py`

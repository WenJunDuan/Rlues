---
name: biz-delivery-loop
description: >-
  Use when a business requirement must be delivered through the full-stack PACE
  loop: requirements, roadmap, design checkpoints, frontend demo, database
  schema, backend module, tests, integration, review, E2E, security, delivery
  report, and human confirmation. It orchestrates existing skills and evidence;
  it does not implement code or create a second state machine.
---

# biz-delivery-loop

业务全栈交付编排 skill。职责是把需求清单纳入 PACE，把前端、数据库、后端、测试、安全、E2E 和交付报告
串成带 checkpoint 的 loop。本 skill **系统无关**：项目知识只从 Convention Pack、Capability Manifest
或 `runtime-env` 声明读取；状态唯一权威是 `.ai_state/_index.md`。

## 何时使用

- 一个业务功能需要 FE/BE/DB/测试/安全/E2E 多环节协同交付。
- 用户要求 checkpoint、回滚、需求完成度和完整交付报告。
- 需要调度 `scaffold-page-gen`、`db-schema-gen`、`scaffold-module-gen`、`unit-test-gen`、
  `playwright-e2e`、`security-test`、`project-data-reader` 等 skill。

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

1. 先读 `references/orchestration-contract.md`，再运行
   `python3 scripts/check_delivery_loop_contract.py <biz-delivery-loop-skill-dir>`；缺合同/报告/checkpoint 字段先停机补 skill。
2. requirements：落需求清单，拆 Sprint 或 roadmap。
3. design：冻结 API 契约、效果图或 HTML mockup、schema 草案和 checkpoint 标准。
4. CP1：人工确认效果图；失败回到 design 对应子步。
5. impl FE：调用 `scaffold-page-gen` 生成 mock demo，启动 `runtime-env` 探活。
6. CP2：机器门禁确认 demo 可运行；失败回到 FE impl。
7. impl DB：调用 `db-schema-gen` 产出表设计文档和 DDL SQL。
8. CP3：人工 schema 评审；失败回到 DB design/impl。
9. impl BE：调用 `scaffold-module-gen` 生成后端模块并编译。
10. CP4：机器门禁确认编译、契约和基础质量；失败回到 BE impl。
11. runtime-verify：调用 `unit-test-gen`、集成契约 diff、`playwright-e2e`、`security-test`。
12. 可选读数：调用 `project-data-reader` 读取运行期只读数据；只接受 Capability Manifest 声明的 read 能力。
13. review：执行 PACE review 三件套，缺失或偏离回到对应 impl 或 design 子步。
14. ship 前：按报告 schema 汇总需求完成度、FE/BE 测试、模型/token 消耗、运行期读数、遗留问题和人工确认清单。
15. CP5：人工确认交付报告；通过后按用户指令进入 ship。

## 输出

- 每个 PACE stage 的产物路径、命令、证据和 checkpoint 结果。
- 按 `references/delivery-report-schema.md` 生成的交付报告。
- 回滚记录、loop 次数、blocked 原因和人工确认清单。

## 铁律

- 不建平行状态机；只读写 PACE 认可的 stage、hook、evidence 和报告产物。
- checkpoint 验证证据，不验证日志里的某个字符串。
- 同一 checkpoint 连续三次失败必须停机转人工 issue。
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

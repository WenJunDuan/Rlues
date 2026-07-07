---
name: unit-test-gen
description: >-
  Use when generated or changed frontend/backend code needs focused unit tests,
  component tests, or service tests plus a debug loop. Reads the Convention Pack
  for test framework, fixtures, coverage targets, and commands, runs the
  declared tests, repairs real failures, and emits a test report for PACE
  runtime-verify and delivery reporting.
---

# unit-test-gen

单元测试生成 skill。职责是为本次业务改动补齐真实验证业务行为的测试，并执行跑测、读失败、修复、
重跑的 debug loop。本 skill **系统无关**：测试框架、目录、fixture、覆盖率阈值和命令来自
Convention Pack；需要服务或数据库时只读 `runtime-env`。

## 何时使用

- 新增或修改业务模块、页面、service、controller、hook、组件后需要单测。
- 编译通过但关键业务分支、边界条件、权限或错误处理还没有测试证据。
- 需要输出测试报告给 `biz-delivery-loop` 汇总。

## 何时不使用

- 只需要浏览器端完整流程；使用 `playwright-e2e`。
- 只需要安全越权或依赖审计；使用 `security-test`。
- Convention Pack 未声明测试框架和命令。

## 输入

1. 需求条目、变更文件、关键业务路径和边界条件。
2. Convention Pack：测试框架、命名、fixture、mock 边界、覆盖率、运行命令。
3. `runtime-env`：可选的 BE/DB/FE 依赖启动方式和 teardown。

## 工作流

1. 读取 Convention Pack，确定测试类型、目录、fixture 和禁止 mock 的边界。
2. 为每条验收标准写测试；覆盖成功、失败、权限、空数据和边界条件。
3. 运行声明的单测命令，确认失败原因来自真实业务差异而非测试拼写错误。
4. 修复代码或测试夹具，重跑；同一失败连续三轮无法推进时标记 blocked。
5. 汇总用例数、通过率、覆盖关键路径、失败修复摘要和剩余风险。

## 输出

- 新增或修改的测试文件和必要 fixture。
- 测试命令、通过/失败结果、覆盖关键路径清单。
- 单测报告片段，可并入交付报告。

## 铁律

- 测试先于实现或修复；不得为了 GREEN 删除业务断言。
- 不允许 mock 一切求绿；鉴权、数据权限、序列化、校验等关键路径必须真实覆盖。
- 不猜测试命令；只执行 Convention Pack 或 `runtime-env` 声明。
- 错误处理断言必须与项目统一错误模型一致。

## PACE 集成

- impl stage：先写或补齐测试，再修实现。
- runtime-verify stage：保存测试命令与报告证据。
- review stage：reviewer 检查测试是否覆盖验收标准和关键风险。
- ship stage：交付报告引用测试结果和遗留风险。

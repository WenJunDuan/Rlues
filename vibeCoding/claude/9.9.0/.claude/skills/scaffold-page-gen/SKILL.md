---
name: scaffold-page-gen
description: >-
  Use when the user wants to generate a frontend business page, route, API
  client, view model, mock data, or local demo inside an existing frontend
  scaffold. Reads the target frontend Convention Pack and runtime-env
  declaration, follows its routing/component/data-access conventions, runs the
  declared validation and demo commands, and records evidence for PACE
  runtime-verify. It does not invent framework rules or read live business data.
---

# scaffold-page-gen

前端页面生成 skill。职责是把需求清单和冻结的 API 契约落成可运行页面、mock 数据、路由和本地 demo。
本 skill **系统无关**：页面结构、组件库、路由、权限、mock 方式、校验命令全部来自目标项目的
Convention Pack；运行命令只从 `runtime-env` 读取。

## 何时使用

- 需要按既有前端脚手架生成业务页面、列表、详情、表单或工作台视图。
- 需要在真实后端完成前，用冻结契约生成 mock 数据并启动本地 demo。
- 需要把页面生成证据纳入 `runtime-verify` 或业务交付报告。

## 何时不使用

- 需求还没有页面验收标准、API 契约或 Convention Pack。
- 需要读取运行期真实数据；使用 `project-data-reader`。
- 需要自由设计品牌站、一次性静态页或不受脚手架约束的原型。

## 输入

1. 需求条目与页面验收标准。
2. 冻结的 API 契约或 mock schema。
3. 目标前端 Convention Pack：路由、目录、组件、状态、权限、i18n、样式、校验命令。
4. `runtime-env`：FE 启动命令、端口、探活 URL、teardown。

## 工作流

1. 定位 Convention Pack。通用约定读 `references/frontend-convention-pack.md`；若 `scaffold_id=quantum-front`
   或目标 pack 路径匹配 `quantum-front/docs/ai/convention-pack`，再读 `references/quantum-front-adapter.md`。
2. 运行 `python3 scripts/check_frontend_pack.py <convention-pack-dir>`，缺必需文件/模板先停机补约定。
3. 读取 API 契约，生成类型、mock 数据、API client 或适配层；不得凭记忆补接口字段。
4. 生成页面、路由/注册、查询条件、表单校验、空态、错误态和权限态。
5. 运行 Convention Pack 声明的 lint/typecheck/build/unit 命令。
6. 从 `runtime-env` 启动 FE demo，访问探活 URL；失败则读错误、修复、重跑。
7. 记录页面路径、命令、探活结果、截图或日志摘要，交给 `runtime-verify`。

## 输出

- 新增或修改的前端页面、路由、API、模型、mock、测试文件。
- 校验命令结果、demo 探活证据、关键页面截图路径。
- 需求条目到页面能力的映射，供 `biz-delivery-loop` 汇总。

## 铁律

- 不猜脚手架；Convention Pack 没声明的结构先停机补约定。
- 不猜环境；端口、命令、URL、teardown 只读 `runtime-env`。
- 不绕过权限、数据域、表单校验和错误态；缺规则时标记 blocked。
- 不把 mock 当真实对接完成；mock 到真实接口必须进入后续集成验证。

## PACE 集成

- design stage：消费页面验收标准、效果图和冻结 API 契约。
- impl stage：生成页面与 mock demo。
- runtime-verify stage：实跑 FE demo、保存截图和探活证据。
- review stage：由 spec-compliance 核对需求、契约和生成文件是否一致。

## References

- `references/frontend-convention-pack.md`: 所有前端脚手架必须提供的 pack contract。
- `references/quantum-front-adapter.md`: quantum-front 的首个具体适配器。
- `scripts/check_frontend_pack.py`: pack 结构和模板完整性校验脚本。

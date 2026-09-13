# PACE 全栈垂直切片准入 (9.9.9)

业务流程由 biz-delivery-loop 编排现有 quantum-codegen 六 mode、quantum-data 与 Convention Pack。单平台能按依赖完成全链；并行有收益时才拆互斥写集，整合责任见 [execution-contracts.md](execution-contracts.md)。

## 真实项目准入

开始真实全栈验收前，由主 agent 在该切片 design 输入部分记录：
- 真实仓库路径/远端标识、基线 commit、允许改动范围、业务动作与 AC 覆盖。
- Convention Pack/runtime-env 的路径与版本，FE 路由、API/DB 入口及现场探活。
- 已授权测试角色与权限差异，只写账号引用，不保存凭证。
- 可重复种子、隔离测试数据、清理步骤，required/advisory OS 与服务。
- 正常、拒绝、越权、失败四类输入及预期 UI/API/DB/审计状态，允许的失败注入。
缺运行必需条件时该切片保持未具备准入；继续独立工作，不缩为 mock 或文档通过。现有授权和确认继续有效，新业务决策才按影响询问。

## 实现与运行

先明确业务规则、API 和数据合同，再按依赖实现 FE/BE/DB。表设计文档与 DDL SQL 分离交付；涉及迁移才增加兼容/回滚验证。mock demo 只支持 UI 设计，不能替代真实全栈链。
集成后真实启动 FE/BE/DB，执行正常、拒绝、越权、失败断言并核对权限/审计。运行只能依据 runtime-env；VM configured、transport available、scenario ready 分开，只有 design 要求的环境构成 required；本机满足合同即可无 VM 闭环。
runner 按选场景→核对代码→准备→断言→采集→teardown 返回 PACE；退出、超时、未知和清理失败分别记录，仅清理本 run 资源。

## 交付与确认

报告复用同一组“需求→产物→证据→状态/遗留”引用。模型用量有原生来源则记录，无来源写 unavailable/null；不能因用量缺失阻塞功能交付。
CP1/CP3/CP5 的人工确认只在 design/用户要求时适用，既有确认引用原记录，不重复询问；机器门禁始终检查实际证据。阶段顺序、一次 review 和 ship 义务仅由 [stages.md](stages.md) 定义。

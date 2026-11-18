# Athena 10.2.0 发布说明

本说明适用于仓库中的 10.2.0 构建。运行 `node vibeCoding/athena/build.mjs` 生成安装包，安装器入口为 `vibeCoding/dist/athena/10.2/cli.cjs`。平台选择、安装预演和回滚步骤见 [安装指南](INSTALL.md)。

- 用 `athena status --brief` 查看当前 sprint、队列和紧急问题。用 `athena tidy --dry-run` 预览已完成条目的归档计划。
- 用 `athena doctor --context` 检查各层载入的上下文。Quantum 产品技能随项目包分发，按项目启用。
- `athena issue pull` 列出可认领的 issue。`athena sprint start --issue <n>` 将工作绑定到跟踪单。真实 tracker 平台联调仍待验证。

当前版本的协作流程与适配器变更见 [CHANGELOG](CHANGELOG.md)。项目状态迁移步骤见 [迁移指南](MIGRATION.md)。

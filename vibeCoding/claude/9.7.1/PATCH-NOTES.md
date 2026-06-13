# Athena v9.7.1 · Patch Notes
范围: 2 文件 (双端 pace/references/orchestration.md). 纯知识补全, 零机制变更.
内容: 长任务三分法 (M14, 官方: 轮询=/loop · 事件=Channels preview · run-until-done=/goal)
+ /goal 机制加深 (evaluator 只读 transcript [官方], 条件三件套, turn 上限必写, claude -p 非交互入口)
+ CX 列归属澄清 (CLI 无内置定时, Automations 是 app 专属, codex exec 官方钦定非交互姿势)
+ loop 设计三问 (说 no 的东西 / 预算 / 落盘).
应用: 覆盖到已部署的 9.7.0 同路径文件即可. .ai_state 零迁移.

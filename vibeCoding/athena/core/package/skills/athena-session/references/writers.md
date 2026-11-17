# 写者

写入分区（谁直做、何时隔离）以 [stages.md](../../pace/references/stages.md)「写入分区」为准（由 `core/pace/stages.yaml` 生成）；本文件只放会话层的写者分工。

- 同时 ≤3 个写者。分档：简单 → 快写者（如 grok）；中等与复杂 → 外部写者（如 codex）；极度复杂 / 跨系统 / 安全 → 主力模型；架构级 → 最强模型（只读出方案，主 agent 落盘）。每刀只 review 一轮，用与写者不同家族的 reviewer，只有 P0 / P1 阻塞；最强模型另在会话末做一次整体 review。
- 每个写者在简报里写明推理档位，不默认继承最高档；用量异常先降档再查。
- 简报必写：边界、允许写集、AC 原文、验证命令；不过度设计、不做防御性编程（对齐主流 agent 工具行为，边界只设在用户输入与跨进程 / 跨租户），不写无效的否定说明与防御性解释；不许删注释或压行挤行数棘轮（超了拆文件）；迁移号预分配；项目代码约定；不执行 athena、不碰 `.ai_state/`；写者每完成一个 AC 就 commit，中断不丢。
- 遇到不熟悉的功能：先检索 GitHub 近 2 年维护活跃、许可证明确的同类开源项目，比较思路、依赖、已知问题，借鉴经过验证的设计，不直接复制不兼容或来源不明的代码。
- UI：Avoid unnecessary secondary labels and descriptions. Let the layout do the explaining（不加副标题、说明段、空态长文案；靠分组、对齐、图标、悬停提示）。
- 写者撞轮次上限或断网 → `SendMessage` 让它续做；会话重启后旧子 agent 不可续，先看其 worktree 的 `git log` / `status`，已提交的照常合入。
- 外部写者用后台命令跟踪完成（不用 nohup）；需要联网 / 跨仓写入时显式开对应权限；它不能提交或建 worktree 时由主 agent 代办。新建 worktree 先装依赖。
- 代写者提交前先看 `git diff --stat` 逐条对照简报 / review 发现；提交信息按实际 diff 写，不照抄写者报告（10-27：返工报告称已修三条，diff 里只有一条）。

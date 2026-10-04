# Athena — 工程协作约定

你对整合后的结果负责，不对流程数量负责。

- 状态：有 `.ai_state/_index.md` 就先读，按指针只读当前任务所需；没有则按本约定直接工作，要跟踪时经用户同意 `athena init`。
- 路由：新任务先分诊（athena-dev）。写不出验收标准 → brainstorm；≥2 个可独立验收切片 → roadmap。用 `athena sprint start` 开 sprint。
- 完成：design 的验收标准都有证据、门禁放行才算完成。收尾前看最后一段：写了「接下来可以…」「要不要我…」「剩余待办」而那件事在本任务范围内，现在做完再收尾。
- 范围：交付物就是任务说的范围，不悄悄缩小、扩大或替换；要改范围先说。
- 写入：小改与单模块 Feature 主 agent 直做；Refactor/System、多写者、或 review 窗口内还有并行写者，用隔离工作区。子 agent 只为隔离或并行而派。
- 验证：`athena run -- <命令>` 跑与改动相称的检查；成功一行，失败才展开。`athena` 的 status / run / sprint / review 是例行动作，直接执行不用问。
- 门禁：被拦按 reason 修；认为误拦，`athena issue add --type gate --text "…"` 记一行并请用户放行，不绕过。
- 事实：API/配置/协议引官方文档或源码；本机没验证的标「待验证」；转述别人的结论写出处。
- 阻塞：同一路径失败三次，带 stderr 与已试方案报告阻塞，不换花样硬试。
- 决策：可逆的实现选择自己定；删数据、发布、付费、推送到别人仓库先确认。
- 记账：`.ai_state` 改动随代码同一提交，不单独提交记账。
- 输出：电报体，结论先行，表格优先；不复述过程，不落盘原始推理。长任务在阶段切换处给一行进度。
- 阶段义务：{{athena:SKILLS_DIR}}/pace/references/stages.md；平台差异：{{athena:SKILLS_DIR}}/pace/references/platform.md。

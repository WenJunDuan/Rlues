# 合入与 review

- 合入前先 `athena sprint resume <slug>`；`athena writer collect` 非快进时 `git merge --no-ff <branch>` 再 collect。
- `athena run` 进行中不切换活跃 sprint（证据按活跃 sprint 归属）。
- review packet 绑定源码树：packet 发出后到 accept 前，主树不提交任何东西（含 review 修复、别刀合入）；工作区新增的未跟踪文件也算进树，要写先放树外。先 accept 落盘（reviewer 原文逐字），再改代码、再 prepare 下一轮。
- 多刀批量：先合完 → 各刀在同一棵树上补证据并 prepare → reviewer 并行 → 逐个 accept → 再动树。等 review 时先把下一批写者派出去。
- 冲突以主线为准、重新应用分支意图；行数基线冲突取实测值（只降不升，补回注释的除外）。
- 跨仓接口升版后，消费方立即同步合同；请求体新字段要有能力位，消费方按位下发，避免连旧版本被拒。
- 每刀 ship 后给用户一行进度：`✅ <slug>：要点`。

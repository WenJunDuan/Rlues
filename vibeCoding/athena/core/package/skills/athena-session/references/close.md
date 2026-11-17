# 收尾

1. 根全量 + lint + build（每个工作仓库），修跨刀问题。
2. 最终整体 review（含依赖是否最新 + 已知漏洞），修 P0 / P1，其余记债后 ship。
3. 更新交接文档（顶部新段，旧段归档）、sprint 总表、`issues.md`；`athena tidy --dry-run` 后再 tidy；`.ai_state` 减负。
4. 各工作仓库：清缓存、废弃测试文件、过期与废弃代码；合并代码、删已合并的 worktree 与分支。
5. 推送（`.ai_state` 记账同提交，见宪法「记账」）。

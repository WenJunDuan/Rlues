# Session log — S4 state-v2

- 2026-09-24：路由 System（athena-10-1 S4）；design AC1–AC6 + 偏差表。
- 2026-09-24：模板 10 个（gate/templates）；CLI status/sprint/ship/issue/tidy/migrate + cli/lib（state 键级原地写、archive、migrate-plan）；session_start 注入 resume ready。
- 2026-09-24：用户改范围：S8 取消；quantum-agent 不在本仓迁移（其 dry-run 报告已删）；最后整理 Rlues `.ai_state`。
- 2026-09-24：review 3 轮（REWORK → CONCERNS → PASS），117/117，athena999 231 OK。
- 2026-09-24：坑：Write 工具建的文件在追加后提交到设备仍是首版（file_uuid 快照）→ 每次改完复制成新文件名再提交并核 sha256。
- 2026-09-24：坑：VM 挂载目录无删除权限时 `git status` 会遗留 index.lock → 门禁 git 调用统一 `GIT_OPTIONAL_LOCKS=0`；本次在 quantum-agent 遗留的空锁已删除（经用户授权）。
- 2026-09-24：坑：复制 index 后未保留 mtime，同秒同长度修改被 git 视为 racy-clean → tree-sha 漏检；已修（utimes）。

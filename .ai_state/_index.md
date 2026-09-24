---
schema: athena-state/2
version: "10.1"
path: ""
stage: ""
sprint: ""
roadmap: "athena-10-1"
next_action: "用户：athena install --platform cc,cx（先 --dry-run）→ athena doctor；quantum-agent 自行迁移；清理 grok worktree/分支"
route: ["2026-09-24 Feature S6 install-doctor: athena install/rollback/doctor 事务式安装 + 9.9.9 退役; review 2 轮; S7 取消","2026-09-24 Feature S3 review-cli: athena review prepare/accept/show + 三端同一合同 + CC workflow; review 2 轮 PASS","2026-09-24 System S4 state-v2: 模板 + CLI(status/sprint/ship/issue/tidy/migrate) + 安全归档; review 3 轮 PASS; S8 取消"]
parallel_writers: 1
exemptions: []
flags: {}
pointers: {queue: "queue.md", issues: "issues.md"}
---
# Project state

Router only (≤3 KB). Written by the `athena` CLI; read `athena status` for the human view.

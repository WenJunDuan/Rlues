---
sprint: "nov18-doctor-index"
path: "Bugfix"
created: "2026-11-18"
req: "/tmp/athena-doctor-user-index.md"
roadmap: ""
item: ""
base_commit: "585951d"
repro_test: ""
review_ignore: []
---

# Bugfix — nov18-doctor-index

## 故障与预期
安装器在重装时保留个人规则索引；doctor 仍将该路径列为旧版残留。
- AC1: 已安装 Claude 的用户规则索引通过 doctor；其他 9.9.9 遗留仍会报告。

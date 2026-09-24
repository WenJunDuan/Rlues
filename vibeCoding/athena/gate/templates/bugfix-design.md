---
sprint: "{{sprint}}"
path: "Bugfix"
created: "{{date}}"
req: "{{req}}"
roadmap: "{{roadmap}}"
item: "{{item}}"
base_commit: "{{base_commit}}"
repro_test: ""
review_ignore: []
---

# Bugfix — {{title}}

## 当前行为

<!-- 复现步骤 + 实际输出；repro_test 指向先红后绿的复现测试。 -->

## 期望行为

## 不变行为

<!-- 这些行为不许变；每条对应一条回归断言。 -->

## 验收标准

<!--
- AC1: 复现测试先红（athena run 记录）后绿
- AC2: 不变行为回归全绿
-->

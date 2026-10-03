---
sprint: "2026-10-03-gate-feedback"
path: "Bugfix"
created: "2026-10-03"
req: "vibeCoding/athena/FEEDBACK.md"
roadmap: ""
item: ""
base_commit: "60bc7ed"
repro_test: ""
review_ignore: []
---

# Bugfix — 2026-10-03-gate-feedback

## 当前行为
FEEDBACK.md G-006…G-011：轮换范围污染、合同定位歧义、文档证据缺口、PATH 提示缺口、push 解析边界、执行环境绕过。

## 期望行为
按用户六条分别先红后绿并提交；完整 fixture 测试和构建成功。

## 不变行为
VERSION 10.1.0；不安装、不推送；G-011 不得把基线不可证明升级为可证明。复合 push 不安全拆执行，不能解析的真实扩展保持拒绝。

## 验收标准
- AC1: G-006 pause 记录实际阶段；packet 排除暂停期间提交并列明范围。
- AC2: G-007 接受 evidence/packet/design 定位且保留严密 verdict 合同。
- AC3: G-008 固定字串 Markdown 断言可证明；其余 other 保持原判。
- AC4: G-009 安装缺 PATH 配置时提示；hook 进程前置 Athena bin。
- AC5: G-010 真实 push 与数据字样区分、逐仓判 stage；无法安全完成部分写明限制。
- AC6: G-011 行内/export 和 runner 选择变量不可证明，凭据漏拒补齐；单调安全回归通过。
- AC7: 完整 unittest fixtures 与发行构建通过；台账有对应提交。

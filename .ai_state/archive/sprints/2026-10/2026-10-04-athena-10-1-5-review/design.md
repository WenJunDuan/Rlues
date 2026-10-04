---
sprint: "2026-10-04-athena-10-1-5-review"
path: "Bugfix"
created: "2026-10-04"
req: ".ai_state/roadmap/athena-10-1-5/design.md"
roadmap: ""
item: ""
base_commit: "1c1cd73"
repro_test: ""
review_ignore: []
---

# Bugfix — 2026-10-04-athena-10-1-5-review

## 当前行为

Claude 分支 d22d135 相对 1c1cd73 的 66 文件迭代仍为候选；版本误写为 10.5.0，插件运行探针未做，架构入口停留在 9.9.8。用户要求整体 review/debug，并在既定迭代设计内收尾，禁止过度设计与防御性编程。

## 期望行为

统一候选版本为 10.1.5；复现并修复迭代实际缺陷；运行本机可完成的检查；将剩余平台能力验证及发布项明确记账。路由为 Bugfix：修正现有实现，不增加新能力。实现使用隔离 worktree。

## 不变行为

沿用原设计 H1–H5、schema v2（state version 10.1）、证据绑树、独立 review、writer 只 fast-forward 的边界。构建目录继续按 major.minor（10.1）。不部署、不打 tag、不 push；不实现下一版 mod hooks 或上架功能。

## 验收标准

- AC1: 当前迭代源码、说明、roadmap 与构建 manifest 的版本统一为 10.1.5；不残留误写版本引用，构建与检查通过。
- AC2: 审查确认的门禁、证据、writer 与插件行为缺陷有先失败后通过的回归验证；既有 fixture 全量通过，环境限制逐项据实记录。
- AC3: 按原 S1–S5 设计完成独立审查并处理发现，CC 插件真实 validate 和可执行本机探针有结果；需要平台会话或付费调用的未验证项仍明确待验证。
- AC4: 当前架构入口、迭代尾项、发布声明反映实际源码与验证结果；不将待发布或未运行的行为评测标为完成。

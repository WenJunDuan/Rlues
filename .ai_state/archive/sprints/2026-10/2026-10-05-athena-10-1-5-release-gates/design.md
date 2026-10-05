---
sprint: "2026-10-05-athena-10-1-5-release-gates"
path: "System"
created: "2026-10-05"
req: ".ai_state/roadmap/athena-10-1-5/design.md"
roadmap: ""
item: ""
base_commit: "45bcf57"
review_ignore: []
---
# Athena 10.1.5 Mac 发布门验证

候选提交 3552697（Claude 在 45bcf57 后调整范围与目录）；安装器形态为本版承诺，插件壳 experimental，P1–P7 与 D-014 顺延。用户已明确授权本机 cc,cx 安装、doctor、真实 CC Quick→ship、rollback，以及保留会话历史的无效备份/缓存清理。源码在隔离 worktree 验证，主 checkout 管 .ai_state。

## 范围与不变量

验证当前候选，不扩展迭代设计。必要缺陷才修；任何源码修复均重跑相应证据并独立复审。先保存可回滚的安装状态；不改用户模型、认证或权限设置，不删除 sessions、history、projects、SQLite、归档或有效回滚链。清理只删除确认无效/可再生且不承载历史的对象，记录路径与空间。main 合入和 v10.1.5 tag 在发布门全部通过后再作决定，不 push。

## 验收

- AC1: Mac 对 3552697 候选源码用 athena run 跑全量 fixture，通过且记录源码树；构建 --check 通过。
- AC2: 真机 athena install --platform cc,cx 成功，候选版本 10.1.5，athena doctor 无 drift；用户自定义配置和会话数据保留。
- AC3: CC 原生安装器形态完成一个隔离测试项目的 Quick sprint 到 ship，捕获实际 hook 生命周期且无 JSON/序列化误拦；不得用直接调用 hook 冒充原生验证。
- AC4: athena rollback 成功恢复安装前版本和配置，doctor 无 drift；有效回滚链与会话历史保留，确认无效的备份/缓存完成有界清理。
- AC5: 记录发布门结果及独立复审结论；依据结果给出 main/tag 决策，未过门不发布。S6 顺延与 experimental 限制保持真实。

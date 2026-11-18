---
sprint: "2026-11-18-codex-reference-sync"
path: "Quick"
created: "2026-11-18"
req: "/tmp/codex-reference-sync-request.md"
roadmap: ""
item: ""
base_commit: "5fceafb"
review_ignore: []
---

# Design — 2026-11-18-codex-reference-sync

## 背景

上一任务只修改个人配置。用户明确要求同步当前参考配置并删除本次备份。

## 方案

首装模板默认模型设为 gpt-6.2-sol，安装指南增加独立 proxy provider 的可复制示例，示例保留 high 推理强度和现有 auth.json 认证。备选为将个人代理地址直接写入通用首装模板；会影响其他安装，故用文档占位 URL。用户本轮要求覆盖此前不固定模型的包内约定，相应更新原断言。

## 验收标准

- AC1: 当前 Codex 模板默认模型为 gpt-6.2-sol；安装指南包含 proxy provider 示例，使用占位地址且不含个人代理 IP。
- AC2: 包配置、提示词和构建测试通过；本机 provider 保持 proxy，本次备份文件已删除；验证时观察到本机已被其他操作改为 gpt-6.2-astra / medium，本任务不覆盖该并发选择。

## 允许写集

- vibeCoding/athena/adapters/cx/package/config.toml
- vibeCoding/athena/docs/INSTALL.md
- vibeCoding/athena/evals/fixtures/test_prompts.py
- 构建生成的 vibeCoding/dist（gitignore）及 Athena 状态
- 删除 ~/.codex/config.toml.before-proxy-20261118-090607

## 不做

不改历史归档模板、不改安装器合并策略、不改其他备份、不推送。

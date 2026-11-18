---
sprint: "2026-11-18-codex-proxy-provider"
path: "Quick"
created: "2026-11-18"
req: "/tmp/codex-proxy-provider-request.md"
roadmap: ""
item: ""
base_commit: "5fceafb"
review_ignore: []
---

# Design — 2026-11-18-codex-proxy-provider

## 背景

用户要求保留代理，按官方自定义 provider 格式配置；当前 provider ID 和显示名均为 OpenAI。
官方参考：https://developers.openai.com/codex/config-advanced/#custom-model-providers

## 方案

将 provider ID 改为 proxy、显示名改为 Codex Proxy。保留代理 URL、Responses 协议、requires_openai_auth，以复用现有 auth.json 凭据。修改前备份配置。用户追加要求：默认模型设为 gpt-6.2-sol，保留 high 推理强度。

## 验收标准

- AC1: provider ID 为 proxy，name 为 Codex Proxy；默认模型为 gpt-6.2-sol，推理强度保留 high，其余配置及凭据不变，通过 TOML 结构对比验证。
- AC2: 新启动 Codex 的 config/read 和 model/list 成功，模型目录包含默认模型；对现有代理的鉴权 models 查询返回 HTTP 200。

验证：athena run --covers AC1,AC2 -- python3 /tmp/codex-proxy-provider-verify.py

## 允许写集

- /Users/mi_manchi/.codex/config.toml
- 对该文件的本地备份
- 当前 sprint 的 Athena 状态及证据

## 不做

不切换到官方服务器、不更改凭据、不迁移历史会话、不发起推理请求。

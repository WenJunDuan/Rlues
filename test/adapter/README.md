# Adapter Docs

文档已重组到 `.ai_state/docs/project/`：
- 总览：`.ai_state/docs/project/modules/adapter.md`
- Gateway：`.ai_state/docs/project/modules/gateway.md`
- SDK：`.ai_state/docs/project/modules/sdk.md`
- 测试清单：`.ai_state/docs/project/testing/quality-checklist.md`

统一外部配置文件：`config.json`（非敏感配置）
密钥与 URL：`.env`（如 API keys、Redis URL、插件外部服务 URL）
（可通过 `ADAPTER_CONFIG_PATH` 指定路径）

配置加载器位置：`adapter/core/config_loader.py`

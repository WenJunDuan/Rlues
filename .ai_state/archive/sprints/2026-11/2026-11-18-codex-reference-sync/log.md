# 参考配置同步

## 2026-11-18

- Codex 首装模板默认模型 gpt-6.2-sol；INSTALL.md 增加 proxy / Codex Proxy / Responses / requires_openai_auth 示例，使用占位 URL。
- 更新原不固定模型断言，保留包内不固定推理强度约定。
- 已重建 vibeCoding/dist；源码及构建产物默认模型一致。历史归档模板不改。
- 通过 athena run：test_package_config.py 10 项、test_prompts.py 17 项、test_build.py 22 项，共 49 项；git diff --check 通过。
- 已删除 ~/.codex/config.toml.before-proxy-20261118-090607。
- 本轮未写本机配置；验证发现本机最新模型为 gpt-6.2-astra、推理 medium，保留该并发修改。provider 仍为 proxy。
- 无剩余任务，未提交或推送。
- 2026-11-18 shipped (evidence e94673a2fcab)

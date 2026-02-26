# Gateway Docs

详见：`.ai_state/docs/project/modules/gateway.md`

统一外部配置文件：`config.json`（`gateway` 段）

## 当前分层

- `http_server.py`：仅负责 FastAPI 路由注册、参数绑定、JSONResponse 输出。
- `access_control.py`：鉴权与访问控制（endpoint scope、task owner 校验）。
- `feature_service.py`：feature API 到 task envelope 的适配与 feature/task 匹配检查。
- `response_mapper.py`：统一错误响应构造与 HTTP 状态码映射。
- `http_access.py`：配置读取与访问策略模型。

## 调用方向

`http_server -> (access_control | feature_service | response_mapper) -> core.api_server`

Gateway 层不直接实现业务执行逻辑，执行链路由 `adapter/core` 与 `adapter/sdk` 负责。

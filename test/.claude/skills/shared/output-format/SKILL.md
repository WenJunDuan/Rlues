# shared/output-format

## 适用场景
当 Orchestrator、Subagent 或 Adapter 需要生成/校验标准输出时使用。

## 目标
1. 统一 ResultEnvelope 字段。
2. 统一错误对象结构。
3. 统一错误码分层（validation/adapter/sdk/schema）。

## 关联规范
- `result-envelope.md`

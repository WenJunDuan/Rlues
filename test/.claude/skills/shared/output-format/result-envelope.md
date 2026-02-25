# ResultEnvelope Contract (V4)

## 1. 顶层字段
必须包含：
- `task_id: string`
- `command: string`
- `status: "completed" | "needs_review" | "failed" | "timeout"`
- `result: object`
- `execution: object`
- `error: object | null`

## 2. result 字段
建议结构：
- `decision: "approved" | "rejected" | "needs_review"`
- `confidence: number (0~1)`
- `summary: string`
- `issues: array`
- `evidence: array`

### 2.1 issues 元素
- `severity: "error" | "warning" | "info"`
- `category: string`
- `description: string`
- `evidence_ref: string (optional)`

### 2.2 evidence 元素
- `id: string`
- `type: string`
- `source: string`
- `content: string`

## 3. execution 字段
建议结构：
- `model_used: string`
- `agents_invoked: array[string]`
- `parallel_tasks: integer`
- `tools_called: array[string]`

## 4. error 字段
失败或降级时必须携带结构化错误：
- `code: string`
- `message: string`
- `recoverable: boolean`
- `details: array (optional)`

## 5. 错误码分层
### 5.1 validation 层
- `VALIDATION_FAILED`
- `VALIDATION_MISSING_FIELD`
- `VALIDATION_TYPE_MISMATCH`
- `VALIDATION_INVALID_VALUE`

### 5.2 adapter 层
- `ADAPTER_PARSE_ERROR`
- `ADAPTER_TASK_NOT_FOUND`
- `ADAPTER_STREAM_NOT_FOUND`
- `ADAPTER_EXECUTION_ERROR`

### 5.3 sdk 层
- `SDK_IMPORT_ERROR`
- `SDK_OPTIONS_ERROR`
- `SDK_QUERY_ERROR`
- `SDK_EVENT_LOOP_ERROR`
- `SDK_RESULT_MAPPING_ERROR`

### 5.4 schema 校验层
- `SCHEMA_MISSING_FIELD`
- `SCHEMA_TYPE_MISMATCH`
- `SCHEMA_INVALID_VALUE`

## 6. 决策兜底规则
1. 若关键信息缺失或冲突：`decision = needs_review`。
2. 若 `confidence < 0.7` 且非 `rejected`：降级 `needs_review`。
3. 发生不可恢复异常：`status = failed`，并写入 `error`。

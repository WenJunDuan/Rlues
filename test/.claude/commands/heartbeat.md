# /heartbeat — System Health Check

## Input
```
command: /heartbeat
context.tenant_id: "system"
context.operator_id: "cron"
payload.check_time: ISO-8601 timestamp
payload.diagnostics: object
```

## Routing
直接在 Orchestrator 层处理，不转发至 Subagent。

## 执行逻辑
1. 收集系统运行时指标：
   - 队列健康度（pending / running / max_concurrent）
   - 错误率（近 N 分钟 failed task 比率）
   - 陈旧任务检测（pending 超过 2× max_concurrent）
2. 汇总为诊断报告。

## 输出
```json
{
  "task_id": "heartbeat-<uuid>",
  "command": "/heartbeat",
  "status": "completed",
  "result": {
    "decision": "approved",
    "confidence": 1.0,
    "summary": "system healthy | degraded | unhealthy",
    "issues": [],
    "evidence": [
      {
        "id": "diag-001",
        "type": "system-diagnostics",
        "source": "adapter://cron",
        "content": "{ ... diagnostics ... }"
      }
    ]
  }
}
```

## 异常
- 若诊断过程本身失败，返回 `status: "failed"` 并携带错误详情。
- 不影响正常业务任务调度。

# Runtime Env Contract

`runtime-env` 是全栈运行环境的唯一声明来源。skill 不允许猜 FE/BE/DB 命令、端口、探活 URL、账号或 teardown；
原则是明确声明、缺项停机、不猜环境。

## Canonical Schema

```yaml
runtime-env:
  frontend:
    command: []
    cwd: ""
    port: 0
    health_url: ""
    ready_timeout_seconds: 0
    teardown: []
  backend:
    command: []
    cwd: ""
    port: 0
    health_url: ""
    ready_timeout_seconds: 0
    teardown: []
  database:
    command: []
    cwd: ""
    port: 0
    health_url: ""
    ready_timeout_seconds: 0
    teardown: []
  test_accounts:
    source: ""
    roles: []
  artifacts:
    evidence_dir: ""
```

兼容读取别名：`fe -> frontend`、`be -> backend`、`db -> database`。写入新 Convention Pack 时必须使用
canonical key；skill 读取旧项目时可接受别名，但报告和修复建议必须输出 canonical key。

## 规则

- `command` 和 `teardown` 使用数组形式，避免 shell 拼接。
- `port` 必须显式声明；端口冲突时按项目约定处理，skill 不自行换端口。
- `health_url` 必须是本环境可访问 URL；探活失败不得继续 E2E 或安全测试。
- `teardown` 必须能清理进程、容器、临时数据或测试账号状态。
- DB 可以是本地、容器或远端测试库，但凭证必须来自安全配置，不写入 skill。
- `frontend`/`backend`/`database` 可声明为 `external: true`，但仍需端口、探活 URL 和清理边界。
- 运行前先做 schema smoke：三类 runtime key 解析后必须只剩 canonical key，未知 key 进入报告的 `runtime_env_warnings`。

## PACE 证据

每次 runtime-verify 至少记录：启动命令摘要、进程或容器标识、端口、探活结果、teardown 结果和失败原因。

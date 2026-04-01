---
name: security-review
description: 安全审查。Path C+ 自动触发或显式调用。检查认证/授权、输入验证、密钥管理、依赖漏洞。
---
# Security Review

## 检查项
1. 认证/授权: 每个端点有权限检查?
2. 输入验证: 外部输入已验证和消毒?
3. 密钥管理: 无硬编码, 用环境变量
4. 依赖: `npm audit` / `pip audit` 无高危
5. 日志: 不记录密码/token/PII
6. CORS/CSP: Web 接口配置正确?

结果追加 quality.md。
如已安装 ECC → `npx ecc-agentshield scan` 做深度扫描。

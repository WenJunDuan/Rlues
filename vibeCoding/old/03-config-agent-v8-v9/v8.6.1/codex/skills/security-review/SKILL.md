---
name: security-review
description: 安全审查清单 (源自 ECC security-review)
context: main
---
Path C+ 的 V 阶段:
1. 调用 security-auditor 子代理
2. 扫描项: 依赖漏洞、硬编码密钥、SQL注入、XSS、CSRF、CORS、文件上传
3. 输出风险等级 A-F
4. Critical/High 必须修复才能通过 cunzhi [VERIFIED]
5. 结果写入 `.ai_state/review.md`

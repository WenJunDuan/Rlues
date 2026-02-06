# Security Rules

## 禁止
- 硬编码密钥/密码/token
- 未验证的用户输入直接使用
- SQL 拼接 (必须参数化)
- 不安全的 eval/exec

## 必须
- 所有公共接口输入验证
- 敏感数据加密存储
- HTTPS only
- 最小权限原则

## 审查触发
vibe-review --security 时加载此规则。

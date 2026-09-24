# VibeCoding Rules

## 代码安全 (源自 ECC security rules)
- 不硬编码密钥、密码、API key、token
- 所有 .env 文件必须在 .gitignore 中
- HTTP 端点必须有认证和输入验证
- SQL 查询必须使用参数化查询, 不拼字符串
- 文件上传必须验证类型和大小
- CORS 仅开放必要域名

## Git 规范
- 使用 conventional commits: feat/fix/refactor/docs/test/chore
- 每个 commit 只做一件事
- commit message 用英文, 第一行 ≤ 72 字符

## 代码质量
- 单文件 ≤ 300 行, 超过则拆分
- 单函数 ≤ 50 行
- 不留 TODO/FIXME — 要么修要么建 issue
- 不留 console.log (调试用完就删)
- 优先 immutable 数据结构

## 测试
- 新功能必须有测试 (Path A 除外)
- 修 bug 先写失败测试再修
- 测试覆盖率目标 ≥ 80%

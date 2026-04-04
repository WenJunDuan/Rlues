# 编程标准

<important if="writing, reviewing, or generating code">
代码质量三级标准。@evaluator 评分时以此为依据。

## P0 — 必须遵守 (违反 → Quality Gate FAIL)
- 无安全漏洞: 无 SQL 注入、XSS、CSRF、硬编码密钥/密码
- 无未处理异常: 每个 async 函数有 try-catch 或 .catch(); 每个 Promise 有错误处理
- 类型安全: TypeScript 项目使用 strict mode; 禁止 `any` 除非有注释说明原因
- 测试覆盖: 每个 Feature 至少 1 个测试; 核心业务逻辑测试覆盖率 > 80%
- 无数据泄露: 日志不打印敏感信息 (密码、token、个人数据)
- 依赖安全: 不引入已知有 CVE 的依赖版本

## P1 — 应该遵守 (违反 → Quality Gate CONCERNS)
- 函数体 < 50 行 (超过则拆分)
- 单一职责: 一个函数/方法做一件事
- 有意义的命名: 变量名表达意图, 不用 x/temp/data/result 等泛名
- 错误消息对用户友好: 不暴露内部实现细节
- 接口最小化: 只暴露必要的 API, 内部实现保持私有
- 幂等性: 同一操作重复执行结果一致 (尤其是 API 和数据库操作)
- 输入验证: 所有外部输入 (用户输入、API 参数) 都有验证

## P2 — 建议遵守 (违反 → 代码注释提醒, 不影响评分)
- 复杂逻辑有注释解释 "为什么" (不是 "做什么")
- 公共 API 有 JSDoc/docstring
- 避免深层嵌套 (< 3 层 if/for)
- 常量提取: 无 magic number/string
- 一致的代码风格 (Prettier/ESLint 格式化)
- 合理的文件组织 (相关代码放在一起)
</important>

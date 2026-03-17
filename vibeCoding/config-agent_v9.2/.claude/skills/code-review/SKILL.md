---
name: code-review
description: 代码审查 — T 阶段在 verification 之后使用
context: main
---
## 管道位置: T (verification之后) → 追加 quality.md (审查部分)

## 审查维度
1. **逻辑**: 边界条件、错误处理、空值检查
2. **安全**: SQL注入、XSS、密钥泄露、权限检查
3. **性能**: N+1查询、不必要的循环、内存泄漏
4. **可维护**: 命名清晰、函数职责单一、注释说明 WHY

## 产出: 追加到 quality.md
```markdown
## 审查报告
- 严重: 0 | 警告: 2 | 建议: 3
- [警告] src/routes/auth.ts:42 — 缺少 rate limiting
- [建议] src/utils/jwt.ts:15 — magic number 应提取为常量
```

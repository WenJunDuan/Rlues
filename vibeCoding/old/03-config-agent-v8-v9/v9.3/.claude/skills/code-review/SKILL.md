---
name: code-review
description: 4 级 LLM-as-Judge spec 合规判定。T 阶段官方 /code-review 做广度扫描后, 本 skill 做 design.md spec 深度合规。
---
# Code Review — LLM-as-Judge

与官方 `/code-review` 分工:
- 官方: 4 parallel agents 扫 bugs + compliance + git blame
- 本 skill: 对标 design.md spec, 输出 4 级判定

## Spec 合规清单
1. 每个 MUST 需求是否实现?
2. 每个源码文件有对应测试?
3. 边界: 空输入/超长/并发/错误路径?
4. 安全: 无硬编码密钥, 输入已验证
5. 可读: 函数 < 50 行, 注释说 WHY, 严格类型
6. 简洁: 无过度工程, 无重复, 无空 catch

## 输出
```json
{"level": "PASS|CONCERNS|REWORK|FAIL", "issues": [...], "summary": "..."}
```

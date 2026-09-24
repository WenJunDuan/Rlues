---
name: code-review
description: 4 级 LLM-as-Judge spec 合规判定。/review 内置做广度后, 本 skill 做 design.md spec 深度合规。
---
# Code Review — LLM-as-Judge

## Spec 合规清单
1. 每个 MUST 需求是否实现?
2. 每个源码文件有对应测试?
3. 边界: 空/超长/并发/错误路径?
4. 安全: 无硬编码密钥, 输入已验证
5. 可读: 函数 < 50 行, 注释说 WHY
6. 简洁: 无过度工程, 无重复, 无空 catch

输出: `{"level": "PASS|CONCERNS|REWORK|FAIL", "issues": [...], "summary": "..."}`

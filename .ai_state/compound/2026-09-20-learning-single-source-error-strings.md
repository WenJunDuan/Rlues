---
doc_type: learning
sprint: 2026-09-20-contract-parser-diagnostics
created: 2026-09-20
---

# 三端同源代码的报错文案必须收敛到单一构造函数

## 现象

切片 4 给「未识别到验收小节」写报错时，spec-gate 与 review-packet 两处各拼一遍同一句提示，×CC/CX/Pi 三端 = 6 份字面拷贝。polish 审查指出：改 wording 时**端内**两处漂移没有任何测试能拦——跨端一致性有 cc==cx 行为断言和 Pi 文本相等断言兜底，端内重复完全裸奔。

## 教训

同一句面向操作者的诊断文案出现在 ≥2 个报错点时，先收敛为单一构造函数（本例 `acceptanceHeadHint`），再让各报错点调用。判据与「无第二消费者不抽象」不冲突——第二消费者已经存在时，不抽象才是债。

## 关联

[[2026-09-20-learning-self-mutating-regression-test]]（同为门禁生态的测试盲区类）；本切片 AC7 的 PiSameSourceParity 连注释都校验，故三端同步义务包含注释字节。

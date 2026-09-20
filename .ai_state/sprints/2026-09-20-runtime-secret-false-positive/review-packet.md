---
source_design_sha256: "646c629f44a062f4896f4e02b04ac4beef63eaf4e628fc66817a5b4e801d8c2c"
mode: "design"
---

# Review Packet — runtime secret 假阳性

## Decision

三处秘密识别中 A（runtime-run.py，CC/CX）与 C（_input-binding 三端）用保守占位符白名单谓词消除 quoted placeholder/reference 假阳性；判不准仍按密钥，真密钥行为逐字不变；不建豁免存储（无消费者，未来若建必须按内容 SHA 绑定）；Pi 无 athena-vm 不伪造对称。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | A 三消费点占位符不再剔除/block（contract/required/collect 端到端） |
| AC2 | 前缀段占位体不判密钥，真实随机体仍判 |
| AC3 | 真密钥回归逐用例保持原行为 |
| AC4 | environment() 占位/描述值不抛、真凭据仍抛，首补对照测试，三端一致 |
| AC5 | 对照矩阵 placeholder×real 成对用例 CC/CX 同夹具同判；runtime-run.py CC==CX 字节入测试 |
| AC6 | Pi 悬空引用记 roadmap 切片 9，本切片不修不造 |

## 审查焦点

谓词白名单边界（会不会放走真密钥；`${…}` 引用整值判定的准确形状）；C 修复后 unverifiable 降级链是否恢复；A 的三个 block 消费点行为分级是否如实。

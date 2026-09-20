---
source_design_sha256: "feea3e8535a11c2ce06dfbf60f88dced039b69dd561196b83fc7128db9ddde5a"
mode: "design"
---

# Review Packet — heredoc 感知 shell guard

## Decision

heredoc 识别单源于 _shell-lex（新 heredocSpans），guard 函数内惰性消费、lexer 缺失回退今日保守行为；quoted 正文全免疫、unquoted 正文仅替换 span 进分析、未闭合照拦；证据侧同函数修正误分段；CX evidence-collector 决策截断修复对齐 CC 模式；承接切片 2 guard 字节钉调整。guard 既有引号扫描保留为回退层（安全关键），完整合并不做——明示给审查挑战。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | quoted 正文免疫（含本会话两个活体样本重放） |
| AC2 | unquoted 正文替换 span 照拦、纯文本不拦 |
| AC3 | 命令位置与未闭合 heredoc fail-closed 不变，既有危险模式全回归 |
| AC4 | heredoc 单源 + 惰性载入 + 缺失回退用例；证据侧不再误分段 |
| AC5 | CX >4000 掩盖管道记 unknown 与 CC 同判 |
| AC6 | 字节钉承接：删「guard 字节不变」，parity 与 gate-sans-lexer 独立保留；roadmap 更正 |
| AC7 | guard/_shell-lex CC==Pi 字节、CX 同夹具同判 |

## 审查焦点

unquoted heredoc 的 bash 展开语义（正文 $(…) 确会执行——只掩文本不掩替换是否完备）；回退路径「缺失≠放行」的证明；掩码实现会不会破坏 span 偏移使既有替换分析错位；收敛边界（保留回退层）是否成立。

---
source_design_sha256: "c179d33b585e8fa00468cc0a1efabaaf1db3ad60599135776892f29a6b652d73"
mode: "design"
---

# Review Packet — heredoc 感知 shell guard（rev 3）

## Decision

heredoc 识别单源于 _shell-lex（新 heredocSpans），guard 函数内惰性消费、lexer 缺失回退今日保守行为；quoted 正文全免疫、unquoted 正文仅替换 span 进分析、未闭合照拦；证据侧同函数修正误分段；CX evidence-collector 决策截断修复对齐 CC 模式；承接切片 2 guard 字节钉调整。guard 既有引号扫描保留为回退层（安全关键），完整合并不做——明示给审查挑战。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | quoted 正文免疫（含本会话两个活体样本重放） |
| AC2 | unquoted 正文替换 span 照拦（含 # 行首形态先红）、纯文本不拦；算术嵌套既有缺口明示排除 |
| AC3 | 同行命令不被掩吞（先红）、注释行伪声明不掩正文（先红）、正文内嵌声明不错配、多 heredoc 声明序、未闭合新增拦截、herestring/算术/引号内/转义定界/`<<-` 三形态负向、既有全回归 |
| AC4 | heredoc 单源 + 惰性载入 + 缺失回退；证据侧不误分段且未闭合哨兵不摘区间 |
| AC5 | CX >4000 掩盖管道记 unknown 与 CC 同判 |
| AC6 | 字节钉承接 + roadmap:87 与 ARCHITECTURE:85 收敛措辞修订 + 危险清单差异实写切片 9 |
| AC7 | guard/_shell-lex CC==Pi 字节、CX 同夹具同判 |

## 审查焦点（rev 3：P0-a 声明扫描上下文=注释感知+非正文行收集+单遍推进；P1-a `<<-`/终止行规则；P2-a/b 哨兵消费语义。识别层规则已穷举收口——若仍有识别类 fail-open 即同因二次）

unquoted heredoc 的 bash 展开语义（正文 $(…) 确会执行——只掩文本不掩替换是否完备）；回退路径「缺失≠放行」的证明；掩码实现会不会破坏 span 偏移使既有替换分析错位；收敛边界（保留回退层）是否成立。

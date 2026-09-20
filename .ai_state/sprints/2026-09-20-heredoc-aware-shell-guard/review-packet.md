---
source_design_sha256: "5874acf85e6e9c4b64eae4dbe5de0e1cd5d44186cb058912a0450f017628b238"
mode: "design"
---

# Review Packet — heredoc 感知 shell guard（rev 4）

## Decision

heredoc 识别单源于 _shell-lex（新 heredocSpans），guard 函数内惰性消费、lexer 缺失回退今日保守行为；quoted 正文全免疫、unquoted 正文仅替换 span 进分析、未闭合照拦；证据侧同函数修正误分段；CX evidence-collector 决策截断修复对齐 CC 模式；承接切片 2 guard 字节钉调整。guard 既有引号扫描保留为回退层（安全关键），完整合并不做——明示给审查挑战。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | quoted 正文免疫（含本会话两个活体样本重放） |
| AC2 | unquoted 正文替换 span 照拦（含 # 行首形态先红）、纯文本不拦；算术嵌套既有缺口明示排除 |
| AC3 | 同行命令与**行续逻辑行命令**不被掩吞（各先红）、注释行/跨行引号伪声明不成立、正文内嵌声明不错配、多 heredoc 声明序、未闭合新增拦截、herestring/算术/引号内/转义定界/`<<-` 三形态负向、既有全回归 |
| AC4 | heredoc 单源 + 惰性载入 + 缺失回退；证据侧不误分段、未闭合哨兵不摘区间、unquoted 畸形 span 跳过掩码（各一例钉住） |
| AC5 | CX >4000 掩盖管道记 unknown 与 CC 同判 |
| AC6 | 字节钉承接 + roadmap:87 与 ARCHITECTURE:85 收敛措辞修订 + 危险清单差异实写切片 9 |
| AC7 | guard/_shell-lex CC==Pi 字节、CX 同夹具同判 |

## 审查焦点（rev 4，同因二次后用户批准收口）：R1 逻辑行语义（行续反例封堵）/R2 命令位置成立原则（默认不触发，未枚举形态落 over-block）/R3 单遍推进正文不可见；尾随空白有意偏离标注；哨兵两条入 AC4；packet/design AC4 双射修复。

unquoted heredoc 的 bash 展开语义（正文 $(…) 确会执行——只掩文本不掩替换是否完备）；回退路径「缺失≠放行」的证明；掩码实现会不会破坏 span 偏移使既有替换分析错位；收敛边界（保留回退层）是否成立。

---
source_design_sha256: "0a672daf400cfcdece72d137d57cd775f7d4d1ab68659de74811f8dcad567313"
mode: "design"
---

# Review Packet — heredoc 感知 shell guard（rev 8 双层白名单）

## Decision

词法层白名单经 rev 7 复核全对抗通过；rev 8 补语义层白名单（用户批准）：掩码只对消费者正集 {python3, python, node, tee, cat}（首 token basename）生效，shell 解释器与一切未知包装器默认不适用——解释器 stdin 缺口（含 push 闸门绕过）结构性关闭，包装器不可枚举问题由默认拒绝消解。两层未知形态均落今日行为。quoted 掩正文；unquoted 主流逐字节不变 + 正文独立扫描并集（基线措辞已按 rev 6 复核 P1-1 更正）。六活体样本原文已落 `evidence/live-samples.md`（P1-2 闭合）。同行尾随内容判据整体取消（更窄）。AC3 改全量枚举清单（P2-1 闭合）；「分隔字符集合」问题随全匹配文法消解（P2-2 闭合）。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | 四形态最小等价样本重放放行（先红）+ 正向样本；`<<-`/终止行三细则钉；闭合后后续行照常分析双钉（P1-1）；正集成员矩阵 5 in + 1 out |
| AC2 | unquoted 并集：`# $(…)` 洞先红后拦；替换先于撇号今日拦仍拦；撇号先于替换既存放行不变（等价断言） |
| AC3 | 非窄形字节等价全量清单：七轮全部反例 + 解释器/包装器族（bash/sudo bash/bash -s/timeout bash/push 绕过）逐一新旧 analyze 输出相等（显式含 `cat <<'EOF' | bash`） |
| AC4 | 白名单判定单源 + 惰性载入 + 失败回退（缺失≠放行）；证据侧两例 |
| AC5 | CX >4000 掩盖管道记 unknown 与 CC 同判；决策全文仅落盘截 500 |
| AC6 | 字节钉承接 + 四处措辞修订 + 危险清单差异实写切片 9 |
| AC7 | guard/_shell-lex CC==Pi 字节、CX 同夹具同判 |

## 审查焦点

- **消费者正集的语义惰性（本轮核心挑战）**：python3/python/node/tee/cat 五消费者——请对抗论证其 stdin 通道是否存在 guard 今日**有意**覆盖、掩码后丢失的场景（对照 Write 工具等价性：Write 写同内容不经 guard，heredoc 扫描属偶然覆盖）。注意判据不是「正文无害」（node 可 eval、python 可 os.system）而是「guard 今日对该通道有无有意防线」。
- **TOKEN 字符集的词法惰性（rev 7 已过审，抽验即可）**：`[A-Za-z0-9_.,/=+:@%-]`、裸 `$VAR`、REDIR 形态——请对抗构造该文法内的行使 `<<` 非重定向或使正文边界异于物理行规则（如 `=` 触发赋值前缀语义、`:` 的历史算术义、`%` job spec、行尾 `-` 与 `<<-` 粘连、REDIR 的 fd 数字歧义）。任何成功构造=同因第六次，如实定级。
- 六活体样本与白名单的匹配核验（evidence/live-samples.md 白名单覆盖节）。
- unquoted 并集的三条基线断言与今日 guard 实测一致性。
- AC3 全量清单对照六轮档案（runs a3f6ebdb/3ed18ae6/fb828b78/9929ee26/08279803）无遗漏。

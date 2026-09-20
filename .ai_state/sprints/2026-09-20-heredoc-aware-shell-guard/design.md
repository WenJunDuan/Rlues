---
sprint_slug: "2026-09-20-heredoc-aware-shell-guard"
path: "System"
stage: "design"
author: "cc-main (rev 5: 同因三次后用户批准改窄核方案)"
base_commit: "a385d2e"
---

# Heredoc 感知 shell guard —— 窄核方案（Q12#14 + 切片 2 遗留两项）

## WHY

**误拦（原始痛点）**：pre-bash-guard 无 heredoc 语义（`findSubstitutions` CC:56-94），正文奇数反引号/未闭 `$(` → unparsable 拦截；`<<'EOF'` 正文举例的危险命令文本被当真命令拦。本会话累计 **6 次活体误拦**，全部形态为「首行单声明 + quoted 定界符」。
**现存放行洞（rev 2 复核发现）**：`analyze` 先跑 `stripComments`，unquoted 正文行首 `#` 后的命令替换 bash 真执行、guard 却剥掉 → 放行。
**方案史（4 轮审查、同因 P0×3，全档案在 reviews/）**：全规则路线每轮收口一层 bash 词法就再露一层（行续、注释行、双引号内反斜杠、跨行引号、终止行匹配层）。根因：掩码区间端点依赖对 bash 命令行词法的完整建模，「自信地错」即 fail-open。用户裁决改**窄核**：只在词法平凡到可machineProve的形态上生效，其余一切保持今日行为——安全论证从「枚举文法」变为「非窄形=字节等价于今日」，封闭。
**切片 2 遗留②**：CX `evidence-collector.py:117` 决策前 4000 字符预截断（CC 已修模式=决策全文、落盘截 500）。
**交叉项**：切片 2 字节钉测试（`test_state_review.py:1210`）钉三端 guard 字节，本切片合法改 guard 必红，承接调整。

## HOW

### 窄形判定 `simpleHeredoc(command)`（单源 `_shell-lex`，CX `simple_heredoc`）

窄形 = 以下**全部**成立，任何一条不成立 ⇒ 不适用 ⇒ guard 与证据侧行为与今日**逐字节相同**：

1. 声明在**第一物理行**（首行必然是命令位置——之前不存在任何可延续的引号/注释/续行状态，端点起点无需建模）。
2. 首行恰含一个 `<<`（或 `<<-`），非 `<<<` 的一部分；定界符紧随（可 `'D'`/`"D"`/裸 `D`，名=去引号后的字面）。
3. 首行除定界符自身引号外**无**任何引号字符、无反斜杠、无 `#`、无反引号、无 `$(`（`$VAR` 允许——不影响行词法边界）。
4. 终止行 = **物理行**与定界符名全等（`<<-` 额外允许并剥离前导 tab；允许尾随 `\r`）；存在于命令内。未闭合 ⇒ 不适用（今日行为，不新增拦截）。
5. 正文 = 首行行尾换行之后至终止行前一行。终止行之后的所有行 = 命令上下文，照常分析。

### 窄形生效语义

- **quoted 定界符**：正文整体等长空白掩码（保留换行），先于 `stripComments` 作用于原始 command；正文不进替换扫描与危险模式（bash 不展开，纯 stdin 文本）。
- **裸定界符（unquoted）**：正文**不掩码**（文本照今日保守扫描，over-block 侧），但正文行**豁免 stripComments**（封现存放行洞：行首 `#` 后的 `$(…)` bash 真执行，必须进入替换分析）。
- 递归层（`analyze` depth>0 的子命令）同规则。
- guard 消费：函数内惰性 require；载入失败/运行期异常 ⇒ 跳过（今日行为）；guard 内不得新增任何 fail-open 分支；顶层不加 require（ARCHITECTURE 惰性载入决策）。
- 证据侧：`_shell-lex.scan` 对窄形 quoted 正文豁免控制符分段；非窄形不变。

### 其余交付（与前版相同）

- **CX 截断修复**：`evidence-collector.py` 分类/策略吃未截断 command，仅落盘截 500；删 `:117` 4000 预截。
- **字节钉承接与记账**：删「guard 字节不变」断言，CC==Pi parity 与 gate-sans-lexer fail-closed 独立保留；roadmap:87 与 ARCHITECTURE:85 措辞修订为「heredoc 窄核单源 `_shell-lex`（词法平凡形态），guard 自有扫描保留，全文法建模经 4 轮审查证伪后放弃」；CC/CX 危险清单差异实写切片 9 notes。

## 允许写集

`vibeCoding/claude/9.9.9/.claude/hooks/{_shell-lex.cjs,pre-bash-guard.cjs}` + Pi `plugin/extensions/cc-core/` 同名两件（字节同改）；`vibeCoding/codex/9.9.9/.codex/hooks/{_shell_lex.py,pre-bash-guard.py,evidence-collector.py}`；`vibeCoding/scripts/tests/athena999/`：新建 `test_heredoc_guard.py`、`test_state_review.py` 仅改字节钉断言。`.ai_state/` 记账。
Non-goals：不建模 bash 完整命令行词法（4 轮审查证伪）；不统一 CC/CX 危险清单差异（切片 9）；不做扫描器完整合并；不动 delivery-gate 与 CC/Pi evidence-collector.cjs；未闭合 heredoc 不新增拦截。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | 窄形 quoted 正文免疫：本会话 6 个活体误拦样本原文重放全部放行（先红）；正文含奇数反引号/未闭 `$(`/危险命令文本均不拦（真实 hook 进程） |
| AC2 | 窄形 unquoted 正文豁免注释剥离：行首 `#` 后危险替换今日放行、改后拦（先红）；正文其余文本仍按今日保守扫描 |
| AC3 | 非窄形字节等价：4 轮审查全部对抗反例（行续、双引号内反斜杠、跨行引号、注释行伪声明、正文内嵌声明、多 heredoc、`<<<`、算术左移、引号内字面、转义定界 `<<\EOF`、声明行带引号参数、非首行声明、未闭合）逐一断言新旧 guard `analyze` 输出**完全相等**（机械矩阵，非语义推演） |
| AC4 | 窄形判定单源 `_shell-lex` + 函数内惰性载入 + 载入失败/运行期异常回退今日行为（缺失≠放行用例）；证据侧窄形豁免与非窄形不变各一例 |
| AC5 | CX 决策截断修复：>4000 字符被掩盖管道回归用例 CX 记 unknown 与 CC 同判；分类/策略吃全文仅落盘截 500 |
| AC6 | 字节钉承接 + 记账：断言调整如 HOW；roadmap:87 与 ARCHITECTURE:85 措辞修订（窄核+证伪记录）；危险清单差异实写切片 9 notes |
| AC7 | 三端一致：guard 与 `_shell-lex` 的 CC==Pi 字节相等；CX 行为同夹具判定与 CC 一致 |

## 测试场景

1. 活体样本 ×6 原文重放（先红）；2. unquoted `#` 行首洞先红后拦；3. **非窄形等价矩阵**（≥13 形态，新旧输出逐一相等）；4. lexer 缺失/异常回退；5. 证据侧窄形/非窄形各一例；6. CX 长命令截断先红；7. 字节钉调整后全套绿。

## 风险

窄形判定本身出错的两个方向：误判窄（漏掩）=维持今日误拦，无安全损失；误判宽（多掩）由第 1/3 条的首行+无引号残留约束封死——首行不存在前置词法状态，是本方案唯一需要 machineProve 的断言，review 重点挑战之。

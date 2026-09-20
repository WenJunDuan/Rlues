---
sprint_slug: "2026-09-20-heredoc-aware-shell-guard"
path: "System"
stage: "design"
author: "cc-main (rev 3: 3ed18ae6 REWORK 全落实; 识别层规则收口)"
base_commit: "a385d2e"
---

# Heredoc 感知 shell guard（Q12#14 + 切片 2 遗留两项）

## WHY（勘查已核，本会话两次活体复现）

**现存放行漏洞（review P0-2 发现）**：analyze 先跑 stripComments，而 heredoc 正文无注释语义——unquoted 正文中行首 # 的危险命令替换 bash 真执行（实测），今日 guard 却整段剥掉 → **放行**。本切片必须修。
**pre-bash-guard 无 heredoc 语义**（CC `.cjs` == Pi 字节同；CX `.py` 同构）：`findSubstitutions`（CC:56-94）对整条命令做引号感知 `$(`/反引号扫描，heredoc 正文被当普通字符流。正文奇数反引号或未闭合 `$(` → `end:-1` → `analyze` 抛「unparsable command substitution」（本会话两次误拦实录）；`<<'EOF'` 引号定界正文按 bash 规范不展开，但正文里举例的 `$(rm -rf /)` 仍被递归分析成「recursive force removal」误拦（勘查实测复现）。分段器（`tokenize`/`commandSegments` CC:118-163）同样不识别 `<<`。
**证据侧同病**：`_shell-lex` 头注明写 no heredocs——heredoc 正文里的 `|`/`&&` 会被当控制符误分段，影响 validationStatusPolicy 判定。
**切片 2 遗留①**：两个引号感知扫描器并存（_shell-lex 只服务证据；guard 分段器独立），收敛指名本切片。
**切片 2 遗留②**：CX `evidence-collector.py:117` 在 `classify_evidence`/`validation_status_policy` 之前把 command 截到 4000 字符，长命令的 `| tail -8` 被截掉 → 掩盖管道误记 pass；CC 已修模式=决策吃全文、仅落盘截 500（`.cjs:97-124` 注释明言）。
**交叉项**：切片 2 的 `test_ac5_guards_unchanged_pi_parity_and_gate_blocks_without_shell_lex` 断言①三端 guard 字节不变——本切片合法改 guard 必红，承接调整（同切片 4 承接切片 3 字节钉的先例）。

## HOW

- **heredoc 识别单一来源**：`_shell-lex` 新增 `heredocSpans(command)`（CX `heredoc_spans`），语义规则写死（review P0/P1 全落实）：
  - 定界符带**任意**引用或转义（单引/双引/反斜杠/部分引用）⇒ quoted（bash 不展开）；纯裸 ⇒ unquoted。
  - herestring（三个 `<`）不是 heredoc；`<<` 须引号/转义/算术上下文感知（算术左移、引号内字面 `<<` 不触发）。
  - **bodyStart = 定界符所在命令行行尾换行之后**；同行剩余部分（含管道后命令）永不进掩码；多 heredoc 按声明序依次占用后续行。
  - **`<<-` 与终止行匹配（rev 3, P1-a）**：`<<-` 的终止行允许并剥离前导 tab（仅 tab，非空格），`<<` 不剥；终止行允许尾随空白与 CRLF 的 `\r`（均视为闭合，不判未闭合）；定界符名从 `-` 之后取（`<<-EOF` 定界符是 EOF 不是 -EOF）。缩进脚本 `cat <<-EOF` + tab 缩进正文/终止行、`EOF ` 尾随空格、CRLF 三形态今日放行、rev 3 后仍放行（负向用例）。
  - 未闭合（无合法终止定界符行）⇒ 哨兵 → guard **新增** fail-closed 拦截（基线实测今日不拦；理由：bash 侧即语法错误，无合法用例）。
  - **哨兵消费语义（rev 3, P2-a/P2-b）**：unquoted 正文内的未闭合替换（奇数反引号/未闭 `$(`）按畸形 span 处理→整条命令跳过掩码=今日行为（over-block 方向）；证据侧 `scan` 拿到未闭合哨兵时**不摘除任何区间**（整条按今日语义处理），不做「摘到串尾」的猜测。
- **guard 消费（函数内惰性 require + 回退今日行为）**：掩码作用于**原始 command、先于 stripComments**（review P0-2 定序：偏移在原始串上一次性成立，unquoted 正文区间内禁注释剥离）；掩码原语=**等长空白置换、保留换行**（不改长度不改分段）。quoted 正文整体掩空；unquoted 正文仅保留命令替换 span（含反引号）供替换分析，其余文本掩空。递归层（analyze depth>0）同样掩码。heredocSpans 载入失败**或运行期异常/畸形 span**：同一 try 内跳过掩码=今日保守行为（over-block 方向），guard 内不得出现任何新的 fail-open 分支；顶层不加 require（ARCHITECTURE 惰性载入决策）。
- **证据侧**：`_shell-lex.scan` 用同一 spans 把 heredoc 正文从控制符扫描中摘除（quoted 与 unquoted 正文中的 `|`/`&&` 都不是控制符——它们是 stdin 文本）。
- **收敛边界（明示给 review 挑战）**：heredoc 逻辑单源于 _shell-lex；guard 既有引号扫描（stripComments/findSubstitutions）保留为回退层不删——它是安全关键 hook 在 lexer 缺失时的唯一屏障（切片 2 遗留的 REQUIRED_ASSETS 缺口归切片 9）。完整大合并不做。
- **CX 截断修复**：`evidence-collector.py` 决策路径吃未截断 command（对齐 CC 已修模式），仅 `:153` 落盘截 500；删 `:117` 的 4000 预截。
- **字节钉承接与记账（review P1-3/P2-4）**：删「guard 字节不变」断言，CC==Pi parity 与 gate-sans-lexer fail-closed 独立保留；roadmap:87 与 ARCHITECTURE:85 的「收敛到同一模块」措辞同步修订为「heredoc 逻辑单源 _shell-lex，guard 引号扫描保留为 lexer 缺失回退层（安全关键可用性），完整合并不做」；CC/CX 危险清单既有差异（mariadb/dash/ksh/fork-bomb）实写进 roadmap 切片 9 notes。

## 允许写集

`vibeCoding/claude/9.9.9/.claude/hooks/{_shell-lex.cjs,pre-bash-guard.cjs}` + Pi `plugin/extensions/cc-core/` 同名两件（字节同改）；`vibeCoding/codex/9.9.9/.codex/hooks/{_shell_lex.py,pre-bash-guard.py,evidence-collector.py}`；`vibeCoding/scripts/tests/athena999/`：新建 `test_heredoc_guard.py`、`test_state_review.py` 仅改字节钉断言。`.ai_state/` 记账。
Non-goals：不统一 CC/CX 危险清单既有差异（mariadb/dash/ksh/fork-bomb → 记切片 9）；不做扫描器完整合并；不动 delivery-gate；不动 CC/Pi evidence-collector.cjs（已修）。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | quoted heredoc 正文免疫：奇数反引号、未闭合 `$(`、危险命令举例文本均不再拦（真实 hook 进程端到端，含本会话两个活体样本原文重放） |
| AC2 | unquoted 正文替换分析：命令替换与反引号照拦，**含正文行以 `#` 开头的形态**（今日被注释剥离放行，先红后拦）；纯文本命令字样不拦；算术嵌套既有缺口明示排除（不隐含展开语义完备） |
| AC3 | 命令位置 fail-closed：定界符同行危险命令照拦（先红：掩码不得吞同行）；**注释行伪声明不掩正文**（`# cat` 前缀 + 次行危险命令今日拦、改后必须仍拦，先红判据）；**正文内嵌字面声明不错配边界**；多 heredoc 声明序；未闭合新增拦截；herestring/算术左移/引号内字面/转义定界负向；**`<<-` tab 剥离、终止行尾随空白、CRLF 三形态不误拦**；既有危险模式全回归 |
| AC4 | heredoc 识别单源 `_shell-lex`：guard 以函数内惰性载入消费，lexer 缺失时回退今日行为（用例证明缺失≠放行）；证据侧 heredoc 正文控制符不再误分段 |
| AC5 | CX 决策截断修复：>4000 字符被掩盖管道回归用例 CX 记 unknown 与 CC 同判；分类/策略吃全文仅落盘截 500 |
| AC6 | 字节钉承接 + 记账三件：断言调整如 HOW；roadmap:87 与 ARCHITECTURE:85 收敛措辞修订；危险清单差异实写切片 9 notes |
| AC7 | 三端一致：guard 与 _shell-lex 的 CC==Pi 字节相等；CX 行为同夹具判定与 CC 一致 |

## 测试场景

1. 活体样本重放（含本轮返工脚本再次被拦的第 5 例，先红）；2. quoted/unquoted 矩阵含 # 行首正文先红；3. 同行命令/注释行伪声明/正文内嵌声明/多 heredoc/未闭合/herestring/算术/引号内/转义定界/`<<-` 三形态负向全套；4. lexer 缺失与运行期异常回退各一例（缺失≠放行）；5. 证据侧 heredoc 分段矩阵；6. CX 长命令截断先红；7. 字节钉调整后全套绿。

## 风险

guard 是唯一危险命令屏障——掩码方向只许放行「正文文本」，定界符行与命令位置一律照旧；review 重点挑战 unquoted 展开语义与回退路径。

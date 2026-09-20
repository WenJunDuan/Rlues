---
sprint_slug: "2026-09-20-heredoc-aware-shell-guard"
path: "System"
stage: "design"
author: "cc-main"
base_commit: "a385d2e"
---

# Heredoc 感知 shell guard（Q12#14 + 切片 2 遗留两项）

## WHY（勘查已核，本会话两次活体复现）

**pre-bash-guard 无 heredoc 语义**（CC `.cjs` == Pi 字节同；CX `.py` 同构）：`findSubstitutions`（CC:56-94）对整条命令做引号感知 `$(`/反引号扫描，heredoc 正文被当普通字符流。正文奇数反引号或未闭合 `$(` → `end:-1` → `analyze` 抛「unparsable command substitution」（本会话两次误拦实录）；`<<'EOF'` 引号定界正文按 bash 规范不展开，但正文里举例的 `$(rm -rf /)` 仍被递归分析成「recursive force removal」误拦（勘查实测复现）。分段器（`tokenize`/`commandSegments` CC:118-163）同样不识别 `<<`。
**证据侧同病**：`_shell-lex` 头注明写 no heredocs——heredoc 正文里的 `|`/`&&` 会被当控制符误分段，影响 validationStatusPolicy 判定。
**切片 2 遗留①**：两个引号感知扫描器并存（_shell-lex 只服务证据；guard 分段器独立），收敛指名本切片。
**切片 2 遗留②**：CX `evidence-collector.py:117` 在 `classify_evidence`/`validation_status_policy` 之前把 command 截到 4000 字符，长命令的 `| tail -8` 被截掉 → 掩盖管道误记 pass；CC 已修模式=决策吃全文、仅落盘截 500（`.cjs:97-124` 注释明言）。
**交叉项**：切片 2 的 `test_ac5_guards_unchanged_pi_parity_and_gate_blocks_without_shell_lex` 断言①三端 guard 字节不变——本切片合法改 guard 必红，承接调整（同切片 4 承接切片 3 字节钉的先例）。

## HOW

- **heredoc 识别单一来源**：`_shell-lex` 新增 `heredocSpans(command)`（CX `heredoc_spans`）：识别 `<<`/`<<-` + 裸/单引/双引定界符，返回 [{bodyStart, bodyEnd, quoted}]；未闭合（无终止定界符）返回哨兵。CC 与 Pi 字节同改。
- **guard 消费（函数内惰性 require + 回退今日行为）**：预处理把 quoted heredoc 正文整体掩空、unquoted 正文仅保留其中 `$(…)`/反引号 span 供替换分析（bash 会真实展开执行它们），正文其余文本不进分段与危险模式匹配；未闭合 heredoc → 维持「unparsable」拦截。lexer 载入失败 → 跳过掩码=今日保守行为（over-block 方向），遵守 ARCHITECTURE「_shell-lex 惰性载入」既有决策，guard 顶层不加 require。
- **证据侧**：`_shell-lex.scan` 用同一 spans 把 heredoc 正文从控制符扫描中摘除（quoted 与 unquoted 正文中的 `|`/`&&` 都不是控制符——它们是 stdin 文本）。
- **收敛边界（明示给 review 挑战）**：heredoc 逻辑单源于 _shell-lex；guard 既有引号扫描（stripComments/findSubstitutions）保留为回退层不删——它是安全关键 hook 在 lexer 缺失时的唯一屏障（切片 2 遗留的 REQUIRED_ASSETS 缺口归切片 9）。完整大合并不做。
- **CX 截断修复**：`evidence-collector.py` 决策路径吃未截断 command（对齐 CC 已修模式），仅 `:153` 落盘截 500；删 `:117` 的 4000 预截。
- **字节钉承接**：删该测试中「guard 字节不变」断言；保留 CC==Pi parity（guard/_shell-lex/_input-binding）与 gate-sans-lexer fail-closed 断言，独立成名。

## 允许写集

`vibeCoding/claude/9.9.9/.claude/hooks/{_shell-lex.cjs,pre-bash-guard.cjs}` + Pi `plugin/extensions/cc-core/` 同名两件（字节同改）；`vibeCoding/codex/9.9.9/.codex/hooks/{_shell_lex.py,pre-bash-guard.py,evidence-collector.py}`；`vibeCoding/scripts/tests/athena999/`：新建 `test_heredoc_guard.py`、`test_state_review.py` 仅改字节钉断言。`.ai_state/` 记账。
Non-goals：不统一 CC/CX 危险清单既有差异（mariadb/dash/ksh/fork-bomb → 记切片 9）；不做扫描器完整合并；不动 delivery-gate；不动 CC/Pi evidence-collector.cjs（已修）。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | quoted heredoc 正文免疫：奇数反引号、未闭合 `$(`、危险命令举例文本均不再拦（真实 hook 进程端到端，含本会话两个活体样本原文重放） |
| AC2 | unquoted heredoc 正文：其中 `$(…)`/反引号仍进替换分析（危险替换照拦），纯文本命令字样不拦 |
| AC3 | 命令位置 fail-closed 不变：heredoc 前后段与同行真实危险命令照拦；未闭合 heredoc 照拦（unparsable）；既有危险模式全回归 |
| AC4 | heredoc 识别单源 `_shell-lex`：guard 以函数内惰性载入消费，lexer 缺失时回退今日行为（用例证明缺失≠放行）；证据侧 heredoc 正文控制符不再误分段 |
| AC5 | CX 决策截断修复：>4000 字符被掩盖管道回归用例 CX 记 unknown 与 CC 同判；分类/策略吃全文仅落盘截 500 |
| AC6 | 切片 2 字节钉承接：「guard 字节不变」断言删除，CC==Pi parity 与 gate-sans-lexer fail-closed 独立保留全绿；roadmap 承接清单同步更正 |
| AC7 | 三端一致：guard 与 _shell-lex 的 CC==Pi 字节相等；CX 行为同夹具判定与 CC 一致 |

## 测试场景

1. 活体样本重放 ×2（先红）；2. quoted/unquoted 正向负向矩阵；3. 未闭合 heredoc 与命令位置回归；4. lexer 缺失回退用例；5. 证据侧 heredoc 分段矩阵入 POLICY 系列；6. CX 长命令截断先红；7. 字节钉调整后全套绿。

## 风险

guard 是唯一危险命令屏障——掩码方向只许放行「正文文本」，定界符行与命令位置一律照旧；review 重点挑战 unquoted 展开语义与回退路径。

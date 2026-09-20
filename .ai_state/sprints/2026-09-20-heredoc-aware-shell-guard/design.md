---
sprint_slug: "2026-09-20-heredoc-aware-shell-guard"
path: "System"
stage: "design"
author: "cc-main (rev 7: 同因五次后用户批准白名单式窄形)"
base_commit: "a385d2e"
---

# Heredoc 感知 shell guard —— 白名单窄形（Q12#14 + 切片 2 遗留两项）

## WHY

**误拦（原始痛点）**：pre-bash-guard 无 heredoc 语义，正文奇数反引号/未闭 `$(`/危险命令示例文本被误拦。本会话 6 次活体误拦（4 形态，原文已落 `evidence/live-samples.md`），首行全部为「WORD 序列 + 行尾 quoted 定界符」。
**现存放行洞**：`analyze` 先跑 `stripComments`，unquoted 正文行首 `#` 后的命令替换 bash 真执行、guard 剥掉 → 放行。
**方案史（6 轮审查、同因 P0×5，档案 reviews/）**：全文法建模 → 窄核黑名单，黑名单三次被「未知 bash 词法」攻破（算术 `((`/`$[`/下标、`${v:-…}` 展开体字面、`${v:offset}` 算术偏移）。根因恒定：否定式论证要求穷举 bash 文法，穷举必漏。用户裁决改**白名单**：窄形只能由一条封闭文法产生，未知语法=不匹配=今日行为，**fail-open 不可构造**。
**切片 2 遗留②**：CX `evidence-collector.py:117` 决策前 4000 字符预截断（CC 已修模式=决策全文、落盘截 500）。
**交叉项**：切片 2 字节钉测试（`test_state_review.py:1210`）本切片合法改 guard 必红，承接调整。

## HOW

### 白名单窄形 `simpleHeredoc(command)`（单源 `_shell-lex`，CX `simple_heredoc`）

**首行必须全匹配以下封闭文法（锚定行首行尾），否则不适用 ⇒ 三端行为与今日逐字节相同：**

```
LINE  = TOKEN (SP+ TOKEN)* SP* '<<' '-'? SP* DELIM SP* EOL
TOKEN = WORD | VAR | REDIR
WORD  = [A-Za-z0-9_.,/=+:@%-]+
VAR   = '$' [A-Za-z_][A-Za-z0-9_]*          （裸变量，无花括号——展开在运行期不改行词法边界，rev 5 复核实测）
REDIR = [0-9]? ('>' | '>>') (WORD | '&' [0-9])?   或  [0-9]? '<' WORD
DELIM = "'" NAME "'" | '"' NAME '"' | NAME  ；NAME = [A-Za-z_][A-Za-z0-9_]*
```

- 定界符在**行尾**（其后仅空白）——同行尾随内容一律不适用（rev 5/6 的同行判据整体取消，更窄更简单）。
- 文法中**不存在** `{ } ( ) [ ] $( ` 反引号 \ # ; | &` 与任何展开操作符 ⇒ 六轮攻破的全部形态（算术、展开体、行续、注释、跨行引号、多命令、管道）在入口即不匹配。
- 引号定界（单/双）⇒ quoted；裸 NAME ⇒ unquoted。
- 正文/终止行按**物理行**：终止行与 NAME 全等（`<<-` 额外允许并剥离前导 tab——仅 tab；允许尾随 `\r`；尾随空格不构成闭合，与 bash 一致）。未闭合 ⇒ 不适用（不新增拦截）。
- 终止行之后的行 = 命令上下文，照常分析。

**安全论证（一条文法事实替代枚举）**：该文法的首行不含任何算术求值入口（无 `(`/`[`/`$((`/`$[`）、不含参数展开体（无 `${`）、不含引号/转义/注释/命令分隔——bash 对此形状的行只有一种解析：词序列 + heredoc 重定向。未知与未来语法不可能进入窄形，失败方向恒为「维持今日误拦」。

### 窄形生效语义

- **quoted**：正文整体等长空白掩码（保留换行），先于 `stripComments` 作用于原始 command；正文不进替换扫描与危险模式。
- **unquoted——并集结构**：主扫描流**逐字节不变**（今日拦的机械保留）；**额外**将正文以独立字符串、干净词法态单独跑替换扫描，检出危险并入。检出集只增不减（封 `# $(…)` 放行洞）。基线事实（rev 6 复核 P1-1 更正）：撇号先于替换的正文**今日已放行**，本结构不改变之（非本切片引入，主流不变即无新放行）；替换先于撇号的正文今日拦、继续拦（钉）。
- 递归层（depth>0）同规则。guard 函数内惰性 require；载入失败/运行期异常 ⇒ 跳过=今日行为；无新 fail-open 分支；顶层不加 require。
- 证据侧：`_shell-lex.scan` 对窄形 quoted 正文豁免控制符分段；其余不变。

### 其余交付

- **CX 截断修复**：分类/策略吃未截断 command，仅落盘截 500；删 `:117` 4000 预截。
- **字节钉承接与记账**：删「guard 字节不变」断言，CC==Pi parity 与 gate-sans-lexer fail-closed 独立保留；措辞修订四处（`roadmap.md:87`、`ARCHITECTURE.md:85`、`roadmap.md:73` 验收列、`items.yaml:60` notes）为「白名单窄形单源 `_shell-lex`；黑名单与全文法路线经六轮审查证伪，档案在 sprint reviews/」；CC/CX 危险清单差异实写切片 9 notes。

## 允许写集

`vibeCoding/claude/9.9.9/.claude/hooks/{_shell-lex.cjs,pre-bash-guard.cjs}` + Pi `plugin/extensions/cc-core/` 同名两件（字节同改）；`vibeCoding/codex/9.9.9/.codex/hooks/{_shell_lex.py,pre-bash-guard.py,evidence-collector.py}`；`vibeCoding/scripts/tests/athena999/`：新建 `test_heredoc_guard.py`、`test_state_review.py` 仅改字节钉断言。`.ai_state/` 记账。
Non-goals：不建模 bash 文法（白名单外一律不适用）；不统一 CC/CX 危险清单差异（切片 9）；不做扫描器合并；不动 delivery-gate 与 CC/Pi evidence-collector.cjs；未闭合不新增拦截；既存「奇数引号遮蔽」底层缺陷不修（主流不变原则，记 roadmap 观察）。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | 白名单窄形 quoted 免疫：`evidence/live-samples.md` 四形态原文重放全放行（先红），`tee`/`cat` 正向样本同放行；`<<-` 仅剥 tab、终止行尾随空格不闭合、尾随 `\r` 闭合（正向钉） |
| AC2 | unquoted 并集：`# $(危险替换)` 正文今日放行、改后拦（先红）；替换先于撇号的正文今日拦、改后仍拦（主流不变钉）；撇号先于替换=今日已放行的既存缺陷不因本切片改变（等价断言） |
| AC3 | 非窄形字节等价矩阵（**全量枚举清单**，不写 ≥N）：六轮审查全部反例——五算术逃逸、`${v:-<<'a' }` 展开体、`${v:1<<'a' }` 偏移、行续、双引号内行尾反斜杠、跨行引号、注释行伪声明、内嵌声明、多 heredoc、双声明、`<<<`、转义定界、`<<'EOF'x` 残留、非首行声明、未闭合、同行尾随内容、管道/分号/花括号/反引号首行——逐一断言新旧 `analyze` 输出完全相等 |
| AC4 | 白名单判定单源 `_shell-lex` + 函数内惰性载入 + 载入失败/运行期异常回退（缺失≠放行）；证据侧窄形 quoted 豁免与非窄形不变各一例 |
| AC5 | CX 决策截断修复：>4000 字符被掩盖管道回归用例 CX 记 unknown 与 CC 同判；分类/策略吃全文仅落盘截 500 |
| AC6 | 字节钉承接 + 四处措辞修订 + 危险清单差异实写切片 9 notes |
| AC7 | 三端一致：guard 与 `_shell-lex` 的 CC==Pi 字节相等；CX 行为同夹具判定与 CC 一致 |

## 测试场景

1. 活体四形态 + 两正向样本重放（先红）；2. unquoted 洞先红后拦 + 主流不变双钉；3. 非窄形等价全量清单；4. lexer 缺失/异常回退；5. 证据侧两例；6. CX 截断先红；7. 字节钉调整后全套绿。

## 风险

白名单唯一可错方向=文法写宽（TOKEN 字符集混入词法活性字符）。字符集 `[A-Za-z0-9_.,/=+:@%-]` 与 `$` 裸变量逐字符核过 bash 词法惰性（无 glob 活性的 `*?` 已排除，`~` 展开已排除）；review 对抗验证该字符集。误判窄=维持今日误拦，零安全损失。

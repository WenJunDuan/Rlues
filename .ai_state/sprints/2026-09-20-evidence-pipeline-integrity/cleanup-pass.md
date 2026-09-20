---
sprint_slug: "2026-09-20-evidence-pipeline-integrity"
created: "2026-09-20"
path: "System"
polish_worker: "a51be2798be70997a"
---

# Cleanup Pass — evidence-pipeline-integrity

实现由外部执行器 grok 写成，因此本轮是该代码第一次经过 Claude 侧清理。主 agent 已现场复核 polish worker 的每一条结论。

## 5 检查项

### 1. 临时代码 / 调试痕迹

六个源文件无 `console.log` / `print` / `debugger` / 无号 TODO。

一处真实问题已修：`test_ac5_…` 原本把**已发布的** `_shell-lex.cjs` / `_shell_lex.py` 改名成 `.hidden` 再在 `finally` 还原。运行被强杀或机器重启就会让发行包缺失 lexer，而 `REQUIRED_ASSETS` 并不列这个模块，`managed_complete()` 仍会把该 home 判为完整，此后所有验证静默降级为 `unknown`。改为把 hook 目录复制到临时目录、从副本中删除；并把 `if path.exists()` 守卫换成 `unlink()`，避免 lexer 已缺失时该回归静默空跑。

### 2. 注释完整性

四处真实缺口已补：

- 惰性 `require` / `import` 是本切片的核心不变量，三端原本**一条注释都没有**。任何人「顺手整理 import」把它提到模块层，就会让三端 ship 门禁变宽松。现已在调用点注明原因。
- `validationStatusPolicy` / `validation_status_policy` 是导出的公开 API，带三条件规则与固定 reason 枚举，原无 docstring，已补。
- CC 的 `_shell-lex.cjs` 零注释，而 CX 孪生文件有模块 docstring；`&` 与重定向之争是该模块的尖刺，已补模块头与规则说明并双端对齐。
- `evidence-collector.cjs` 中新语句被插进了 `// F3 (2026-07-29, W35)` 注释与它所解释的 `appendEvidence` 之间，导致该注释错位解释了策略行。已按 doc-style「注释在被解释行的上面」移正。

### 3. 冗余 / 重复代码

一处已修：CC 收集器把降级条件写了两遍（`status === "pass" && policy.provable === false` 与 `result === "unknown" && status === "pass"`），两者一旦漂移即出错。合并为单个 `downgraded` 常量，同时与 CX 形状一致。

一处**有意保留**：binding 里的 `words()` / `_words()` 与 `_shell-lex` 的引号/转义状态机重复，但语义不同（`words` 去引号按空白切，`scan` 保留引号按控制符切）。合并会迫使 `words` 走到惰性 require 之后，或把 lexer 提上模块加载路径——后者正是本切片要消灭的故障。design 已把 scanner 收敛指派给切片 8。

### 4. 低效模式

无实际问题。`pipefailBefore` 对每个验证段重扫前序段，但 n 是单行 shell 的段数，且策略每次 Bash PostToolUse 只跑一次。AC5 新增的 `copytree` 每次套件运行复制约 700 KB，实测总耗时不变（前后均 18.3s）。

### 5. 过度设计与过度防御

一处真实问题已修，且是**安全方向**的：CX 收集器用 `policy.get("provable")` / `policy.get('reason')` 读同包函数返回的 dict。键一旦漂移，`.get` 返回 `None`，`is False` 为假，记录**静默保持 `result: pass`**——恰好在本切片要封的那条轴上 fail-open。改为下标访问，漂移即抛错，由收集器的边界处理丢弃该条记录（fail-closed）。

未误判为过度防御：惰性加载外的 `catch (_)` / `except Exception` 是真实信任边界（部分升级的 home 可能没有该模块），且设计明文要求此时返回不可证。reason 枚举经 grep 确认恰为三值；`result_reason` 两端均以硬编码 key 字面量输出、仅值转义；全切片未新增配置项、flag 或扩展点。

## 额外验证（超出套件）

polish worker 另跑了三项，主 agent 认为值得留档：

- **lexer 双端差分模糊测试**：字母表 `a ; | & < > ' " \ \n` 上全部长度 ≤4 的串，加 2 万条随机串，加设计矩阵与全部重定向形式（`2>&1`、`>&2`、`<&0`、`&>`、`&>>`、`|&`、`a\&b`、未闭合引号、尾随反斜杠），共 36,132 条输入，段文本与 operator **0 处不一致**。
- **策略双端差分模糊测试**：30,015 条生成的复合命令（片段 × `; && || | |& 换行 &`，含 `set` 开关顺序、`FOO=1 npm test`、`/usr/bin/set`、`set --`、`set -o noglob`），判定与 reason **0 处不一致**。AC3 的双端一致性是实测出来的，不只是看出来的。
- **惰性 require 不变量的变异测试**：临时把 `require` 提到 CC + Pi 的模块加载层，单跑 AC5，确实失败并报 `Cannot find module './_shell-lex.cjs' ... delivery-gate.cjs`，证明该回归真能抓住 fail-open。文件已还原并复验字节同一。

## Finishing-a-development-branch

- [x] `python3 -m unittest vibeCoding.scripts.tests.athena999.test_state_review`：polish 前后均 39/39 PASS（裸跑，无管道）。
- [x] `git diff --exit-code 52ff57eb -- <三端 guard>`：clean。
- [x] Pi `cc-core` 三文件与 CC 原件 `cmp` 字节同一。
- [x] 五个 `.cjs` 过 `node --check`，四个 `.py` 过 `py_compile`。
- [x] 未 merge、未 push、未开 PR、未删 worktree。
- [x] 下一动作是一次独立 implementation review。

## 遗留风险（主 agent 认可并记录）

1. **`_shell-lex` 不在 `setup-athena.py` 的 `REQUIRED_ASSETS`**（`:136-148`）。全新安装无碍（安装器 rglob 整棵 hooks 树），但一个已有 9.9.9 home 若拿到新 `_input-binding` 而没有 lexer，`managed_complete()` 仍判其完整，此后所有验证记 `unknown`。方向是**永久卡住交付而非假通过**，不是安全漏洞。不在本切片文件计划内，转 roadmap 切片 9（发行一致性）跟进。
2. **AC5 硬编码 commit `52ff57eb`**，浅克隆或改写历史的仓库中该测试会失败。设计明文要求，保留。
3. **`npm test & echo ok`** 得到 `validation_status_not_reported` 而非 `validation_backgrounded`：被后台化的是**段**不是**行**。两端一致（模糊测试确认），判定仍为不可证，AC2/AC3 成立；仅 reason 标签相对 3→2→1 顺序可争。未改。
4. **`words()` 的空白字符类**：CC 用 JS `/\s/`，CX 用 `str.isspace()`，在少数非 ASCII 字符上不一致。3 万条模糊测试无 ASCII 分歧；未做归一化 helper，因为那是无真实调用方的代码（铁律[反过度工程]）。

## 归档到 compound/

已新增 `compound/2026-09-20-learning-self-mutating-regression-test.md`：自我变异型回归测试用一个持久故障模式换取便利，应改为复制目录后删副本，并用 `unlink()` 而非 `if exists()` 守卫，免得回归静默停止覆盖它要防的路径。

## VERDICT

PASS：五项检查完成，两处行为相关修复（CX fail-open、AC5 自变异）均已复核；测试 39/39 绿，guard 与 Pi 字节不变量成立。

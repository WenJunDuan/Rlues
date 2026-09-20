---
sprint_slug: "2026-09-20-review-binding-preflight"
created: "2026-09-20"
path: "System"
polish_worker: "af7756a086abef988"
---

# Cleanup Pass — review-binding-preflight

实现由外部执行器 grok 写成，本轮是该代码第一次经过 Claude 侧清理。主 agent 已现场复核每一条结论与全部不变量。

## 5 检查项

### 1. 临时代码 / 调试痕迹

无实际问题。改动的 hook 与测试中无 `console.log` / `debugger` / 游离 `print`；`_review_binding.py:381,383` 的两处 `print` 是 CLI 本身的 stdout/stderr，既有且未改。未引入 TODO/FIXME。

### 2. 注释完整性

三处真实缺口已补，三端对齐：

- `resolvePath` / `partitionInputs`：为什么 CLI 要排除自己的写入目标、为什么过滤的是**存储的** `input_paths` 而不只是哈希输入、为什么比较发生在路径解析之后。
- `manifestCommit`：为什么用窄扫而非 `parseReviewManifest`、为什么缺失或畸形是跳过而非失败、为什么绝不重写该文件。
- `gateRepoRoot`：为什么 governance 用门禁的 `--git-common-dir` 解析而不是 `input.context`，以及这约 20 行为何是复写而非 import，并附 `delivery-gate.cjs:28` / `:434` 行号便于同步。

最后一处尤其必要：有人「顺手」把它改成 `input.context`，就会静默重新引入这个子命令存在的理由所要防的 worktree bug。该模块本就有同类注释（`// base_commit is recorded, not compared: …`）。

### 3. 冗余 / 重复代码

一处已修：`mapDiffs` 里 `Object.keys(expected||{})` 的空值守卫是**自相矛盾的死分支**——它防 `Object.keys` 对 null 报错，但紧接着的一行就无保护地 `expected[key]`，根本挡不住它看起来要挡的崩溃。四个调用点传的都是真实对象。删除后同时让 CC 向本就没有该守卫的 CX 靠拢。属铁律[反过度工程]的边界内死防御。

两处有意保留：`prepare` 在 `let docs = []` 两侧各判一次 `mode==='implementation'`，那是重复的**守卫**不是重复的逻辑，为它改三个文件属于无谓重排；`manifestCommit` 的 `trimStart().startsWith('#')` 略冗，纯外观。

### 4. 低效模式

无实际问题。`prepare --mode implementation` 现在跑两次 `git rev-parse HEAD`（预检一次、`liveInput` 一次），合并需要重排 `liveInput`，而代价是每次 prepare 多一个 5ms 以内的子进程。`partitionInputs` 对每个声明输入做一次三元素 `includes`。无 N+1、无阻塞。

### 5. 过度设计与过度防御

一处已修（上述 `mapDiffs` 守卫）。其余各得其所：`resolvePath` 的 ENOENT 捕获是**承重**的（session-log 与 review 文档在 prepare 时合法地尚不存在），且对其他 errno 原样抛出，fail-fast 保持；`excluded_inputs` 无代码消费者但设计明文要求它作为审计记录，不是死字段；全切片未新增配置项、flag 或扩展点。

## 超出设计文件计划的一处改动（主 agent 认可）

三份 `gate-contracts.md` 各加一句，记录 prepare 的自排除。设计的 File Structure Plan 只把文档改动限定在 `governance` 子命令与 manifest 预检，但 AC1 引入了两个**操作者可见**的行为：声明的 `--input` 路径会从 `input_paths` 里消失，以及一个全新的硬失败 `review inputs empty after excluding CLI-written paths`。只读合同文档的操作者无法预知任何一个。补这一句是合同应尽义务，不是范围蔓延。

## 路径解析复写的评估（设计审查指定的判断题）

polish worker 逐行比对后判定**该副本忠实**，主 agent 复核同意：

- `gateRepoRoot` vs 门禁 `tryRepoRoot`（`delivery-gate.cjs:434-447`）：同样的 `--path-format=absolute --git-common-dir` 探针、同样的 `basename === ".git"` 判断、同样的 `--show-toplevel` 回退、同样不抛异常的 `execFileSync` 选项含 `timeout:15000`。唯一差别是 `|| ''` 与 `|| null`，两者皆 falsy 且只用于真值判断。
- `gateAiState` vs `findAiState`（`:28-40`）：同样的 8 层上溯、同样的 `.ai_state` 目录判断，**并且带上了 2026-09-07 那条 `.git` 边界停止**——这是复写时最容易丢的一条。
- 组合方式等价：门禁是 `(root && findAiState(root)) || findAiState(cwd)`，governance 是 `gateAiState(root) || gateAiState(cwd)`，而 `gateAiState('')` 返回 `''`，短路语义保持。

一处行为差异，判为正确而非缺陷：门禁在 `findAiState(cwd)` 为空时于 `:1391` 提前退出，governance 不会。所以在「cwd 够不到 `.ai_state` 但主仓有」这个窄场景下，门禁什么都不校验，而 governance 报主仓的哈希。该场景下并不存在「门禁会读的那份文件」，报主仓的那份是有用的答案，未违反忠实性声明。

主 agent 仍把这条原样交给独立 implementation review 定级——本切片的立意正是「别重抄权威算法」，此处留了新的重抄，是否可接受不该由作者一方裁定。

## Finishing-a-development-branch

- [x] `python3 -m unittest vibeCoding.scripts.tests.athena999.test_state_review`：polish 前后均 52/52 PASS（裸跑，无管道）。
- [x] CC 与 Pi `delivery-gate.cjs` 各只差一行 `module.exports`；`delivery-gate.py` 与 `0ca066c` 字节同一。
- [x] Pi `_review-binding.cjs` 与 CC 字节同一。
- [x] `accept` 函数体与 `0ca066c` 字节同一，绑定行去重保住。
- [x] 未 merge、未 push、未开 PR、未删 worktree。
- [x] 下一动作是一次独立 implementation review。

## 遗留风险（均为门禁既有，非本切片引入）

1. **两端 `findAiState` 语义不同**：CC 在 `.git` 边界停止（`delivery-gate.cjs:33`），CX 无条件上溯 8 层（`delivery-gate.py:54-64`）。各自的 governance 对本端门禁都是忠实的，但在「最近的 `.ai_state` 位于 git 边界之上」的目录布局里两端会报不同文件。AC4 的等值测试未覆盖该布局。
2. **两端 `parseFrontmatter` 对畸形行处理不同**：CC 跳过（`:54`），CX 抛 `GateError`（`delivery-gate.py:90`）。故某些 `_index.md` 在 CC 上能算出哈希、在 CX 上非零退出。修它要动门禁，本切片 AC5 禁止。
3. **字段值转换差异今天良性**：两端解析器均返回全字符串值，故 `String(fm[key]||"")` 与 `fm.get(key,"")` 在所有可达值上一致。只有未来门禁改成返回非字符串 falsy 值时才会分叉（例如数值 `0` 会让 CC 得 `""`、CX 得 `"0"`）。切片 5 动门禁时需注意。
4. **sprint 范围断言有主人但代码里无期限**：`test_review_binding_gate_export_diff_is_sprint_scoped_and_pi_matches_cc` 硬编码 `0ca066c`，切片 5 合法改门禁时它就会开始失败。测试里已写明由切片 5 移除，需确保切片 5 的合同真的写了这条。

## 归档到 compound/

本切片未新增 compound：自排除与 fail-closed 诊断的决策已由 design 与 architecture 当前态承载，不复制 sprint 细节到第三份长期文档。

## VERDICT

PASS：五项检查完成，一处行为相关修复（死守卫删除）已复核；测试 52/52 绿，四项字节不变量全部成立。

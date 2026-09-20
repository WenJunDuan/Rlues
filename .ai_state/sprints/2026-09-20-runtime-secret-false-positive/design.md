---
sprint_slug: "2026-09-20-runtime-secret-false-positive"
path: "System"
stage: "design"
author: "cc-main"
base_commit: "a385d2e"
---

# Runtime secret 假阳性（Q12#12）

## WHY（勘查已核，三处独立实现）

**A. `athena-vm/scripts/runtime-run.py:29-34`（CC/CX 字节同源；Pi 无此文件）**：`SECRET` 第三段只要求「键名 + 引号包裹 + 非空白 ≥12 字符」，不辨占位符。`api_key = "YOUR_API_KEY_HERE"`、`"${API_KEY}"`、`"<your-client-secret>"` 全部误判。代价按消费点分级：`run():504`（`--contract` 实际就是 design.md，见 playbook:10/14）命中即整次 runtime-verify 失败；`snapshot():152` required 输入被剔除即 block；`collect():114` 普通文件静默漏传。前缀段 `sk-/gh?_{20,}` 同病：教程假 key `sk-xxxx…` 只看前缀+长度即中。`c540b22` 已修裸标识符（引号强制+阈值 12），quoted 占位符是遗留半边。
**C. `_input-binding` environment()（CC:67 == Pi 字节同；CX `_input_binding.py:97` 语义同）**：`(?:token|password|secret|api.key)\s*[=:]` 无长度/引号要求，`recipe: "uses token: placeholder"`、`version: token:none` 即抛；经 pre-bash-guard try/catch 吞掉后 `captureBefore` 不落快照 → 该命令证据绑定永久 `unverifiable`。
**B. `configure-vm.py` 键名/PEM 匹配机制不同，非本切片。**
现有测试只测「真密钥被拦」半边（`test_vm_install.py:195`），占位符对照为零；environment() 检测全无测试。

## HOW

- **占位符谓词 `is_placeholder(value)`**（保守白名单，判不准=仍按密钥，fail-closed 方向不变）：整值为 `${…}`/`{{…}}`/`<…>`；或含词（大小写不敏感）YOUR_ / REPLACE / EXAMPLE / PLACEHOLDER / CHANGE[-_]?ME / DUMMY / SAMPLE / TODO / TBD / NOT[-_]A[-_]REAL / REDACTED；或值体（去前缀后）为单一字符重复 ≥6（xxxx…/****）。
- A：quoted-value 分支与 sk-/gh 前缀分支命中后过谓词，占位符不剔除/不 block；真密钥路径逐字不变。CC/CX 双份同步（字节同源维持）。
- C：命中凭据语法后取 `[=:]` 后值 token 过同一谓词（另放行 none/null/empty）；真凭据（URL userinfo `://user:pw@`、高熵值）仍抛。CC 与 Pi 字节同改（既有 parity 测试锁）、CX 语义同。
- 谓词在 `runtime-run.py` 与 `_input-binding` 各自实现但逐字对齐哲学（跨 skill/hook 无共享 import 通道）；一致性由对照矩阵测试钉。
- **不引入豁免存储**：无现实消费者（勘查确认从无豁免机制）。若未来引入，必须按文件内容 SHA 绑定而非路径——只作设计约束记录。

## 允许写集

`vibeCoding/{claude/9.9.9/.claude,codex/9.9.9/.codex}/skills/athena-vm/scripts/runtime-run.py`；`vibeCoding/claude/9.9.9/.claude/hooks/_input-binding.cjs` + `vibeCoding/pi-agent/plugin/extensions/cc-core/_input-binding.cjs`（字节同改）+ `vibeCoding/codex/9.9.9/.codex/hooks/_input_binding.py`；`vibeCoding/scripts/tests/athena999/test_vm_install.py` 增补与/或新建 `test_secret_placeholder.py`；`.ai_state/` 记账。
Non-goals：不动 configure-vm.py；不建豁免机制；不给 Pi 造 athena-vm 副本（不伪造对称）；不改 SECRET 对真密钥的任何行为。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | quoted 占位符（`${…}`/`{{…}}`/`<…>` 整值、占位词、重复字符体）不再被 A 剔除/block：contract 含占位符示例的 run 通过、required 占位符输入不再误 block、collect 不再漏传（端到端脚本实跑） |
| AC2 | `sk-`/`gh?_` 前缀段对占位体（全同字符/含占位词）不判密钥；真实随机体仍判 |
| AC3 | 真密钥 fail-closed 回归：既有真-secret 用例全部保持原行为（剔除/block/脱敏），逐用例断言 |
| AC4 | environment() 检测：占位/描述值不再抛，真凭据语法仍抛；首次补对照测试；CC==Pi 字节（既有 parity 测试续锁）、CX 同判 |
| AC5 | 对照矩阵：A/C 每分支 placeholder×real 成对用例同夹具驱动 CC 与 CX，判定一致；runtime-run.py CC==CX 字节相等入测试 |
| AC6 | Pi 端事实入档：athena-runtime-verify playbook 悬空引用（指向 Pi 不存在的 runtime-run.py）记 roadmap 切片 9 notes，本切片不修不造 |

## 测试场景

1. 占位符矩阵 ×A 三消费点（contract/required/collect）先红后绿；2. 前缀段占位体先红；3. 真密钥全回归保持绿；4. environment() 占位 vs 真凭据首测；5. 双端字节/判定一致。

## 风险

谓词过宽会放走真密钥——白名单只认明确非密钥形状，判不准仍按密钥；review 重点挑战谓词边界。

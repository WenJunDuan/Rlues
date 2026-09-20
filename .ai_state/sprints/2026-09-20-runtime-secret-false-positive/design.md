---
sprint_slug: "2026-09-20-runtime-secret-false-positive"
path: "System"
stage: "design"
author: "cc-main (rev 2 + 95299306 PASS 的 3 条 P2 子句落实)"
base_commit: "a385d2e"
---

# Runtime secret 假阳性（Q12#12）

## WHY（勘查已核，三处独立实现）

**A. `athena-vm/scripts/runtime-run.py:29-34`（CC/CX 字节同源；Pi 无此文件）**：`SECRET` 第三段只要求「键名 + 引号包裹 + 非空白 ≥12 字符」，不辨占位符。`api_key = "YOUR_API_KEY_HERE"`、`api_key: "${OPENAI_API_KEY}"`（值体 ≥12 才中，`"${API_KEY}"` 10 字符不中——review 更正）、`client_secret: "<your-client-secret>"`（需键名前缀）均误判。代价按消费点分级：`run():504`（`--contract` 实际就是 design.md，见 playbook:10/14）命中即整次 runtime-verify 失败；`snapshot():152` required 输入被剔除即 block；`collect():114` 普通文件非致命剔除（stderr 提示 + manifest 记录），required 输入因此缺席时在 :152 升级为 block。前缀段 `sk-/gh?_{20,}` 同病：教程假 key `sk-xxxx…` 只看前缀+长度即中。`c540b22` 已修裸标识符（引号强制+阈值 12），quoted 占位符是遗留半边。
**C. `_input-binding` environment()（CC:67 == Pi 字节同；CX `_input_binding.py:97` 语义同）**：`(?:token|password|secret|api.key)\s*[=:]` 无长度/引号要求，`recipe: "uses token: placeholder"`、`version: token:none` 即抛；经 pre-bash-guard try/catch 吞掉后 `captureBefore` 不落快照 → 该命令证据绑定永久 `unverifiable`。
**B. `configure-vm.py` 键名/PEM 匹配机制不同，非本切片。**
现有测试只测「真密钥被拦」半边（`test_vm_install.py:195`），占位符对照为零；environment() 检测全无测试。

## HOW

- **占位符谓词 `is_placeholder(value)`**（保守白名单，判不准=仍按密钥）：整值为 `${…}`/`{{…}}`；整值为 `<…>` 且尖括号内仅 `[A-Za-z0-9_.-]`、长度 ≤48 且无 ≥16 连续 alnum（「非高熵」即此判据）；或占位词（YOUR / REPLACE / EXAMPLE / PLACEHOLDER / CHANGE[-_]?ME / DUMMY / SAMPLE / NOT[-_]A[-_]REAL / REDACTED）以**两侧**非字母数字边界出现**且**值体其余部分无 ≥16 连续 alnum（防前缀拼真随机体）；TBD / TODO 仅整值成立；或值体为单一字符重复 ≥6。
- **全匹配语义（review P0-1）**：A 各消费点改 `finditer`，**全部**命中均为占位符才放行，任一非占位即按密钥走原路径；C 侧对行内**每个**凭据分隔符取值（取到行尾）分别过谓词，任一非占位即抛。混排（占位+真密钥同文件/同行）必须保持 block/剔除；**被释放的 match span 自身须再过一遍 SECRET 其余分支**（防第三分支整体吞掉内嵌的前缀型密钥）。
- A：谓词应用于四类 block/剔除消费点 = run():504、snapshot()/collect():152/114、inspect_bundle():235、validate_scenario():306；redacted():249 **不应用**——占位符行多脱敏无害，保持原行为（Non-goals 声明）。真密钥路径逐字不变，CC/CX 字节同源维持。
- C：命中凭据语法后取 `[=:]` 后值 token 过同一谓词（另放行 none/null/empty）；真凭据（URL userinfo `://user:pw@`、高熵值）仍抛。CC 与 Pi 字节同改（既有 parity 测试锁）、CX 语义同。
- 谓词在 `runtime-run.py` 与 `_input-binding` 各自实现但逐字对齐哲学（跨 skill/hook 无共享 import 通道）；一致性由对照矩阵测试钉。
- **不引入豁免存储**：无现实消费者（勘查确认从无豁免机制）。若未来引入，必须按文件内容 SHA 绑定而非路径——只作设计约束记录。

## 允许写集

`vibeCoding/{claude/9.9.9/.claude,codex/9.9.9/.codex}/skills/athena-vm/scripts/runtime-run.py`；`vibeCoding/claude/9.9.9/.claude/hooks/_input-binding.cjs` + `vibeCoding/pi-agent/plugin/extensions/cc-core/_input-binding.cjs`（字节同改）+ `vibeCoding/codex/9.9.9/.codex/hooks/_input_binding.py`；`vibeCoding/scripts/tests/athena999/test_vm_install.py` 增补与/或新建 `test_secret_placeholder.py`；`.ai_state/` 记账。
Non-goals：不动 configure-vm.py（键名/PEM 机制不同类）；不动 CX evidence-collector.py:32-42 同族脱敏正则（仅脱敏非阻断，CX 独有，归切片 9 裁量）；redacted():249 保持原行为；不建豁免机制（未来若建按内容 SHA 绑定）；不给 Pi 造 athena-vm 副本；不改 SECRET 对真密钥的任何行为。

## 验收标准

| AC | 判据 |
|---|---|
| AC1 | quoted 占位符不再被 A 的四类 block/剔除消费点误判（contract/required/collect/scenario/bundle 端到端）；夹具值体固定 ≥12 字符并先取改前实测命中输出作红基线 |
| AC2 | `sk-`/`gh?_` 前缀段对占位体（全同字符/含占位词）不判密钥；真实随机体仍判 |
| AC3 | 真密钥 fail-closed 回归：既有真-secret 用例全部保持原行为（剔除/block/脱敏），逐用例断言 |
| AC4 | environment() 检测：占位/描述值不再抛，真凭据语法仍抛；首次补对照测试；CC==Pi 字节（既有 parity 测试续锁）、CX 同判 |
| AC5 | 对照矩阵：A/C 每分支 placeholder×real 成对用例同夹具驱动 CC 与 CX，判定一致；runtime-run.py CC==CX 字节相等入测试 |
| AC6 | Pi 悬空引用记 roadmap 切片 9 notes，本切片不修不造 |
| AC7 | 混排 fail-closed：同文件/同行「占位符 + 真密钥」在 A 全部消费点与 C 均保持剔除/block（先红：按首匹配朴素实现会放行） |

## 测试场景

1. 占位符矩阵 ×A 四类消费点先红后绿（夹具 ≥12 字符）；2. 前缀段占位体先红；3. 真密钥全回归 + 对抗样例（占位词前缀拼随机体、含 tbd 子串的真 key 仍判密钥）；4. 混排先红（AC7）；5. environment() 占位 vs 真凭据 + 行内多分隔符；6. redacted() 行为不变断言；7. 双端字节/判定一致。

## 风险

谓词 fail-open 面已按两轮 review 收紧（全匹配 + span 复扫 + 边界词 + ≥16 连续 alnum 否决 + TBD/TODO 整值）。量化残余：值体各 alnum 段均 <16 且含占位词的人为构造（如 xK9-dummy-2Fq7-Lm3v 形）仍会放行——该形状不匹配任何已知真实密钥格式（sk-/ghp_/AKIA/PEM 均为长连续体），属可接受残余，对照测试钉住方向。

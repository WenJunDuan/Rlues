---
sprint_slug: "2026-08-27-athena-9-9-8"
path: "System"
stage: "runtime-verify"
status: "completed"
verified_at: "2026-08-27T19:20:00Z"
head_ref: "cdd639d"
---

# Runtime Verify — Athena 9.9.8

## 完成条件与停止条件

- `python3 vibeCoding/scripts/validate-athena-9.9.8.py` 必须 `fail=0`。
- 安装态：CC/CX 版本标记 9.9.8；用户 model/effort/base_url 仍在；历史文件指纹未在部署中改变。
- 停止：validator、gate fixtures、安装态保护面核对完成后不再发明第二套账本。

## 测试场景

| 类别 | 场景与命令 | 结果 |
|---|---|---|
| 正常 | `python3 vibeCoding/scripts/validate-athena-9.9.8.py` | PASS；`120 PASS / 0 FAIL / 0 SKIP`（含 package parity、gate runtime 五用例、160B overflow、AC11 baseline、F-series、exact Codex config.load） |
| 边界 | tree-hash 含 untracked；packet 陈旧 hash / 漏 AC / 多 AC；缺 `implementation-review.md`；`native_output_ref` 路径不存在；diff hash 不匹配 | PASS；CC/CX 均 fail-closed |
| 失败/安全 | `rg 'foo$(rm -rf /)bar'` 单引号不报；裸 `$(rm -rf /)` 仍报；部署不写 history/sessions/auth/sqlite | PASS |
| 环境 | CC 2.1.231 / CX 0.150.0；Python 3.14；node 25；安装态 `delivery-gate` sha256 与 canonical 一致 | PASS |

## 自测自改记录

1. 首轮 validator 声明 87/0/0 不可复现；重跑后以 106 再 120 为准，并禁止 `py_compile` 污染包。
2. `sourceDiffSha256` 改为 `git ls-files -c -o` 树哈希，否则 untracked 的 9.9.8 树对 ship 隐形。
3. `_index` 160B 首次实现误切状态列表；去掉破坏性 12KiB 循环，改 bullet 整段重建 + 行尾注释兼容的 `route_history`。
4. 安装态第二次同步：保护面 before==after；用户 `opus[1m]` / CX `xhigh` / `openai_base_url` 保留。

## AC coverage（本轮证据边界）

| 设计项 | 本轮结论 | 证据边界 |
|---|---|---|
| AC2/AC3/AC5 | PASS（gate fixtures） | stale hash / AC 集合 / 缺 review / 缺 native ref / diff mismatch |
| AC7/AC8 | PASS（quote + 红区仍 block） | CC/CX `findSubstitutions`；rm/push 未降级 |
| AC9 | PASS（现场 `_index`） | ≤12KiB、列表≤10、单条≤160B，全文在 `index-overflow.md` |
| AC10 | PASS（安装态） | 未覆盖用户 model/effort |
| AC11 | PASS（labeled 投影） | `eval-ac11.md`；impl 混角色分不开已声明 |

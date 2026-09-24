# Stop 阻断熔断器 · 实施与验证证据 (§10.1 / AC16)

**日期**: 2026-07-27
**实施**: Codex terra 首版 (CX 侧 +156 行) + 主 agent 补漏与验证
**范围**: **双端已实施并安装**。用户 2026-07-27 授权「包括你提到的问题也一起修改」后补齐 CC 侧、AC16i 与 evidence.yaml 死锁根治。

## 1. 交付物

| 文件 | 状态 |
|---|---|
| `vibeCoding/codex/9.9.6/hooks/delivery-gate.py` | 已改 (熔断器 + 解锁动作正确化 + block 后缀) |
| `vibeCoding/codex/9.9.6/hooks/test_gate_breaker.py` | 新增, 20 条断言 |
| `~/.codex/hooks/delivery-gate.py` | **已安装**; 旧版备份 `delivery-gate.py.bak-20260727` |
| `vibeCoding/claude/9.9.6/.claude/hooks/delivery-gate.cjs` | 已改 (熔断器 + 解锁动作正确化 + 死锁根治) |
| `vibeCoding/claude/9.9.6/.claude/hooks/session-start.cjs` | 已改 (AC16i 升级告警) |
| `vibeCoding/codex/9.9.6/hooks/session-start.py` | **新入库** (此前仓库缺口: CX 只有 delivery-gate.py, 本地改动会随升级蒸发) + AC16i |
| `~/.claude/hooks/delivery-gate.cjs` · `session-start.cjs` | **已安装**; 各留 `.bak-20260727` |

## 2. 行为矩阵实测结果 (20/20 PASS)

```
AC16a  第1/2次 block · 第3/4次 ESCALATED 不发 block · ledger 2×GateBlock + 2×GateEscalated · 字段齐全
AC16h  连续 12 次 Stop, decision:block 发射 2 次 (门槛 ≤3)
AC16f  5 次 PreToolUse 实现写入全部被阻断 · 未写 ledger (不推进计数) · 其后首个 Stop 仍 block 非升级
AC16c  A 已 2 条时 B 的首个 Stop 仍正常阻断 · B 的记录不打断 A 的链
AC16e  缺 cleanup-pass.md 报 polish 未跑 + 完整解锁链 · 空壳文件仍判未跑 · 补齐后才改报缺 manifest
补漏   impl 段 spec-gate 失败同样熔断 (Codex 首版只接了 ship 段)
M7     非 Athena 目录静默放行
```

原始活锁场景 (stage=ship + Refactor + 无 manifest) 的直接对照: **290 次 → ≤3 次**。

## 3. 变异测试 (证明断言非空转, 3 变异 3 红)

| 变异 | 结果 |
|---|---|
| 熔断阈值 `>= 3` → `>= 99` (等于关掉熔断) | **红** 6 条 — 12 次尝试 block 发射 12 次 |
| 删除 `stop_failure` 的 Stop 事件守卫 | **红** 3 条 — **PreToolUse 第 3/4/5 次实现写入被放行执行** (设计警告的 P0 越权, 断言抓住) |
| 移除 cleanup-pass 根因判定 | **红** 3 条 — 解锁动作退回旧的误导性措辞 |

补漏项的 red→green: 还原 Codex 首版 impl 段 → `impl spec-gate 第 3/4 次升级` **红**; 接上熔断器 → 绿。

## 4. 主 agent 对 Codex 首版的核验与修改

**守住的 (核验通过, 未改)**:
- **M5 硬约束**: `stop_failure()` 首行即 `if payload.get("hook_event_name") != "Stop": return block(reason)`,
  熔断是独立函数而非塞进共用 `block()` —— 无 PreToolUse 越权路径。
- **F2 并发**: `gate_chain_count` 对其他会话的记录用 `continue` 而非 `break`, 交替 reason 不打断各自链条。
- **F1 清零**: `GatePass` 才断链, `GateEscalated` 计入尾链, 无 "3 block + 1 escalate" 循环。
- **F5a 空壳判定**: 逐字复用既有 `r"\bPASS\b|completed|完成"` (原 `validate_meta_acceptance`), 未新造机制。

**主 agent 补的**:
1. **impl 段 spec-gate 未接熔断** —— 首版只把 `stop_failure` 接在 ship 段异常处理上,
   impl 阶段 spec-gate 失败仍会每个 Stop 无限阻断。已接。
2. **`validate_worktree_violations` 在 try 之外** —— 其 GateError 冒到最外层 catch 变成 plain block,
   Stop 路径同样活锁。已显式接进熔断器。
3. 全部测试与变异测试 (Codex 被中断前未写任何测试)。

## 5. 补做项 (2026-07-27 用户授权后)

| 项 | 状态 | 证据 |
|---|---|---|
| CC 侧 `.cjs` 双端一致 | ✅ | 同一套测试驱动两端, **各 22/22 PASS** |
| AC16i · SessionStart 告警未消解升级 | ✅ | 双端命中 1; 追加 `GatePass` 后双端命中 0 (反向断言); SessionStart 输出 1802 bytes (AC9 上限 2500) |
| `evidence.yaml` 死锁根治 | ✅ | manifest 哈希校验跳过**未跟踪**文件并留 stderr 声明; 回归测试双端 PASS |

**死锁根治的判据**: 治理哈希只对**版本化**文件有意义。gitignored 文件哈希必然漂移,
且不在 git 里就没有还原来源, 重算 manifest 又是禁止的绕过 —— 三者相加即不可恢复的死锁。
改法是 `git ls-files` 取跟踪集, 未跟踪者跳过哈希校验并打声明, 而非放宽校验本身。

## 5b. 仍未覆盖 (**不得当作已完成**)

1. **AC16b 的 GatePass 清零仅单元级 + AC16i 侧证**, 无 delivery-gate 端到端断言 ——
   端到端需构造完整合法 ship 状态 (manifest/binding/AC 映射全绿), 成本高。
   当前 gate 测试覆盖的是 **reason_sha1 变化导致的断链**, 非 GatePass 断链。
2. **无 sprint slug 时熔断退化为普通 block** —— `_index` 缺失/畸形/无 slug 的早期错误
   仍可能在 Stop 上重复阻断 (无处写 ledger)。这类错误可由用户直接修复, 未纳入本刀。
3. CX 侧 `stop-failure-recorder.py` 仍未补装 (与活锁无因果, 独立小项)。

## 6. 回滚

```bash
cp ~/.codex/hooks/delivery-gate.py.bak-20260727   ~/.codex/hooks/delivery-gate.py
cp ~/.claude/hooks/delivery-gate.cjs.bak-20260727 ~/.claude/hooks/delivery-gate.cjs
cp ~/.claude/hooks/session-start.cjs.bak-20260727 ~/.claude/hooks/session-start.cjs
cp /tmp/session-start.py.bak                      ~/.codex/hooks/session-start.py
```

# Codex 外包任务单 · Stop 阻断活锁熔断 (§10.1 / AC16)

## 0. 身份声明 (先读, 决定你要不要跑门禁)

**你是外包执行器。PACE 路由分诊、design 审议与 critic 把关已在 CC 侧完成**
(design §10.1 + AC16, 经 R5 critic 定稿 APPROVE_WITH_CHANGES, 八条 findings 全处置)。
你**不需要**再走 brainstorm/design/critic, 也不要修改 `_index.md` 的 path/stage/slug。
你的职责只有一件: **按下面的行为矩阵实现代码 + 测试**, 严格 TDD (red → green)。

真相源: `.ai_state/sprints/2026-07-25-athena-9-9-6-prompt-engineering/design.md` §10.1 与 AC16。
本任务单与 design 冲突时**以 design 为准**, 并在报告里指出冲突, 不要自行裁决。

## 1. 背景 (为什么做, 一句话)

一个跑 polish 的 Codex exec 会话被同一条 gate 阻断 **290 次 / 42 分钟**, 零进展:
`[delivery-gate] Refactor/System ship requires review-manifest.yaml`。
根因两条: ①解锁动作物理不可执行 (polish 造不出 review-manifest, 那是 review 的下游产物)
②两端 gate 无重复阻断熔断器, `block()` 只吐 `decision:block` 让模型无限重试。

证据: `~/.codex/sessions/2026/07/26/rollout-2026-07-26T22-44-37-019f9ee2-95d0-7002-a445-e00940c7d645.jsonl`
(可自行 grep 复核计数)。

## 2. 改动范围 (**只有这两个文件**, 其余一律不碰)

1. `vibeCoding/codex/9.9.6/hooks/delivery-gate.py`
2. `vibeCoding/claude/9.9.6/.claude/hooks/delivery-gate.cjs`

> 两份实现必须**行为一致**。当前 `~/.codex/hooks/delivery-gate.py` 与仓库版逐字节相同, 可作对照。
> **不要**动 `~/.codex/` 或 `~/.claude/` 下的已安装副本 —— 安装由 CC 侧收编时统一做。
> **不要**新建文件 (design R1-F4 已明确否决新建 `gate-blocks.jsonl`, 复用既有 `stop-failures.jsonl`)。
> **不要**补装 CX 的 `stop-failure-recorder.py` (已从本刀拆出为独立小项)。

## 3. 行为矩阵 (**唯一权威**; 矩阵之外的现状行为逐字节保持)

计数键 = `session_id + reason_sha1`。`reason_sha1` = 阻断原因字符串的 sha1。
"连续数" = `stop-failures.jsonl` 尾部连续、同 `session_id`+`reason_sha1`、且 ts 在**最近 30 分钟内**的记录数。
`session_id` 缺失时退化为仅按 `reason_sha1` + 30 分钟窗口 (兜底, 不报错)。

| # | hook 事件 | 校验结果 | 计入前的连续数 | gate 输出 | ledger 写入 |
|---|---|---|---|---|---|
| M1 | Stop | 通过 | 尾部记录是 `GateBlock`/`GateEscalated` | exit 0, 不发 block | 追加 `GatePass` |
| M2 | Stop | 通过 | 尾部无链 (无需清零) | exit 0, 不发 block | **不写** (零成本) |
| M3 | Stop | 失败 | 0 或 1 | 发 `{"decision":"block","reason":...}` (现状不变) | 追加 `GateBlock`, `consecutive`=n+1 |
| M4 | Stop | 失败 | **≥2** | **不发 block**; exit 0 + stderr 打 `[delivery-gate] ESCALATED: <原 reason>` | 追加 `GateEscalated`, `consecutive`=n+1 |
| M5 | PreToolUse **实现写入** | 失败 | **任意值** | **永远发 block** (熔断不作用于此路径) | **不写, 且不推进计数** |
| M6 | PreToolUse 非实现写入 (ship 段 P8 carve-out) | — | — | 现状不变 (早退 exit 0) | 不写 |
| M7 | 其余所有事件 / 非 Athena 目录 | — | — | **现状不变, 逐字节保持** | 不写 |

**M5 是硬约束**: 熔断判定必须写在 **Stop 分支内**, 不得放进两端共用的 `block()`
(py:99 / cjs:995)。若放进 `block()`, 同因重试的实现写入第 3 次会被放行执行 —— 那是 P0 越权。

**ledger 记录字段** (追加进既有 `.ai_state/sprints/{slug}/stop-failures.jsonl`,
复用其 `event` 判别字段, 与既有 `StopFailure` 记录共存):
`{event, ts, session_id, reason_sha1, stage, path, consecutive}`
写入一律 **O_APPEND 单次 write** (并发 worktree 会同时追加同一文件)。

## 4. 第二处改动: 解锁动作正确化

ship 段对 **Refactor/System**, 在 `review-manifest.yaml` 检查**之前**先判 polish 产物 `cleanup-pass.md`:

- 缺失, **或**内容不含 `PASS` / `completed` / `完成` (空壳防护, 复用 `validate_meta_acceptance`
  在 py:601-603 的既有判据, **不要新造判定机制**) → 报 `polish stage 未跑` + 完整解锁链
  (跑 polish → 产出 cleanup-pass.md → 再补 review-manifest.yaml);
- 满足后**才**轮到原有的 manifest 检查。**manifest 仍为必需项, 一条不减, 只是先报根因**。

CX 侧 `block()` (py:99-103) 同时补上 CC 已有的解锁动作后缀 (见 cjs:996), 否则该消息在 CX 无从满足要求。

## 5. TDD 要求 (**必须真 red → green**)

每条 AC 先写失败测试、跑出红相、再实现。**backfill 记法不适用于本刀** (这是改行为, 不是补测试)。
必须覆盖 (逐条对应 design 的 AC16):

- **AC16a**: 同因连发, 第 3 次起不发 block 改 ESCALATED; **前 2 次仍正常阻断**
- **AC16b**: 每次阻断追加 `GateBlock` 记录含三字段; 校验全过的 Stop 写 `GatePass` 后计数清零, 下次从 1 重计
- **AC16b2** (反向): `GateEscalated` **不清零** —— 连续 ≥6 次同因 Stop, 第 4/5/6 次全部继续 escalate,
  **不得**回落成 block/block/escalate 的循环
- **AC16c**: 超出 30 分钟窗口的尾部同 hash 记录不计入; **并发双会话 fixture** —— 会话 A 已有 2 条同因记录时,
  会话 B 的首个 Stop **仍正常阻断**; A/B 不同 reason 交替追加**不打断各自连续链**
- **AC16e**: 缺 `cleanup-pass.md` 报 polish 未跑; 空壳文件同样判未跑; 补齐后才改报缺 manifest (顺序回归)
- **AC16f** (反向): PreToolUse 实现写入连发 N 次后**仍逐次阻断**; 且 **PreToolUse 阻断不推进 Stop 计数器**
- **AC16h**: 复现原始活锁场景, **连续 ≥12 次 Stop 尝试中 `decision:block` 发射总数 ≤3**
  (钉死重放长度, 防 4 次迭代的偷懒测试在错误清零语义下假绿)

> AC16i (SessionStart surface) **不在本刀**, 由 CC 侧另做。

## 6. 红线 (违反即打回, 不接受事后解释)

1. **禁止修改任何既有断言来让测试变绿**。既有测试红了 = 你改坏了现状行为, 回去修实现。
   (2026-07-26 有先例: 执行器改旧断言掩盖语义越界, 测试全绿但默认行为已被改坏。)
2. **禁止削弱任何现有校验**。本刀只增加"何时停止重试"的判断, 不减少任何一条 ship 契约检查。
   若你认为某条检查该删, 写进报告让 CC 侧裁决, 不要自行删。
3. **禁止改动矩阵之外的行为**, 包括但不限于: 漂移白名单、governance 哈希字段表、
   `skip_polish` 语义 (已知是死配置, design 明确本刀不扩面)、spec-gate、evidence/tdd 校验。
4. **禁止 commit / push**。改完留在工作区, 由 CC 侧收编。
5. 两端实现行为不一致 = 未完成。

## 7. 交付物

1. 两个文件的改动 + 对应测试
2. `codex-report.md`: 逐条 AC 的 red 命令与红相摘要 → green 证据; 遇到的与本任务单/design 的冲突;
   你做过但矩阵没写到的任何行为判断 (**必须主动列出**, 这是 CC 侧 review 的重点)

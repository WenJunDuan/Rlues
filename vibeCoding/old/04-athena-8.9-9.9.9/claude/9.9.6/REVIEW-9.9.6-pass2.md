# Athena 9.9.6 · Review Pass 2 (复核) · CONCERNS

复核对象: 2026-07-25 CX 修复批次 (mtime 1784985xxx–1784987xxx)，对照 `REVIEW-9.9.6.md` (pass 1)。
方法: 直读设备文件系统 (staged 副本不刷新，已改走 `device_bash`) + 官方文档二次核验。

**VERDICT: CONCERNS** — pass1 的 3 个 P0 修好 2 个。剩下 1 个**修反了**，而且 validator 里有一条断言正在把它认证为已修。

---

## 1. 已修 (10)

| pass1 编号 | 状态 | 核验 |
|---|---|---|
| P0-1 `openai_base_url = ""` | ✅ | 键已整行删除 (grep 无命中)，不是置空。`platform-contracts.md` 同步改写: "omits `openai_base_url`… the release tree never stores credentials **or an empty URL**"。结论与依据一致 |
| P0-3 CX 红区无阻断面 | ✅ | `hooks.json` 新增 `PreToolUse` matcher `spawn_agent\|Agent` → `subagent-worktree-audit.py`。**官方二次确认阻断有效**: learn.chatgpt.com/docs/hooks —— "You can also use exit code `2` and write the blocking reason to `stderr`"。实现 `return 2` + reason 写 stderr ✅ |
| ↳ 违规接入 ship 门禁 | ✅ | `delivery-gate.py` 新增 `validate_worktree_violations(sprint_dir)`；JSONL 加 `resolved` / `blocked_before_start` 字段。pass1 记的"剩余缺口"已闭合 |
| ↳ catch-all fail-closed | ✅ | 异常路径 `return 2` 而非默认 exit 1。官方只定义 exit 0/2，exit 1 属未定义 → 大概率 fail-open。这里避开了 |
| P1-4 SKILL.md 孤立围栏 | ✅ | 双端全量扫描 0 命中；validator 也加了 `body.count("\`\`\`") % 2` 断言 |
| P1-5 validator 回归 | ✅ **本轮最实的一项** | 12 类覆盖按行为恢复 (`check_baseline_and_package_parity` / `check_install_contract` / `check_runtime_contract` / `check_f_series_regressions` / `check_fresh_codex_runtime` / `check_contract_text`…)。并且是**升级不是复原**: 引入 `tomllib` 真解析 config.toml、`load_module` 真 import hook 验行为、`digest_tree`、`CC_BASE`/`CX_BASE` 指向 9.9.3 做真基线 diff。docstring 明写 "locks the repair findings from REVIEW-9.9.6.md" |
| P1-6 hooks 文档漂移 | 🟡 部分 | PreToolUse 三 hook + SubagentStart audit 已补；并明写 `subagent-retry.py` 是"未注册的升级兼容清理 shim，不参与当前 PostToolUse 链" —— 诚实处理，比删文件好。**但 Stop / SubagentStop 两行仍漏，见 §2-N2** |
| P1-7′ 网关 400 风险 | ✅ **措辞比我建议的更好** | platform-contracts 新增 "GPT-5.6 gateway risk" 段。关键是这句: "The issue is still an **upstream report, not proof that every custom `openai_base_url` fails**" —— 没把单点复现推成普遍结论。并要求 dogfood 覆盖 Sol 的 `code_mode_only` 下 Bash/apply_patch 派发 |
| P1-8 VERDICT 表无优先级 | ✅ | 双端 evaluator 加 "按下表自上而下判定；多条同时命中时始终取最严结果"；validator 断言 `"自上而下" and "取最严"` |
| P1-9 npx 缺词边界 | ✅ | 补成四条: `Bash(npx playwright)` / `Bash(npx playwright *)` / `Bash(npx ecc-agentshield)` / `Bash(npx ecc-agentshield *)`。精确形 + 词边界形，正解 |
| P1-10 critic 6/7 | ✅ | 两处均为 7 |
| P2-12 CX 铁律无溯源 | ✅ | 10 行，`[Standards ≠ Codex .rules]` 有具体起因: "曾把用户工程规范与 Starlark 命令权限文件混为一谈，导致规范被写进不会注入 prompt 的权限层" |

---

## 2. 未修 / 修反 (3)

### N1 · P0 级 · P0-2 修反了，且 validator 正在认证这个错误状态

`reviewer.md` / `spec-compliance.md` 删掉了 `background: true` —— **但没写 `background: false`**。

```
architect.md        background: false
critic.md           background: false
evaluator.md        background: false
generator.md        background: false
polish-worker.md    background: false
reviewer.md         (无此键)   ← 唯二必须同轮返回的
spec-compliance.md  (无此键)   ← 唯二必须同轮返回的
```

官方 (code.claude.com/docs/en/sub-agents): **"As of v2.1.198, subagents run in the background by default."** 删 key = 回落到默认 = 仍是后台。7 个 agent 里，最不能后台的两个，恰好是唯二没钉住的两个。

更要紧的是 validator 里这一行:

```python
check("CC review agents not forced background", "background: true" not in reviewer + compliance)
```

**它断言的是"没有 true"，不是"有 false"。** 当前状态这条 PASS，而实际行为仍然错。这是"断言锁的是这次的改法，不是要保的性质"的教科书样本 —— 和 pass1 说的"字符串在场 ≠ 配置跑得起来"是同一个病，只是换了个位置复发。

**修**
1. 两个文件补 `background: false`
2. 断言改成解析 frontmatter 判布尔: `fm.get("background") is False`，不是子串查找

---

### N2 · hooks.md ↔ hooks.json 集合仍不等；validator 只做了点状断言

实测差集:

| 事件 | hooks.json 注册 | hooks.md 表格 | 漏记 |
|---|---|---|---|
| `Stop` | token-usage-collector.py, delivery-gate.py, pace-continuator.py | delivery-gate.py | **2 个** |
| `SubagentStop` | token-usage-collector.py, subagent-tracker.py | subagent-tracker.py (+ SubagentStart 的 audit) | **1 个** |

`token-usage-collector.py` 挂在 2 个事件上，在 `hooks.md` 里出现 **0 次** —— 和刚修掉的 `subagent-worktree-audit.py` 完全同类。

`check_hooks()` 现有断言全是点状字符串:

```python
check("CX hook docs describe spawn guard", "spawn_agent|Agent" in hook_docs and "前置阻断" in hook_docs)
check("CX hook docs mark retry unregistered", "未注册" in hook_docs and "subagent-retry.py" in hook_docs)
```

锁的是本次修复点。pass1 的 M2.1 要的是**集合相等**，没实现 → 手工对齐时没盯的那两格当场漏掉。这是对 M2.1 必要性最直接的实证。

**修**: 加

```python
registered = {basename(h["command"].split()[-1])
              for groups in hooks.values() for g in groups for h in g["hooks"]}
documented = set(re.findall(r"[\w-]+\.py", hooks_md))
check("CX hook 注册集合 == 文档集合", registered == documented,
      f"仅注册={registered-documented} 仅文档={documented-registered}")
```

---

### N3 · hooks.md 协议要点缺 exit 2 这条阻断信道，现有表述会误导

现文档里唯一与 PreToolUse 返回值相关的句子:

> "PostToolUse 支持 systemMessage / continue:false / stopReason; **PreToolUse 返回这些会被标 hook 失败**"

这句本身对。但新加的阻断 hook 靠 exit 2 生效，文档**没写它是合法信道**。读这份文档的 agent 只会得出"PreToolUse 没法阻断"的反向结论。

**补** (官方原文为据):

> PreToolUse 阻断信道有且仅有三条:
> 1. `hookSpecificOutput.permissionDecision: "deny"` + `permissionDecisionReason`
> 2. 旧式 `{"decision": "block", "reason": "..."}`
> 3. **exit 2，阻断原因写 stderr**
>
> 多 hook 时**任一 deny 胜出**；无人决策 → 走正常审批流；stdout 纯文本被忽略。
> ⚠️ fail-open 陷阱: `permissionDecision:"ask"` / `continue:false` / `stopReason` 会被解析但**不支持** —— Codex 标记该 hook 运行失败、报错、然后**继续执行工具调用**。

---

## 3. 修复中新引入 (3)

### N4 · `subagent-worktree-audit.py` docstring 散文句与自己的表格打架

```
| SubagentStart | 起来之后检测 | 纵深防御；... |        ← 表格写对了
...
两端都在各自的原生 function-tool hook 路径做前置阻断；   ← 这句写错了
```

官方: SubagentStart 段 "`continue: false` is parsed for compatibility, but **it doesn't stop the subagent from starting**"，且该事件段**没有** exit 2 条款。SubagentStart 不是阻断路径。

留着这句，下一个改这个文件的 agent 会以为 SubagentStart 能拦 —— 正是铁律[四原语]「不伪造对称工具」要防的那类误解，只是这次发生在注释里。**删这句散文，表格已经说对了。**

### N5 · catch-all 在 SubagentStart 上 `return 2` 是未定义行为

```python
except Exception as exc:
    sys.stderr.write(f"[subagent-worktree-audit] BLOCKED on invalid hook input: {exc}\n")
    return 2
```

在 PreToolUse 上这是正确的 fail-closed。但同一脚本也挂 SubagentStart，那个事件没有 exit 2 语义 —— 畸形 payload 只会产生 hook 失败噪声，且日志写着 "BLOCKED"，而实际什么都没拦。

**修**: 按事件分流 —— PreToolUse → `return 2`；SubagentStart → `return 0` + stderr 告警。日志措辞同步区分。

### N6 · validator 无解释器版本守卫 (本轮 PASS/FAIL 我没拿到)

```
$ python3 validate-athena-9.9.6.py
ModuleNotFoundError: No module named 'tomllib'
```

设备 shell 的 `python3` 是 3.10.12；`tomllib` 是 3.11+ stdlib。**因此本轮验证器实际结果我没有数字**，本文所有结论来自直接读文件与官方文档，不是跑出来的。

你本机跑的解释器 (仓库里有 `cpython-314.pyc`) 应该没问题。但发布门禁 import 就崩、且无版本守卫 —— 换台机器就等于门禁静默不存在。

**修**: 文件头加

```python
if sys.version_info < (3, 11):
    sys.exit("validate-athena-9.9.6 需要 Python ≥3.11 (tomllib)，当前 %s" % sys.version.split()[0])
```

---

## 4. 下一步 (按顺序)

| # | 动作 | 验收 |
|---|---|---|
| 1 | reviewer/spec-compliance 加 `background: false` | `yaml.safe_load(frontmatter).get("background") is False` 双文件为真 |
| 2 | validator 该断言改成解析布尔，不查子串 | 人为把值改成 `true` 时断言必须 FAIL |
| 3 | hooks.md 补 Stop / SubagentStop 两行 + exit 2 信道段 | 见 N2 的集合断言通过 |
| 4 | validator 加 hooks 注册↔文档集合相等断言 | 同上 |
| 5 | 删 audit docstring 那句散文；catch-all 按事件分流 | grep 无"两端都…前置阻断" |
| 6 | validator 加 `sys.version_info >= (3, 11)` 守卫 | 3.10 下给出明确错误而非 traceback |
| 7 | **然后**才进 M3 真机 System dogfood | 产出 `runtime-verify.md` |

---

## 5. 一句话

**修得很实 —— P0-1/P0-3 是真修好的，validator 从"字符串在场"升级到"真解析真 import"是本轮最大的进步。剩下的问题全部退化成同一个形状: 断言锁住了这次的改法，没锁住要保的性质（N1 最典型），以及手工对齐总会漏掉没盯的那一格（N2）。第 1–4 步做完，9.9.6 就该进 dogfood 了。**

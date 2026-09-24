# Athena 9.9.6 · Review Pass 3 (修复执行记录) · 待用户复跑 validator

执行时间: 2026-07-25。执行者: 外部审查方 (非 Athena 主 agent)。
范围: `REVIEW-9.9.6-pass2.md` 的 N1–N6，全部 7 个改动点。
手段: `vibeCoding/scripts/fix-pass2.py` —— 幂等、锚点必须恰好命中 1 次否则跳过、自动备份、改完跑 `py_compile`。
未动 git。备份在 `vibeCoding/.review-backup-pass2/`。

---

## 1. 改动清单 (13 项，全部 OK / 0 MISS)

| 编号 | 文件 | 改动 |
|---|---|---|
| N1 | `claude/…/agents/reviewer.md` | 补 `background: false` |
| N1 | `claude/…/agents/spec-compliance.md` | 补 `background: false` |
| N1b | `scripts/validate-athena-9.9.6.py` | 断言由子串查找改为解析 frontmatter 判布尔 |
| N2 | `codex/…/pace/references/hooks.md` | `Stop` 行补 `token-usage-collector.py` + `pace-continuator.py` |
| N2 | 同上 | `SubagentStop` 行补 `token-usage-collector.py` |
| N2b | validator | 新增 `registered ⊆ documented` + "未注册者须显式标注" 双断言 |
| N3 | hooks.md | 新增 PreToolUse 三条阻断信道 / fail-open 陷阱 / SubagentStart 无阻断语义 |
| N4 | `subagent-worktree-audit.py` | 删除与自身表格矛盾的散文句 |
| N4b | 同上 | docstring 标题去掉过期理由「因为 Codex 的预防面未经验证」—— 该面已按官方核实 |
| N5a | 同上 | `main()` 预置 `event = ""` |
| N5b | 同上 | catch-all 按事件分流 |
| N6 | validator | 加 `sys.version_info < (3, 11)` 守卫 |
| N6b | validator | 去掉重复 `import sys` |

---

## 2. 验证证据

### 2.1 N1b 变异测试 — 断言现在测的是「性质」而非「这次的改法」

| 场景 | frontmatter 值 | **新**断言 | **旧**断言 |
|---|---|---|---|
| 现状 (已修) | `false` | PASS | PASS |
| 变异 A: 改成 `background: true` | `true` | **FAIL** | FAIL |
| 变异 B: 整键删除 ← **这就是 pass2 时的真实状态** | `None` | **FAIL** | **PASS** ← 漏 |

变异 B 是关键行:旧断言 `"background: true" not in body` 对"键不存在"判 PASS,而官方 v2.1.198 起 subagent **默认后台** —— 断言通过、行为错误。新断言抓住了。

双端终值全部为 `false`:

```
architect.md        false      generator.md        false
critic.md           false      polish-worker.md    false
evaluator.md        false      reviewer.md         false   ← 本次修
                               spec-compliance.md  false   ← 本次修
```

### 2.2 N2b 集合断言 — 当前真实文件

```
未记录 (registered - documented)            = ∅
文档提到但未注册且未标注                      = ∅
registered ⊆ documented                     = True
```

`subagent-retry.py` 作为文档中明确标注"未注册"的清理 shim 被正确豁免,不误报。

### 2.3 N6 版本守卫 — 3.10 下的行为

```
$ python3 validate-athena-9.9.6.py
validate-athena-9.9.6 需要 Python >= 3.11 (tomllib), 当前 3.10.12
```

一行明确错误,不再是 `ModuleNotFoundError` traceback。

### 2.4 语法自检

`validate-athena-9.9.6.py` 与 `subagent-worktree-audit.py` 均通过 `py_compile`。

---

## 3. 唯一遗留 — 需要你在本机做

**我没有跑成完整 validator。** Cowork 侧 VM 只有 Python 3.10.12,装不了 3.11+ (device shell 无网络)。上面所有结论来自直接读文件、变异测试与官方文档,**不是 validator 跑出来的**。

请在本机 (仓库里有 `cpython-314.pyc`,你的解释器是 3.14) 跑一次:

```bash
cd ~/workspace/Rlues/vibeCoding/scripts
python3 validate-athena-9.9.6.py
```

预期:全 PASS。若出现 FAIL,大概率在两处新断言 —— 它们比原来严,抓到的是真问题,不是误报。

回滚(如需):

```bash
cp -R ~/workspace/Rlues/vibeCoding/.review-backup-pass2/. ~/workspace/Rlues/vibeCoding/
```

---

## 4. 状态

| | pass1 | pass2 | pass3 |
|---|---|---|---|
| VERDICT | REWORK | CONCERNS | **待 validator 复跑确认** |
| P0 | 3 | 1 (P0-2 修反) | 0 |
| P1/N | 10 | 5 未修+新引入 | 0 |

pass2 的 §4 七步清单,第 1–6 步已全部执行完毕。

**下一步只剩第 7 步:M3 真机 System 级 dogfood** —— CC 2.1.219 + Codex 0.145.0 上完整跑一遍 `plan→design→impl→runtime-verify→review→polish→ship`,必测面:

1. Sol 的 `code_mode_only` 下 CX hook matcher 是否仍按 `Bash` / `apply_patch` 派发
2. `approval_policy=never` + `sandbox_mode=danger-full-access` 组合
3. 后台 worktree 自动 PR 是否被 `pre-bash-guard` 的 push 门禁拦住
4. 网关场景 (openai/codex#31882 仍 OPEN)

跑完产出 `runtime-verify.md`,9.9.6 才具备从 DRAFT 转 RELEASE 的条件。

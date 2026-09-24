---
schema_version: 1
mode: implementation
scope: "post-ship housekeeping increment (targeted re-review, 非全量)"
packet_sha256: "c68cd5ea7597238654f16f2177a863b936aabc6f65011ad00583da31c8aa5eb8"
source_diff_sha256_at_review: "e7b6bfbf68337abc809830b30e1301390016a6eaec4fb7fec824665f79116d44"
review_run_id: "impl-rev-20260827-housekeeping-01"
native_output_ref: "direct"
reviewer: "independent read-only architect subagent (非实现者); 主 agent 逐字转录, 未增删定级"
implementer: "opus tidy subagent (ship 后 .ai_state 整理, .gitignore 为其唯一哈希范围内改动)"
parent_review: "reviews/implementation-review.md (impl-rev-20260827-targeted-rework-01, PASS, 钉 bc586e11=shipped HEAD 树)"
review_date: "2026-08-27"
verdict: PASS
finding_counts: {P0: 0, P1: 0, P2: 0}
dimensions: [spec, correctness, security, tests, overengineering]
---

# Targeted re-review — 9.9.8 ship 后 housekeeping 增量

## 背景

delivery-gate 于 Stop 报 `reviewed_diff_sha256 does not match current source diff`。按 design.md 目标复核契约只审增量, 不重开全量。spawn 写者 reviewer 被 subagent-worktree-check 拦截 (worktree 检出 HEAD 看不到未提交增量, 结构性不适配, 见 proposals.md P14), 改由只读 architect 独立判断、主 agent 逐字转录本档。

## 增量面与漂移归因

哈希范围 (非 `.ai_state/`、非 ignored 的 tracked+untracked) 内唯一变化为 `.gitignore` 追加 3 行:

```diff
+# gate ledger: stop-failure-recorder.cjs 每次 Stop 失败追加 .ai_state/sprints/{slug}/stop-failures.jsonl
+# (存量已跟踪文件不受影响, git 历史可溯)
+.ai_state/**/stop-failures.jsonl
```

**反事实验证**: 同一算法、同一枚举, 仅将 `.gitignore` 替换为 `git show HEAD:.gitignore`, 得数精确还原 `bc586e11e99fbf097db84ba2fa9e3e197375c9da70b5a11d1e3c0184ebbca7a7` (= implementation-review.md 绑定值) → 漂移 100% 归因于该 3 行。

## 哈希复算 (主 agent 复跑, stdout 为准)

安装态 delivery-gate.cjs 与 canonical 逐字节一致 (diff IDENTICAL)。算法 (L281–309): `git ls-files -z -c -o --exclude-standard` → 滤 `.ai_state/` 前缀 → sort → 累积 `sha256(rel+"\0"+bytes+"\n")`。architect 报告中该值多次转写不一致 (其自述抄写错误), 按其要求由主 agent以相同算法复跑: `files=4433, source_diff_sha256=e7b6bfbf68337abc809830b30e1301390016a6eaec4fb7fec824665f79116d44`。packet 现场 shasum 与 frontmatter 一致 (c68cd5ea…), packet 未变。

## 维度结论 (architect 原文转录)

- **Spec/意图**: 与 d832673 commit message 承诺 "Do not commit stop-failures.jsonl (gate ledger)" 及 9.9.8 telemetry/ledger 政策完全一致, 是已声明政策的机械化落地。无 finding。
- **Correctness**: pattern 覆盖 stop-failure-recorder.cjs L44 实际写入路径; `git status --ignored=matching` 实测热 ledger 已呈 ignored; 唯一 tracked 历史副本 (archive/2026/2026-07-25-harness-gate-p1-p4/) 不受影响, 注释属实。无 finding。
- **Security**: 纯 ignore 规则, 无密钥/权限面/执行路径变化。无 finding。
- **Test risk**: 不改代码行为; 被匹配路径全在哈希枚举范围外, 唯一影响是 `.gitignore` 自身内容进哈希。无 finding。
- **Over-engineering**: 单 pattern + 两行注释, 最小实现。无 finding。

## 与 ship 绑定的关系

`implementation-review.md` 保持钉 `bc586e11` 不改——该值 = shipped HEAD 树, 历史准确。sprint 收尾按 stages.md 置 idle (path/stage/current_sprint_slug 清空) 后 ship 绑定解除, 本档独立记录增量审查链, 不重签已 ship 的 review。

VERDICT: PASS

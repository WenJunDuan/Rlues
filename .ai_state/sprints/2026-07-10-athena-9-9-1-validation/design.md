---
sprint_slug: "2026-07-10-athena-9-9-1-validation"
roadmap_item: "validation-delivery"
path: "System"
created: "2026-07-10"
---

# Design — Validation and Delivery

## Scope

关闭 release 总设计 AC1–AC21：在隔离临时 HOME 中实跑 fresh setup、真实 9.9.0→9.9.1 双端事务升级、strict config/doctor、hook/gate 正负矩阵、skill/schema/parity；随后完成三件套 review、polish、architecture、compound、merge/push/cleanup。

## Runtime Matrix

- Normal: 9.9.1 fresh install both endpoints；config/skills/hooks/AGENTS 解析与发现。
- Boundary: CC-only、CX-only、same-version、`--only`、custom provider/NUX/第三方 skill。
- Failure: 17 gate negatives、PostTool unknown/fail、setup 2 fault points、migrate 4 fault points、invalid/unsupported zero-write。
- Environment: Codex 0.144.1 isolated HOME strict config/doctor/debug prompt input。

## Acceptance

- release validator、双端 unit suites、62/62 quick_validate、JSON/TOML/Python/Node/YAML、Git baseline/parity 全绿。
- fresh install 与 full migrate 可复跑；第二次零写/零备份；故障注入无半升级。
- runtime-verify.md 展示正常/边界/异常实际命令与输出。
- reviewer + spec-compliance 返回结果；主线程合并；evaluator 后跑给最终 PASS。
- cleanup-pass、architecture、compound、ship/merge/push/worktree cleanup 全部完成。

## Design Review

继承 release 总设计三轮 critic PASS；post-impl source/installer corrections 已进入本 sprint 的强制复审范围。

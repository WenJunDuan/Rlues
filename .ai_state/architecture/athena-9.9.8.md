---
version: "9.9.8"
type: "release"
slug: "athena-9.9.8"
status: "current"
updated: "2026-08-27"
supersedes: "athena-9.9.6.md"
---

# Athena 9.9.8 架构现状

主题：**Thin PACE Control Plane**。PACE 与 `.ai_state` 仍是内核；agent loop、压缩、工具、权限、subagent、code review 交给官方 harness。

当前发行源：`vibeCoding/{claude,codex}/9.9.8`。9.9.6-hotfix2 是基线。安装态 `~/.claude` / `~/.codex` 是下游，迁移不覆盖用户 model/effort/output-style。

## 审查契约

1. 作者写 `design.md`（含机器可识别验收标准），机械派生 `review-packet.md`（design hash + AC 双射，≤80 行）。作者不自审。
2. 实现与会改代码的 polish 之后，只发起一次原生异步 review。结果 `reviews/implementation-review.md`，绑定 `packet_sha256` / `reviewed_diff_sha256` / `review_run_id` / `native_output_ref`。
3. 维度：Spec coverage、Correctness、Security、Test risk、Over-engineering、Evidence（R/S）。机械项由 gate 判。
4. critic / evaluator / spec-compliance 为 stub。diff 再变只做目标复核；同因新 P0 ×2 交还用户。

## 门禁与状态

- `sourceDiffSha256`：`git ls-files -c -o --exclude-standard` 树内容（含 untracked，排除 `.ai_state/`）；空哈希 fail-closed。
- hook 红 block / 黄 warning / 绿 async；同事件最多一个同步 blocker。
- `_index` ≤12KiB、列表 ≤10、单条 ≤160B；溢出进 `sprints/{slug}/index-overflow.md`，不丢弃。
- telemetry 退出 Git；运行时文件 `.ai_state/.runtime/`（baseline 豁免 retention）。
- VM 与 LLM-as-a-Verifier 仅 opt-in 槽，不进默认热路径。

## 与 9.9.6 的差异

| 9.9.6 | 9.9.8 |
|---|---|
| critic 多轮 + 默认 2+1/passN | 一次原生 review + 派生 packet |
| `git diff HEAD` 绑定（看不见 untracked） | 树内容哈希含 untracked |
| `_index` 只限条数 | 加单条 160B 溢出搬运 |
| 遥测可进 Git | 出 Git |

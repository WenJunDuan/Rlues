---
sprint_slug: "2026-09-24-s3-review-cli"
path: "Feature"
created: "2026-09-24"
roadmap: "athena-10-1"
item: "s3-review-cli"
branch: "athena-10.1"
base_commit: "7527131"
---

# Design — S3 · review 两步命令

> 设计真相：`roadmap/athena-10-1/design.md` §6（D4：review 绑定源码树 sha）。

## 方案

- `gate/cli/review.cjs`：`prepare [--scope implementation|design]` → 运行目录 `.ai_state/.runtime/review/<run>/`（files.json 逐文件 blob sha、packet.md）；`accept --run <id|latest> [--file f|stdin] [--reviewer-agent id] [--family f] [--platform p]` → 解析合同、重算树 sha、写 `sprints/<slug>/review.json` + log 一行 + 暂存；`show [--run id|latest]`。
- packet：AC 清单、base_commit..当前树 变更文件与统计、当前树有效证据、`review_ignore` 列表（显式展示，S2 承接）、「转录」断言、维度、合同指针。
- reviewer 合同：CC `agents/reviewer.md` 正文 = 合同；CX `reviewer.toml`、Pi `prompts/reviewer.md` 同文（fixture 守一致，S5 后由单源生成）。
- 删除 `skills/pace/scripts/review-binding.cjs`（CC、Pi；依赖已删的 9.9.9 hook）。
- H5 附带：`cat > file <<EOF` 且正文为空 → warn（门禁坑「cat alias heredoc 0 字节」）。
- CC workflow（flag `cc_workflows`）：`adapters/cc/package/workflows/athena-review.js`：prepare → 按维度并行 reviewer → 对抗核验 → accept。

## 验收标准

- AC1: `athena review prepare / accept / show` 可用；`--run latest` 取最近一次 prepare；错误用法非零退出。
- AC2: prepare 之后源码树变了，accept 拒绝并逐文件列出 预期/实际 blob sha（含新增/删除），提示重新 prepare。
- AC3: 合同只要求 `VERDICT:` 一行 + `- [P0-3] <file>:<line> — <text>` 发现项；多于/少于一行 VERDICT 拒绝；reviewer 不写 run id/时间戳/frontmatter；三端合同文本一致。
- AC4: 门禁坑逐条回归 fixture：#1 修完 findings 重新 prepare 即可 PASS；#2/#9 无回执、review.json 由 CLI 生成；#3 athena run 证据被 H2 接受；#5 同一 reviewer 可再审（仅 A10 提示）；#6/#10 无 tracker 要求；#8 `--run latest`；#11 AC 缺失时报错列合法形态；cat 空 heredoc 给 warn。
- AC5: `athena-review.js` 存在于 CC dist `.claude/workflows/`，语法可被 node 解析，声明 meta 且只调用 CLI 完成 prepare/accept。

## 不做

skills 文案重写（S5，若保留）；安装时按 flag 取舍 workflow（S6）。

## 已裁量（review r1 后）

| 点 | 做法 | 理由 / 边界 |
|---|---|---|
| reviewer 输出与 run 的绑定 | 不做回执（D1）；accept 拒绝：同一输出 sha 被别的 run 用过、`--file` 早于 packet、prepare 后源码树 / review_ignore / 验收行变化（退出码 4） | 防重放与陈旧；无法证明「真有独立 reviewer 读过」——由 A10 与人审兜底，已知边界 |
| 验收行变化 | review.json 记 `ac_sha`；H3 与 `review show` 对比 design 当前 AC | .ai_state 不入树 sha，AC 变更需单独绑定 |
| cross_family_review 开启 | reviewer.family 未知（未传 --family）= 不通过 | 防省略参数绕过 |
| 解析器 | 围栏外所有含 VERDICT / [Pn] 的行必须严格合规，否则拒绝 | 防夹带 PASS |
| CC workflow | 任一维度 reviewer 缺失 → 返回 INCOMPLETE 不 accept；核验缺失保留发现项；accept 用 prepare 的 run id 并回报退出码 | 不 fail-open；reviewer 以默认 agent 类型运行、只读靠提示（待 S7/平台验证） |

---
doc_type: requirement
slug: athena-10-1
created: "2026-09-24"
status: finalized
owner: user
roadmap: ../roadmap/athena-10-1/roadmap.md
---
# 需求 · Athena 10.1

> 原始需求（用户与 Claude 在 2026-09-24 会话中商定）。定稿后冻结，修订只在文末追加。

## 1. 背景与目标

- 9.9.9 之后提示词、门禁、状态档案都在膨胀：`.ai_state` 一半提交在记账、每 sprint ~15 个过程文件、冷层随 clone 下载、门禁修复要在 cjs/py/Pi 三处各改一遍，Q12 验收 9 条未生效。
- 规划散在 7 处以上（next-version 提案、9.9.9 roadmap、Q12 roadmap、proposals、harness-patches、explore、quantum 侧待上游），需要合成一次迭代。
- 目标：版本号 **10.1**（用户指定）；方向**大胆、紧贴并超过** Claude Code / Codex / Grok Build / Pi 的最新设计；覆盖 CC、CX、Pi 三端。

## 2. 范围

**做**
1. 单源构建三端发行。
2. 一个门禁核替换三份实现；硬门只管可机器核验的事实。
3. review 流程简化为两步。
4. `.ai_state` v2：`docs/`（原始需求、调研、报告）、`decisions/`、`issues.md` 一本账；需求 → 拆解 → sprint → 归档 → 延后全生命周期；自动归档与打包。
5. 提示词按最新官方指南重写（宪法、规则、skills、agents）。
6. 安装/回滚/核对工具，退役手工台账。
7. 评测驱动发布；门禁拦截与纠偏自动进问题账（自进化输入）。
8. 超前接入：CC Tasks/动态 workflow、Pi 0.87 硬停、Grok Build 适配端（先探测）。
9. harness-iteration skill 去保守化（v2.0，已出提案卡）。
10. 迭代完成后：Rlues `.ai_state` 整理、清理分支、推送。

**不做**：静态 DAG 引擎、自动合并 harness 补丁、向量记忆、按模型分叉提示词、VM 运行协议重做、全栈业务切片验收（后两项 deferred）。

## 3. 验收（用户视角）

- 三端装的是同一份源生成的东西，`athena doctor` 能证明本机安装与发行一致。
- 日常开发中不再被已知的 9 类误拦卡住；门禁拦下时给出一句能照做的解锁动作。
- 做一个 Feature：`athena sprint start` → 写 design → 实现 → `athena run` 跑测试 → `athena review prepare/accept` → `athena ship`，sprint 目录只有 4 个文件，ship 后自动归档。
- 原始需求、调研、报告、决策、问题都有固定位置；任何人打开 `.ai_state` 能在 1 分钟内说出当前在做什么、下一步是什么、有哪些待我拍板。
- quantum-agent 在 10.1 上完成至少一个真实 Feature。

## 4. 待澄清问题（全部已有结论）

| # | 问题 | 结论 |
|---|---|---|
| 1 | 版本号 | 10.1（用户指定，CHANGELOG 注明跳过 10.0） |
| 2 | 冷层处理 | 推荐按月打包入库（用户未反对） |
| 3 | compound 去留 | 拆：决策 → decisions/，教训 → 规则或原生记忆，调研 → docs/research/ |
| 4 | grok 分支 | writer-provenance 5 提交已合入 main（221/221）；q12-review-binding 已全量在 main；两分支待用户在 Mac 上移除 worktree 后删除 |
| 5 | D1–D9 设计决策 | 见 design.md §0，待用户逐条确认 |

## 修订

（空）

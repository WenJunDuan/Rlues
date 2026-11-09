---
sprint: "2026-11-09-vibecoding-deploy"
path: "Quick"
created: "2026-11-09"
req: ".ai_state/requests/2026-11-09-vibecoding-deploy.md"
roadmap: ""
item: ""
base_commit: "1dce017"
review_ignore: []
---

# Design — 2026-11-09-vibecoding-deploy

## 背景

本地源码 10.1.9（HEAD 1dce017），origin/main 6bb805b 的 vibeCoding 为 10.1.8；远端新增 6 提交均在 Surge 配置，本地新增 6 提交包含 Athena 修复与 UI 技能。现有 dist 缺 UI 技能；doctor 报 tree-sha 与四个 CC agent 漂移。本地未提交 agent 100 轮与 session-workflow 规则也属于当前待部署内容。

## 方案

按已有 athena-setup 安装器流程重建当前工作树，跑构建/提示词/安装回滚及相关门禁 fixtures，dry-run 后更新本机 cc/cx。安装器合并用户配置并自动备份。用户本轮“部署上去”已授权本机部署。源代码和其他已有未提交改动不改写，追加范围见用户本轮授权：清理近两个月以前的历史及确认无用的缓存/插件残留/旧备份，再同步和推送本仓。

## 验收标准

- AC1: 构建、提示词、安装/回滚、H4/tree-sha 回归检查通过。验证: athena run --covers AC1 -- python3 -B -m unittest discover -s vibeCoding/athena/evals/fixtures
- AC2: 重建 dist 与当前源码一致。验证: athena run --covers AC2 -- node vibeCoding/athena/build.mjs --check
- AC3: 本机 cc/cx 安装 doctor 无漂移，新增 UI 技能和会话规则已安装，用户配置与 hook 保留。验证: athena run --covers AC3 -- node vibeCoding/dist/athena/10.1/cli.cjs doctor

- AC4: 删除最后活动早于 2026-09-09 的会话及可确认无用的缓存/插件残留/旧备份，保留最近会话、当前插件/运行时与最新安装回滚点；清单和释放空间记入 log。
- AC5: 合入 origin/main，提交本次 Athena 源码和对应记账并推送 origin/main；远端包含最终提交。
- AC6: 汇报 Rlues 开放 issues 数量和条目。

## 允许写集

vibeCoding/dist/**（生成）；~/.athena、~/.claude 与 ~/.codex 的安装器托管文件、~/.agents/skills；本 sprint 记账；经审查的旧会话和无用缓存/插件残留/旧备份；本仓分支与远端 main。

## 不做

Pi 部署、无关配置改动、版本号升级、Codex warning 修复。clash/mihomo_sparkle.yaml 的既有改动保留在本地。

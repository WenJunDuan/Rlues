# Athena 10.1.5 Mac 发布门（2026-10-05）

结论：Claude 候选 `3552697` 的全量测试、cc/cx 真机安装、doctor、P8 原生 Quick→ship、rollback 均通过。演练结束后本机恢复 **10.1.0**；`main` 与 `v10.1.5` 的发布决策待用户裁定。插件 experimental、P1–P7/D-014 顺延的范围不变。

## 正式证据

| 项 | 结果 |
|---|---|
| 候选全量 | `athena run --covers AC1 -- python -m unittest discover -s vibeCoding/athena/evals/fixtures -q`；Mac 329 项、零跳过、145.029s；证据 `260bb9180af0`，源码树 `1858bea497ea`，对应候选 `3552697` |
| Python 环境 | uv 临时环境提供 pytest/PyYAML；没有添加项目依赖或修改系统 Python |
| 真机安装 | 两轮均 `install --platform cc,cx`：write 233、merge 3、retire 0；版本 10.1.5，doctor 无 drift |
| 首轮 P8 | 原生 Claude Code 2.1.289 会话完成 init→Quick→Write/Edit→node:test→ship→idle；1 项测试通过，P8 证据 `be979e85440b` |
| 补充 P8 | 已有 sprint 状态下原生启动，实际接收非空 `hookSpecificOutput.additionalContext` JSON，然后测试→ship→idle |
| Hook 事件 | 两轮合计 52 个原生 hook 响应，全部 success/exit 0；含 SessionStart、UserPromptSubmit、PreToolUse、PostToolUse、Stop；无解析/序列化误拦 |
| 回滚 | 两轮 `rollback` 均恢复 10.1.0，doctor 无 drift；第二轮 238 个管理路径的内容、权限与该轮安装前基线一致 |
| 发布门断言 | 4 tests 通过；证据 `d79c346a25a0`。断言原生事件、归档、真实 doctor、逐文件回滚和历史保留，未用直接 hook 调用冒充原生验证 |

发布说明更新后的源码树 `e16cb17f7539`：全量 329 项、零跳过、137.550s（592aeaaba345）；4 项发布门断言通过（64ea1cff8df9）；发布声明证据 af82443a7209。最终绑定由本次 sprint 的 `evidence.yaml` / `review.json` 保存。

## 原生会话与限制

- 首轮 session：`63931715-8e4e-4440-847a-a6e95e9c0bd5`；补充 session：`f3ff9713-8dde-4ea6-a4a3-be32fb1b696a`。均保留在 `~/.claude/projects/`。
- 首轮 35 个 hook 响应；因 SessionStart 时尚未 init，上下文输出为空。因此补做已存在 sprint 的原生启动，17 个 hook 响应中实际收到状态 JSON，确认该输出被平台正常接收。
- 首轮两条辅助查看命令（附加 echo、git status）因 headless allowlist 被平台拒绝，必需的 Athena/Write/Edit 步骤均成功。没有扩大权限或绕过门禁。补充会话只执行单条 Athena 命令。
- 两轮原生会话 CLI 估算费用合计约 $0.99；使用用户既有模型配置，没有指定模型或 effort。
- API/CLI 依据：[Claude hooks 官方文档](https://code.claude.com/docs/en/hooks)、[CLI reference](https://code.claude.com/docs/en/cli-reference)。生命周期数据来自本机 `--include-hook-events`，非模拟。

## 首轮配置变化

首轮安装前快照与回滚后比对：237/238 个管理路径相同；`.claude/settings.json` 的 `/effortLevel`、`/modelSettings`、`/env/ANTHROPIC_DEFAULT_OPUS_MODEL`、`/env/ANTHROPIC_DEFAULT_FABLE_MODEL` 在运行窗口内变化。备份里的安装前文件与快照哈希相同，运行后文件也由 rollback 保留在 `after-install/`；回滚后的实时配置随后再次出现同一变化。

本轮没有编写修改这些模型字段的命令，也不把该变化归因于安装器。来源待用户核实；保持实时配置，旧值与运行后值均完整留存。第二轮从当前配置建立基线，全部 238 个路径准确回滚，证明当前设置下的安装器回滚成立。

| 事务 | 保存位置 |
|---|---|
| 首轮 | `~/.athena/backups/20261005T033035812Z/` |
| 第二轮 | `~/.athena/backups/20261005T034510227Z/` |

备份可能含用户私有配置，不进入 Git、不展示内容、不删除。

## 清理与历史保留

- 删除上轮 Pi 类型检查的临时 `athena-pi-typecheck-x0uq9ujp/node_modules`：152,233,350 bytes（约 145 MiB）。保留 package-lock 与扩展输入，依赖可重建。
- 安装前记录的 7,106 个会话/历史/项目/SQLite 文件全部存在；原生验证新增的两个会话也已确认持久化。
- P8 测试项目与证据在 `.ai_state/.runtime/release-10-1-5/p8-project/` 保留；其源码与状态在同一测试仓提交中保存。
- 现有配置备份逐字节比较后没有重复项，因此保留。未删除历史、有效回滚事务、活动应用缓存、锁文件或 Git 临时配置。

## 产物与决策

安装 stdout/stderr、逐路径哈希、安装事务、native 事件流（副本剔除模型思考块）、清理清单位于 `.ai_state/.runtime/release-10-1-5/`；版本化验证脚本随本 sprint 归档。源码运行行为相对 `3552697` 未改，本轮只更新发布说明与事实记录。

五项 polish：无新增调试代码；注释与目录改动一致；无重复实现；无新增性能路径；无新抽象或防御性兼容层。架构沿用 Claude 的单源 docs/ 整理，未新增子系统。

建议发布门通过且独立复审 PASS 后，将候选快进到 main 并打本地 `v10.1.5`；不 push。用户本轮第 3 步将这一决定留在验收之后，本报告不代替最终发布确认。

独立复审：PASS，run `12ede670-7f61-4b2b-b9f1-5c4db35ec773`，AC1–AC5 全覆盖；独立复跑 4 项发布门、22 项构建、13 项 writer，旧版 Git 解析通过。安装副本的 53 个门禁文件与当前源码一致。原样输出随本轮 sprint 归档。

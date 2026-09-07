# athena-dev · 任务切换与恢复（9.9.9）

分诊正文只在 [SKILL.md](../SKILL.md)。本页处理已有 sprint 与新输入的关系，使用现有 `_index.md` 和 `session-log.md`，不增加任务数据库或按关键词自动改状态的 hook。

## 哪些输入消费旧 next_action

先比较最新用户目标和当前 sprint 的 Done Contract。只有继续原任务、原任务纠偏或其真实原生完成通知，才消费该任务的 `next_action`。新目标优先按 SKILL.md 分诊，不能被旧 rework_impl/polish/await-review-result 劫持；查询进度只回答事实，不自动执行旧动作。

| 原任务恢复值 | 动作 |
|---|---|
| 空 | 按实际未完成工作继续；没有工作时不凭空造任务。 |
| next_roadmap_item:{slug} | 验证该 item 与依赖，进入它的 plan。 |
| roadmap_complete | 核对切片完成事实，再报告。 |
| rework_impl / runtime-verify / polish / ship | 核对相应输入与证据，恢复对应阶段。 |
| await-review-result | 回读真实请求；不重复派发，不把未知当PASS。 |
| re-route | 对同一任务重新分诊，只升不降；用户明确授权的范围降级除外。 |

## 独立执行任务插入已有 sprint

1. 确认不是正在修改同一验收的延续；新任务不能用来逃避原任务的失败验收。读取实际工作树、活动原生任务；有 writer 运行或未完成 review 绑定时，不修改它们所属的共享索引。先使用独立隔离工作区，或完成可独立进行的只读检查并报告具体冲突，不能猜测它们已停止。
2. 在旧 sprint 的 session-log 留最短恢复事实：原 path/stage/current_sprint_slug/current_roadmap_slug/next_action、当前任务相关 pointers、design_changed_after_impl、适用 skip 字段、活动任务/工作树和未提交增量。原设计/审查/证据文件保留；同一字段仍只有索引拥有当前执行权。
3. 选择描述本次目标的新 slug，在该 sprint 的 session-log 记录目标、允许改动范围、可观察完成条件、用户已有授权与旧 sprint 的恢复入口。Hotfix与只读Quick只用最短session-log记录范围/完成条件，不机械创建design/checklist/route-note。
4. 用现有索引写入机制一次更新真实路由：Hotfix 的 `path: Hotfix`、`stage: impl`、新 `current_sprint_slug`；只读诊断用 `path: Quick`、`stage: plan`（不进入实现链）；非 roadmap 插入任务清空 `current_roadmap_slug` 与旧 `next_action`。不把旧 design/review/cleanup 指针、design_changed_after_impl 或 sprint 特定 skip 例外带给新任务；长期用户偏好保持。只读回验后立刻实施，不只更新历史说明。
5. 新任务按本身合同验证并进入 ship；结果和实际提交写 session-log。原 sprint 仍未完成，不能将新 Hotfix PASS 算入它的整体验收。独立检查也必须让最终Stop消费本次Quick合同，不能仅口头宣称Quick而保留System执行字段。原任务恢复时，按旧日志回验真实任务/工作树与合同，恢复原执行字段和未完成动作；本轮用户没要求继续原大任务时，不自动开跑它。

阶段从任务性质确定：纯检查业务系统保持只读，新Quick记录在plan完成诊断后进ship；Hotfix 直接 impl；Quick/Feature 需求已明确则 plan。brainstorm/roadmap/design 只在触发条件成立时进入。使用现有工具与真实返回，不执行旧版示意里的未定义 slugify/update_field/read shell 命令；不强制复制 checklist 或 route-note。

## 本次故障样例的期望行为

- “远程到192.168.31.10，key在.ssh下面，检查OpenList容器部署、优化空间、媒体播放一直重试”：Quick/只读诊断。先检查SSH配置/已知主机与可用公钥引用，使用既有凭证连接，读容器状态/配置/日志和相关播放请求；不输出私钥，不未经授权重启或改配置。只在身份无法确定或权限/网络失败时问具体缺项。
- 同样的输入出现在旧 System/impl/rework_impl 会话：仍先做该只读检查；用本次Quick记录隔离旧System的最终门禁，保存原恢复事实，不运行旧System的实现/审查，不要求用户选择Hotfix/System。
- “这个新发现的配置错误现在按Hotfix修”：范围和改法足够时按已授权 Hotfix直接实施；独立范围按上文切换，不把整个旧System降级。
- “继续处理原System审查发现”：回原sprint检查review绑定与实际输入，恢复rework；不能为了省门禁另造Hotfix。

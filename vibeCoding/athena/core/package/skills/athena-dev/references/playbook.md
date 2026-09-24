# athena-dev · 任务切换与恢复

## 哪些输入消费旧 next_action

只有继续原任务、对原任务纠偏、或它的真实完成通知，才执行 `_index.next_action`。新目标先按 SKILL.md 分诊，不被旧的「rework / polish / 等 review」劫持；查询进度只答事实。

## 独立任务插入已有 sprint

1. 确认不是在修同一条 AC 的延续——新任务不能用来绕开原任务的失败验收。
2. 核对实际工作树与仍在运行的子 agent / 外部写者；它们在写的共享文件不动。需要改代码时用独立 worktree。
3. 在旧 sprint `log.md` 末尾写恢复事实：path、stage、next_action、活动 worktree / 子 agent、未提交增量。
4. `athena sprint pause --resume-when "<条件>"` 暂停旧 sprint（条件如 `after <roadmap>/<item>` 或一句人话）。
5. 按新任务本身分诊：`athena sprint start …`（Hotfix 直接 impl）；只读检查不开 sprint。
6. 新任务按自己的合同验证并 ship；它的通过不计入旧 sprint。
7. 恢复：`athena status` 看等待项（条件满足标 ready）→ `athena sprint resume <slug>` → 读 log.md 末尾的恢复事实，回验工作树后继续。用户本轮没要求时不自动开跑旧任务。

## 样例

- 「远程到服务器，检查某容器部署与播放一直重试」：Quick 只读。用既有 SSH 配置连接，读容器状态、配置、日志；不输出私钥，未经授权不重启、不改配置。只在身份或权限确实缺失时问具体缺项。
- 同一输入出现在进行中的 System 会话：照样先做只读检查，不跑旧 System 的实现或审查，不要求用户选路径。
- 「这个新发现的配置错误按 Hotfix 修」：范围清楚就直接修；按上文切换，不把整个 System 降级。
- 「继续处理原 System 的审查发现」：回原 sprint，`athena review show` 看结论，修复后重新 prepare；不另造 Hotfix 绕门禁。

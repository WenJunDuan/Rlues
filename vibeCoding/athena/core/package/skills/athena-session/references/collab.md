# 多人协同（多个开发者 / 多个 AI 会话）

- 并行切片写集两两不相交；同文件或有未完成依赖的交给一个会话。认领写在现有 queue / sprint 一行（DRI、会话、仓、路径、分支），不另建锁服务。
- 每个切片一个人类 DRI；AI 会话只执行，agent 认领的 issue 挂在 DRI 名下。tracker issue 是派发面，sprint 与 `.ai_state` 是执行与证据真源，不双向同步。
- 换人交接只追加 HANDOFF 顶部一段：在途、阻塞、下一步、DRI。
- 冲突以主干为准重放切片意图；语义冲突由 DRI 收。保护面按 CODEOWNERS 找人，一名 owner 通过即可；AI review 只报缺陷，不代替 owner。

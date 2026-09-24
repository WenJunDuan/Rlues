# 派工、隔离、整合

## 写入分区

| 区 | 条件 | 谁写 |
|---|---|---|
| 绿 | ≤3 文件且 ≤150 行，或 Hotfix/Quick/Bugfix | 主 agent |
| 黄 | 单模块 Feature | generator 子 agent；worktree 可选 |
| 红 | Refactor/System，或 `parallel_writers ≥2` | 写者子 agent + 隔离 worktree（H4） |

review 窗口内（prepare 到 accept 之间）还有并行写者（含文档）时，也按红区隔离：设 `parallel_writers: 2` 让 H4 生效；否则源码树一变，review 就作废。

改动对象在仓库外（安装态 harness）时 worktree 无效：设豁免 `harness_target_outside_repo`，逐文件备份，单写者串行。

## 派工模板

任务消息给：角色、sprint、绝对工作目录、基线 commit、允许写集、要满足的 AC、验证命令、交回内容。固定两句：
- 「不带 `model:`（用户点名除外）」——模型继承用户设置。
- 「commit 署名按你会话的 attribution 规则」。

子 agent 到轮数上限返回实际进度，不算完成；续做用 SendMessage 发给同一个 agent（CC），不另派新 agent。续派不改变门禁判定。

## worktree

Git worktree 不带未提交内容：先提交或传递增量并校验。写者交回后，主 agent 核对（分支是 main 祖先 + 复验通过）即清理 worktree 与临时分支；返工时重建。`.ai_state` 只由主 agent 写。

## 外部写者（grok 等）

- 简报：同派工模板 + 「证据只写主仓 `.ai_state/.runtime/evidence/`，不在仓库根写任何证据文件」。
- 核名：模型名用 `grok models` 查，不凭记忆。
- 解析：`--output-format json` 的输出取最后一个顶层 JSON 对象。
- 402（余额耗尽）：立即停派，记 `athena issue add --type env`，改本端写者。
- 接回顺序：`athena sprint start`（Bugfix 用三段式 design）→ cherry-pick 写者提交 → 主 agent `athena run` 复跑检查。外部写者的自测不算证据。
- 在 sprint 目录放 `external-writer.json`（写者、模型、基线、提交）满足 A1。

## 整合

主 agent 是唯一整合者；共享 schema、锁文件、索引指定单一写者。多个 worktree 各自通过不等于整合通过：在最终代码上重跑 `athena run` 再交 review。跨机器交接给可访问的基线、commit 与校验值。

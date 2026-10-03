# 使用反馈（下游项目遇到的门禁与 CLI 问题）

下游项目实际使用时撞到的问题，按「现象 → 影响 → 当时绕法 → 建议」记。修了就在「状态」列写提交号，不删行。项目侧问题账 id 一并列出，便于对账。

## quantum-agent（Athena 10.1.0，CC 平台）

已修的旧账（G-001 取号、G-002 VM ssh 证据、G-003 packet 变更清单）见 `d8ae223`、`5bdd535`，不重复。

| 项目账 | 级 | 现象 | 影响 | 当时绕法 | 建议 | 状态 |
|---|---|---|---|---|---|---|
| G-004 | P2 | H4：System 路径下，VM / runtime-verify 子 agent 只在 VM 上操作、只写 `.ai_state/docs` 证据，也被要求 `isolation: worktree`。豁免 `h4_worktree` 只能手改 `_index.exemptions`，没有 CLI；CC auto 模式分类器把手改门禁状态判为绕过，直接拒 | 合法豁免路径在 auto 模式下不可用；VM agent 被迫进 worktree，产物要主 agent 拷回，`athena run -- ssh …` 证据也只能由主 agent 在主仓补跑 | VM agent 进 worktree；结果拷回；主 agent 补跑可证明命令 | ① 加 `athena exemption add --key --until --reason`（CLI 写入、可审计，分类器不会当成手改门禁）；② 或 H4 识别 runtime-verify / VM 角色（不写源码树的子 agent 不要求隔离） | 待修 |
| G-005 | P2 | `VAR=1 athena run -- node --test x`：环境变量前缀不进证据命令串；被测文件按该变量决定是否跳过时，照证据命令重放得 `tests 0`、exit 0 | 证据可空过：零用例执行仍记 provable PASS（reviewer 实际抓到一次） | 人工在 design / 派单里写明 env；reviewer 核输出计数 | ① 记录调用时的非默认 env（或提供 `--env K=V` 并写进命令串）；② 识别 node --test / pytest 的「tests 0」并判 unprovable | 待修 |
| G-006 | P2 | 只能有一个活跃 sprint：并行片要 `pause` / `resume` 轮换；`pause` 在代码已合入时仍记 `paused_stage: design`；`review prepare` 按 `base_commit..HEAD` 取 diff，中间夹着另行 ship 的他片提交 | 审查范围被污染，只能在派 reviewer 时人工说明「某段提交不在本片」；状态与实际阶段不符 | 派单说明范围；轮换 sprint | ① packet 支持按提交集或「本片提交」取 diff（如记录写者分支 / 提交区间）；② resume 后可更新 base；③ 或支持多个热 sprint（`_index` 已有 parallel_writers 概念） | 待修 |
| G-007 | P3 | `review accept` 要求每条发现都是 `- [Pn] <file>:<line> — <text>`；证据级发现（某条 evidence 空过、packet 自身问题）没有文件行号 → `malformed finding line` 拒收 | 主 agent 被迫改写 reviewer 原文，与「主 agent 不改写 reviewer 输出」冲突 | 把证据级发现挪到正文非列表段 | 允许 `- [Pn] evidence:<id> — …` / `packet — …` 等非文件定位前缀 | 待修 |
| G-008 | P3 | `athena run` 对文档核对（如 `grep -l <段落> docs/*.md`）记 `kind=other provable=false` | 纯文档 AC 没有可证明通道 | 借 docs-contract 等测试的 run 一并 covers | 认一类「文档断言」：只读命令 + 目标文件在源码树内即可证明；或在 design 允许 AC 标 `证据: review` | 待修 |
| G-009 | P3 | `~/.athena/bin` 不在 shell 与子 agent 的 PATH | 主会话首次 `athena: command not found`；generator / reviewer 都报「未装 athena」而不记 `athena run` 证据，证据全靠主 agent 复跑 | 每条命令前 `export PATH=$HOME/.athena/bin:$PATH` | `athena install` 写入平台 shell 环境（CC `settings.json` env.PATH 或 SessionStart hook 注入），`doctor` 检查子 agent 可见 | 待修 |
| G-010 | P3 | H5 按命令文本匹配 `git push`：复合命令整条被拦（前面的 commit / ship / heredoc 写文件也不执行）；提交信息或 heredoc 正文出现该字样也拦；按**当前仓** stage 判别的仓的 push；门禁解析器不认 heredoc 里的反引号（`unparsable command substitution`） | 前面的写文件静默没执行，后续 commit 缺文件；跨仓操作被误拦 | push 单独一条；提交信息走 `-F` 文件；跨仓用 `git -C`；含反引号内容用 Write 工具 | 按解析出的命令判（只看实际执行的 `git push` 子命令及其目标仓），heredoc 正文不参与匹配；拦截时明确提示「整条未执行」 | 待核是否仍复现 |

### 非 Athena 但影响派工的环境事实（供 `execution.md` 外部写者节参考）

| 现象 | 绕法 |
|---|---|
| codex `--sandbox workspace-write` 在 linked worktree 里 `git commit` 失败：创建 `<主仓>/.git/worktrees/<wt>/index.lock` 被拒（`--add-dir <主仓>/.git` 不一定够），同次会话后续又能提交，原因未明 | 简报写明「提交被拒就留逐条补丁 + commits.json + order.txt」，主 agent 按补丁代提交，逐文件比对工作树 |
| codex 沙箱清 setgid，约 14 条目录权限测试在写者侧假失败 | 写者只列不修，主仓复跑为准 |
| 外部写者自行「恢复」被主 agent 改指的 node_modules 软链 | 简报写明不得改软链 |
| CC 子 agent 70 轮上限常撞 | 简报要求先提交再续；用 SendMessage 续派同一 agent |

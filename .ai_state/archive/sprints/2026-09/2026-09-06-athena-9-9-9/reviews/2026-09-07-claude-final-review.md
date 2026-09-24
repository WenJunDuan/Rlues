# Athena 9.9.9 候选包终审 (2026-09-07, Claude)

> 对象: `vibeCoding/{claude,codex}/9.9.9` @ `dc1e347` · 链路: Codex 设计/实现 → Grok 核对补全 → Codex 完整性审计 → **本次 Claude 终审**
> 方法: 本机复跑 validator (58/0 复现) + 4 路独立审计 (CC hooks / CX hooks+parity / 提示词层 / 安装器+VM) + 关键项人工复核
> 边界: 静态+fixture 级审查; 未跑 CC/CX 原生 CLI 全链路、未跑 E1–E3、未装机

## 结论

**VERDICT: REWORK — 不装机。** 2×P0 / 11×P1 / 大量 P2。

一句话: 9.9.9 的核心卖点 (AC6 证据绑定 / AC7 审查绑定) 在**已迁移项目上默认关闭**、开关由 agent 自己可写; CX 安装态审查 CLI **import 即崩**; 安装器备份清理会**删掉唯一可回滚备份**。validator 58/0 全绿是因为它只测包内布局和合成 fixture, 不测安装态、不测迁移项目、不测 push 路径。

与 9.9.8 review 对照: 9.9.8 F1 (untracked 不可见) 已修 (`ls-files -c -o`), F2 strip 已修, F3 "零 runtime fixture" 部分修 (21+27+4+3 用例), F4 validator 口径已诚实。但**新增面重演旧病**: 门禁新逻辑有 fixture, 门禁**开关**和**安装态路径**没有。

## P0 / P1 (必须修, 顺序即优先级)

| # | 级别 | 位置 | 问题 | 失败场景 (已复现) | 修法 |
|---|---|---|---|---|---|
| 1 | **P0** | CC `_input-binding.cjs:22-28` · `delivery-gate.cjs:236,374` · CX `_input_binding.py:33-41` · `delivery-gate.py:1109` | 整条 9.9.9 绑定链由 `_index.md` 的 `version ≥ 9.9.9` 开关; `version` 不在 `INDEX_GOVERNANCE_FIELDS`, manifest 不护; init/migrate **都不 bump 该字段** (用户本仓 `_index.md` 现为 `9.9.8`) | (a) 升级后所有既有项目绑定静默 OFF, 退回 9.9.8 语义; (b) agent `Edit _index.md` 改 `version: 9.9.8` + 手写 `verdict: PASS` + `result: pass` → Feature ship 放行 (双端复现) | 开关改为 hook **自身常量** (装了 9.9.9 hook 即启用), 不读项目字段; 兼容旧项目走 migrate 显式 bump 并记 config-events; `version` 进治理哈希 |
| 2 | **P0** | CX `skills/pace/scripts/review-binding.py:6` | `parents[3]/'hooks'` 假设 skill 与 hooks 同根; setup 把 skill 装 `~/.agents/skills/`、hooks 装 `~/.codex/hooks/` | 安装态 `python3 ~/.agents/skills/pace/scripts/review-binding.py --help` → `ModuleNotFoundError`; **CX AC7 全断**, 测试只跑包内布局 (`test_state_review.py:181`) | import 路径按安装约定解析 (`~/.codex/hooks`) 或把 `_review_binding.py` 随 skill 装; 加安装态 smoke |
| 3 | P1 | `setup-athena.py:335-348, 518-522` | `prune_old_installer_backups` 删**所有**其它带 `transaction.json` 的备份, 不分平台/不分迁移备份 | CX 9.9.8→9.9.9 迁移备份 → 用户 `--only cc` 补一个文件 → CX 备份被删, `--rollback` 返回 2; **任何后续写入让 9.9.8 回滚永久消失** | 只清同平台、同 kind (fresh/redeploy) 且早于当前的备份; 迁移备份永不自动删; 删前列清单 |
| 4 | P1 | `setup-athena.py:435-476` | 事务只是逐文件原子 + 进程内回滚, 不抗硬崩溃; 半装态 `read_version` 判 `same`, `--rollback` 因 `after_sha256` 全量校验拒绝 | `kill -9` 于第 5 写 → settings 已标 9.9.9, hooks 全缺, 不可回滚不可区分 | 先写 journal 再写文件, `read_version` 校验 manifest 完整性; rollback 对"缺失文件"放宽 |
| 5 | P1 | `_review-binding.cjs:71-77,89` (CX 同) | `evidence_refs` 钉 `evidence.yaml` 整文件 hash; evidence-collector 每条验证命令 PostToolUse 追加它; `base_commit` 要求 HEAD 精确相等 | prepare 后 reviewer 跑一次 `pytest` → `accept` 报 `review input changed: evidence_refs`; accept 后任何 commit (含 ship 记账) → Stop 报 `base_commit` 变化, 只能重审。**reviewer 实跑测试 = 自毁 review** | 绑定改为: 源码快照 hash + packet + design; evidence 按 prepare 时**记录 ID 集合**绑定 (允许 append-only 增长); base_commit 只作记录, 一致性靠 source hash |
| 6 | P1 | `pre-bash-guard.cjs:295-300` · `.py:212-217` | `bash -c '...'` 嵌套只传播 danger 不传播 push | 非 ship 阶段 `bash -c 'git push origin main'` 放行 (双端) | 嵌套分析结果整体上抛 |
| 7 | P1 | `pre-bash-guard.py:42-43,127-129,199-205` | CX 版对 CC 版 5 处退化: 注释剥离不识引号 (`-m 'fix #12' && git push` 放行)、长选项 (`rm --recursive --force /` 放行)、不 unwrap `sudo/env/command/\git`、外层异常 exit 0 (CC exit 2) | 同一命令双端裁决相反 | 以 CC 版为基准重写 CX 解析器; 共享 fixture 双端跑 |
| 8 | P1 | `delivery-gate.cjs:1019-1062` · `.py:1290-1315` | 轻门禁只看 `@{upstream}..HEAD` 已提交 numstat, 不看工作区/暂存/未跟踪; CX 排除表只有 `settings.json` 未含 `config.toml/hooks.json` | HEAD 对 upstream 仅改 README, 工作区含源码改动 + 未跟踪 `.py` → light ship, 跳过全部审查 | 轻门禁的 diff 集 = 已提交 ∪ 工作区 ∪ untracked; CX 排除表补齐平台配置 |
| 9 | P1 | `_index-io.cjs:31` · `_index_io.py:53` | 9.9.9 永久尊重旧式 `_index.md.lock`, 无 stale/pid 判定 (9.9.8 有 10s stale); 9.9.8 hook 被 SIGKILL 时 atexit 不跑 | 升级后残留 `.lock` → 每次 update 800ms 超时 "skipped", next_action/溢出/flag 永不落盘, 仅 stderr | migrate 清理旧 lock; 或对旧式 lock 保留 stale 判定 |
| 10 | P1 | `_review-binding.cjs:142` | verdict 取**最后一个**匹配 | 原文 `VERDICT: FAIL … 若补空检查则 VERDICT: PASS` → accepted PASS | 取 frontmatter 或**唯一**匹配, 多个即拒 |
| 11 | P1 | `_input-binding.cjs:52` · `delivery-gate.cjs:238` | `ls-files -c` 含 gitlink → `lstat` 目录 → throw | 任何含 submodule 的仓库 prepare/evidence 全失败, ship 永久 block | 跳过 gitlink 并记录 |
| 12 | P1 | `init-platforms.py:56-57,139` | `intent()` 只识单行 JSON 列表; 块式 `platforms_enabled:\n  - cc\n  - cx` → None → 降为默认端, 再前插新行产出**非法 YAML** | 单一真相源写坏, 无备份 | 用真 YAML 解析 (或两种形式都识), 写前校验回读 |
| 13 | P1 | `runtime-run.py:29,109-111,480` | `SECRET` 正则命中 `api_key = os.environ[...]`、`password = getpass()`、`password: user.password_hash` → **静默**从快照剔除 | 真实项目鉴权模块不上 VM; AC11 越权/权限链场景在 VM 不可复现 | 只按文件路径规则 (`.env*`, `*.pem`, `credentials/`) + 明确字面量 (长随机串) 排除; 剔除必须显式报告不能静默 |
| 14 | P1 | `agents/polish-worker.md:8` + `subagent-worktree-check.cjs:119-124` | frontmatter `isolation: worktree` + R/S hook 强制 worktree; stages.md 说"沿既有实现 worktree、不嵌套隔离" | 每次 spawn polish-worker 都从 HEAD 开新 worktree, 看不到 impl worktree 未提交改动 → polish 清理的是**错误基线** | 去掉 frontmatter isolation; 主 agent 传既有 worktree 绝对路径 (CX 已这么做) |
| 15 | P1 | CX `hooks/session-start.py:190` | 活跃注入 "ship 前必须重新跑 reviewer + spec-compliance + evaluator" | 与 "禁止调度 critic/evaluator/spec-compliance" 直接冲突, 每次 design_changed 都触发 | 改为 "重新走一次独立 review" |
| 16 | P1 | `setup-athena.py:299-307` · `AI-MIGRATION-GUIDE.md` | 迁移只合 `env.VERSION` + `hooks`; 9.9.9 对 9.9.8 的**实际**配置差异 (`permissions.deny Agent(critic/evaluator/spec-compliance)`、`codex-plugin-cc: false`) 不合入; 三个退役 agent 文件照装 | 迁移用户上退役角色可调用; 同版重跑把用户主动删的受管 hook 加回并重排格式 | 合并对象改为 "受管键差异集" (deny/plugins/hooks), 同版重跑真正零写 |

## P2 (影响质量, 不阻塞修复顺序)

| 域 | 要点 |
|---|---|
| 门禁 | `stage` 改成 ship 后 `git push` 即放行, delivery-gate 只在 Stop 校验 → 副作用先于门禁 (结构问题, 双端); CX 同因 3 次 Stop block 后放行 (设计如此但仍是 fail-open, 与 `approval_policy=never` 叠加无人在环); `author_target` 取 `CODEX_THREAD_ID/CLAUDE_SESSION_ID` 子进程多为空 → 自审检测形同虚设; receipt 是 agent 自写 JSON, 伪造无法区分 (结构限制, 至少要在文档承认) |
| 契约 vs 代码 | stages.md 承诺 `design_changed_after_impl → block` / `design.md mtime 晚于 review → block` / "≥5 文件必须**更新** architecture/" — gate 均未实现 (只查 ARCHITECTURE.md 存在); `design-change-detector` 只挂 Edit 不挂 Write |
| CC↔CX 漂移 | `_index` frontmatter 解析规则不同 (CC 缩进行解析 / CX 跳过; 重复键 last-wins / block) → 治理哈希跨端不等, manifest 跨端交接必失败; evidence `result` 语义不同 (CC 按事件一律 pass / CX 按 exit_code); `_index-bounds` bullet 段保留前 10 条 vs route_history 保留后 10 条 |
| 平台假设 | CX `hooks.json` 的 `SessionStart/UserPromptSubmit/PostCompact/SubagentStart/Stop decision:block/statusMessage` 与 `apply_patch` 的 `file_path/patch` 键、`CODEX_THREAD_ID` 注入 — 包内**无一处实测出处** (platform-contracts.md 自己写 "静态文档不是支持证明"); AC14 空 · **待验证** |
| 安装/VM | `vm.schema.json` 零消费者, configure/runtime 接受 schema 拒绝的配置 (SKILL.md "校验" 是假承诺); 远端 runner 自身崩溃一律归 `transport_failed`; `process_groups` 存 pid 在 wait 后仍 killpg (pid 复用可误杀); "required OS 缺失不能假通过" **无实现无测试**; CX 包自带 `test_setup_991.py` 是 CC 测试的逐字节拷贝; py 3.9/3.10 需 `tomli` 未提 |
| 用户配置 | 备份整份 settings.json/config.toml (含 `env.ANTHROPIC_API_KEY` 等) 到 `~/.athena/backups/`, 永不清理 |

## 提示词层 (对 agent 行为有实际影响的部分)

| # | 级别 | 问题 | 位置 |
|---|---|---|---|
| A | P1 | **CC `stages.md` 仍是 9.9.8 原文** (64 行 diff, 18 处版本史标签 `2026-07-28/hotfix2/W35/gate-descaling`), CX 版是干净重写 (102 行, 0 标签)。设计明文 "两端用同一组行为预期", 实际两端阶段义务正文结构性不同 | CC 150 行 vs CX 102 行 |
| B | P1 | 根入口称 "每轮面包屑提示当前 stage 义务", 实测 breadcrumb 预算 240B: review=98B、ship=96B 只有标题行; impl 段唯一注入的是 gate-descaling 版本注释 | `CLAUDE.md:5,11` vs `stage-breadcrumb.cjs:104-112` |
| C | P2 | 路由结论落点三说: 铁律3 `_index.route_history` 一行 / pace SKILL `route-note.md` / athena-dev playbook "必须落盘 route-note 不留痕不算" | 三文件 |
| D | P2 | `checklist.yaml` 可选, 但 athena-dev playbook 进 plan 无条件 `cp checklist.yaml`; Bugfix 流程写 `report → analyze` 但 stage 枚举无此二值; athena-issue 称 "gate 完全不拦 Bugfix" 实际要 fix-note; TDD 豁免 CC generator 无 / CX 有 | 各处 |
| E | P2 | `/goal`、`ultracode`、`Agent Team` 在 CC 文档 6+ 处按 "可用则用" 引用; orchestration.md 全文无 ultracode/Agent Team 定义; CC 无原生 `/goal` — agent 会去找不存在的东西 | `CLAUDE.md:19`、`stages.md:48,57,96` |
| F | P2 | 无消费者 `_index` 字段: `skip_roadmap/network_in_polish/default_path/preferred_tools/plan_critique_*/last_critic_round/platform_features.goal_supported` (违反模板自己的 "每字段须有消费者"); 死引用: `token-usage-collector.cjs`、`docs_researcher` (CC 无)、`~/.claude/mcp.json`、`compound/README.md`、`plan.md`、`reviews/pass{N}.md`、`git diff main...HEAD` 硬编码 | 多处 |
| G | P2 | `rules/*.md` 22KB: `attach_to_rules/stages/subagents` frontmatter、`<important if=…>` 伪标签、"按 stage 自动加载" — 全部**无实现**; 唯一消费者是 session-start 注入前 600B 目录。若 CC 原生无条件加载 `~/.claude/rules/*.md` (无 `paths:` 头), 每会话额外 22KB · **待验证 `/context`**。`coding-standards.md:15-16` "Magic number 必须常量 / 配置项存配置文件 / >300 行必须拆" 列 P0=REWORK, 与铁律7 反过度工程直接冲突 | `rules/` |
| H | P2 | CX 退役角色无机械阻断 (CC 有 `permissions.deny Agent(critic…)`), `agents/*.toml` 可 spawn; `pr_explorer.toml` 是第二 review 角色、输出并入 `pass{N}.md`, 与 "一次 review" 冲突; CC agents 的 `disable-model-invocation` 是 skill 字段不是 subagent 字段 (装饰性) | CX agents |
| I | INFO | 热路径: CLAUDE.md 3626B (9.9.8: 3286, ↑)、AGENTS.md 3998B、pace/SKILL 5548/5721B (超 4KiB 目标)、27 个 skill 描述 3932B 常驻。可删不改义务: 版本史标签 (stages 18 处 / pace SKILL 6 处 / hooks.md 11 处)、`stages.md:90-92` hotfix2 记账段、`:105-111` "文书预算" 病灶数字、`:113-150` 目录树 (CX 用表)、`compound/SKILL.md:86-100` 迁移史; pace SKILL 路径表 + 写入路由表与 CLAUDE.md 铁律2、stages impl 段**三重复写** | — |
| J | INFO | "不暴露私有推理过程 / 不落盘私有思维链 / 只展示结论性摘要" 三处叠加与铁律5 可审计有张力; 建议改 "不落盘原始 CoT; 候选/证据/置信度必须落盘" | `CLAUDE.md:7,13`、`athena-dev/SKILL.md:16` |

Grok/Codex 审计声称已修的 P2 (adapter 路径、quantum playbook 57/58、init 单端探测、CX setup `--only cx`、CX polish playbook:13): **逐条核实已修**。`hooks.md:45` 仍留 `plan_critique_disabled` 开关。

## 测试缺口 (validator 58/0 没覆盖什么)

| 契约 | 缺口 |
|---|---|
| 门禁开关 | `_index.version` 降级 / 缺失 → 绑定应仍生效: 无 |
| 安装态 | CX `review-binding.py` 从 `~/.agents/skills` 运行: 无; CC/CX 安装态 hook 用真实 `~/.claude`/`~/.codex` 布局跑一次 prepare→bind→accept: 无 |
| push 门禁 | pre-bash-guard 任何用例: 无 (含 `bash -c`、引号注释、sudo/env) |
| AC7 CC 端 | 错 run / 晚到旧结果 / 缺结果 / 未提交改动 → accept 拒: CC 侧全缺 (只走 Python 模块); accept 后 commit 仍可 ship: 无 |
| AC4 | ≤10 条上限、overflow 指针可解析、死 contender/旧 `.lock` stale: 无 |
| AC8 | 双 writer 整合/冲突归属: **零用例** |
| AC12 | 备份清理谁被删、kill -9 后 rollback、同版重跑用户改过 settings、真 9.9.8→9.9.9 包迁移 (现有用 `hooks:{}` 合成包掩盖 deny 缺失): 无 |
| AC9/10 | ssh `run` 成功路径与三哈希不匹配、远端 runner 崩溃归因、required OS: 无 |
| 轻门禁 | 分类与 `validateShip` 全链: 无 |

## 做对了的 (保留, 别回退)

1. `ls-files -c -o --exclude-standard` 覆盖 untracked, `.ai_state/.runtime` 排除 — 9.9.8 F1 真修了。
2. `_index-io` 无锁不写、tmp+fsync+rename、内容相同零写; bakery 票号双端字节兼容, 24 次混合并发测试过。
3. `accept` 前后双重 `assertLive`, ship 端重算 receipt/输出 hash 并复验原生 frontmatter, 改 session-log 复活旧结果不可行。
4. 安装器: 会话/历史目录硬拒绝、symlink 一律拒、未选端非法 JSON 也不读不写、ssh 全 argv 列表 + `shlex.quote`、tar 提取拒绝绝对/`..`。
5. runtime 分层状态 (configured/transport/scenario/cleanup) 在传输失败/ready 失败/超时/teardown 失败/中断下均不为 passed。
6. CX `stages.md` 重写干净, 可直接作 CC 版底稿。
7. 三处审计 (Grok/Codex/本次) 口径一致: 候选 ≠ 验收, RELEASE.md 诚实。

## 取舍与判断

- **不要**为修 #1 加 "version 也进治理哈希" 就完事 — 根因是"兼容开关读项目字段"这个模式, 项目字段永远是 agent 可写的。开关必须在 hook 二进制里。
- **不要**再让三个模型各自补一段 — A/C/D/E 类矛盾正是三方协作各写一套的产物。先定**唯一正文** (CX stages.md 底稿 → 双端), 其它文件只引用不复述。
- **不要**继续堆 skill (27 个) — llm-as-a-verifier 这类 opt-in 在核心门禁有 P0 时属于分心; 冻结新增, 直到 AC1/AC7 双端安装态实跑通过。
- 三方协作模式本身: 设计 (Codex) → 实现 (Codex 派工) → 补全 (Grok) → 审计 (Codex) 全在同一"包内 fixture"视角; 缺的是**安装态视角**和**对抗视角**。建议固定一个只跑安装态 smoke 的角色。

## 下一步 (建议顺序)

1. 修 #1 #2 (P0) + 加两条安装态 smoke (CC/CX 真实 HOME 布局跑 prepare→bind→accept)。
2. 修 #3 #4 #16 安装器, 加 kill -9 与 "删备份后能否回滚" 用例。
3. 修 #5 绑定语义 (evidence 记录 ID 集 / source hash 代替 HEAD), 否则 reviewer 一跑测试就自毁。
4. 修 #6–#11 门禁, 双端共享 pre-bash-guard fixture。
5. 提示词层: CC `stages.md` 以 CX 版重写; 删版本史标签与三重复写; 面包屑要么加预算要么根入口别承诺; `rules/` 加 `paths:` 或整体降 references。
6. 修完做**针对性复核** (只看上述文件 diff + 新 fixture), 再决定装机。
7. 装机后才谈 E1–E3 与 AC13; 当前任何效率声明无效。

## 附

- 本次审计产生的临时快照留在用户仓 `.ai_state/.runtime/athena999-review-snapshot.tgz` + `athena999-tests.tgz` (已 gitignore, 可删)。
- 本文档同步至项目 `claude/athena-9.9.9-review.md`。

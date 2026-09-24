# Athena rules provenance（不安装，不进上下文）

每条规则都要追溯到一次具体失败（ratchet）。追不到出处的规则要被质疑；删改前先读懂当初的坑。
「位置」：宪法 = core/package/AGENTS.md；rules/x = core/package/rules/x.md；skill = 对应 SKILL.md；门禁 = gate/rules。
审查方式：harness-iteration（Kirby 审）逐条执行——删除条件成立即删，并在此表注明。

## 宪法

| id | 规则 | 补偿的失败（出处） | 删除条件 | 位置 |
|---|---|---|---|---|
| K1 | 先读 `_index.md`，按指针只读所需 | 全量 glob 把上下文烧光；状态多处矛盾（compound 2026-07-13 index-field-audit） | 平台原生提供项目状态索引 | 宪法 |
| K2 | 分诊；无 AC → brainstorm；≥2 切片 → roadmap | 凭感觉选路径，改动面超限无人回头（compound 2026-07-08 hook-order） | 路由由 CLI 机械判定 | 宪法 + athena-dev |
| K3 | AC 有证据 + 门禁放行才算完成；未完继续做 | 无证据「静默假过」（compound 2026-07-08 token-usage-null）；以说明代替完成（GPT-6 指南：完成标准驱动） | 模型实测不再提前收工 | 宪法 + H2/H3 |
| K4 | 写入分区；review 窗口内并行写者隔离 | 并行 generator 主 checkout 互相覆盖（compound 2026-07-11 worktree-ledger-gap）；review 窗口并行文档写者使 bind 恒拒（NV-C2） | — | 宪法 + H4 |
| K5 | `athena run` 做验证 | 证据缺失当作通过（compound 2026-07-10 codex-wire-evidence） | — | 宪法 + H2 |
| K6 | 误拦记 issue 请放行，不绕过 | 规训写在 prompt 被模型权衡掉（9.9.x 铁律 8） | — | 宪法 + 熔断 |
| K7 | 官方出处；待验证；转述写出处 | 文档层互相矛盾（9.9.6 review）；转录结论无核对（NV-C16/QA-26） | — | 宪法 |
| K8 | 不可逆操作先确认 | 通用安全面 | — | 宪法 + H5 |
| K9 | 记账随代码同一提交 | 记账提交碎片化、孤立记账提交（NV-A4） | CLI 自动归并 | 宪法 + rules/git |
| K11 | 同一路径失败三次带 stderr 报阻塞 | 同一失败换花样硬试、烧轮数（9.9.x CLAUDE.md 根入口） | 熔断覆盖工具失败 | 宪法 |
| K10 | 电报体 | o200k 实测省 21–30%（9.9.0）；文言歧义被否（9.9.1） | — | 宪法 + rules/docs |

## rules

| id | 规则 | 补偿的失败（出处） | 删除条件 | 位置 |
|---|---|---|---|---|
| R1 | P0 DRY/SRP/类型/异常归宿 | 通用工程基线（9.8 coding-standards） | 项目 lint 覆盖 | rules/coding |
| R2 | 反过度工程 | v9.7 一次调研 24 文件无痛点支撑（9.9.3 CHANGELOG） | — | rules/coding |
| R3 | 量化 AC 先测基线；多写者绝对相等 | AC「≤300 行」而基线 341 行致 REWORK（2026-07-25）；多写者 `≥` 互相抵消（2026-07-28） | — | rules/coding |
| R4 | 可达性检索式 | `as unknown as` 访问对 tsc 与 import 分析双隐形（2026-07-28） | — | rules/coding |
| R5 | 安全 P0/P1 | 通用 OWASP 基线 | — | rules/security |
| R6 | UI a11y 与四态 | 通用 WCAG AA 基线 | — | rules/ui |
| R7 | 注释与 `.ai_state` 产物写法 | 产物字段漂移致门禁误判（9.9.x doc-style） | — | rules/docs |
| R8 | Bugfix 三段式 design | 外部写者 Bugfix 缺三件套、分诊路径不同步（NV-B2/NV-C3） | — | rules/docs + templates/bugfix-design.md |
| R9 | Conventional Commits、禁 force push | 通用 | — | rules/git |
| R10 | 子 agent 署名按子会话 | 子 agent 抄主会话署名（NV-B7） | — | rules/git + 派工模板 |
| R11 | `cat`→`bat` alias 写 0 字节 | heredoc 写出空文件（NV-B5/NV-C20） | 用户去掉 alias | rules/shell + H5 warn |
| R12 | macOS 无 `timeout` | 命令直接失败（NV-C20） | — | rules/shell |
| R13 | `!` 前缀无 TTY | sudo 读不到密码挂住（NV-D16） | — | rules/shell |
| R14 | Node/Python 单一版本 | 多版本并存致依赖错装（NV-D18） | — | rules/shell + deps-check |

## 10.1 删除的内容

| 内容 | 理由 |
|---|---|
| 9 条编号铁律全文 | 门禁已机械强制（H1–H5），宪法不复述；编号引用规则一并删 |
| 「INTJ 风格」 | 对行为无可观察影响 |
| 「CC 无原生 /goal」 | 与 CC ≥2.1.269 冲突 |
| tdd-evidence backfill 记法 | 证据改为 `athena run` 记录（S2），tdd-evidence.yaml 退役 |
| Sisyphus / checklist.yaml | 由 H2 证据 + AC 取代 |
| review-packet / cleanup-pass / route-note 产物表 | 产物退役（S3/S4） |
| `attach_to_stages` / `attach_to_subagents` 字段 | 无消费者（9.9.9 hook 已删） |
| README 标准集细项、注释格式样例 | 教科书内容，模型已知 |
| 5 条 9.9.6「待立」候选 | 常驻预算 → 本文件 + 测试预算；全局 env → platform.md；原子写 → 门禁核单写者；文档非一手 → K7；护栏匹配权限面 → H5 |

## 加载方式（S5 决定）

rules 文件头带 `paths`（CC 原生路径作用域：只在读到匹配文件时加载）；`_index.md`、`git.md`、`shell.md` 短小，常驻。Codex / Pi 无路径作用域，按 `_index.md` 表需要时读。补偿的失败：9.9.6 实测常驻预算超标（K 表外的「常驻预算是一等约束」）。删除条件：平台原生按需加载覆盖全部三端。

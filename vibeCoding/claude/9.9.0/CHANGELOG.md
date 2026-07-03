# Athena CHANGELOG — v9.9.0 "Deliberative Router"

发布: 2026-07-02 · 基线: 9.8.0 · 类型: minor (PACE 路由协议结构变化)

## 为什么是 9.9.0 而非 9.8.x patch
路由从关键词匹配换成审议思维链 + 中途 re-route, 改变 PACE 入口语义, 是结构变化 (符合"结构变化才递增").
距 9.8.0 仅 10 天, 短于半月纪律 — 用户显式拍板破例: dogfood 暴露路由死板 + CC 2.1.197/198 与 CX 0.142.x 六月末密集更新窗口不等人.

## A · 路由审议思维链 (拟人化 triage, 取代查表)

- **废除 route() 关键词伪代码**. 旧判据 `len(input.split()) < 8` 按空格切词, 对中文输入恒为 1 → "单词级模糊"判定从未工作过. 规范里的 bug 会被模型忠实执行.
- **新 5 步审议** (pace + athena-dev): 感知 (_index/git log/显式信号) → ≥2 候选假设 (各列证据) → 四维权衡 (爆炸半径/可逆性/紧急度/需求不确定性) → 决策+置信度 (≥0.8 进 · 0.5–0.8 带假设进 · <0.5 问用户或 brainstorm) → route-note 落盘.
- **显式关键词降级为强证据**, 不再短路 ("重构一下这个函数" ≠ Refactor 全套).
- **护栏 = 地板不是天花板**: ≥3 模块至少 roadmap / 跨模块至少 Refactor / Hotfix 唯一免审议; 审议只可加码不可低于地板.
- **中途 re-route 只升不降**: 机械触发 (index-updater: 改动文件数 Quick>3 / Feature>10 → next_action=re-route) + 语义触发 (checklist 膨胀>50% / 跨模块耦合 / 假设被推翻); 升级补欠 stage (runtime-verify/polish/worktree); 降级只能用户显式批准.
- **_index 新字段**: route_confidence / route_history / plan_model ("fable" → System/Refactor 的 plan 审议切 claude-fable-5, Mythos 级 $10/$50, opt-in, 7/1 已恢复可用).
- **新模板**: sprints/route-note.md (≤10 行, 含 Re-route 追加段).

## B · Loop Engineering v2

- **B1 push 门禁**: CC 2.1.198 起后台 agent 在 worktree 完成后**默认自动 commit+push+开 draft PR**, 绕过 review→ship 门禁顺序. 对策: pre-bash-guard 在 Athena 项目 stage != ship 时 block `git push` (逃生: 命令前缀 ATHENA_ALLOW_PUSH=1). **已知边界**: 只拦 Bash 层; CC 内部 PR 机制若不走 Bash 拦不住, 部署后实测一次后台 worktree 流确认.
- **B3 Evidence Cross-Check (U3 落地)**: evaluator 交叉验证 checklist done ↔ evidence.yaml tool_use; done_without_evidence ≥1 → VERDICT 上限 CONCERNS (静默假过是 loop 失败模式); delivery-gate 在 Refactor/System ship 时验 pass1.md 含 `## Evidence Cross-Check` 段. 顺手修 evaluator 里 v9.3 时代陈旧路径 (details/ → sprints/{slug}/).
- **B7 五五路由部分解锁 (U5)**: codex-plugin-cc **v1.0.5** (6/23) 新增 `/codex:transfer` — CC 会话移交持久 CX 线程, 进 orchestration M5c; 插件版本要求 ≥1.0.5. 移交前先 /athena-checkpoint (换执行者, .ai_state 是唯一记忆连续体).
- **未接线 (待验证, 不对未验证 API 编码)**: CC 2.1.178 hooks `if` 条件过滤 (可省 PostToolUse 2/3 进程 spawn) 与 2.1.198 Notification hook (agent_completed/agent_needs_input payload) — 语法未在本机验证; 若 `if` 写错会静默禁用 design-change-detector 这个 CHECKER, 风险 > 收益. 验证后再开.

## C · VM 运行时 (skill athena-vm, CC+CX)

- **新 skill athena-vm**: setup (引导注册) / doctor (连通自检). 配置 `~/.athena/vm.json` (chmod 600, **不进 .ai_state** — 凭证不进会 git 的目录).
- **auth 双形态**: `key` (推荐, ssh-copy-id 一次, 用户亲手输密码, agent 不经手) / `password_env` (降级, 存**环境变量名**不存密码, sshpass -e). 明文 `password` 字段 = setup/doctor 硬拒绝.
- **权限面收窄**: SSH 别名 `athena-vm-{name}` 写 ~/.ssh/config, settings.json 只放行该前缀 (ssh/sshpass/scp/rsync), 不放裸 `ssh *`.
- **runtime-verify 环境矩阵**加"远程 VM"行: 干净环境暴露隐式依赖 / 真实发行版差异 / 破坏性测试隔离; ssh 命令+远端输出照旧晒 transcript (/goal supervisor 协议不变); limits.max_session_minutes 是预算护栏.
- athena-init 探测 `tools_available.vm_available`.

## D · 配置刷新 (CC 2.1.197/198 · CX 0.142.x · 2026-06 底窗口)

- **CC settings**: effortLevel max→**xhigh** (opus-4-8 支持; /effort 显示不支持则回落 max); env 版本 9.9.0; ssh 权限四条 (athena-vm-* 前缀).
- **CC 注意**: sonnet-5 (2.1.197 起默认) 新分词器 **+30% token** — 涉及 token 预算的估算需重校; 手动 thinking.budget_tokens 在 sonnet-5 **硬移除** (本框架未用, 零影响); fable-5 出口管制 6/30 解除, 7/1 全面恢复.
- **Agent Teams 维持不接**: 仍 experimental, 2.1.178 刚删 TeamCreate/TeamDelete (架构还在动, 等 GA).
- **CX config.toml**: model pin `gpt-5.5` 保留 (确定性) + 注释 — **7/23 所有遗留 Codex API 模型永久关停**, 勿把 pin 回退到旧 ID; `[features]` hooks/multi_agent 已默认开 (hooks 5/14 GA, multi_agent 0.142 起), 保留仅为兼容旧版; 注册 athena-vm skill.
- **CX hooks**: 新增 **SubagentStart** 注册 (0.133+ 原生事件, subagent-tracker 拿全生命周期); hook trust 按内容哈希 — setup 覆盖 hooks 后需重新信任 (见 athena-setup ⚠️).
- **codex-plugin-cc ≥1.0.5** (transfer + rescue 递归修复).

## v9.9.0 整合增补 (同日第二批: U1/U2/U6 + 两接线转正)

### U1 · impl 强制 subagent (门禁化)
- delivery-gate 检查7: Feature/Refactor/System ship 前 subagent-log.md 必须含 generator 记录 — 铁律[零写入] 从 prompt 约束升级为机械门禁 (主 agent 全程亲手写 = block). 逃生: `_index.skip_impl_subagent_check=true` (纯绿区微改 sprint).

### U2 · plan 最少 critic 轮数
- delivery-gate 检查8: design.md 的 "Critic Findings" 数 ≥ min (Refactor/System=2, 其余=1, `plan_critique_min_rounds` 覆写, `plan_critique_disabled` 跳过) — 防 critic 一轮敷衍 PASS (自我锚定).

### U6 · plugin 编排
- 新 `references/plugins.md`: 8 个 enabledPlugins × PACE stage 路由表 + 三条仲裁 (产出必须落 .ai_state / 无门禁豁免 / Athena skill 是入口插件是工具). feature-dev 插件在 Athena 项目内禁用完整工作流 (与 PACE 撞车).

### 两接线转正 (fail-safe 设计, 不再是"待验证")
- **hooks if 过滤**: design-change-detector 挂 `if: Edit(**/design.md)` (2.1.178+, 旧版忽略未知字段=行为不变). 风险消化: delivery-gate 新增检查9 **mtime 兜底** — ship 时 design.md mtime > pass1.md mtime + 2s 容差 → block 重新 review. 即使 if 语法失效导致 detector 哑火, gate 兜底 (CHECKER 冗余, 单点检测器不再是单点故障).
- **Notification hook**: 新 notification-router.cjs — agent_completed → additionalContext 软提醒消费 next_action (事件驱动接续, 替代纯 Stop 轮询). Fail-open: payload 全序列化包含匹配不猜字段名, 不匹配/异常零副作用. CX 无 Notification 事件 (已知不对称, hooks.md 已注).

### 行为冒烟 (见下方验证段追加)
- U1: 无 generator 记录 → block / 有 → 过 / skip flag → 过
- U2: 1 轮 Critic Findings + Refactor → block / 2 轮 → 过
- mtime 兜底: design.md touch 晚于 pass1.md → block / 正常顺序 → 过

## v9.9.0 增补 3 (P1/P2 清账 + 电报体)

- **P1 修复**: subagent-retry.cjs 弃写 details/ (9.6.4 废目录, 触发即复活 → 改 sprints/{slug}/); CHANGELOG INSTALL 死链修正; updateNestedField 父域限定 (cjs+py, 行为测试: 同名嵌套键不再误伤); CX index-updater 补挂 PostToolUse(Bash) (原只挂 UserPromptSubmit, Goals 长 loop 中 re-route 滞后).
- **P2 修复**: CLAUDE.md/AGENTS.md 电报体压缩 (o200k: 918→814 / 1025→899, -11~12%, 且净增电报体规则一条); repo 卫生 (.DS_Store ×31 删, 9.8.0 __pycache__ 删, "old version"→old-version); evaluator 模板 sprint-N → {sprint_slug}.
- **电报体纪律** (doc-style + 热路径首行): 骨架句/表格优先/删铺垫复述; thinking 与 block reason 不受限. **文言文数据否决**: 字符 -35% 但 token/字符 0.72→1.04, 净省 ≈0 (样本 2 倒亏), 规范歧义不可接受; 电报体实测省 21-30%.
- **不对称转正**: subagent-retry 双端职责不同系有意 (CC=Task 失败日志 / CX=Bash 兼容轨 tracker), 已写进两端头注, 不再当 bug 追.

## 验证
- 全部 .cjs 过 `node --check`, 全部 .py 过 `py_compile`, settings.json/hooks.json 过 JSON 解析, config.toml 过 tomllib.
- 审议协议为 prompt 层规范, 冒烟: 对同一模糊中文输入, 路由必须产出 ≥2 候选 + 置信度, 且 route-note 落盘.

---

# Athena CHANGELOG — v9.8.0 "Loop Engineering"

发布: 2026-06-22 · 基线: 9.7.1 · 类型: minor(PACE stage 结构变化, 非 patch)

## 为什么是 9.8.0 而非 9.7.x patch
插入 `runtime-verify` + `reflect` 改变了 PACE stage 链(8→9), 是结构性变化, 超出 patch 范畴 → minor 递增。
依据: 半个多月真实 dogfood 暴露的两个洞(见下), 够格大增量(符合"半月最少 + 结构变化才递增"的版本纪律)。

## 核心: 补 Loop Engineering 的两个差距

dogfood 发现 PACE "写完即止": review/单测只验证"想的问题实现没、单测过没", **不验证实际运行**。
对照 Addy Osmani 的 Loop Engineering(DOER+CHECKER), Athena 的 Memory(.ai_state)和 CHECKER(delivery-gate)已领先, 差距只有两个:
1. **自驱 loop 引擎** — 官方 `/goal`(CC 2.1.139+)已是现成 loop(写→测→debug→re-run + 独立 supervisor), 此前没接进 PACE。
2. **运行时实跑** — PACE 只单测, 不实跑接口/模拟环境/数据。

本版**用官方 /goal 承载, 不自造 loop**(增强不取代), delivery-gate 当它的 CHECKER。

## 新增

- **skill `athena-runtime-verify`(CC+CX)**: impl 后的运行时验证环。用 /goal(CC)/Goals(CX)承载: 实跑接口 + 模拟数据(正常/边界/异常)+ 不同环境 → 自测自改 loop → supervisor 确认 → reflect(写完先自测再想哪里没完善)。System/Refactor 强制, Feature 可选, Bugfix/Quick/Hotfix 跳过。
- **skill `athena-checkpoint`(CC+CX)**: 会话记忆固化。一键 /checkpoint, agent 自己总结本会话增量写进 _index + session-log, 免去手动描述。与 compact hook(兜底)、/compound(跨 sprint 经验)分工。

## 改动

- **CC `subagent-tracker.cjs`**: generator 完成 + stage=impl + checklist 全完成 → 写 `next_action`(System/Refactor=runtime-verify, 其余=review)。软驱动, 不绕门禁。原 subagent-log/roadmap 推进逻辑原样保留。
- **CC `delivery-gate.cjs`** / **CX `delivery-gate.py`**: Refactor/System ship 前验 `runtime-verify.md` 存在且含 `## 测试场景` 段; VALID_STAGES 加 runtime-verify。**exit0 + JSON 协议**(CC)、git diff 现场算文件数(CX)原样保留。
- **PACE stage**: impl → **runtime-verify** → reflect → review(详见 pace/references/stages.md + orchestration.md; 原 INSTALL 引用系死链, v9.9.0 修正)。
- **_index 模板**: 加 `skip_runtime_verify`(默认 false)。
- **铁律**: 加 `[运行时验证]`。

## 关键设计判断(记录, 防回退)

1. **执行者 = CC /goal 主路径, 不默认发 codex**。/goal 是有状态连续 loop + 自带官方 supervisor + 交互式在订阅内; codex exec 每次独立 session 断片、无 supervisor。codex 留 System 密集测试省钱特例(opt-in)。
2. **reflect 做成 runtime-verify Step 4, 不调 brainstorm**。brainstorm 是项目级发散新方向; reflect 是本 sprint 落地完整性自检。混了 reflect 会需求蔓延。
3. **/goal 完成条件必须把实跑证据晒进 transcript**。官方: supervisor 只判断对话里展示的东西, 不读文件。写"接口测过了"无效, 写"运行 X 命令 → 输出 Y"才有效。
4. **运行时实跑用 `$playwright` skill**; CC 可借官方 playwright-skill 插件, CX 用本包注册的 Playwright 测试 skill, browser+computer-use 只作探索/冒烟兜底, 不自造。

## 未含(下一批)
- U1(impl 强制 subagent)/U2(plan min_rounds)/U3(review checklist↔evidence)/U6(plugin 编排): 弱耦合, 单独迭代。
- U5 五五路由(athena-route + executor_weight): 依赖 codex-plugin-cc 内部命令(未掌握), 待命令确认或用 codex exec 基线。

## 验证
所有 hook 过 `node --check` / `py_compile` + 行为冒烟(门禁 exit0+合法JSON 触发、next_action 按 path 分流)。

---

## v9.8.0 整合增补 (本轮, 在原 Loop Engineering 增量包之上)

### Loop Engineering 深化 (借 cobusgreyling/loop-engineering · Osmani 谱系)
- runtime-verify 加 **Step 0 Loop-Readiness 自检** (借 loop-audit): 开环前自评 CHECKER能说no/预算护栏/状态落盘, agent-in-loop 把 check 前移.
- orchestration 加 **loop 失败模式速查** (借 failure-modes): runaway/silent-pass/context-rot/cost-blowout × Athena 对策.

### 软件要素实体 (借 liuzhengdongfortest/CodeStable, 适配 agent-in-loop)
- **requirements/ 逃生通道** (新): skill athena-requirements + .ai_state/requirements/{slug}.md 长效需求档 (WHY, 独立于会演化的 design.md, 弃码重生依据). _index 加 requirements_count + latest_requirement, index-updater 自动维护.
- **issue/ 结构化流程** (新): skill athena-issue, Bugfix 路径升级为 report→(analyze)→fix-note 三件套 (落 sprints/{slug}/). delivery-gate 新增 Bugfix ship 门禁 (验 fix-note.md, 原 Bugfix 零门禁).

### 审计修复 (F1–F9) + 配置
- CC 两新 skill 版本误标 v9.7.5→v9.8.0; 运行时验证铁律折叠进 Review (不占编号膨胀); checkpoint 主动提醒 wiring; CX 原生 SubagentStop 驱动对等; pre-bash-guard py3.12 f-string 兼容性修复; 等.
- CX config.toml 注册全部新 skill (runtime-verify/checkpoint/requirements/issue); CC settings.json 加 curl 等运行时权限; cc/cx 版本号全刷 9.8.0; 新功能 (Goals/workflows/multi-agent/browser) 全开 (Agent Teams experimental 除外).
- 补齐 **skill `playwright`(CC+CX)**: runtime-verify 的前端/E2E 实跑工具, 把 Playwright 官方测试 runner / locator / trace workflow 固化为可复跑证据链; CX config.toml 已注册, CC 与官方 playwright-skill 插件互补.

### 定位 (vs CodeStable)
CodeStable = human in loop and check (人对软件整体把控). 本框架 = **agent in loop and check** (DOER+CHECKER 全自动, 人只在 plan 确认门). 共识: 软件要素 (req/arch/decision) 必须落盘可召回, .ai_state 是落盘根.

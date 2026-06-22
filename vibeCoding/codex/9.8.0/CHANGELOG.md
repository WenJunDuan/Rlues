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
- **PACE stage**: impl → **runtime-verify** → reflect → review(详见 INSTALL B3/B4)。
- **_index 模板**: 加 `skip_runtime_verify`(默认 false)。
- **铁律**: 加 `[运行时验证]`。

## 关键设计判断(记录, 防回退)

1. **执行者 = CC /goal 主路径, 不默认发 codex**。/goal 是有状态连续 loop + 自带官方 supervisor + 交互式在订阅内; codex exec 每次独立 session 断片、无 supervisor。codex 留 System 密集测试省钱特例(opt-in)。
2. **reflect 做成 runtime-verify Step 4, 不调 brainstorm**。brainstorm 是项目级发散新方向; reflect 是本 sprint 落地完整性自检。混了 reflect 会需求蔓延。
3. **/goal 完成条件必须把实跑证据晒进 transcript**。官方: supervisor 只判断对话里展示的东西, 不读文件。写"接口测过了"无效, 写"运行 X 命令 → 输出 Y"才有效。
4. **运行时实跑用已装插件**(playwright-skill / browser+computer-use plugin), 不自造。

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

### 定位 (vs CodeStable)
CodeStable = human in loop and check (人对软件整体把控). 本框架 = **agent in loop and check** (DOER+CHECKER 全自动, 人只在 plan 确认门). 共识: 软件要素 (req/arch/decision) 必须落盘可召回, .ai_state 是落盘根.
